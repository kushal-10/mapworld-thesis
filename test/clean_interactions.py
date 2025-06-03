import json

int_path = "results/gpt-4o-mini-2024-07-18-t0.0--gpt-4o-mini-2024-07-18-t0.0/escape_room/0_small/episode_9/interactions.json"

# base_path = "results/gpt-4o-mini-2024-07-18-t0.0--gpt-4o-mini-2024-07-18-t0.0/escape_room/0_small/episode_"
base_path = "results/gpt-4.1-mini-t0.0--gpt-4.1-mini-t0.0/escape_room/0_small/episode_"
file_path = "/interactions.json"

for i in range(10):
    int_path = base_path + str(i) + file_path
    with open(int_path, "r") as f:
        json_data = json.load(f)

    save_path = f"results/temp_interactions_{i}.json"
    with open(save_path, "w") as f:
        json.dump(json_data, f, indent=4)