import os

import numpy as np
from clemcore.clemgame import GameInstanceGenerator

from engine.map_assignments import assign_room_categories, assign_images
from engine.maps import BaseMap

# TODO:  Add self.tags and every "English" text in instance generator itself. No english specific code in master

# CONFIG
N = 10 # Number of instances per experiment
np_rng = np.random.default_rng(seed=42)
random_seeds = [np_rng.integers(1,1000) for i in range(N)]
RESOURCES_DIR = os.path.join(os.path.dirname(__file__), "resources")

class EscapeRoomInstanceGenerator(GameInstanceGenerator):
    def __init__(self):
        super().__init__(os.path.dirname(os.path.abspath(__file__)))


    def on_generate(self, **kwargs):
        explorer_prompt = self.load_template(os.path.join(RESOURCES_DIR, "initial_prompts", "explorer.template"))
        guide_prompt = self.load_template(os.path.join(RESOURCES_DIR, "initial_prompts", "guide.template"))
        explorer_reprompt = self.load_template(
            os.path.join(RESOURCES_DIR, "re_prompts", "explorer_correct_move.template")
        )
        explorer_fail_reprompt = self.load_template(
            os.path.join(RESOURCES_DIR, "re_prompts", "explorer_incorrect_move.template")
        )

        experiments = self.load_json(os.path.join(RESOURCES_DIR, "experiment_config.json"))

        for exp in experiments.keys():
            experiment = self.add_experiment(exp)
            game_id = 0
            size = experiments[exp]["size"]
            rooms = experiments[exp]["rooms"]
            graph_type = experiments[exp]["type"]
            ambiguity = experiments[exp]["ambiguity"]
            distance = experiments[exp]["distance"]
            start_type = experiments[exp]["start_type"]
            end_type = experiments[exp]["end_type"]

            for i in range(N):
                base_map = BaseMap(m=size, n=size, n_rooms=rooms, graph_type=graph_type, seed=random_seeds[i])
                map_metadata = base_map.metadata(start_type=start_type,
                                             end_type=end_type,
                                             ambiguity=ambiguity,
                                             distance=distance)
                map_metadata["explorer_prompt"] = explorer_prompt
                map_metadata["guide_prompt"] = guide_prompt
                map_metadata["explorer_reprompt"] = explorer_reprompt
                map_metadata["explorer_failed_reprompt"] = explorer_fail_reprompt

                escape_room_instance = self.add_game_instance(experiment, game_id)

                for orig_k, orig_v in map_metadata.items():
                    # convert tuple keys to strings
                    if isinstance(orig_k, tuple):
                        k = str(orig_k)
                    else:
                        k = orig_k

                    # convert tuple values to strings (if you want)
                    if isinstance(orig_v, tuple):
                        v = str(orig_v)
                    else:
                        v = orig_v

                    escape_room_instance[k] = v

                game_id += 1


if __name__ == '__main__':
    # EscapeRoomInstanceGenerator().generate()
    pass