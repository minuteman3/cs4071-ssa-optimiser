import json
from ssa import toSSA
from graphs import Graph
import copy
from constant_propagation import constant_propagation
from util import (build_graph, get_statements, get_variables, defines_variable,
                 is_conditional_branch, remove_marked_statements, is_var, get_blocks)

LIVE_OPS = ["STR", "BX", "BL", "SWI", "return"]

def aggressive_dead_code_elimination(code):
    graph = build_graph(code)
    cdg = graph.control_dependence_graph()
    mark_all(code)
    unmark_live(code, cdg)
    remove_unreachable_blocks(code, graph)
    remove_marked_statements(code)
    mark_all(code)
    unmark_live(code, cdg)
    remove_marked_statements(code)
    remove_dead_blocks(code)
    remove_dead_variables(code)

def mark_all(code):
    for block in code["blocks"]:
        for statement in block["code"]:
            statement["delete"] = True

def unmark_live(code, cdg):
    live_statements = []
    statements = get_statements(code)
    for statement in statements:
        if statement["statement"]["op"] in LIVE_OPS:
            del statement["statement"]["delete"]
            live_statements.append(statement)
    worklist = [ls["statement"][x] for ls in live_statements for x in ls["statement"] if x.startswith("src") and is_var(ls["statement"][x])]
    while len(worklist):
        next_var = worklist.pop()
        for statement in statements:
            s = statement["statement"]
            statement_vars = [s[var] for var in s if var.startswith("src") and is_var(s[var])]
            if "dest" in s and s["dest"] == next_var and "delete" in s:
                del s["delete"]
                worklist.extend(statement_vars)
                live_statements.append(statement)
    for block in code["blocks"]:
        if len(block["next_block"]) > 1:
            nb = 0
            for statement in block["code"]:
                if is_conditional_branch(statement) and "delete" in statement:
                    next_block = block["next_block"][nb]
                    for ls in live_statements:
                        if cdg.has_path(next_block, ls["block"]) and "delete" in statement:
                            del statement["delete"]
                    nb += 1

def remove_unreachable_blocks(code, graph):
    for block in code["blocks"]:
        if len(block["next_block"]) > 1:
            for statement in block["code"]:
                if is_conditional_branch(statement) and "delete" in statement:
                    nb = block["next_block"].pop(0)
                    graph.remove_edges((block["name"], nb))
    i = 0
    while i < len(code["blocks"]):
        if not graph.has_path(code["blocks"][0]["name"], code["blocks"][i]["name"]):
            del code["blocks"][i]
        else:
            i += 1

def remove_dead_blocks(code):
    graph = build_graph(code)
    rg = graph.reverse()
    blocks = get_blocks(code)
    worklist = []
    for block in code["blocks"]:
        worklist.append(block)
    while len(worklist):
        block = worklist.pop()
        if len(block["code"]) == 0:
            block["delete"] = True
            for b in rg[block["name"]]:
                pb = code["blocks"][blocks[b]]
                worklist.append(pb)
                for idx,nb in enumerate(pb["next_block"]):
                    if nb == block["name"]:
                        pb["next_block"][idx] = block["next_block"][0]
    i = 0
    while i < len(code["blocks"]):
        if "delete" in code["blocks"][i]:
            del code["blocks"][i]
        else:
            i += 1

def remove_dead_variables(code):
    variables = get_variables(code)
    blocks = get_blocks(code)
    for variable in variables:
        v = variables[variable]
        if "def_site" not in v:
            for use in v["uses"]:
                b, s = blocks[use["block"]], use["statement"]
                statement = code["blocks"][b]["code"][s]
                for u in [u for u in statement if u.startswith("src") and statement[u] == variable]:
                    del statement[u]


def main():
    with open('example.json') as input_code:
        code = json.loads(input_code.read())
        cfg = toSSA(code)
        aggressive_dead_code_elimination(code)
        constant_propagation(code)
        aggressive_dead_code_elimination(code)
        print json.dumps(code, indent=4)

if __name__ == "__main__":
    main()
