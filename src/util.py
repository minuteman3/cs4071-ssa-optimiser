from collections import defaultdict


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
                variables[var]["uses"].append({
                    "block": block["name"],
                    "statement": idx
                })
    for v in variables:
        if "uses" not in variables[v]:
            variables[v]["uses"] = []
    return variables

"""
Modifies `code` in place to delete statement. Can throw KeyError if code passed
is not well formed.
"""
def remove_statement(code, statement):
    for block in code["blocks"]:
        for i, s in enumerate(block["code"]):
            if s == statement:
                del block["code"][i]
                return

"""
Iterates over all blocks and deletes any statements marked for deletion.
"""
def remove_marked_statements(code):
    for block in code["blocks"]:
        for idx, statement in enumerate(block["code"]):
            if "delete" in statement:
                del block["code"][idx]

"""
True if `val` is a constant literal.
"""
def is_constant_val(val):
    return val.startswith('#')

"""
True if `val` is a variable. Always true if `is_constant_val` is false.
"""
def is_var(val):
    return not is_constant_val(val)

"""
True if statement is a copy operation, ie. statement["op"] == "MOV.
"""
def is_copy(statement):
    return statement["op"] == "MOV"

"""
Returns true if a statement is a Phi function and all operands of the phi
function are the same constant value.
"""
def is_constant_phi(statement):
    operands = [statement[x] for x in statement if x.startswith("src")]
    return (statement["op"] == "phi" and
            all(op == operands[0] for op in operands))
