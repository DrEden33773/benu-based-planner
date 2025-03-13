from enum import StrEnum
from typing import Any

from planner_profile import STR_TUPLE_SPLITTER


class VarPrefix(StrEnum):
    DataGraph = " "
    EnumerateTarget = "f"
    DbQueryTarget = "A"
    IntersectTarget = "T"
    IntersectCandidate = "C"
    DataVertexSet = "V"

    def __add__(self, other: Any):
        return self.value + STR_TUPLE_SPLITTER + str(other)
