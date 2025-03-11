from dataclasses import dataclass, field
from enum import StrEnum, auto
from parser.pg_parser import AttrPG


class InstructionType(StrEnum):
    Init = auto()
    """ BENU.INI """

    GetAdj = auto()
    """ BENU.DBQ """

    Intersect = auto()
    """ BENU.INT """

    Foreach = auto()
    """ BENU.ENU """

    TCache = auto()
    """ BENU.TRC """

    Report = auto()
    """ BENU.RES """


@dataclass
class ExecInstruction:
    type: InstructionType
    """ 指令类型 """
    target_var: str
    """ 生成变量 """

    single_op: str = ""
    """ 输入变量 (单个) """
    multi_ops: list[str] = field(default_factory=list)
    """ 输入变量 (多个) """

    v_constraint: dict[str, AttrPG] = field(default_factory=dict)
    """
    顶点约束
    
    - `key`: `v_label`
    - `value`: `v_attr`
    """

    expand_e_constraint: dict[str, tuple[str, AttrPG]] = field(default_factory=dict)
    """
    扩展边约束
    
    - `key`: `eid`
    - `value`: (`e_label`, `e_attr`)
    """

    depend_on: list[str] = field(default_factory=list)
    """ 依赖变量 """

    def is_single_op(self) -> bool:
        return bool(self.single_op)
