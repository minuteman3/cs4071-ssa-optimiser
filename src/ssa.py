import copy
import json

import graphs

def getName(name, num):
    return name + "-" + str(num)
        

def renamePart(part, stat, counts, stacks):
    if part in stat and stat[part][0] != '#':
        if stat[part] not in counts:
            counts[stat[part]] = 0
            stacks[stat[part]] = [0]
        
        newname = stat[part] + "-" + str(stacks[stat[part]][-1])
        
        stat[part] = getName(stat[part], stacks[stat[part]][-1])


def renameVars(code, graph, blocks, block, done, counts, stacks):

    if block in done:
        return
    
    done.add(block) 

    defs = {}


    for stat in blocks[block]['code']:

        if stat['op'] != 'phi':
            for x in ['src1', 'src2']:
                renamePart(x, stat, counts, stacks)
            
        if 'dest' in stat:
            if stat['dest'] not in counts:
                counts[stat['dest']] = 0
                stacks[stat['dest']] = [0]

            if stat['dest'] not in defs:
                defs[stat['dest']] = 0

            defs[stat['dest']] += 1
    
            counts[stat['dest']] += 1
            stacks[stat['dest']].append(counts[stat['dest']])
        
            stat['dest'] = getName(stat['dest'], stacks[stat['dest']][-1])
    
    for succ in graph[block]:
        index = graph.pred(succ).keys().index(block)

        for stat in blocks[succ]['code']:
            if stat['op'] != 'phi':
                break

            if stat['operands'][index] not in counts:
                counts[stat['operands'][index]] = 0
                stacks[stat['operands'][index]] = [0]

            stat['operands'][index] = getName(stat['operands'][index], stacks[stat['operands'][index]][-1])
    
    for succ in graph[block]:
        renameVars(code, graph, blocks, succ, done, counts, stacks)

    for var in defs:
        for _ in range(defs[var]):
            stacks[var].pop()
    



"""
Inserts phi fucntions into the graph where they are needed.
Operates in-place.
"""
def insertPhis(code, graph, blocks):
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
                    blocks[y]['code'].insert(0, {"op": "phi", "dest": var, "operands": [var for _ in graph.pred(y)]})

                    phis[y].add(var)

                    if y not in defsites[var]:
                        worklist.add(y)
    
def toSSA(code):
    graph = graphs.Graph()

    blocks = {}

    for b in code['blocks']:
        graph.add_nodes(b['name'])
        blocks[b['name']] = b

    for b in code['blocks']:
        for e in b['next_block']:
            graph.add_edges((b['name'], e))
    
    graph.set_root(code['blocks'][0]['name']) # is it ok to just use the first block as root?


    insertPhis(code, graph, blocks)
    renameVars(code, graph, blocks, graph.root, set(), {}, {})
   
def main():
    code = json.loads(open('example.json').read())
    toSSA(code)
    print json.dumps(code, indent=4)


if __name__ == "__main__":
    main()