import json

import graphs

"""
Removes constant parameters to phi-functions, by creating temporary variables in the corresponding
predecessors. This is a necessary preprocessing step before transforming TSSA into CSSA.
See page 55 of Translation to normal form handout.
"""
def fixConstants(code, graph, blocks):
    fixed = 0

    for b in code["blocks"]:
        for op in b["code"]:
            if op["op"] == "phi":
                for part in op:
                    if part.startswith("src"):
                        if op[part].startswith("#"):
                            index = int(part[3:]) - 1
                            blocks[graph.pred(b["name"]).keys()[index]]["code"].append({"op": "MOV", "dest": "ConstFix" + str(fixed), "src": op[part]})
                            op[part] = "ConstFix" + str(fixed)

                            fixed += 1
"""
Turns SSA code into normal code.
Not yet fully functioning.
"""
def fromSSA(code):
    graph = graphs.Graph()

    blocks = {}

    for b in code['blocks']:
        graph.add_nodes(b['name'])
        blocks[b['name']] = b

    for b in code['blocks']:
        for e in b['next_block']:
            graph.add_edges((b['name'], e))

    graph.set_root(code['blocks'][0]['name']) # is it ok to just use the first block as root?

    fixConstants(code, graph, blocks)


def main():
    code = json.loads(open('tssa.json').read())
    fromSSA(code)
    print json.dumps(code, indent=4)


if __name__ == "__main__":
    main()
