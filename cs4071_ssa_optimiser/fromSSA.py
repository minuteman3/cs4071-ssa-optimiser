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
                            insertBlock = blocks[graph.pred(b["name"]).keys()[index]]["code"]
                            toInsert = {"op": "MOV", "dest": "ConstFix" + str(fixed), "src": op[part]}

                            # Make sure to insert before branch
                            if len(insertBlock) > 0 and insertBlock[-1]["op"].startswith("B"):
                                insertBlock.insert(-1, toInsert )
                            else:
                                insertBlock.append(toInsert)

                            op[part] = "ConstFix" + str(fixed)

                            fixed += 1
"""
Converts to CSSA, using  Method I from book, so generates a lot of unnecessary copy statements.
Should switch to Method III at some point.
"""
def toCSSA(code, graph, blocks):
    fixConstants(code, graph, blocks)

    copies = 0

    for b in code["blocks"]:
        for op in b["code"]:
            if op["op"] == "phi":
                for part in op:
                    if part.startswith("src"):
                        pass
                        index = int(part[3:]) - 1
                        insertBlock = blocks[graph.pred(b["name"]).keys()[index]]["code"]
                        toInsert = {"op": "MOV", "dest": "CSSACopy" + str(copies), "src": op[part]}
                        
                        # Make sure to insert before branch
                        if len(insertBlock) > 0 and insertBlock[-1]["op"].startswith("B"):
                            insertBlock.insert(-1, toInsert )
                        else:
                            insertBlock.append(toInsert)

                        op[part] = "CSSACopy" + str(copies)
                        copies += 1

                    elif part == "dest":
                        index = 0
                        for o in b["code"]:
                            if o["op"] != "phi":
                                break
                            index += 1

                        b["code"].insert(index, {"op" : "MOV", "dest": op["dest"], "src": "CSSACopy" + str(copies)})
                        op["dest"] = "CSSACopy" + str(copies)
                        copies += 1


"""
Takes a list of sets of objects,  with objects in the same set taken to be equivalent.
Flattens this list to a dict mapping each object to another, with equivalent objects 
all mapping to the same object.
"""
def flattenEquivs(equivs):
   
    changed = True 

    while(changed):
        changed = False
        for i in range(len(equivs)):
            for v in equivs[i]:
                for j in range(len(equivs)):
                    if i != j and v in equivs[j]:
                        for x in equivs[j]:
                            equivs[i].add(x)
                        del equivs[j]
                        changed = True
                        break
                if(changed):
                    break
            if(changed):
                break

    mappings = {}

    for s in equivs:
        d = s.pop()
        s.add(d)
        for v in s:
           mappings[v] = d

    return mappings

"""
Coalesces phi-functions according to sreedhars method.
Does not deal with live range interference, this must be 
dealt with before calling this function.
"""
def coalescePhis(code):
    equivs = []

    for b in code["blocks"]:
        for op in b["code"]:
            if op["op"] == "phi":
                opequivs = set()
                for part in op:
                    if part != "op":
                        opequivs.add(op[part])
                equivs.append(opequivs)


    mappings = flattenEquivs(equivs)


    for b in code["blocks"]:
        toremove = []
        
        for i in range(len(b["code"])):
            if b["code"][i]["op"] == "phi":
                toremove.append(i)
                continue
            for part in b["code"][i]:
                if (part == "dest" or part.startswith("src")) and b["code"][i][part] in mappings:
                    b["code"][i][part] = mappings[b["code"][i][part]]
        
        for i in toremove:
            del b["code"][i]


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

    toCSSA(code, graph, blocks)

    coalescePhis(code)

def main():
    code = json.loads(open('tssa.json').read())
    fromSSA(code)
    print json.dumps(code, indent=4)

    print flattenEquivs([set(["a", "b", "c"]), set(["b", "d"]), set(["d", "e", "f"]), set(["f", "r"]), set(["x", "y"])])


if __name__ == "__main__":
    main()
