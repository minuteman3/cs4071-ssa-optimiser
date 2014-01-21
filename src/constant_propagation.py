import json
from ssa import toSSA
from util import (remove_statement,
                  is_var,
                  is_copy,
                  is_constant_val,
                  is_constant_phi,
				  _fold_constant,
				  _do_op)

FOLDABLE_OPS = ["MUL", "SUB", "RSB", "ADD"]



"""
Driving function for the Simple (non-conditoinal) Constant Propagation
algorithm specified in the SSA Optimization Algorithms handout.

Transforms `code` in place with three transformations:
    * Eliminates phi functions where all phi-function operands are equal,
      replacing such functions with a copy operation.
    * Constant folds operations on two constant variables, eg.
        ADD R0, #1, #5
      By performing the specified operation and replacing the statement
      with a copy operation with the result, eg.
        ADD R0, #1, #5  --->  MOV R0, #6
    * Copy propagation taking single argument phi functions or copy assignments
      of the form x <- Phi(y) or x <- y, deleting them and replacing all uses
      of `x` by `y`.
"""
def constant_propagation(code):
    worklist = []
    for block in code["blocks"]:
        for statement in block["code"]:
            worklist.append(statement)
    while len(worklist):
        s = worklist.pop(0)
        if is_constant_phi(s):
            _convert_phi_to_copy(s)
        if s["op"] in FOLDABLE_OPS:
            if is_constant_val(s["src1"]) and is_constant_val(s["src2"]):
                _fold_constant(s)
        if is_copy(s) and "src2" not in s:
            _propagate_constant(code, worklist, s)



"""
Updates a statement in place, converting a phi function into a copy operation.
Corrupts code unless `is_constant_phi(statement)` is true.
"""
def _convert_phi_to_copy(statement):
    srcs = [x for x in statement if x.startswith("src")]
    val = statement[srcs[0]]
    for src in srcs:
        del statement[src]
    statement["op"] = "MOV"
    statement["src1"] = val





def _propagate_constant(code, worklist, statement):
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





def main():
    with open('example.json') as input_code:
        code = json.loads(input_code.read())
        cfg = toSSA(code)
        constant_propagation(code)
        print json.dumps(code, indent=4)


if __name__ == "__main__":
    main()
