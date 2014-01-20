from graphs import Graph
from collections import defaultdict

DEFINING_OPS = ["MOV", "ADD", "MUL", "SUB", "RSB", "LDR", "phi"]

UNCONDITIONAL_BRANCHES = ["B", "BX", "BL"]

"""
Constructs the control flow graph of `code`
"""
def build_graph(code):
    graph = Graph()
    blocks = [b["name"] for b in code["blocks"]]
    edges = [(b["name"], e) for b in code["blocks"] for e in b["next_block"]]
    graph.add_nodes(*blocks)
    graph.add_edges(*edges)
    return graph

"""
Builds a list of all statements in `code` containing the following information
for each statement:

    {
        "block": Name of block containing statement
        "statement": Literal copy of statement in question
    }
"""
def get_statements(code):
    statements = [{"block": b["name"], "statement": s} for b in code["blocks"] for s in b["code"]]
    return statements
	
"""
Builds a list of all statements in `block` containing the following information
for each statement:

    {
        "block": Name of block containing statement
        "statement": Literal copy of statement in question
    }
"""
def get_statements_in_block(block):
    statements = [s for s in block["code"]]
    return statements

"""
Returns true if `statement` defines a variable
"""
def defines_variable(statement):
    return statement["op"] in DEFINING_OPS

"""
Returns true if `statement` is a conditional branch.
"""
def is_conditional_branch(statement):
    return statement["op"].startswith("B") and statement["op"] not in UNCONDITIONAL_BRANCHES

"""
Returns a dictionary mapping block names to indexes in the "blocks" array of `code`.
"""
def get_blocks(code):
    blocks = {}
    for idx,block in enumerate(code["blocks"]):
        blocks[block["name"]] = idx
    return blocks


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
        i = 0
        while i < len(block["code"]):
            if "delete" in block["code"][i]:
                del block["code"][i]
            else:
                i+= 1

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