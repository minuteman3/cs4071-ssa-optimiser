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
				  get_statements)

	
	
"""
Driving function for the Conditional Constant Propagation
 specified in the SSA Optimization Algorithms handout.

 Marks code as not executed, constant, variable.
 Then deletes none executed code and transforms constant code in place. 

 Currently missing check for any variable with no definition - inputs to program
 
"""

def conditional_propagation(code):
	worklist = []
	for block in code["blocks"]:
		if block["name"] == "b1":
			worklist.append(block)
		block["delete"] = True
		
	blocks = get_blocks(code)
	variables = get_variables(code)
	statements = get_statements(code)
	
	#print json.dumps(statements, indent=4) 

	for v in variables: 
		variables[v]["evidence"]=False
	#print json.dumps(variables, indent=4)	
		
	while len(worklist):
		b = worklist.pop(0)
		del b["delete"]  	
		if len(b["next_block"]) == 1:  
			worklist.append(code["blocks"][blocks[b["next_block"][0]]])
				
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
        constant_propagation(code)
        print json.dumps(code, indent=4)
        conditional_propagation(code)
        #print json.dumps(code, indent=4)


if __name__ == "__main__":
    main()

			