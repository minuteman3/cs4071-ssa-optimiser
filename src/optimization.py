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
            if is_consant_phi(s):
                convert_phi_to_copy(s)

def is_constant_phi(statement):
    operands =  statement["operands"]
    return operands[0][0] == '#' and all(op == operands[0] for op in operands)

def convert_phi_to_copy(statement):
    val = statement["operands"][0]
    del statement["operands"]
    statement["op"] = "MOV"
    statement["src1"] = val

def main():
    x = {'op':'phi','operands':['#1'],'dest':'x'}
    #with open('example.json') as input_code:
        #code = json.loads(input_code.read())
        #toSSA(code)
        #constant_propagation(code)


if __name__ == "__main__":
    main()
