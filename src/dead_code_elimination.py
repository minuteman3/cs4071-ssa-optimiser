import json
from ssa import toSSA
from util import (get_variables,
                  is_var,
                  remove_marked_statements)

"""
Simple (non-aggressive) dead-code elimination using the algorithm from
the SSA Optimization Algorithms handout.

Transforms `code` in place, eliminating statements defining variables
that are never used.
"""
def dead_code_elimination(code):
    variables = get_variables(code)
    worklist = variables.keys()
    while len(worklist):
        v = worklist.pop(0)
        if not len(variables[v]["uses"]):
            s = variables[v]["def_site"]["statement"]
            for idx, block in enumerate(code["blocks"]):
                if block["name"] == variables[v]["def_site"]["block"]:
                    b = idx
                    break
            if code["blocks"][b]["code"][s]["op"] in NO_SIDE_EFFECTS:
                for var in [code["blocks"][b]["code"][s][x] for x in
                            code["blocks"][b]["code"][s] if x.startswith("src")]:
                    if is_var(var) and var not in worklist:
                        worklist.append(var)
                code["blocks"][b]["code"][s]["delete"] = True
    remove_marked_statements(code)


def main():
    with open('example.json') as input_code:
        code = json.loads(input_code.read())
        cfg = toSSA(code)
        dead_code_elimination(code)
        print json.dumps(code, indent=4)

if __name__ == "__main__":
    main()
