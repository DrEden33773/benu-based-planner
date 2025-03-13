from dataclasses import dataclass, field


@dataclass
class A:
    member: list[int] = field(default_factory=list)

    def __post_init__(self):
        self.member = [1, 2, 3]

    def operate_via_delegation(self):
        b = B(self)
        b.add_one_element(4)
        print(self.member)


@dataclass
class B:
    wrapped: A

    def add_one_element(self, element: int):
        self.wrapped.member.append(element)


if __name__ == "__main__":
    a = A()
    a.operate_via_delegation()
