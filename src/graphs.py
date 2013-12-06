import copy

class GraphException(Exception):
    pass

class Graph(dict):
    def __init__(self):
        self.root = None
        super(dict, self)

    """Set the root node of the graph"""
    def set_root(self, node):
        if node not in self:
            raise GraphException("Cannot set root to node not in graph")
        self.root = node

    """
    Add an arbitrary number of nodes to the graph. Duplicate nodes are
    ignored.
    """
    def add_nodes(self, *nodes):
        for node in [node for node in nodes if node not in self]:
            self[node] = set([])

    """
    Add an arbitrary number of edges to the graph. Duplicate edges are
    ignored.

    Throws GraphException if an edge mentions a vertex that does not exist.
    """
    def add_edges(self, *edges):
        for edge in edges:
            if edge[0] not in self or edge[1] not in self:
                raise GraphException("Cannot add edge {} to graph. One or more vertices mentioned does not exist.".format(edge))
            if edge[0] != edge[1]:
                self[edge[0]] = self[edge[0]].union(set([edge[1]]))

    """
    Convenience method. Returns a Nodeset, a set-like
    object that has had the - operator defined for set difference.
    """
    def nodeset(self):
        return Nodeset(self.keys())

    """
    Returns the set of immediate predecessors for a given node.
    """
    def pred(self, node):
        return set([k for k in self.nodeset() if node in self[k]])

    """
    Naive quadratic time dominators algorithm taken from

        https://en.wikipedia.org/wiki/Dominator_%28graph_theory%29

    Used because implementing Lengauer-Tarjan was too much effort.

    Requires you to have set a root node for the graph. If you haven't,
    defaults to using a node called "start".

    Throws GraphException if the root node is not set and there is no
    node named "start".
    """
    def dominators(self):
        if self.root is None and "start" not in self:
            raise GraphException("Requires a root node is set or 'start' exists in graph")
        root = self.root if self.root else "start"
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


"""
Convenience class. Set-like object defining - operator
as set difference.
"""
class Nodeset(set):
    def __sub__(self, other):
        return self.difference(set([other]))
