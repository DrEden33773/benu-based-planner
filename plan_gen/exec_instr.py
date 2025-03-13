from dataclasses import dataclass, field
from enum import StrEnum, auto

from plan_gen.common import STR_TUPLE_SPLITTER, VarPrefix


class InstructionType(StrEnum):
    Init = auto()
    """ BENU.INI """

    GetAdj = "get_adj"
    """ BENU.DBQ """

    Intersect = auto()
    """ BENU.INT """

    Foreach = auto()
    """ BENU.ENU """

    TCache = auto()
    """ BENU.TRC """

    Report = auto()
    """ BENU.RES """

    @staticmethod
    def _get_cost_dict():
        return {
            InstructionType.Init: 0,
            InstructionType.GetAdj: 1,
            InstructionType.Intersect: 2,
            InstructionType.Foreach: 3,
            InstructionType.TCache: 4,
            InstructionType.Report: 5,
        }

    def compare(self, other: "InstructionType") -> int:
        """比较两个指令类型的代价 (左 - 右)"""
        return self._get_cost_dict()[self] - self._get_cost_dict()[other]


@dataclass
class ExecInstruction:
    type: InstructionType
    """ 指令类型 """

    target_var: str
    """ 生成变量 """

    vid: str
    """ 模式图顶点 vid """

    extend_eid_list: list[str] = field(default_factory=list)
    """ 模式图扩展边 eid 列表 """

    single_op: str = ""
    """ 输入变量 (单个) """

    multi_ops: list[str] = field(default_factory=list)
    """ 输入变量 (多个) """

    depend_on: list[str] = field(default_factory=list)
    """ 依赖变量 """

    def is_single_op(self) -> bool:
        """是否为 `单输入变量` 操作"""

        return bool(self.single_op)

    def resolve_vid_from_target_var(self):
        """从 `target_var` 解析 vid"""

        if self.target_var == VarPrefix.DataVertexSet:
            return ""
        return self.target_var.split(STR_TUPLE_SPLITTER)[1]

    def resolve_vids_from_multi_ops(self):
        """从 `multi_ops` 解析 vids"""

        vids: list[str] = []
        for op in self.multi_ops:
            if op == VarPrefix.DataVertexSet:
                vids.append("")
            else:
                vids.append(op.split(STR_TUPLE_SPLITTER)[1])
        return vids
