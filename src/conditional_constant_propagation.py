import json
from ssa import toSSA
from util import (remove_statement,
                  is_var,
                  is_copy,
                  is_constant_val,
                  is_constant_phi,
				  get_variables,
				  remove_block)
	
	
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
	
	variables = get_variables(code)
	#for v in variables:
	#	v["evidence"]=False
		
		
	while len(worklist):
		b = worklist.pop(0)
		b["delete"] = False 	
		#if len(b["next_block"])
		#	worklist.append(b["next_block"])
		#for s in b["code"]:
	
	for block in code["blocks"]:
		if block["delete"] is True:
			remove_block(code,block)
			#print json.dumps(block, indent=4)
	
def main():
    with open('example.json') as input_code:
        code = json.loads(input_code.read())
        cfg = toSSA(code)
        conditional_propagation(code)
        print json.dumps(code, indent=4)


if __name__ == "__main__":
    main()

			