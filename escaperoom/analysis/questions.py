import json
import pandas as pd
import os

def analyse(episode_interactions):

    moves_made = 0
    efficient_moves = 0
    questions_asked = 0
    failed_escapes = 0
    successful_escapes = 0

    for turn_idx, turn in enumerate(episode_interactions["turns"]):
        # Walk through log_to_self items from DGM
        for event in turn:
            action = event["action"]
            if action["type"] == "move":
                moves_made += 1
                if action["content"] == "efficient":
                    efficient_moves += 1
            elif action["type"] == "question":
                questions_asked += 1
            elif action["type"] == "escape":
                if action["content"] == "success":
                    successful_escapes += 1
                else:
                    failed_escapes += 1

    return questions_asked, moves_made, efficient_moves, failed_escapes, successful_escapes


def walk_results():
    interaction_files = []

    base_dir = 'results'
    for dirname, _, filenames in os.walk(base_dir):
        for filename in filenames:
            filepath = os.path.join(dirname, filename)
            if filename.endswith("interactions.json"):
                interaction_files.append(filepath)

    ints = 0
    for file in interaction_files:
        with open(file, 'r') as f:
            episode_interactions = json.load(f)

        qa, mm, em, fe, se = analyse(episode_interactions)
        if qa:
            ints += 1
            print(file, qa, mm, em, fe, se)

    print(ints)

if __name__ == '__main__':
    walk_results()