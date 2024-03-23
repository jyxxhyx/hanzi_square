from typing import Set, Tuple, Dict, List


class Graph(object):
    def __init__(self, data):
        self.nodes: Set[str] = set()
        self.arcs: Dict[Tuple[str, str], str] = dict()
        self.chars: Dict[str, List[Tuple[str, str]]] = dict()
        self.data = data

    def generate(self, is_clear_node=True):
        for char, pairs in self.data.items():
            for pair in pairs:
                node0, node1 = pair[0], pair[1]
                self.nodes.add(node0)
                self.nodes.add(node1)
                for arc in [(node0, node1), (node1, node0)]:
                    if arc in self.arcs:
                        continue
                    self.arcs[arc] = char
                    # 有可能两个字符可以拼成多个字，不过应该不影响计算，忽略之
                    # arcs.setdefault(arc, list()).append(char)
                    self.chars.setdefault(char, list()).append(arc)
        if is_clear_node is True:
            # 为了缩小问题规模做一些清理
            # 目前清理了本身是偏旁部首的字
            for node in self.nodes:
                if node in self.chars:
                    del self.chars[node]
