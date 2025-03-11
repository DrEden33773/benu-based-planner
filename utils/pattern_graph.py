from dataclasses import dataclass, field
from parser.common import Edge
from parser.pg_parser import AttrPG


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

    vv_to_e: dict[tuple[str, str], Edge] = field(default_factory=dict)
    """ `(from_vid, to_vid)` -> `edge` """

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
            self.vv_to_e[(edge.from_vid, edge.to_vid)] = edge

    def get_adj_v(self, vid: str):
        """获取顶点 vid 的邻接顶点集合"""

        adj_v = set[str]()
        for from_vid, to_vid in self.vv_to_e:
            if from_vid == vid:
                adj_v.add(to_vid)
            elif to_vid == vid:
                adj_v.add(from_vid)
        return adj_v

    def get_adj_e(self, vid: str):
        """获取顶点 vid 的邻接边集合"""

        adj_e = set[Edge]()
        for from_vid, to_vid in self.vv_to_e:
            if from_vid == vid or to_vid == vid:
                adj_e.add(self.vv_to_e[(from_vid, to_vid)])
        return adj_e

    def get_out_degree(self, vid: str):
        """获取顶点 vid 的出度"""

        return sum(1 for start, _ in self.vv_to_e if start == vid)

    def get_in_degree(self, vid: str):
        """获取顶点 vid 的入度"""

        return sum(1 for _, end in self.vv_to_e if end == vid)

    def get_all_vertices(self):
        """获取所有顶点集合"""

        return self.v_labels.keys()

    def get_v_constraint(self, vid: str):
        """获取顶点 vid 的标签和属性"""

        return self.v_labels[vid], self.v_attrs[vid]

    def get_e_constraint_from_edge(self, edge: Edge):
        """获取边 edge 的标签和属性"""

        return self.e_labels[edge], self.e_attrs[edge.eid]

    def get_e_constraint_from_vids(self, from_vid: str, to_vid: str):
        """获取边 (from_vid, to_vid) 的标签和属性"""

        edge = self.vv_to_e[(from_vid, to_vid)]
        return self.e_labels[edge], self.e_attrs[edge.eid]

    def get_adj_e_constraints(self, vid: str):
        """获取顶点 vid 的邻接边的标签和属性"""

        adj_e_constraints = dict[str, tuple[str, AttrPG]]()
        for from_vid, to_vid in self.vv_to_e:
            if vid in (from_vid, to_vid):
                edge = self.vv_to_e[(from_vid, to_vid)]
                adj_e_constraints[edge.eid] = self.get_e_constraint_from_edge(edge)
        return adj_e_constraints
