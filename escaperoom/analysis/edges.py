import json
import os

instances_path = os.path.join("escaperoom", "in", "instances.json")

with open(instances_path) as f:
    instances = json.load(f)

edges = []
for exps in instances["experiments"]:
    game_instances = exps["game_instances"]
    for game_instance in game_instances:
        unnamed_edges = game_instance["unnamed_edges"]
        edges.append(len(unnamed_edges))
        if len(unnamed_edges) == 10:
            print(len(unnamed_edges), exps["name"], game_instance["game_id"])


print(max(edges), min(edges), sum(edges) / len(edges))