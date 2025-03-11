from enum import StrEnum
from typing import Any

STR_TUPLE_SPLITTER = "^"
ALLOW_UNI_INTERSECT = True


class VarPrefix(StrEnum):
    DataGraph = " "
    EnumerateTarget = "f"
    DbQueryTarget = "A"
    IntersectTarget = "T"
    IntersectCandidate = "C"
    DataVertexSet = "V"

    def __add__(self, other: Any):
        return self.value + STR_TUPLE_SPLITTER + str(other)


if __name__ == "__main__":
    for i, e in enumerate(VarPrefix):
        print(e + i)
