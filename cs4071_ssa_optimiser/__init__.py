from .constant_propagation import constant_propagation
from .dead_code_elimination import dead_code_elimination
from .ssa import toSSA

def optimise(code):
    toSSA(code)
    constant_propagation(code)
    dead_code_elimination(code)
    return code
