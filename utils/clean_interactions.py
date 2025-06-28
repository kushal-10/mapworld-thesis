import json
import os

results_path = "results"

for dirname, _, filenames in os.walk(results_path):
    for filename in filenames:
        if filename.endswith("interactions.json") or filename.endswith("requests.json"):
            filepath = os.path.join(dirname, filename)
            with open(filepath, 'r') as f:
                json_data = json.load(f)

            with open(filepath, 'w') as f:
                json.dump(json_data, f, indent=4)