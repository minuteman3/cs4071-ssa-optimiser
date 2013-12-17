import json
from ssa import toSSA
from collections import defaultdict

FOLDABLE_OPS = ["MUL","SUB","RSB","ADD"]
NO_SIDE_EFFECTS = ["MOV","ADD","SUB","RSB","MUL"]

def do_op(op, val1, val2):
    return {
        "MUL": val1 * val2,
        "SUB": val1 - val2,
        "RSB": val2 - val1,
        "ADD": val1 + val2
    }.get(op, None)


def constant_propagation(code):
    worklist = []
    for block in code["blocks"]:
        for statement in block["code"]:
            worklist.append(statement)
    while len(worklist):
        s = worklist.pop(0)
        if is_constant_phi(s):
            convert_phi_to_copy(s)
        if s["op"] in FOLDABLE_OPS:
            if is_constant_val(s["src1"]) and is_constant_val(s["src2"]):
                fold_constant(s)
        if is_copy(s) and "src2" not in s:
            propagate_constant(code, worklist, s)


"""
Returns true if a statement is a Phi function and all operands of the phi
function are the same constant value.
"""
def is_constant_phi(statement):
    operands = [statement[x] for x in statement if x.startswith("src")]
    return (statement["op"] == "phi" and
            all(op == operands[0] for op in operands))

def convert_phi_to_copy(statement):
    val = statement["src1"]
    for src in [x for x in statement if x.startswith("src")]:
        del statement[src]
    statement["op"] = "MOV"
    statement["src1"] = val

def fold_constant(statement):
    val1 = int(statement["src1"][1:])
    val2 = int(statement["src2"][1:])
    const = do_op(statement["op"], val1, val2)
    if const is not None:
        statement["op"] = "MOV"
        statement["src1"] = "#" + str(const)
        del statement["src2"]

def is_constant_val(val):
    return val[0] == '#'

def is_var(val):
    return val[0] == 'R'

def is_copy(statement):
    return statement["op"] == "MOV"

def propagate_constant(code, worklist, statement):
    val = statement["src1"]
    var = statement["dest"]
    remove_statement(code, statement)
    for block in code["blocks"]:
        for statement in block["code"]:
            for field in statement:
                if statement[field] == var:
                    statement[field] = val
                    if statement not in worklist:
                        worklist.append(statement)

def remove_statement(code, statement):
    for block in code["blocks"]:
        for i, s in enumerate(block["code"]):
            if s == statement:
                del block["code"][i]
                return

def get_variables(code):
    variables = defaultdict(dict)
    for block in code["blocks"]:
        for idx, statement in enumerate(block["code"]):
            if "dest" in statement:
                variables[statement["dest"]]["def_site"] = {
                    "block": block["name"],
                    "statement": idx
                }
            for var in [statement[x] for x in statement
                        if x.startswith("src") and is_var(statement[x])]:
                if "uses" not in variables[var]:
                    variables[var]["uses"] = []
                variables[var]["uses"].append({"block":block["name"], "statement":idx})
    for v in variables:
        if "uses" not in variables[v]:
            variables[v]["uses"] = []

    return variables

def dead_code_elimination(code):
    variables = get_variables(code)
    worklist = variables.keys()

    while len(worklist):
        v = worklist.pop(0)
        if not len(variables[v]["uses"]):
            s = variables[v]["def_site"]["statement"]
            for idx,block in enumerate(code["blocks"]):
                if block["name"] == variables[v]["def_site"]["block"]:
                    b = idx
                    break
            if code["blocks"][b]["code"][s]["op"] in NO_SIDE_EFFECTS:
                for var in [code["blocks"][b]["code"][s][x] for x in
                            code["blocks"][b]["code"][s] if x.startswith("src")]:
                    if is_var(var) and var not in worklist:
                        worklist.append(var)
                del code["blocks"][b]["code"][s]


def main():
    with open('example.json') as input_code:
        code = json.loads(input_code.read())
        toSSA(code)
        dead_code_elimination(code)
        constant_propagation(code)
        print json.dumps(code, indent=4)



if __name__ == "__main__":
    main()
