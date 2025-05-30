from parser.common import Op
from parser.pg_parser import ParserPG
from plan_gen.common import VarPrefix
from plan_gen.exec_instr import ExecInstruction, InstructionType
from planner_profile import ALLOW_UNI_INTERSECT
from utils.pattern_graph import PatternGraph


class PlanGenerator:
    def __init__(self, pg_parser: ParserPG) -> None:
        self.pg = PatternGraph(
            v_labels=pg_parser.v_labels,
            e_labels=pg_parser.e_labels,
            v_attrs=pg_parser.v_attrs,
            e_attrs=pg_parser.e_attrs,
        )
        """ `模式图` (`Pattern Graph`, aka. `pg`) """

        self.matching_order: list[str] = []
        """ 顶点匹配顺序 """
        self.matching_order_pairs: list[tuple[str, str]] = []
        """ 顶点匹配顺序 (带标签) """
        self.vertex_metrics: dict[str, float] = {}
        """ 顶点 `选择性与度数` 评分 """

        self.exec_plan: list[ExecInstruction] = []
        """ 最终执行计划 """

    def generate_optimal_plan(self, O3: bool = True):
        """生成最优执行计划"""

        if self.pg.v_num == 0:
            return

        self._compute_vertex_metrics()
        self._determine_matching_order_on_metrics()

        self._generate_raw_plan()
        if O3:
            self._apply_optimization()

    def dump_plan_to_json_file(self, file_path: str) -> None:
        """将执行计划转储到 JSON 文件"""
        json_plan = self.generate_json_exec_plan()

        if not file_path.endswith(".json"):
            file_path += ".json"

        with open(file_path, "w") as file:
            file.write(json_plan)

        print(f'  Plan saved to "{file_path.replace("\\", "/")}"')

    def generate_json_exec_plan(self):
        """生成执行计划的 JSON 文本"""

        from plan_gen.plan_serializer import PlanSerializer

        return PlanSerializer(self).serialize_json()

    def _apply_optimization(self):
        """应用优化策略"""
        if not self.exec_plan:
            return

        from plan_gen.plan_optimizer import PlanOptimizer

        PlanOptimizer(self).apply_optimization()

    def _generate_raw_plan(self):
        """生成原始执行计划 (无优化, 按照给定顺序)"""
        ordered = self.matching_order
        if not ordered:
            return

        exec_plan: list[ExecInstruction] = []
        f_set = set[str]()

        # 第一个点
        vid = ordered[0]
        all_adj_eid = [e.eid for e in self.pg.get_adj_e(vid)]
        # Init (直接在这里加上 `点约束`)
        exec_plan.append(
            ExecInstruction(
                vid=vid,
                type=InstructionType.Init,
                single_op=None,
                target_var=VarPrefix.EnumerateTarget + vid,
            )
        )
        # GetAdj
        exec_plan.append(
            ExecInstruction(
                vid=vid,
                type=InstructionType.GetAdj,
                single_op=VarPrefix.EnumerateTarget + vid,
                target_var=VarPrefix.DbQueryTarget + vid,
                extend_eid_list=all_adj_eid,
            )
        )
        f_set.add(vid)

        # 后续点
        for vid in ordered[1:]:
            operands = set(f_set)
            operands &= self.pg.get_adj_v(vid)

            # (load constraints)
            all_adj_eid = [e.eid for e in self.pg.get_adj_e(vid)]

            # Intersect (这一步就加上 `对 scope 进行 点约束`)
            if not operands:
                # fi = {}, 没有邻接集

                # 感觉这里 BENU 的处理不合适, 直接用 Init 指令就行
                exec_plan.append(
                    ExecInstruction(
                        vid=vid,
                        type=InstructionType.Init,
                        single_op=None,
                        target_var=VarPrefix.EnumerateTarget + vid,
                    )
                )
            elif len(operands) == 1:
                # Ci = {Ax}
                exec_plan.append(
                    ExecInstruction(
                        vid=vid,
                        type=InstructionType.Intersect,
                        single_op=VarPrefix.DbQueryTarget + operands.copy().pop(),
                        target_var=VarPrefix.IntersectCandidate + vid,
                    )
                )
            else:
                # Ti = {Aw, Ax, ..., Ay, Az}
                multi_ops = [VarPrefix.DbQueryTarget + op for op in operands]
                exec_plan.append(
                    ExecInstruction(
                        vid=vid,
                        type=InstructionType.Intersect,
                        multi_ops=multi_ops,
                        target_var=VarPrefix.IntersectTarget + vid,
                    )
                )
                exec_plan.append(
                    ExecInstruction(
                        vid=vid,
                        type=InstructionType.Intersect,
                        single_op=VarPrefix.IntersectTarget + vid,
                        target_var=VarPrefix.IntersectCandidate + vid,
                    )
                )

            # Foreach (只有 operands 非空时才需要, operands 为空 => 前驱指令就是 Init)
            if operands:
                exec_plan.append(
                    ExecInstruction(
                        vid=vid,
                        type=InstructionType.Foreach,
                        single_op=VarPrefix.IntersectCandidate + vid,
                        target_var=VarPrefix.EnumerateTarget + vid,
                    )
                )
            # GetAdj (加上 `扩展边约束`)
            exec_plan.append(
                ExecInstruction(
                    vid=vid,
                    type=InstructionType.GetAdj,
                    single_op=VarPrefix.EnumerateTarget + vid,
                    target_var=VarPrefix.DbQueryTarget + vid,
                    extend_eid_list=all_adj_eid,
                )
            )
            f_set.add(vid)

        # Report
        embedding = [VarPrefix.EnumerateTarget + fid for fid in f_set]
        exec_plan.append(
            ExecInstruction(
                vid="",
                type=InstructionType.Report,
                multi_ops=embedding,
                target_var=VarPrefix.EnumerateTarget,
            )
        )

        self.compute_exec_plan_dependencies(exec_plan)
        self._remove_unused_dbq(exec_plan)
        self.elimination_uni_operand(exec_plan)

        self.exec_plan = exec_plan

    def compute_exec_plan_dependencies(self, exec_plan: list[ExecInstruction]):
        """构建执行计划的依赖关系"""

        depend_record: dict[str, set[str]] = {}
        """ `vid` -> `depend_set` """

        for instr in exec_plan:
            depend_set = set[str]()
            if instr.single_op:
                op = instr.single_op
                if op != VarPrefix.DataVertexSet:
                    depend_set.add(op)
                if op in depend_record:
                    depend_set.update(depend_record[op])
            else:
                depend_set.update(instr.multi_ops)
                for op in instr.multi_ops:
                    if op in depend_record:
                        depend_set.update(depend_record[op])
            depend_record[instr.target_var] = depend_set
            instr.depend_on = list(depend_set)

    def _remove_unused_dbq(self, exec_plan: list[ExecInstruction]):
        """移除未使用的 DBQ (GetAdj) 操作"""
        depend_set = set[str]()
        for instr in exec_plan:
            if instr.single_op:
                depend_set.add(instr.single_op)
            else:
                depend_set.update(instr.multi_ops)

        new_exec_plan: list[ExecInstruction] = []
        for instr in exec_plan:
            if (
                instr.type == InstructionType.GetAdj
                and instr.target_var not in depend_set
            ):
                continue
            new_exec_plan.append(instr)

        del exec_plan[:]
        exec_plan.extend(new_exec_plan)

    def elimination_uni_operand(self, exec_plan: list[ExecInstruction]):
        """
        消除单操作数的交集操作

        - 仅当 common.ALLOW_UNI_INTERSECT 为 `False` 时有效
        """

        new_exec_plan: list[ExecInstruction] = []
        record: dict[str, str] = {}

        for instr in exec_plan:
            if instr.type in (InstructionType.Init, InstructionType.Report):
                # Init 和 Report 操作不需要处理
                new_exec_plan.append(instr)
                continue

            if instr.type == InstructionType.Intersect and instr.single_op:
                if not ALLOW_UNI_INTERSECT and instr.target_var.startswith(
                    VarPrefix.IntersectTarget
                ):
                    record[instr.target_var] = instr.single_op
                    continue

            # 替换掉 `对应指令被移除` 的操作数
            if instr.is_single_op():
                if instr.single_op in record:
                    instr.single_op = record[instr.single_op]
            else:
                temp_ops = list(instr.multi_ops)
                for op in instr.multi_ops:
                    if op in record:
                        temp_ops.append(record[op])
                        temp_ops.remove(op)
                instr.multi_ops = temp_ops
            new_exec_plan.append(instr)

    def _compute_vertex_metrics(self):
        """综合评估顶点选择性和连接性"""

        def is_bridge_vertex(vid: str) -> bool:
            """检测顶点是否是连接多个分支的关键节点"""
            neighbors = self.pg.get_adj_v(vid)
            return len(neighbors) >= 3

        for vid in self.pg.v_labels:
            score = 0.0

            # 1. 属性过滤选择性
            if vid in self.pg.v_attrs:
                attr_desc = self.pg.v_attrs[vid]
                if attr_desc.op in (Op.Eq, Op.Ne):
                    score += 100  # 等值过滤最高优先级 (也包括 `不等值`)
                else:
                    score += 50  # 数值范围过滤

            # 2. 连接性评估 (GOpt 的星型模式检测)
            in_degree = self.pg.get_in_degree(vid)
            out_degree = self.pg.get_out_degree(vid)
            score += 20 * (in_degree + out_degree)  # 高度数顶点优先

            # 3. 路径中心性 (BENU 的桥接顶点优先)
            if is_bridge_vertex(vid):
                score += 150

            self.vertex_metrics[vid] = score

    def _determine_matching_order_on_metrics(self):
        """构建顶点匹配顺序 (基于顶点评分)"""
        self.matching_order = sorted(
            self.pg.get_all_vertices(),
            key=lambda vid: self.vertex_metrics[vid],
            reverse=True,
        )
        self.matching_order_pairs = [
            (vid, self.pg.v_labels[vid]) for vid in self.matching_order
        ]

    def _calc_equivalent_vertices(self) -> list[list[str]]:
        """构建等价点集"""

        vertices = map(lambda x: x[0], self.matching_order_pairs)
        equivalent_vertices: list[list[str]] = []
        for v_curr in vertices:
            flag = True
            if equivalent_vertices:
                for ev in equivalent_vertices:
                    v_prev = ev[0]
                    adj_curr, adj_prev = (
                        self.pg.get_adj_v(v_curr),
                        self.pg.get_adj_v(v_prev),
                    )
                    adj_curr.remove(v_prev)
                    adj_prev.remove(v_curr)
                    if adj_curr == adj_prev:
                        ev.append(v_curr)
                        flag = False
                        break
            if flag:
                equivalent_vertices.append([v_curr])
        return equivalent_vertices
