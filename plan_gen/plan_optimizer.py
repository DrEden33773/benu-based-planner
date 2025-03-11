from plan_gen.plan_generator import PlanGenerator


class PlanOptimizer:
    def __init__(self, plan_generator: PlanGenerator) -> None:
        self.plan_generator = plan_generator
