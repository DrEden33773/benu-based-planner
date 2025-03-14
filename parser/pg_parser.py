"""
# pg_parser

`模式图` 解析器.
"""

from functools import lru_cache
from parser.common import AttrType, Edge, Op, ParsingPGError
from typing import Optional, TypedDict

type NullableAttrPG = SerializableAttrPG | dict[str, str]


class SerializableAttrPG(TypedDict):
    attr: str
    op: Op
    value: int | float | str
    type: AttrType


@lru_cache
def attr_pg_to_serializable(attr_pg: Optional["AttrPG"]) -> NullableAttrPG:
    return (
        {
            "attr": attr_pg.attr,
            "op": attr_pg.op,
            "value": attr_pg.r_value,
            "type": attr_pg.r_type,
        }
        if attr_pg
        else {}
    )


class AttrPG:
    attr: str
    op: Op
    r_value: int | float | str
    r_type: AttrType

    def __init__(self, attr: str, raw_pred: str) -> None:
        self.attr = attr

        # Op
        cursor = 0
        raw_op_chars = list[str]()
        while cursor < len(raw_pred) and not (
            raw_pred[cursor].isdigit() or raw_pred[cursor] in ("'", '"')
        ):
            raw_op_chars.append(raw_pred[cursor])
            cursor += 1
        raw_op = "".join(raw_op_chars)
        match raw_op:
            case "=":
                self.op = Op.Eq
            case "<":
                self.op = Op.Lt
            case ">":
                self.op = Op.Gt
            case "!=":
                self.op = Op.Ne
            case "<=":
                self.op = Op.Le
            case ">=":
                self.op = Op.Ge
            case _:
                raise ParsingPGError(f"Invalid operator: {raw_op}")

        # Literal
        match raw_pred[cursor]:
            case c if c.isdigit():
                # Check if we have a float (has decimal point) or integer
                raw_value = raw_pred[cursor:]
                if "." in raw_value:
                    self.r_value = float(raw_value)
                    self.r_type = AttrType.Float
                else:
                    self.r_value = int(raw_value)
                    self.r_type = AttrType.Int
            case c if c == "'" and raw_pred[-1] != "'":
                raise ParsingPGError("Unclosed string literal (missing `'`).")
            case c if c == '"' and raw_pred[-1] != '"':
                raise ParsingPGError('Unclosed string literal (missing `"`).')
            case c if c == "'" or c == '"':
                self.r_value = raw_pred[cursor + 1 : -1]  # remove quotes
                self.r_type = AttrType.String
            case _:
                raise ParsingPGError(f"Unexpected character: {raw_pred[cursor]}")

        # Currently, `string` only support `Eq` and `Ne`.
        if self.r_type == AttrType.String and self.op not in (Op.Eq, Op.Ne):
            raise ParsingPGError(
                f"Invalid operator for string literal: {self.op.name}({self.op})"
            )

    def __repr__(self) -> str:
        displayed_r_value = (
            f"'{self.r_value}'" if self.r_type == AttrType.String else self.r_value
        )
        return f"AttrDesc(attr: '{self.attr}', op: {self.op.name}, r_value: {displayed_r_value}, r_type: {self.r_type})"


@lru_cache(maxsize=128)
def parse_attr_pg(attr: str, raw_pred: str) -> AttrPG:
    return AttrPG(attr, raw_pred)


class ParserPG:
    """Pattern Graph (模式图) 解析器."""

    def __init__(self, src: str):
        self.src = src

        self.v_num = 0
        self.e_num = 0
        self.v_attr_num = 0
        self.e_attr_num = 0

        self.v_labels = dict[str, str]()
        self.e_labels = dict[Edge, str]()
        self.v_attrs = dict[str, AttrPG]()
        self.e_attrs = dict[str, AttrPG]()

        self.vv_to_e = dict[tuple[str, str], Edge]()
        """ Mapping from (start_vid, end_vid) to edge. """

        self.line = 0

    def preview(self):
        HEADER = " Parsing Result "
        print("=" * 10 + HEADER + "=" * 10)

        print("Vertex labels: {")
        for vid, v_label in self.v_labels.items():
            print(f"  {vid}: {v_label},")
        print("}")

        print("Edge labels: {")
        for edge, e_label in self.e_labels.items():
            print(f"  {edge}: {e_label},")
        print("}")

        print("Vertex attributes: {")
        for vid, v_attr in self.v_attrs.items():
            print(f"  {vid}: {v_attr}")
        print("}")

        print("Edge attributes: {")
        for eid, e_attr in self.e_attrs.items():
            print(f"  {eid}: {e_attr}")
        print("}")

        print("=" * (20 + len(HEADER)) + "\n")

    def parse(self):
        lines = self.src.strip().split("\n")
        lines = list(filter(lambda x: x, lines))
        if len(lines) < 1:
            raise ParsingPGError("Missing `N M C1 C2` args.")

        args = lines[0].split()
        if len(args) != 4:
            raise ParsingPGError("Invalid `N M C1 C2` args.")

        self.v_num, self.e_num, self.v_attr_num, self.e_attr_num = map(int, args)
        self.line += 1

        for line in lines[self.line : self.line + self.v_num]:
            args = line.split()
            if len(args) != 2:
                raise ParsingPGError("Invalid `(vid, v_label)` pair.")
            vid, v_label = args
            self.v_labels[vid] = v_label
        self.line += self.v_num

        for line in lines[self.line : self.line + self.e_num]:
            args = line.split()
            if len(args) != 4:
                raise ParsingPGError(
                    "Invalid `[eid, start_vid, end_vid, e_label]` tuple."
                )
            eid, start_vid, end_vid, e_label = args
            edge = Edge(eid, start_vid, end_vid)
            self.e_labels[edge] = e_label
            # if (e := self.vv_to_e.get((start_vid, end_vid))) and e != edge:
            #     raise ParsingPGError(
            #         f"Duplicate edge from `{start_vid}` to `{end_vid}`."
            #     )
            self.vv_to_e[(start_vid, end_vid)] = edge
        self.line += self.e_num

        for line in lines[self.line : self.line + self.v_attr_num]:
            args = line.split()
            if len(args) < 3:
                raise ParsingPGError("Invalid `[vid, attr, pred]` tuple.")
            vid, attr, splitted_pred = args[0], args[1], args[2:]
            raw_pred = "".join(splitted_pred)
            try:
                self.v_attrs[vid] = parse_attr_pg(attr, raw_pred)
            except ParsingPGError as e:
                raise e
        self.line += self.v_attr_num

        for line in lines[self.line : self.line + self.e_attr_num]:
            args = line.split()
            if len(args) < 3:
                raise ParsingPGError("Invalid `[eid, attr, pred]` tuple.")
            eid, attr, splitted_pred = args[0], args[1], args[2:]
            raw_pred = "".join(splitted_pred)
            try:
                self.e_attrs[eid] = parse_attr_pg(attr, raw_pred)
            except ParsingPGError as e:
                raise e
        self.line += self.e_attr_num
