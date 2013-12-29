import json
from ssa import toSSA
from graphs import Graph
from util import build_graph

LIVE_OPS = ["LDR", "STR", "BX", "BL", "SWI"]

def aggressive_dead_code_elimination(code):
    cdg = build_graph(code).control_dependence_graph()

def mark(code):
    for block in code["blocks"]:
        for statement in block["code"]:
            if statement["op"] in LIVE_OPS:
                statement["live"] = True

def main():
    with open('example.json') as input_code:
        code = json.loads(input_code.read())
        cfg = toSSA(code)
        aggressive_dead_code_elimination(code)
        #print json.dumps(code, indent=4)

if __name__ == "__main__":
    main()
