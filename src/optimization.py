import json
from ssa import toSSA

def constant_propagation(code):
    worklist = []
    for block in code["blocks"]:
        for statement in block["code"]:
            worklist.append(statement)
    while len(worklist):
        s = worklist.pop(0)
        if s["op"] == "phi":
            operands = s["operands"]
            if is_constant_phi(s):
                convert_phi_to_copy(s)
        if is_copy(s) and "src2" not in s:
            propagate_constant(code, worklist, s)
        #if is_copy(s) and is_var(s["src1"]) and "src2" not in s:
            #propagate_constant(code, worklist, s)


def is_constant_phi(statement):
    operands =  statement["operands"]
    return is_constant_val(operands[0]) and all(op == operands[0] for op in operands)

def convert_phi_to_copy(statement):
    val = statement["operands"][0]
    del statement["operands"]
    statement["op"] = "MOV"
    statement["src1"] = val

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

def main():
    with open('example.json') as input_code:
        code = json.loads(input_code.read())
        toSSA(code)
        constant_propagation(code)
        print json.dumps(code, indent=4)



if __name__ == "__main__":
    main()
