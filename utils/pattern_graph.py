from dataclasses import dataclass, field
from typing import Optional

from parser.common import Edge
from parser.pg_parser import AttrPG, SerializableAttrPG, attr_pg_to_serializable

type AttrInfo = Optional[SerializableAttrPG]

type VertexInfo = tuple[str, AttrInfo]
""" ### 标签, (属性) """
type EdgeInfo = tuple[str, str, str, AttrInfo]
""" ### 起点 vid, 终点 vid, 标签, (属性) """


type VertexInfoDict = dict[str, VertexInfo]
type EdgeInfoDict = dict[str, EdgeInfo]


@dataclass
class PatternGraph:
    """
    模式图 (多重有向图)

    - 类似 networkx.MultiDiGraph
    """

    v_labels: dict[str, str]
    """ `vid` -> `v_label` """
    e_labels: dict[Edge, str]
    """ `edge` -> `e_label` """

    v_attrs: dict[str, AttrPG]
    """ `vid` -> `v_attr` """
    e_attrs: dict[str, AttrPG]
    """ `eid` -> `e_attr` """

    vv_to_es: dict[tuple[str, str], list[Edge]] = field(default_factory=dict)
    """ `(from_vid, to_vid)` -> `[edges]` """

    v_num = 0
    e_num = 0
    v_attr_num = 0
    e_attr_num = 0

    def __post_init__(self):
        self.v_num = len(self.v_labels)
        self.e_num = len(self.e_labels)
        self.v_attr_num = len(self.v_attrs)
        self.e_attr_num = len(self.e_attrs)
        for edge in self.e_labels:
            from_vid, to_vid = edge.from_vid, edge.to_vid
            self.vv_to_es.setdefault((from_vid, to_vid), []).append(edge)

    def get_adj_v(self, vid: str):
        """
        获取顶点 vid 的邻接顶点集合

        - 连接 `邻接顶点 adj_vid` 和 `顶点 vid` 的边, 方向不限
        """

        adj_v = set[str]()
        for from_vid, to_vid in self.vv_to_es:
            if from_vid == vid:
                adj_v.add(to_vid)
            elif to_vid == vid:
                adj_v.add(from_vid)
        return adj_v

    def get_adj_e(self, vid: str):
        """
        获取顶点 vid 的邻接边集合

        - 邻接边, 可以是 vid 的 `出边` 或 `入边`
        """

        adj_e = set[Edge]()
        for from_vid, to_vid in self.vv_to_es:
            if from_vid == vid or to_vid == vid:
                adj_e.update(self.vv_to_es[(from_vid, to_vid)])
        return adj_e

    def get_out_degree(self, vid: str):
        """获取顶点 vid 的出度"""

        return sum(
            len(edges) for (start, _end), edges in self.vv_to_es.items() if start == vid
        )

    def get_in_degree(self, vid: str):
        """获取顶点 vid 的入度"""

        return sum(
            len(edges) for (_start, end), edges in self.vv_to_es.items() if end == vid
        )

    def get_all_vertices(self):
        """获取所有顶点集合"""

        return self.v_labels.keys()

    def get_v_info(self, vid: str) -> VertexInfo:
        """
        获取顶点 vid 的:

        - 标签
        - 属性
        """

        return self.v_labels[vid], attr_pg_to_serializable(self.v_attrs.get(vid))

    def get_all_v_info(self) -> VertexInfoDict:
        """
        获取所有顶点的:

        - vid
        - 标签
        - 属性
        """

        return {vid: self.get_v_info(vid) for vid in self.v_labels}

    def get_e_info(self, edge: Edge) -> EdgeInfo:
        """
        获取边 edge 的:

        - 起点 vid
        - 终点 vid
        - 标签
        - 属性
        """

        return (
            edge.from_vid,
            edge.to_vid,
            self.e_labels[edge],
            attr_pg_to_serializable(self.e_attrs.get(edge.eid)),
        )

    def get_adj_e_info(self, vid: str) -> EdgeInfoDict:
        """
        获取顶点 vid 所有邻接边的:

        - eid
        - 起点 vid
        - 终点 vid
        - 标签
        - 属性

        (邻接边 `不限制` 方向)
        """

        return {edge.eid: self.get_e_info(edge) for edge in self.get_adj_e(vid)}

    def get_all_e_info(self) -> EdgeInfoDict:
        """
        获取所有边的:

        - eid
        - 起点 vid
        - 终点 vid
        - 标签
        - 属性
        """

        return {edge.eid: self.get_e_info(edge) for edge in self.e_labels}
