import copy
import json

import graphs

"""
Inserts phi fucntions into the graph where they are needed.
Operates in-place.
"""
def insertPhis(code):
    graph = graphs.Graph()

    blocks = {}

    for b in code['blocks']:
        graph.add_nodes(b['name'])
        blocks[b['name']] = b

    for b in code['blocks']:
        for e in b['next_block']:
            graph.add_edges((b['name'], e))
    
    graph.set_root(code['blocks'][0]['name']) # is it ok to just use the first block as root?

    dominance_frontiers = graph.dominance_frontiers()

    defsites = {}
    phis = {}

    for b in blocks:
        for y in dominance_frontiers[b]:
            phis[y] = set()

        for op in blocks[b]['code']:
            if 'dest' in op:
                if op['dest'] not in defsites:
                    defsites[op['dest']] = set()
                
                defsites[op['dest']].add(b)
    

    for var in defsites:
        worklist = copy.deepcopy(defsites[var])

        while len(worklist) > 0:
            n = worklist.pop()

            for y in dominance_frontiers[n]:
                if var not in phis[y]:
                    blocks[y]['code'].insert(0, {"op": "phi", "operands": [var for _ in graph.pred(y)]})

                    phis[y].add(var)

                    if y not in defsites[var]:
                        worklist.add(y)
    
   
def main():
    code = json.loads(open('example.json').read())
    insertPhis(code)
    print json.dumps(code, indent=4)


if __name__ == "__main__":
    main()
