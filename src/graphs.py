import copy


class GraphException(Exception):
    pass


class Graph(dict):
    def __init__(self):
        self.root = None
        self.dominator_sets = None
        super(dict, self)

    """
    Set the root node of the graph

    Throws GraphException if the node passed does not exist within the graph.
    """
    def set_root(self, node):
        if node not in self:
            raise GraphException("Cannot set root to node not in graph")
        if node != self.root:
            #Invalidate dominators if we're changing root
            self.dominator_sets = None
        self.root = node

    """
    Add an arbitrary number of nodes to the graph. Duplicate nodes are
    ignored.
    """
    def add_nodes(self, *nodes):
        for node in [node for node in nodes if node not in self]:
            self.dominator_sets = None
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
                self.dominator_sets = None
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

    Requires you to have set a root node for the graph.

    Throws GraphException if no root node has been set.
    """
    def dominators(self):
        if self.root is None:
            raise GraphException("Requires a root node to be set")
        dominators = {}
        temp = None

        dominators[self.root] = set([self.root])

        for node in self.nodeset() - self.root:
            dominators[node] = self.nodeset()

        while temp != dominators:
            temp = copy.deepcopy(dominators)
            for node in self.nodeset() - self.root:
                predom = self.nodeset()
                for pred in self.pred(node):
                    predom = predom.intersection(dominators[pred])
                dominators[node] = set([node]).union(predom)

        self.dominator_sets = dominators
        return dominators

    """
    True if node1 dominates node2

    Throws GraphException if no root node has been set.
    """
    def dom(self, node1, node2):
        if not self.dominator_sets:
            self.dominators()
        return node1 in self.dominator_sets[node2]

    """
    True if node1 strictly dominates node2

    Throws GraphException if no root node has been set.
    """
    def strict_dom(self, node1, node2):
        if not self.dominator_sets:
            self.dominators()
        return self.dom(node1, node2) and node1 != node2

    """
    Finds the immediate dominator of the given node if one exists.

    Throws GraphException if no root node has been set.
    """
    def idom(self, node):
        if not self.dominator_sets:
            self.dominators()
        strict_doms = [n for n in self if self.strict_dom(n, node)]
        for dom in strict_doms:
            if len([n for n in strict_doms if self.strict_dom(dom, n)]):
                continue
            else:
                return dom

    """
    Returns the dominator tree of the graph it is called upon where
    the dominator tree is a tree where each node's children are those
    nodes it immediately dominates in the graph.

    Throws GraphException if no root node has been set.
    """
    def dominator_tree(self):
        if self.root is None:
            raise GraphException("Requires a root node to be set")
        dominator_tree = Graph()
        dominator_tree.add_nodes(*self.keys())
        for node1 in self:
            edges = [(node1, node2) for node2 in self if self.idom(node2) == node1]
            dominator_tree.add_edges(*edges)
        return dominator_tree

    """
    Computes the dominance frontier of the given node.

    Throws GraphException if no root node has been set.
    """
    def dominance_frontier(self, node):
        frontier = [n for n in self if len([n1 for n1 in self.pred(n) if self.dom(node, n1)]) and not self.strict_dom(node, n)]
        return set(frontier)

    """
    Computes the dominance frontiers of all nodes in the graph.

    Throws GraphException if no root node has been set.
    """
    def dominance_frontiers(self):
        return {node: self.dominance_frontier(node) for node in self}

    """
    Reverses all edges in the graph, returning the new reversed
    graph. Optionally takes a node as a parameter and sets the
    root of the newly reversed graph to that node.

    Throws GraphException if a root for the reversed graph is
    passed that does not exist within the graph.
    """
    def reverse(self, reverse_root=None):
        if reverse_root is not None:
            if reverse_root not in self:
                raise GraphException("Node {} does not exist in the reverse graph".format(reverse_root))
            else:
                reverse = Graph()
                reverse.add_nodes(*self.keys())
                reverse.set_root(reverse_root)
                for node1 in self:
                    edges = [(node1, node2) for node2 in self if node1 in self[node2]]
                    reverse.add_edges(*edges)
                return reverse


"""
Convenience class. Set-like object defining - operator
as set difference.
"""
class Nodeset(set):
    def __sub__(self, other):
        return self.difference(set([other]))


"""
Main function to run whilst testing
"""
def main():
    graph = Graph()

    #The graph we've been using all the time in class.
    graph.add_nodes("start", 1, 2, 3, 4, 5, 6, 7, "exit")
    graph.add_edges(("start", 1), (1, 2), (2, 3), (2, 4), (3, 5), (3, 6), (5, 7), (6, 7), (7, 2), (4, "exit"))
    graph.set_root("start")

    print graph.dominance_frontiers()
    print graph.reverse("exit").dominance_frontiers()

if __name__ == "__main__":
    main()
