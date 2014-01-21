import json
from ssa import toSSA
from constant_propagation import constant_propagation
from util import (remove_statement,
                  is_copy,
                  is_constant_val,
                  is_constant_phi,
		  get_variables,
		  get_blocks,
		  get_statements,
		  _fold_constant,
		  _do_op,
		  get_statements_in_block,
		  is_var)

FOLDABLE_OPS = ["MUL", "SUB", "RSB", "ADD"]	
MEMORY_OPS = ["BL","LDR"] 
CONDITIONAL_BRANCH = ["BEQ","BNE","BLT","BLE","BGT","BGE"]


"""
Driving function for the Conditional Constant Propagation
 specified in the SSA Optimization Algorithms handout.

 Marks code as not executed, constant, variable.
 Then deletes none executed code and transforms constant code in place. 
 
"""
variables = 0

def conditional_propagation(code):
	worklist = []	
	blocks = get_blocks(code)	
	global variables
	variables = get_variables(code)
	
	for v in variables: 
	# Variables with no definition must be input to the program  
		if variables[v].has_key("def_site"):
			variables[v]["evidence"] = "never" 
		else:
			variables[v]["evidence"] = "over"
	
	for block in code["blocks"]:
		block["delete"] = True
		#Entry block is always executable
		if block["name"] == code["starting_block"][0]:
			add_block_to_worklist(block, worklist)
			block["delete"] = False
			

	branch = "nil"
		
	
			
	while len(worklist):
		s = worklist.pop(0)
		# Executable Blocks with only 1 successor, that block must also be executable
		if len(get_block(s, code, blocks)["next_block"]) >= 1:
			if get_next_block(code, blocks, s, 0)["delete"] and len(get_block(s, code, blocks)["next_block"]) == 1:
				get_next_block(code, blocks, s, 0)["delete"] = False
				add_block_to_worklist(get_next_block(code, blocks, s, 0), worklist)
			
		if "dest" in s:
			#any overloaded variable cannot chance state
			if variables[s["dest"]]["evidence"] != "over":
				#Any executable statement v := x op y with x and y constant and exectuable , set v to constant x op y
				#Any executable statement v := x op y with x or y is overloaded and exectuable, set v overloaded
				if is_executable (code, s["src1"], variables):
					if s["op"] == "MOV":
						if is_constant_val(s["src1"], variables):
							if get_value (variables, s["dest"]) == "never":
								variables [s["dest"]]["evidence"] = get_value (variables, s["src1"])
								update_worklist(code, worklist, s)
							elif get_value (variables, s["dest"]) != get_value (variables, s["dest"]):
								variables [s["dest"]]["evidence"] = "over"
								update_worklist(code, worklist, s)
						else:
							variables [s["dest"]]["evidence"] = "over"
							update_worklist(code, worklist, s)
							
					if s["op"] in FOLDABLE_OPS:
						if is_executable (code, s["src2"], variables):
							if is_constant_val(s["src1"], variables) and is_constant_val(s["src2"], variables):
								try:
									val1 = int(get_value(variables, s["src1"])[1:])
									val2 = int(get_value(variables, s["src2"])[1:])
								except ValueError:
									return
								const = "#" + str(_do_op(s["op"], val1, val2))
								
								if get_value (variables, s["dest"]) == "never":
									variables [s["dest"]]["evidence"] = const
									update_worklist(code, worklist, s)
								elif get_value (variables, s["dest"]) != const:
									variables [s["dest"]]["evidence"] = "over"
									update_worklist(code, worklist, s)
							else:
								variables [s["dest"]]["evidence"] = "over"
								update_worklist(code, worklist, s)
				
				# If v assigned from phi op, and if all srcs that are constant and executable are the same and there are no variables that have seen evidence of use, assign constant value to v. 
				# If v assigned from phi op, and at least 2 srcs are different constants and are executable, v is a overloaded
				# If v assigned from phi op, and at least 1 srcs is overloaded and is executable, v is overloaded
				if s["op"] == "phi":
					operands = [s[x] for x in s if x.startswith("src")]		
					for o in operands:
						if is_executable (code, o, variables):
							if is_constant_val(o, variables):
								if get_value (variables, s["dest"]) == "never":
									variables [s["dest"]]["evidence"] = get_value (variables, o)
									update_worklist(code, worklist, s)
								elif get_value (variables, s["dest"]) != get_value (variables, o):
									variables [s["dest"]]["evidence"] = "over"
									update_worklist(code, worklist, s)
							else:
								variables [s["dest"]]["evidence"] = "over"
								update_worklist(code, worklist, s)
								
				# If value loaded from memory, evidence of overloading
				if s["op"] in MEMORY_OPS:
					variables[s["dest"]]["evidence"] = "over"
					update_worklist(code, worklist, s)
					
		if s["op"] == "CMP":
			# if branch instruction, if either src is a overloaded, then both paths may be executed and should be added to the worklist to be marked as such and their statements analysed. 
			if is_var(s["src1"], variables) or is_var(s["src2"], variables):
				add_block_to_worklist(get_next_block(code, blocks, s, 0) , worklist)
				get_next_block(code, blocks, s, 0)["delete"] = False
				add_block_to_worklist(get_next_block(code, blocks, s, 1) , worklist)
				get_next_block(code, blocks, s, 1)["delete"] = False
				
			#If a branch and both srcs are constant, add appropriate path to work path. 
			else:
				val1 = int(get_value(variables,s["src1"])[1:])
				val2 = int(get_value(variables,s["src2"])[1:])
				if val1 > val2 :
					branch = "gt"
				elif val1 < val2 :
					branch = "lt"
				else:
					branch = "eq"
						
		#Note - these do not take in to account all possible instructions in the arm instruction set, such as any operation being conditional
		if branch != "nil":
			if s["op"] == "BEQ":	
				if branch == "eq":
					get_next_block(code, blocks, s, 0)["delete"] = False
					add_block_to_worklist(get_next_block(code, blocks, s, 0) , worklist)
				else:
					get_next_block(code, blocks, s, 1)["delete"] = False
					add_block_to_worklist(get_next_block(code, blocks, s, 1) , worklist)
			if s["op"] == "BNE":
				if branch != "eq":
					get_next_block(code, blocks, s, 0)["delete"] = False
					add_block_to_worklist(get_next_block(code, blocks, s, 0) , worklist)
				else:
					get_next_block(code, blocks, s, 1)["delete"] = False
					add_block_to_worklist(get_next_block(code, blocks, s, 1) , worklist)
			if s["op"] == "BLT":
				if branch == "lt":
					get_next_block(code, blocks, s, 0)["delete"] = False
					add_block_to_worklist(get_next_block(code, blocks, s, 0) , worklist)
				else:
					get_next_block(code, blocks, s, 1)["delete"] = False
					add_block_to_worklist(get_next_block(code, blocks, s, 1) , worklist)
			if s["op"] == "BLE":
				if branch == "eq" or branch == "lt" :
					get_next_block(code, blocks, s, 0)["delete"] = False
					add_block_to_worklist(get_next_block(code, blocks, s, 0) , worklist)
				else:
					get_next_block(code, blocks, s, 1)["delete"] = False
					add_block_to_worklist(get_next_block(code, blocks, s, 1) , worklist)
			if s["op"] == "BGT":
				if branch == "gt":
					get_next_block(code, blocks, s, 0)["delete"] = False
					add_block_to_worklist(get_next_block(code, blocks, s, 0) , worklist)
				else:
					get_next_block(code, blocks, s, 1)["delete"] = False
					add_block_to_worklist(get_next_block(code, blocks, s, 1) , worklist)
			if s["op"] == "BGE":
				if branch == "eq" or branch == "gt" :
					get_next_block(code, blocks, s, 0)["delete"] = False
					add_block_to_worklist(get_next_block(code, blocks, s, 0) , worklist)
				else:
					get_next_block(code, blocks, s, 1)["delete"] = False
					add_block_to_worklist(get_next_block(code, blocks, s, 1) , worklist)

						

	# Delete any block that is not executed
	for block in code["blocks"]:
		i = 0
		#delete references to deleted blocks
		while i < len(block["next_block"]):
			if code["blocks"][blocks[block["next_block"][i]]]["delete"]:
				del block["next_block"][i]
			else:
				i += 1
				
	for block in code["blocks"]:
		if not block["delete"]:
			del block["delete"]
 
			
	i = 0
	while i < len(code["blocks"]):
		if "delete" in code["blocks"][i]:
			del code["blocks"][i]
		else:
			i += 1
			
	worklistfix = []
	for block in code["blocks"]:
		for statement in block["code"]:
			worklistfix.append(statement)
			
	while len(worklistfix):
		s = worklistfix.pop(0)
		#propogate constants
		if "dest" in s:
			if variables[s["dest"]]["evidence"].startswith('#'):
				_propagate_constant(code, s, variables[s["dest"]]["evidence"])
		
		#remove any branch ops that are constant
		if s["op"] == "CMP":
			if is_constant_val(s["src1"], variables) and is_constant_val(s["src2"], variables):
				print s
				remove_statement(code, s)
		if s["op"] in CONDITIONAL_BRANCH:
			block = get_block(s, code, blocks)["code"]
			if not any(statement["op"] == "CMP" for statement in block):
				remove_statement(code, s)
			
		if s["block"]:
				del s["block"]
			

			
