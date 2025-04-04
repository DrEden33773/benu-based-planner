from plan_gen.common import VarPrefix
from plan_gen.exec_instr import ExecInstruction, InstructionType
from plan_gen.plan_generator import PlanGenerator
from utils.apriori import Apriori


class PlanOptimizer:
    def __init__(self, plan_generator: PlanGenerator) -> None:
        self.plan_generator = plan_generator
        self.exec_plan = plan_generator.exec_plan
        self.pg = plan_generator.pg

        self.Ti = 0

    def apply_optimization(self):
        if not self.exec_plan:
            return

        # 1. 移除 `公共子表达式`
        self._eliminate_cse()

        # 2. 展开所有指令 (multi_ops 最多只有两个 operands)
        self._flatten()

        # 3. 指令重排序
        self._reorder()

        # 4. `三角形` 模式缓存
        # TODO: 尚未完全实现, 暂时禁用
        # self._triangle_cache()

    def _triangle_cache(self):
        """`三角形` 模式缓存"""

        start_vid = ""
        indices: list[int] = []
        loop_level = 0
        t_cache_loop_level = 0

        for i, instr in enumerate(self.exec_plan):
            match instr.type:
                case InstructionType.Init:
                    start_vid = instr.resolve_vid_from_target_var()
                case InstructionType.Foreach:
                    loop_level += 1
                case InstructionType.Intersect if not instr.is_single_op():
                    op1, op2 = instr.multi_ops
                    if op1.startswith(VarPrefix.DbQueryTarget) and op2.startswith(
                        VarPrefix.DbQueryTarget
                    ):
                        # X <- Intersect(Ai, Aj)
                        vid1, vid2 = instr.resolve_vids_from_multi_ops()
                        if (vid1 == start_vid and vid2 in self.pg.get_adj_v(vid1)) or (
                            vid2 == start_vid and vid1 in self.pg.get_adj_v(vid2)
                        ):
                            indices.append(i)
                            t_cache_loop_level = loop_level
                case _:
                    pass

        if len(indices) > 1 or t_cache_loop_level > 1:
            for idx in indices:
                instr = self.exec_plan[idx]
                vid1, vid2 = instr.resolve_vids_from_multi_ops()
                new_ops = [
                    VarPrefix.DbQueryTarget + vid1,
                    VarPrefix.DbQueryTarget + vid2,
                ]
                new_ops += instr.multi_ops
                instr.multi_ops = new_ops
                instr.type = InstructionType.TCache

        print("    [Triangle Cache ... Done]")

    def _reorder(self):
        """指令重排序"""

        exec_plan = self.exec_plan
        self.plan_generator.compute_exec_plan_dependencies(exec_plan)  # redundant

        certain_set: set[str] = {exec_plan[0].target_var}

        for i in range(1, len(exec_plan)):
            candidates: list[int] = []

            # 1. 找到所有依赖于 certain_set 的指令
            for j in range(i, len(exec_plan)):
                if exec_plan[j].target_var in certain_set:
                    candidates.append(j)

            # 2. 选择代价最小的指令
            instr_pos = -1
            if candidates:
                instr_pos = candidates[0]
                if len(candidates) > 1:
                    for idx in candidates[1:]:
                        if exec_plan[idx].type.compare(exec_plan[instr_pos].type) < 0:
                            instr_pos = idx

            # 3. 移动
            if instr_pos > 0:
                certain_set.add(exec_plan[instr_pos].target_var)
                exec_plan[i], exec_plan[instr_pos] = exec_plan[instr_pos], exec_plan[i]
            certain_set.add(exec_plan[i].target_var)

        print("    [Reorder Instructions ... Done]")

    def _flatten(self):
        """展开所有指令 (multi_ops 最多只有 2 个 operands)"""

        exec_plan = self.exec_plan
        instr_idx: list[int] = []
        defined_vars: list[str] = []

        for idx, instr in enumerate(exec_plan):
            defined_vars.append(instr.target_var)
            if instr.type == InstructionType.Intersect and len(instr.multi_ops) > 2:
                instr_idx.append(idx)

        offset = 0
        for idx in instr_idx:
            # pos 应该是 instr 位置的前一个, 因为 add 和 remove 操作会改变位置
            pos = idx + offset - 1
            operators = [
                op for op in exec_plan[pos + 1].multi_ops if op in defined_vars
            ]  # similar to: retainAll

            while len(operators) > 2:
                op1, op2 = operators.pop(), operators.pop()
                new_operators = [op1, op2]
                operators.remove(op1)
                operators.remove(op2)
                self.Ti += 1
                operators.insert(0, VarPrefix.IntersectTarget + f"@{self.Ti}")
                old_instr = exec_plan[pos + 1]
                new_instr = ExecInstruction(
                    vid=old_instr.vid,
                    type=InstructionType.Intersect,
                    multi_ops=new_operators,
                    target_var=VarPrefix.IntersectTarget + f"@{self.Ti}",
                )
                pos += 1
                exec_plan.insert(pos, new_instr)
                offset += 1

            new_operators = list(operators)
            pos += 1
            exec_plan[pos].multi_ops = new_operators

        print("    [Flatten Instructions ... Done]")

    def _eliminate_cse(self):
        """移除 `公共子表达式`"""
        exec_plan = self.exec_plan

        while True:
            data_list: list[set[str]] = []
            instr_idx: list[int] = []
            int_ops_pos: dict[str, int] = {}

            # 1. 找到所有的 `INT` 操作
            for idx, instr in enumerate(exec_plan):
                if instr.type == InstructionType.GetAdj:
                    int_ops_pos[instr.target_var] = idx
                elif (
                    instr.type == InstructionType.Intersect and not instr.is_single_op()
                ):
                    int_ops_pos[instr.target_var] = idx

                    operands = set(instr.multi_ops)
                    data_list.append(operands)
                    instr_idx.append(idx)

            # 2. 使用 Apriori 找到 `频繁项集` (support >= 2)
            apriori = Apriori(data_list=data_list, min_support=2)
            freq_set = apriori.gen_max_size_freq_set()

            # 3. 找到 `最大频繁项集` (support 最大)
            max_freq_set: frozenset[str] = frozenset()
            max_freq_set_size = 0
            max_freq_support = 0
            for k, v in freq_set.items():
                if v > max_freq_support:
                    max_freq_support = v
                    max_freq_set = k
                    max_freq_set_size = len(k)
                elif v == max_freq_support:
                    l1 = sorted([int_ops_pos[var] for var in max_freq_set])
                    l2 = sorted([int_ops_pos[var] for var in k])
                    for e1, e2 in zip(l1, l2):
                        if e1 > e2:
                            max_freq_support = v
                            max_freq_set = k
                            max_freq_set_size = len(k)

            # 4. 消除 `公共子表达式`
            if max_freq_set_size >= 2:
                self.Ti += 1
                flag = True  # freq-item-set 第一次出现, 则为 True

                for i, operands in enumerate(data_list):
                    if max_freq_set <= operands:
                        operands.add(VarPrefix.IntersectTarget + self.Ti)
                        operands -= max_freq_set
                        if flag:
                            operators = list(max_freq_set)
                            operators.sort(key=lambda s: int_ops_pos[s])
                            old_instr = exec_plan[instr_idx[i]]
                            new_instr = ExecInstruction(
                                vid=old_instr.vid,
                                type=InstructionType.Intersect,
                                target_var=VarPrefix.IntersectTarget + self.Ti,
                                multi_ops=operators,
                            )
                            exec_plan.insert(instr_idx[i], new_instr)
                            flag = False
                        if len(operands) > 1:
                            exec_plan[instr_idx[i] + 1].multi_ops = list(operands)
                        else:
                            exec_plan[
                                instr_idx[i] + 1
                            ].single_op = operands.copy().pop()
            else:
                break

        # 5. 消除 `单操作数` 的 `INT` 操作
        # (e.g. `X <- Intersect(Y)`)
        self.plan_generator.elimination_uni_operand(exec_plan)

        print("    [Eliminate Common Subexpressions ... Done]")
