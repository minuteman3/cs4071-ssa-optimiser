from .constant_propagation import constant_propagation
from .conditional_constant_propagation import conditional_propagation
from .dead_code_elimination import dead_code_elimination
from .ssa import toSSA
from .fromSSA import fromSSA
from .aggressive_dead_code_elimination import aggressive_dead_code_elimination
import json


def optimise(code):
    toSSA(code)
    conditional_propagation(code)
    constant_propagation(code)
    dead_code_elimination(code)
    aggressive_dead_code_elimination(code)
    #conditional_propagation(code)
    constant_propagation(code)
    fromSSA(code)
    return code
