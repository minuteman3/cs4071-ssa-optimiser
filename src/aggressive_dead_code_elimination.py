import json
from ssa import toSSA
from graphs import Graph
import copy
from constant_propagation import constant_propagation
from util import (build_graph, get_statements, get_variables, defines_variable,
                 is_conditional_branch, remove_marked_statements, is_var, get_blocks)

LIVE_OPS = ["STR", "BX", "BL", "SWI", "return", "CMP"]

"""
Aggressively finds and eliminates dead code using the algorithm described in the
``SSA Optimization Algorithms'' handout.

    1. Marks all statements to be deleted.
    2. Unmarks statements that perform "live operations":
        * I/O
        * Memory writes (STR)
        * Branch & Exchange (BX) and Branch & Link (BL)
        * Software Interrupts (SWI)
        * Status register updates (CMP), operations with the `S` flag.
    3. Unmarks statements defining variables used in live statements.
    4. Unmarks conditional branches that directly control execution of live statements.
    5. Removes blocks that now cannot be reached from the START node.
    6. Deletes all marked statements.
    7. Removes variables from phi functions whose definitions have been eliminated.
    8. Removes blocks which contain no statements.
    9. Iteratively finds a least fixed point at which no further statements are removed.

A least fixed point solution is used despite not being mentioned in the description
of the algorithm as testing showed subsequent attempts calls to the function may
eliminate further code. This arises from the three phases of unmarking, particularly
``unmark_live_variable_definitions'', interacting with one another and finding new
results to be deleted after the removal of certain blocks/edges.
"""
def aggressive_dead_code_elimination(code):
    code2 = None
    # Iterative least fixed point solution, keep performing DCE until no code
    # is eliminated.
    while code2 != code:
        code2 = copy.deepcopy(code)
        graph = build_graph(code)
        cdg = graph.control_dependence_graph()
        live_statements = []
        mark_all(code)
        unmark_live_ops(code, live_statements)
        unmark_live_variable_definitions(code, live_statements)
        unmark_live_conditional_branches(code, live_statements, cdg)
        remove_unreachable_blocks(code, graph)
        remove_marked_statements(code)
        remove_dead_variables(code)
        remove_dead_blocks(code)

"""
Marks all statements in ``code`` to be deleted.
"""
def mark_all(code):
    for block in code["blocks"]:
        for statement in block["code"]:
            statement["delete"] = True

"""
Unmarks all instrinsically live statements. Live statements are operations
with side effects, such as software interrupts and operations have an effect
on the CPSR or Link Register such as CMP, BX, BL, and operators with the S flag.
"""
def unmark_live_ops(code, live_statements):
    statements = get_statements(code)
    for statement in statements:
        s = statement["statement"]
        if s["op"] in LIVE_OPS or s["op"].endswith("S"):
            del s["delete"]
            live_statements.append(statement)

"""
Unmarks all statements that define variables used in statements that have already
been unmarked.
"""
def unmark_live_variable_definitions(code, live_statements):
    statements = get_statements(code)
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


"""
Unmarks all conditional branch statements that directly control execution of statements
that have already been unmarked.
"""
def unmark_live_conditional_branches(code, live_statements, cdg):
    statements = get_statements(code)
    worklist = [block for block in code["blocks"]]
    blocks = get_blocks(code)
    while len(worklist):
        block = worklist.pop()
        if len(block["next_block"]) > 1:
            nb = 0
            for statement in block["code"]:
                if is_conditional_branch(statement) and "delete" in statement:
                    next_block = block["next_block"][nb]
                    worklist.append(code["blocks"][blocks[next_block]])
                    for ls in live_statements:
                        if cdg.has_path(next_block, ls["block"]) != ls["block"] in cdg[next_block]:
                            print "{} | {}".format(next_block, ls["block"])
                            print json.dumps(cdg, indent=4)
                            print live_statements
                        if ls["block"] in cdg[next_block] and "delete" in statement:
                            del statement["delete"]
                    nb += 1

"""
Deletes all blocks that cannot be reached from the START block.
"""
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

"""
Deletes all blocks that contain no statements.
"""
def remove_dead_blocks(code):
    graph = build_graph(code)
    rg = graph.reverse()
    blocks = get_blocks(code)
    worklist = [block for block in code["blocks"]]
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

"""
Deletes mentions of variables in statements whose definitions have been deleted.

This should only remove variable names from PHI functions.
"""
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
        print json.dumps(code, indent=4)

if __name__ == "__main__":
    main()
