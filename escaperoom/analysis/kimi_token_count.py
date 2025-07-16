import json
import os
import pandas as pd

base_dir = "results/KimiVL-A3B-Thinking-t0.0--KimiVL-A3B-Thinking-t0.0/escape_room"

raw_df = pd.read_csv("results/raw.csv")

exps_to_dir = {"large": '2_large', "star": '11_star', "ladder": '10_ladder', "medium_ambiguity": '4_medium_ambiguity',
        "small": '0_small', "medium": '1_medium', "path": '9_path', "high_ambiguity": '5_high_ambiguity',
        "tree": '12_tree', "low_dual_ambiguity": '6_low_dual_ambiguity', "no_ambiguity": '3_no_ambiguity',
        "medium_dual_ambiguity": '7_medium_dual_ambiguity', "high_dual_ambiguity": '8_high_dual_ambiguity',
        "adjacent": '13_adjacent'}

dirs_to_exp = {v: k for k, v in exps_to_dir.items()}

aborted_files = []
for i in range(len(raw_df)):
    if raw_df.iloc[i]["model"] == "KimiVL-A3B-Thinking-t0.0--KimiVL-A3B-Thinking-t0.0":
        if raw_df.iloc[i]["metric"] == "Aborted":
            if raw_df.iloc[i]["value"] == 1.0:
                episode = raw_df.iloc[i]["episode"]
                experiment = raw_df.iloc[i]["experiment"]
                file_path = os.path.join(base_dir, experiment, episode, "thoughts.json")

thought_files = []
for dirname, _, filenames in os.walk(base_dir):
    for filename in filenames:
        if filename.endswith("thoughts.json"):
            file_path = os.path.join(dirname, filename)
            if file_path not in aborted_files:
                thought_files.append(file_path)

counts = []
for file_path in thought_files:
    with open(file_path) as f:
        thoughts = json.load(f)
    turns = thoughts["turns"]

    for turn in turns:
        for t in turn:
            if t["action"]["type"] == "get message":
                response = t["action"]["content"]
                splits = response.split(" ")
                if len(splits) == 1:
                    print(file_path)
                counts.append(len(splits))

print(sum(counts)/len(counts), max(counts), min(counts))

counts.sort()
print(counts)