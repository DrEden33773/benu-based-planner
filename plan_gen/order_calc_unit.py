from plan_gen.exec_instr import ExecInstruction
from plan_gen.plan_generator import PlanGenerator

raise NotImplementedError("`OrderCalcUnit` is not implemented.")


class OrderCalcUnit:
    def __init__(self, plan_generator: PlanGenerator) -> None:
        self.plan_generator = plan_generator
        self.exec_plan = plan_generator.exec_plan
        self.pg = plan_generator.pg
        self.matching_order_pairs = plan_generator.matching_order_pairs
        self.matching_order = plan_generator.matching_order

        self.db_cost = -1
        self.optimal_db_matching_order: list[list[int]] = []
        self.optimal_computational_exec_plan: list[list[ExecInstruction]] = []

        self.equivalent_vertices: list[list[str]] = []
        self.matched_adj: list[str] = ["" for _ in range(self.pg.v_num)]
        self.matched_v: list[str] = []
        self.estimated_cost: list[int] = []

    def generate_optimal_order(self):
        """生成最优顺序"""

        self._calc_equivalent_vertices()

        # TODO

    def _calc_equivalent_vertices(self):
        """构建等价点集"""

        vertices = self.matching_order
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

        self.equivalent_vertices = equivalent_vertices
