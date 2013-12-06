import copy

class Graph(dict):
    def add_node(self, *nums):
        for num in [num for num in nums if num not in self]:
            self[num] = set([])

    def add_edge(self, nfrom, nto):
        self[nfrom] = self[nfrom].union(set([nto]))

    def add_edges(self, *edges):
        for edge in edges:
            if edge[0] != edge[1]:
                self[edge[0]] = self[edge[0]].union(set([edge[1]]))

    def nodeset(self):
        return Nodeset(self.keys())

    def pred(self, node):
        return set([k for k in self.nodeset() if node in self[k]])

    def dominators(self, root):
        assert(root in self)
        dominators = {}
        temp = False

        dominators[root] = set([root])

        for node in graph.nodeset() - root:
            dominators[node] = graph.nodeset()

        while temp != dominators:
            temp = copy.deepcopy(dominators)
            for node in graph.nodeset() - root:
                predom = graph.nodeset()
                for pred in graph.pred(node):
                    predom = predom.intersection(dominators[pred])
                dominators[node] = set([node]).union(predom)

        return dominators


class Nodeset(set):
    def __sub__(self, other):
        return self.difference(set([other]))


graph = Graph()

graph.add_node("start",1,2,3,4,5,6,7,"exit")
graph.add_edges(("start",1),(1,2),(2,3),(2,4),(3,5),(3,6),(5,7),(6,7),(7,2),(4,"exit"))

print graph.dominators("start")
