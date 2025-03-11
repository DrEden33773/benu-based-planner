from dataclasses import dataclass
from enum import StrEnum


class ParsingPGError(RuntimeError):
    pass


class Op(StrEnum):
    Eq = "="
    Ne = "!="
    Gt = ">"
    Ge = ">="
    Lt = "<"
    Le = "<="


class AttrType(StrEnum):
    Int = "int"
    String = "string"


@dataclass
class Edge:
    eid: str
    from_vid: str
    to_vid: str

    def __hash__(self):
        return hash(self.eid)

    def __repr__(self) -> str:
        return f"Edge(id='{self.eid}', '{self.from_vid}'->'{self.to_vid}')"
