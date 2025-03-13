import json
from parser.common import AttrType, Op
from typing import TypedDict

from plan_gen.exec_instr import ExecInstruction, InstructionType
from plan_gen.plan_generator import PlanGenerator
from utils.pattern_graph import EdgeInfoDict, VertexInfoDict


class Attr(TypedDict):
    attr: str
    op: Op
    value: int | str
    type: AttrType


class Vertex(TypedDict):
    vid: str
    label: str
    attrs: list[Attr]


class Edge(TypedDict):
    eid: str
    src_vid: str
    dst_vid: str
    label: str
    attrs: list[Attr]


class DisplayedInstr(TypedDict):
    type: InstructionType
    single_op: str
    multi_ops: list[str]
    target_var: str
    vid: str
    expand_eid_list: list[str]


def to_displayed_instr(exec_instr: ExecInstruction) -> DisplayedInstr:
    return {
        "type": exec_instr.type,
        "single_op": exec_instr.single_op,
        "multi_ops": exec_instr.multi_ops,
        "target_var": exec_instr.target_var,
        "vid": exec_instr.vid,
        "expand_eid_list": exec_instr.extend_eid_list,
    }


class PlanDict(TypedDict):
    matchingOrder: list[str]
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
            "matchingOrder": self.matching_order,
            "vertices": self.pg.get_all_v_info(),
            "edges": self.pg.get_all_e_info(),
            "instructions": [to_displayed_instr(instr) for instr in self.exec_plan],
        }

        return json.dumps(plan_dict, indent=2)
