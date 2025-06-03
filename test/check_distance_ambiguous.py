import os
import json
import ast

with open(os.path.join("escaperoom_ambiguous", "in", "instances.json"), "r") as f:
    json_data = json.load(f)


exps = json_data["experiments"]

e1 = exps[1]
distances = 0
insts = 0

st_dists = 0
for inst in e1["game_instances"]:
    insts += 1
    n2c = inst["node_to_category"]

    nodes = {}
    for k, v in n2c.items():
        if v.endswith("1") or v.endswith("2") or v.endswith("3"):
            vsp = v[:-2].strip()
            if vsp not in nodes:
                nodes[vsp] = [k]
            else:
                nodes[vsp].append(k)

    set1_dist = 0
    set2_dist = 0
    for k in nodes.keys():
        nodes_1 = nodes[k]

        if len(nodes_1) == 2:
            node1 = ast.literal_eval(nodes_1[0])
            node2 = ast.literal_eval(nodes_1[1])
            set1_dist = abs(node1[0] - node2[0]) + abs(node1[1] - node2[1])
        else:
            node1 = ast.literal_eval(nodes_1[0])
            node2 = ast.literal_eval(nodes_1[1])
            node3 = ast.literal_eval(nodes_1[2])
            dist1 = abs(node1[0] - node3[0]) + abs(node1[1] - node3[1])
            dist2 = abs(node2[0] - node3[0]) + abs(node2[1] - node3[1])
            dist3 = abs(node1[0] - node2[0]) + abs(node1[1] - node2[1])
            set2_dist = (dist1 + dist2 + dist3)/2

    distances += (set1_dist + set2_dist)/2

    st1 = ast.literal_eval(inst["start_node"])
    st2 = ast.literal_eval(inst["target_node"])
    st_dist = abs(st1[0] - st2[0]) + abs(st1[1] - st2[1])
    st_dists += st_dist


print(distances/insts) # 2.0 avg for [2] || 2.1333 for [3] || 1.6 avg for [2,3]
print(st_dists/insts) # 2.1 avg for [2] || 2.2 for [3] || 2.2 avg for [2,3]