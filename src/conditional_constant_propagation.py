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
				  get_statements_in_block)

FOLDABLE_OPS = ["MUL", "SUB", "RSB", "ADD"]	
	
"""
Driving function for the Conditional Constant Propagation
 specified in the SSA Optimization Algorithms handout.

 Marks code as not executed, constant, variable.
 Then deletes none executed code and transforms constant code in place. 
 
"""

def conditional_propagation(code):
	worklist = []
	for block in code["blocks"]:
		#Entry block is always executable
		if block["name"] == "b1":
			worklist.append(block)
		block["delete"] = True
		
	blocks = get_blocks(code)
	variables = get_variables(code)
	
	
	#print json.dumps(statements, indent=4) 

	for v in variables: 
		# Variables with no definition must be input to the program  
		if variables[v].has_key("def_site"):
			variables[v]["evidence"] = False 
		else:
			variables[v]["evidence"] = True
	#print json.dumps(variables, indent=4)	
		
	while len(worklist):
		b = worklist.pop(0)
		del b["delete"]  
		# Executable Blocks with only 1 successor, that block must also be executable 
		if len(b["next_block"]) == 1:  
			worklist.append(code["blocks"][blocks[b["next_block"][0]]])
		
		statements = get_statements_in_block(b)		
		#Any executable statement v := x op y with x and y constant, set v to constant x op y (This feels redundant following constant propagation but is in notes given ). If evidence has been found that at least 1 of the source values will have at least 2 different values, then v is also a true variable. 
		for s in statements:
			if s["statement"]["op"] in FOLDABLE_OPS:
				if is_constant_val(s["statement"]["src1"]) and is_constant_val(s["statement"]["src2"]):
					_fold_constant(s["statement"])
					variables[s["statement"]["dest"]]["evidence"] = "constant"
				elif variables[s["statement"]["src1"]]["evidence"] or variables[s["statement"]["src2"]]["evidence"]:
					variables[s["statement"]["dest"]]["evidence"] = True
					
				
		#print json.dumps(variables, indent=4)		
		#for s in b["code"]:
	
	i = 0
	while i < len(code["blocks"]):
		if "delete" in code["blocks"][i]:
			del code["blocks"][i]
		else:
			i += 1

	
def main():
    with open('example.json') as input_code:
        code = json.loads(input_code.read())
        cfg = toSSA(code)
       # constant_propagation(code)
        #print json.dumps(code, indent=4)
        conditional_propagation(code)
        print json.dumps(code, indent=4)


if __name__ == "__main__":
    main()

			