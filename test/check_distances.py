import os
import json
import ast

with open(os.path.join("escaperoom", "in", "instances.json"), "r") as f:
    json_data = json.load(f)


exps = json_data["experiments"]

e1 = exps[0]

insts = 0
st_dists = 0
for e in exps:
    for inst in e["game_instances"]:
        insts += 1
        st1 = ast.literal_eval(inst["start_node"])
        st2 = ast.literal_eval(inst["target_node"])
        st_dist = abs(st1[0] - st2[0]) + abs(st1[1] - st2[1])
        st_dists += st_dist

print(st_dists/insts) # 1.7 avg