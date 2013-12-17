import json
from ssa import toSSA
from collections import defaultdict

FOLDABLE_OPS = ["MUL","SUB","RSB","ADD"]

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
        if s["op"] == "phi":
            if is_constant_phi(s):
                convert_phi_to_copy(s)
        if s["op"] in FOLDABLE_OPS:
            if is_constant_val(s["src1"]) and is_constant_val(s["src2"]):
                fold_constant(s)
        if is_copy(s) and "src2" not in s:
            propagate_constant(code, worklist, s)


def is_constant_phi(statement):
    operands =  statement["operands"]
    return is_constant_val(operands[0]) and all(op == operands[0] for op in operands)

def convert_phi_to_copy(statement):
    val = statement["operands"][0]
    del statement["operands"]
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
                if isinstance(statement[field], list):
                    statement[field] = [val if x == var else x for x in statement[field]]
                    if statement not in worklist:
                        worklist.append(statement)
                elif statement[field] == var:
                    statement[field] = val
                    if statement not in worklist:
                        worklist.append(statement)

def remove_statement(code, statement):
    for block in code["blocks"]:
        for i, s in enumerate(block["code"]):
            if s == statement:
                del block["code"][i]
                return

def build_datastructures(code):
    statements = []
    variables = defaultdict(dict)
    blocks = code["blocks"]
    for block in blocks:
        for idx, statement in enumerate(block["code"]):
            #statement_info = {
                #"containing_block": block["name"],
                #"previous_statement": block["code"][idx - 1] if idx > 0 else None,
                #"next_statement": block["code"][idx + 1] if idx < len(block["code"]) - 1 else None,
                #"vars_defined": statement["dest"] if "dest" in statement else None,
                #"vars_used": [statement[x] for x in statement.keys()
                              #if x.startswith("src") and is_var(statement[x])],
                #"statement_idx": idx
            #}
            #statements.append(statement_info)
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

    return blocks, statements, variables

def main():
    with open('example.json') as input_code:
        code = json.loads(input_code.read())
        toSSA(code)
        b, s, v = build_datastructures(code)
        #print json.dumps(s, indent=4)
        print json.dumps(v, indent=4)
        constant_propagation(code)
        #print json.dumps(b, indent=4)
        #print json.dumps(code, indent=4)



if __name__ == "__main__":
    main()