def get_block(statement, code, blocks):
	return code["blocks"][blocks[statement["block"]]]

def get_next_block(code, blocks, statement, direction):
	return code["blocks"][blocks[get_block(statement, code, blocks)["next_block"][direction]]]
	
def add_block_to_worklist(block, worklist):
	for statement in block["code"]:
		statement["block"] = block["name"]	
		worklist.append(statement)

def update_worklist(code, worklist, s):
	var = s["dest"]
	for block in code["blocks"]:
		if not block["delete"]:
			for statement in block["code"]:
				statement["block"] = block["name"]
				if s != statement:
					for field in statement:
						if statement[field] == var:
							if statement not in worklist:
								worklist.append(statement)									
						
"""
True if `val` is a constant literal.
"""
def is_constant_val(val, variables):
	if val.startswith('#') or variables[val]["evidence"].startswith('#'):
		return True
	else:
		return False
		
"""
True if `val` is a variable. Always true if `is_constant_val` is false.
"""
def is_var(val, variables):
    return not is_constant_val(val, variables)		
		
		
def is_executable (code, var, variables):
	if var.startswith('#'):
		return True
	blocks = get_blocks(code)
	return not code["blocks"][blocks[variables[var]["def_site"].get("block")]]["delete"]

	
	
def _propagate_constant(code, statement, const):
    val = const
    var = statement["dest"]
    remove_statement(code, statement)
    for block in code["blocks"]:
        for statement in block["code"]:
            for field in statement:
                if statement[field] == var:
                    statement[field] = val
					

def get_value (variables, var):
	if var.startswith('#'):
		return var
	return variables [var]["evidence"]

	
def main():
    with open('example.json') as input_code:
        code = json.loads(input_code.read())
        cfg = toSSA(code)
        #constant_propagation(code)
        #print json.dumps(code, indent=4)
        conditional_propagation(code)
        print json.dumps(code, indent=4)


if __name__ == "__main__":
    main()

			
