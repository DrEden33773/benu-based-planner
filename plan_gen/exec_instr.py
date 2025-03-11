from dataclasses import dataclass, field
from enum import StrEnum, auto
from functools import lru_cache
from parser.common import AttrType, Op
from parser.pg_parser import AttrPG
from typing import Any, TypedDict


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


class Attr(TypedDict):
    attr: str
    op: Op
    value: int | str
    type: AttrType


@lru_cache
def attr_pg_to_dict(attr_pg: AttrPG) -> Attr:
    return {
        "attr": attr_pg.attr,
        "op": attr_pg.op,
        "value": attr_pg.r_value,
        "type": attr_pg.r_type,
    }


@dataclass
class ExecInstruction:
    scope: str
    """ 作用域 (仅 DEBUG 使用, 追踪当前匹配进行到了哪个 vid) """

    type: InstructionType
    """ 指令类型 """
    target_var: str
    """ 生成变量 """

    single_op: str = ""
    """ 输入变量 (单个) """
    multi_ops: list[str] = field(default_factory=list)
    """ 输入变量 (多个) """

    v_constraint: dict[str, Attr | dict[str, Any]] = field(default_factory=dict)
    """
    顶点约束
    
    - `key`: `v_label`
    - `value`: `v_attr`
    """

    expand_e_constraint: dict[str, tuple[str, Attr | dict[str, Any]]] = field(
        default_factory=dict
    )
    """
    扩展边约束
    
    - `key`: `eid`
    - `value`: (`e_label`, `e_attr`)
    """

    depend_on: list[str] = field(default_factory=list)
    """ 依赖变量 """

    def is_single_op(self) -> bool:
        return bool(self.single_op)
