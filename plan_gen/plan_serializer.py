import json
from typing import Optional, TypedDict

from plan_gen.exec_instr import ExecInstruction, InstructionType
from plan_gen.plan_generator import PlanGenerator
from utils.pattern_graph import EdgeInfoDict, VertexInfoDict


class DisplayedInstr(TypedDict):
    vid: str
    type: InstructionType
    expand_eid_list: list[str]
    single_op: Optional[str]
    multi_ops: list[str]
    target_var: str
    depend_on: list[str]


def to_displayed_instr(exec_instr: ExecInstruction) -> DisplayedInstr:
    # 对 list 排序, 确保每次生成的指令 `相同` 且 `可预测`
    return {
        "vid": exec_instr.vid,
        "type": exec_instr.type,
        "expand_eid_list": sorted(exec_instr.extend_eid_list),
        "single_op": exec_instr.single_op,
        "multi_ops": sorted(exec_instr.multi_ops),
        "target_var": exec_instr.target_var,
        "depend_on": sorted(exec_instr.depend_on),
    }


class PlanDict(TypedDict):
    matching_order: list[str]
    vertices: VertexInfoDict
    edges: EdgeInfoDict
    instructions: list[DisplayedInstr]


class PlanSerializer:
    def __init__(self, plan_generator: PlanGenerator) -> None:
        self.plan_generator = plan_generator
        self.matching_order = plan_generator.matching_order
        self.exec_plan = plan_generator.exec_plan
        self.pg = plan_generator.pg

    def serialize_json(self) -> str:
        """生成执行计划的 JSON 文本"""

        plan_dict: PlanDict = {
            "matching_order": self.matching_order,
            "vertices": self.pg.get_all_v_info(),
            "edges": self.pg.get_all_e_info(),
            "instructions": [to_displayed_instr(instr) for instr in self.exec_plan],
        }

        return json.dumps(plan_dict, indent=2)
