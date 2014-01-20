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


"""
Driving function for the Conditional Constant Propagation
 specified in the SSA Optimization Algorithms handout.

 Marks code as not executed, constant, variable.
 Then deletes none executed code and transforms constant code in place. 
 
"""
variables = 0

def conditional_propagation(code):
	worklistBlock = []
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
			worklistBlock.append(block)
			
	while len(worklistBlock):
		branch = "nil"
		b = worklistBlock.pop(0)			
		b["delete"] = False
			
		# Executable Blocks with only 1 successor, that block must also be executable 
		if len(b["next_block"]) == 1:  
			code["blocks"][blocks[b["next_block"][0]]]["delete"] = False
			worklistBlock.append(code["blocks"][blocks[b["next_block"][0]]])	
			
		worklistState = []	
		for statement in b["code"]:
						statement["block"] = b["name"]	
						worklistState.append(statement)
						
		while len(worklistState):
			s = worklistState.pop(0)
			
			if "dest" in s:
				if variables[s["dest"]]["evidence"] != "over":
				
					if is_executable (code, s["src1"], variables):
						if s["op"] == "MOV":
						 	if is_constant_val(s["src1"], variables):
								if get_value (variables, s["dest"]) == "never":
									variables [s["dest"]]["evidence"] = get_value (variables, s["src1"])
									update_worklist(code, worklistState, s)
								elif get_value (variables, s["dest"]) != get_value (variables, s["dest"]):
									variables [s["dest"]]["evidence"] = "over"
									update_worklist(code, worklistState, s)
							else:
								variables [s["dest"]]["evidence"] = "over"
								update_worklist(code, worklistState, s)
								
						if s["op"] in FOLDABLE_OPS:
							if is_executable (code, s["src2"], variables):
								if is_constant_val(s["src1"], variables) and is_constant_val(s["src2"], variables):
									try:
										val1 = int(get_value(variables, s["src1"])[1:])
										val2 = int(get_value(variables, s["src2"])[1:])
									except ValueError:
										return
									const = "#" + str(_do_op(statement["op"], val1, val2))
									
									if get_value (variables, s["dest"]) == "never":
										variables [s["dest"]]["evidence"] = const
										update_worklist(code, worklistState, s)
									elif get_value (variables, s["dest"]) != const:
										variables [s["dest"]]["evidence"] = "over"
										update_worklist(code, worklistState, s)
								else:
									variables [s["dest"]]["evidence"] = "over"
									update_worklist(code, worklistState, s)
					
					if s["op"] == "phi":
						operands = [s[x] for x in s if x.startswith("src")]		
						for o in operands:
							if is_executable (code, o, variables):
								if is_constant_val(o, variables):
									if get_value (variables, s["dest"]) == "never":
										variables [s["dest"]]["evidence"] = get_value (variables, o)
										update_worklist(code, worklistState, s)
									elif get_value (variables, s["dest"]) != get_value (variables, s["dest"]):
										variables [s["dest"]]["evidence"] = "over"
										update_worklist(code, worklistState, s)
								else:
									variables [s["dest"]]["evidence"] = "over"
									update_worklist(code, worklistState, s)
					
					if s["op"] in MEMORY_OPS:
						variables[s["dest"]]["evidence"] = "over"
						update_worklist(code, worklistState, s)
						
			if s["op"] == "CMP":
					# if branch instruction, if either src is a confirmed variable, then both paths may be executed and should be added to the worklist to be marked as such and their statements analysed. 
				if is_var(s["src1"], variables) or is_var(s["src2"], variables):
					if not code["blocks"][blocks[b["next_block"][0]]]["delete"]:
						worklistBlock.append(code["blocks"][blocks[b["next_block"][0]]])
					if not code["blocks"][blocks[b["next_block"][1]]]["delete"]:
						worklistBlock.append(code["blocks"][blocks[b["next_block"][1]]])
					
				#If a branch and both srcs are constant, add appropriate path to work path. 
				if is_constant_val(s["src1"],variables) and is_constant_val(s["src2"],variables):
	#print variables[s["src1"]]["evidence"]
					#print s["src2"]
					val1 = int(get_value(variables,s["src1"])[1:])
					val2 = int(get_value(variables,s["src2"])[1:])
					if val1 < val2 :
						branch = "gt"
					elif val1 > val2 :
						branch = "lt"
					else:
						branch = "eq"
							
			#Note - these do not take in to account all possible instructions in the arm instruction set
			if branch != "nil":
				if s["op"] == "BEQ":	
					if branch == "eq":
						worklistBlock.append(code["blocks"][blocks[b["next_block"][1]]])
					else:
						worklistBlock.append(code["blocks"][blocks[b["next_block"][0]]])
				if s["op"] == "BNE":
					if branch != "eq":
						worklistBlock.append(code["blocks"][blocks[b["next_block"][1]]])
					else:
						worklistBlock.append(code["blocks"][blocks[b["next_block"][0]]])
				if s["op"] == "BLT":
					if branch == "lt":
						worklistBlock.append(code["blocks"][blocks[b["next_block"][1]]])
					else:
						worklistBlock.append(code["blocks"][blocks[b["next_block"][0]]])
				if s["op"] == "BLE":
					if branch == "eq" or branch == "lt" :
						worklistBlock.append(code["blocks"][blocks[b["next_block"][1]]])
					else:
						worklistBlock.append(code["blocks"][blocks[b["next_block"][0]]])
				if s["op"] == "BGT":
					if branch == "gt":
						worklistBlock.append(code["blocks"][blocks[b["next_block"][1]]])
					else:
						worklistBlock.append(code["blocks"][blocks[b["next_block"][0]]])
				if s["op"] == "BGE":
					if branch == "eq" or branch == "gt" :
						worklistBlock.append(code["blocks"][blocks[b["next_block"][1]]])
						del b["next_block"][0]
					else:
						worklistBlock.append(code["blocks"][blocks[b["next_block"][0]]])
							
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


def update_worklist(code, worklist, statement):
	var = statement["dest"]
	for block in code["blocks"]:
		if not block["delete"]:
			for statement in block["code"]:
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


	for v in variables: 
		print ""	
		print json.dumps(v, indent=4) 
		print json.dumps(variables[v]["evidence"], indent=4) 

if __name__ == "__main__":
    main()

			
