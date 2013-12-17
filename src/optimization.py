import json
from ssa import toSSA
from collections import defaultdict

FOLDABLE_OPS = ["MUL", "SUB", "RSB", "ADD"]
NO_SIDE_EFFECTS = ["MOV", "ADD", "SUB", "RSB", "MUL"]

"""
Switch statement used by constant folding optimization, instructing the
optimizer how to fold an operation correctly.

Parameter `op` should be statement["op"] from the code, and all arguments
in `vals` should be of type int.

Throws TypeError if all vals are not ints.
"""
def _do_op(op, *vals):
    if not all(isinstance(val, int) for val in vals):
        raise TypeError
    return {
        "MUL": vals[0] * vals[1],
        "SUB": vals[0] - vals[1],
        "RSB": vals[1] - vals[0],
        "ADD": vals[0] + vals[1]
    }.get(op, None)


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
        if _is_constant_phi(s):
            _convert_phi_to_copy(s)
        if s["op"] in FOLDABLE_OPS:
            if _is_constant_val(s["src1"]) and _is_constant_val(s["src2"]):
                _fold_constant(s)
        if _is_copy(s) and "src2" not in s:
            _propagate_constant(code, worklist, s)


"""
Returns true if a statement is a Phi function and all operands of the phi
function are the same constant value.
"""
def _is_constant_phi(statement):
    operands = [statement[x] for x in statement if x.startswith("src")]
    return (statement["op"] == "phi" and
            all(op == operands[0] for op in operands))

"""
Updates a statement in place, converting a phi function into a copy operation.
Corrupts code unless `_is_constant_phi(statement)` is true.
"""
def _convert_phi_to_copy(statement):
    val = statement["src1"]
    for src in [x for x in statement if x.startswith("src")]:
        del statement[src]
    statement["op"] = "MOV"
    statement["src1"] = val

"""
Performs constant folding in place. For an operation to be successfully folded
three predicates must be true:

    * All src parameters for the statement must be constant values.
    * statement["op"] must be in FOLDABLE_OPS
    * statement["op"] must have a case in `_do_op`

If any of these predicates are false calling _fold_constant(statement) will have
no effect on `statement`.
"""
def _fold_constant(statement):
    try:
        val1 = int(statement["src1"][1:])
        val2 = int(statement["src2"][1:])
    except ValueError:
        return
    const = _do_op(statement["op"], val1, val2)
    if const is not None:
        statement["op"] = "MOV"
        statement["src1"] = "#" + str(const)
        del statement["src2"]

"""
True if `val` is a constant literal.
"""
def _is_constant_val(val):
    return val[0] == '#'

"""
True if `val` is a variable. Always true if `_is_constant_val` is false.
"""
def _is_var(val):
    return val[0] != '#'

"""
True if statement is a copy operation, ie. statement["op"] == "MOV.
"""
def _is_copy(statement):
    return statement["op"] == "MOV"


def _propagate_constant(code, worklist, statement):
    val = statement["src1"]
    var = statement["dest"]
    _remove_statement(code, statement)
    for block in code["blocks"]:
        for statement in block["code"]:
            for field in statement:
                if statement[field] == var:
                    statement[field] = val
                    if statement not in worklist:
                        worklist.append(statement)

"""
Modifies `code` in place to delete statement. Can throw KeyError if code passed
is not well formed.
"""
def _remove_statement(code, statement):
    for block in code["blocks"]:
        for i, s in enumerate(block["code"]):
            if s == statement:
                del block["code"][i]
                return

"""
Builds a list of all variables in `code` containing the following information
for each variable:

    {
        "def_site": {
            "block": Name of block where this variable was defined,
            "statement": Index of the statement in which this variable is
                         defined within the "code" field of the block specified
                         by "block".
        },
        "uses": List of locations at which this variable is used of the form:
                [{
                    "block": As above,
                    "statement": As above
                }]
    }
"""
def _get_variables(code):
    variables = defaultdict(dict)
    for block in code["blocks"]:
        for idx, statement in enumerate(block["code"]):
            if "dest" in statement:
                variables[statement["dest"]]["def_site"] = {
                    "block": block["name"],
                    "statement": idx
                }
            for var in [statement[x] for x in statement
                        if x.startswith("src") and _is_var(statement[x])]:
                if "uses" not in variables[var]:
                    variables[var]["uses"] = []
                variables[var]["uses"].append({
                    "block": block["name"],
                    "statement": idx
                })
    for v in variables:
        if "uses" not in variables[v]:
            variables[v]["uses"] = []
    return variables

"""
Simple (non-aggressive) dead-code elimination using the algorithm from
the SSA Optimization Algorithms handout.

Transforms `code` in place, eliminating statements defining variables
that are never used.
"""
def dead_code_elimination(code):
    variables = _get_variables(code)
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
                    if _is_var(var) and var not in worklist:
                        worklist.append(var)
                code["blocks"][b]["code"][s]["delete"] = True
    _delete_marked_statements(code)

"""
Iterates over all blocks and deletes any statements marked for deletion.
"""
def _delete_marked_statements(code):
    for block in code["blocks"]:
        for idx, statement in enumerate(block["code"]):
            if "delete" in statement:
                del block["code"][idx]

def main():
    with open('example.json') as input_code:
        code = json.loads(input_code.read())
        cfg = toSSA(code)
        dead_code_elimination(code)
        constant_propagation(code)
        print json.dumps(code, indent=4)


if __name__ == "__main__":
    main()
