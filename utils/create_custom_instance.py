import json
import os
import pandas as pd

base_dir = "results_paper/KimiVL-A3B-Thinking-t0.0--KimiVL-A3B-Thinking-t0.0/escape_room"

exps_to_dir = {"large": '2_large', "star": '11_star', "ladder": '10_ladder', "medium_ambiguity": '4_medium_ambiguity',
        "small": '0_small', "medium": '1_medium', "path": '9_path', "high_ambiguity": '5_high_ambiguity',
        "tree": '12_tree', "low_dual_ambiguity": '6_low_dual_ambiguity', "no_ambiguity": '3_no_ambiguity',
        "medium_dual_ambiguity": '7_medium_dual_ambiguity', "high_dual_ambiguity": '8_high_dual_ambiguity',
        "adjacent": '13_adjacent', "near": '14_near', "far": "15_far"}

dirs_to_exp = {v: k for k, v in exps_to_dir.items()}

custom_instances = {"experiments": []}

raw_df = pd.read_csv("results_paper/raw.csv")


instance_paths = []
for dirname,_, filenames in os.walk(base_dir):
    for filename in filenames:
        if filename.endswith("instance.json"):
            file_path = os.path.join(dirname, filename)
            if "o4-mini-t0.0--o4-mini-t0.0" in file_path:
                interactions_file = file_path.replace("instance.json", "interactions.json")
                if not os.path.exists(interactions_file):
                    instance_paths.append(file_path)


exp_data = {}
instance_paths.sort()
for file in instance_paths:
    interactions_file = file.replace("instance.json", "interactions.json")
    if not os.path.exists(interactions_file):
        exp_split = file.split("/")[-3]
        exp_name = dirs_to_exp[exp_split]
        with open(file) as json_file:
            inst = json.load(json_file)
            if exp_name not in exp_data:
                exp_data[exp_name] = {"name": exp_name, "game_instances": [inst]}
            else:
                exp_data[exp_name]["game_instances"].append(inst)

print(len(instance_paths))
for k, v in exp_data.items():
    custom_instances["experiments"].append(v)

with open(os.path.join("escaperoom", "in", "custom_instances.json"), "w") as f:
    json.dump(custom_instances, f, indent=4)

