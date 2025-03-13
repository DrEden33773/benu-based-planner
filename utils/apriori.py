from dataclasses import dataclass, field


@dataclass
class Apriori:
    """Apriori algorithm for frequent item-set mining."""

    data_list: list[set[str]] = field(default_factory=list)
    min_support: int = 2

    def gen_max_size_freq_set(self):
        max_freq_set: dict[frozenset[str], int] = {}
        c1 = self.find_candidates_1()
        temp_freq_set = self.find_freq_set(c1)

        while temp_freq_set:
            max_freq_set = temp_freq_set
            Ck = self.apriori_gen(list(max_freq_set.keys()))
            temp_freq_set = self.find_freq_set(Ck)

        return max_freq_set

    def apriori_gen(self, Lk: list[frozenset[str]]):
        """
        `L_{k} -> C_{k + 1}`

        - join `l1` and `l2` for each item in `L_{k}`
        - then generate `C_{k + 1}`
        """

        Ck: list[frozenset[str]] = []

        for i, s1 in enumerate(Lk):
            s1_size = len(s1)
            for s2 in Lk[i + 1 :]:
                s_temp = s1.union(s2)
                if len(s_temp) == s1_size + 1 and s_temp not in Ck:
                    Ck.append(s_temp)

        return Ck

    def find_candidates_1(self):
        """Find all `C1` (1-item sized candidates)"""

        c1: list[frozenset[str]] = []
        item_set: set[str] = set()

        for data in self.data_list:
            item_set.update(data)
        for item in item_set:
            c1.append(frozenset({item}))

        return c1

    def find_freq_set(self, Ck: list[frozenset[str]]):
        """
        `C_{k} -> L_{k}`

        - find candidates (in `C_{k}`) that have `support >= min_support`
        """
        freq_set: dict[frozenset[str], int] = {}

        for c in Ck:
            count = sum([c <= d for d in self.data_list])
            if count >= self.min_support:
                freq_set[frozenset(c)] = count

        return freq_set
