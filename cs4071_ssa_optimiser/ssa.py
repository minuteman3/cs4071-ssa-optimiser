import copy
import json
from util import build_graph

def getName(name, num):
    return name + "-" + str(num)

"""
Helper function for renameVars
Used to do the same operation on 'src1' and 'src2'
"""
def renamePart(part, stat, counts, stacks):
    if part in stat and stat[part][0] != '#':
        if stat[part] not in counts:
            counts[stat[part]] = 0
            stacks[stat[part]] = [0]

        newname = stat[part] + "-" + str(stacks[stat[part]][-1])

        stat[part] = getName(stat[part], stacks[stat[part]][-1])

"""
Renames variables to convert to ssa.
Operates in-place.
Must be called on code that has already has phi functions.
"""
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

            phiparam = "src" + str(index + 1)

            if stat[phiparam] not in counts:
                counts[stat[phiparam]] = 0
                stacks[stat[phiparam]] = [0]

            stat[phiparam] = getName(stat[phiparam], stacks[stat[phiparam]][-1])

    for succ in graph[block]:
        renameVars(code, graph, blocks, succ, done, counts, stacks)

    for var in defs:
        for _ in range(defs[var]):
            stacks[var].pop()




"""
Inserts phi functions into the graph where they are needed.
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

                    phi = {"op": "phi", "dest": var}
                    for i in range(len(graph.pred(y))):
                        phi["src" + str(i + 1)] = var

                    blocks[y]['code'].insert(0, phi)

                    phis[y].add(var)

                    if y not in defsites[var]:
                        worklist.add(y)

"""
Converts code to SSA form.
Operates in-place
"""
def toSSA(code):
    graph = build_graph(code)
    graph.set_root(code["blocks"][0]["name"])
    blocks = {b["name"]: b for b in code["blocks"]}
    insertPhis(code, graph, blocks)
    renameVars(code, graph, blocks, graph.root, set(), {}, {})
    return graph

def main():
    code = json.loads(open('example.json').read())
    toSSA(code)
    print json.dumps(code, indent=4)


if __name__ == "__main__":
    main()
