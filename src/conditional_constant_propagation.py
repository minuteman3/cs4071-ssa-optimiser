import json
from ssa import toSSA
from constant_propagation import constant_propagation
from util import (remove_statement,
                  is_var,
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


"""
Driving function for the Conditional Constant Propagation
 specified in the SSA Optimization Algorithms handout.

 Marks code as not executed, constant, variable.
 Then deletes none executed code and transforms constant code in place. 
 
"""
variables = 0

def conditional_propagation(code):
	worklist = []
	for block in code["blocks"]:
		#Entry block is always executable
		if block["name"] == "b1":
			worklist.append(block)
		block["delete"] = True
		
	blocks = get_blocks(code)
	global variables 
	variables = get_variables(code)
	
	
	#print json.dumps(statements, indent=4) 

	for v in variables: 
		# Variables with no definition must be input to the program  
		if variables[v].has_key("def_site"):
			variables[v]["evidence"] = False 
		else:
			variables[v]["evidence"] = True
	
		
	while len(worklist):
		b = worklist.pop(0)
		b["delete"] = False
		# Executable Blocks with only 1 successor, that block must also be executable 
		if len(b["next_block"]) == 1:  
			#print json.dumps(code["blocks"][blocks[b["next_block"][0]]], indent=4)	
			worklist.append(code["blocks"][blocks[b["next_block"][0]]])
		
		statements = get_statements_in_block(b)		
		branch = "nil"
		for s in statements:
			if is_copy (s["statement"]):
					if variables[s["statement"]["dest"]]["evidence"] == False:
				 		variables[s["statement"]["dest"]]["evidence"] = s["statement"]["src1"]
					else:
						variables[s["statement"]["dest"]]["evidence"] = True

			if s["statement"]["op"] in FOLDABLE_OPS:
			
				#Any executable statement v := x op y with x and y constant, set v to constant x op y (This feels redundant following constant propagation but is in notes given ).
				if is_constant_val(s["statement"]["src1"]) and is_constant_val(s["statement"]["src2"]):
					if is_constant_val(s["statement"]["src1"]):
						variables[s["statement"]["dest"]]["evidence"] = s["statement"]["src1"]
					else:
						variables[s["statement"]["dest"]]["evidence"] = variables[s["statement"]["src1"]]["evidence"]

				#If evidence has been found that at least 1 of the source values will have at least 2 different values, then v is also a true variable. 
				elif variables[s["statement"]["src1"]]["evidence"] or variables[s["statement"]["src2"]]["evidence"]:
					variables[s["statement"]["dest"]]["evidence"] = True
			
			# If value loaded from memory, evidence of true variable
			if s["statement"]["op"] in MEMORY_OPS:
				variables[s["statement"]["dest"]]["evidence"] = True
				
			if s["statement"]["op"] == "phi":
				operands = [s["statement"][x] for x in s["statement"] if x.startswith("src")]
				# If v assigned from phi op, and at least 2 srcs are constant and are executable, v is a true variable
				for o in operands:
					for n in operands:
						if o != n and is_constant_val(o) and is_constant_val(n) and is_executable(code, o) and is_executable(code, n):
							variables[s["statement"]["dest"]]["evidence"] = True
							
				# If v assigned from phi op, and at least 1 srcs is a true variable and is executable, v is a true variable
				for o in operands:
						if is_var(o) and is_executable(code, o):
							variables[s["statement"]["dest"]]["evidence"] = True
				
				# If v assigned from phi op, and if all srcs that are constant and executable are the same and there are no variables that have seen evidence of use, assign constant value to v. 				
				for o in operands:
					for n in operands:
						if variables[n].has_key("evidence"):
							evidence = variables[n]["evidence"]
						else:
							evidence = False
						if is_constant_val(o) and is_executable(code, o) and (not is_executable(code, n) or (o == n and is_constant_val(n)) or not evidence):
							print "-----------------------------------------"
							#print get_value (variables, s, o);
							#print get_value (variables, s, n);
							#print variables[s["statement"]["dest"]]["evidence"]
                                        		#variables[s["statement"]["dest"]]["evidence"] = s["statement"]["src1"]
							#print variables[s["statement"]["dest"]]["evidence"]
							#print json.dumps( s["statement"], indent=4)
							#print "########################################"
							#print json.dumps( variables[s["statement"]["dest"]], indent=4)
							#_propagate_constant(code, s["statement"], o)
							
			if s["statement"]["op"] == "CMP":
				# if branch instruction, if either src is a confirmed variable, then both paths may be executed and should be added to the worklist to be marked as such and their statements analysed. 
				if is_var(s["statement"]["src1"]) or is_var(s["statement"]["src2"]):
					if not code["blocks"][blocks[b["next_block"][0]]]["delete"]:
						worklist.append(code["blocks"][blocks[b["next_block"][0]]])
					if not code["blocks"][blocks[b["next_block"][1]]]["delete"]:
						worklist.append(code["blocks"][blocks[b["next_block"][1]]])
				
				#If a branch and both srcs are constant, add appropriate path to work path. 
				if is_constant_val(s["statement"]["src1"]) and is_constant_val(s["statement"]["src2"]):
					print variables[s["statement"]["src1"]]["evidence"]
					print s["statement"]["src2"]
					val1 = 1
					val2 = 0

					if val1 > val2 :
						branch = "gt"
					elif val1 < val2 :
						branch = "lt"
					else:
						branch = "eq"

					
			#Note - these do not take in to account all possible instructions in the arm instruction set
			if branch != "nil":
				if s["statement"]["op"] == "BEQ":	
					if branch == "eq":
						worklist.append(code["blocks"][blocks[b["next_block"][0]]])
					else:
						worklist.append(code["blocks"][blocks[b["next_block"][1]]])
				if s["statement"]["op"] == "BNE":
					if branch != "eq":
						worklist.append(code["blocks"][blocks[b["next_block"][0]]])
					else:
						worklist.append(code["blocks"][blocks[b["next_block"][1]]])
				if s["statement"]["op"] == "BLT":
					if branch == "lt":
						worklist.append(code["blocks"][blocks[b["next_block"][0]]])
					else:
						worklist.append(code["blocks"][blocks[b["next_block"][1]]])
				if s["statement"]["op"] == "BLE":
					if branch == "eq" or branch == "lt" :
						worklist.append(code["blocks"][blocks[b["next_block"][0]]])
					else:
						worklist.append(code["blocks"][blocks[b["next_block"][1]]])
				if s["statement"]["op"] == "BGT":
					if branch == "gt":
						worklist.append(code["blocks"][blocks[b["next_block"][0]]])
					else:
						worklist.append(code["blocks"][blocks[b["next_block"][1]]])
				if s["statement"]["op"] == "BGE":
					if branch == "eq" or branch == "gt" :
						worklist.append(code["blocks"][blocks[b["next_block"][0]]])
						del b["next_block"][0]
					else:
						worklist.append(code["blocks"][blocks[b["next_block"][1]]])
						
	# Delete any block that is not executed
	for block in code["blocks"]:
		if not block["delete"]:
			del block["delete"]
	
	i = 0
	while i < len(code["blocks"]):
		if "delete" in code["blocks"][i]:
			del code["blocks"][i]
		else:
			i += 1


"""
True if `val` is a constant literal.
"""
def is_constant_val(val):
	if val.startswith('#') or variables[val]["evidence"]:
		return True
	else:
		return False
		
		
def is_executable (code, var):
	if is_constant_val(var):
		return True
	blocks = get_blocks(code)
	variables = get_variables(code)
	if "delete" in code["blocks"][blocks[variables[var]["def_site"].get("block")]]:
		return code["blocks"][blocks[variables[var]["def_site"].get("block")]]["delete"]
	else:
		return True
	
	
def _propagate_constant(code, statement, const):
    val = const
    var = statement["dest"]
    remove_statement(code, statement)
    for block in code["blocks"]:
        for statement in block["code"]:
            for field in statement:
                if statement[field] == var:
                    statement[field] = val

def get_value (variables, s, var):
	if is_constant_val(var):
		return var
	return variables[s["statement"]["dest"]]["evidence"]
	
def main():
    with open('example.json') as input_code:
        code = json.loads(input_code.read())
        cfg = toSSA(code)
        #constant_propagation(code)
        #print json.dumps(code, indent=4)
        conditional_propagation(code)
        #print json.dumps(code, indent=4)

		
"""
	for v in variables: 
		print "#####################"	
		print json.dumps(v, indent=4) 
		print json.dumps(variables[v], indent=4) 

"""
if __name__ == "__main__":
    main()

			
