from clemcore.clemgame import GameInstanceGenerator
from engine.ade_maps import ADEMap

import os
import numpy as np
from typing import Tuple

# TODO: Move this to initial_prompt.template under resources
EXPL_PROMPT = """
You’re exploring Mapworld, a network of various connected rooms, and your aim is to reach the Escape Room.
Here is the description of what the Escape Room looks like:  $INIT_DESCRIPTION

At each step you will receive the image of your current room. Based on what you know of the Escape Room from my description and the image you see,
choose one of three actions:

1. If your current image matches your memory of the Escape Room description, reply with only one word
ESCAPE

2. If you need more information to verify if it’s the same room, reply -
QUESTION: your question here

3. If your current room is definitely a different room, pick a direction from $DIRECTIONS to move, and reply -
MOVE: direction you chose

Do not generate any additional text.
"""

EXPL_REPROMPT = """
Now you made a move to this room, and you can either ESCAPE, ask me a QUESTION or MOVE in one of these directions 
$MOVES
"""

EXPL_FAIL_REPROMPT = """
We are still in this room, and you can either ESCAPE, ask me a QUESTION or MOVE in one of these directions 
$MOVES
"""

# TODO: change $MOVES to $DIRECTIONS

GUIDE_PROMPT = """
You’re guiding me through Mapworld to the Escape Room. I don’t know what it looks like, but you have its image.

First, describe your image in this format and nothing else:
DESCRIPTION: your description of the image

Whenever I ask a question, answer based only on your image in this format and nothing else:
ANSWER: your answer
"""

# TODO:  Add self.tags and every "English" text in instance generator itself. No english specific code in master


N = 10 # Number of instances per experiment
np.random.seed(999)
random_seeds = [np.random.randint(1,1000) for i in range(N)]
print(random_seeds)


class EscapeRoomInstanceGenerator(GameInstanceGenerator):
    def __init__(self):
        super().__init__(os.path.dirname(os.path.abspath(__file__)))


    def on_generate(self):
        experiments = {
            "small": {"size": 5, "rooms":4, "type": "cycle", "ambiguity": None},
            "medium": {"size": 5, "rooms": 6, "type": "cycle", "ambiguity": None},
            "large": {"size":5, "rooms": 8, "type": "cycle", "ambiguity": None},
            "low_ambiguity": {"size": 5, "rooms": 8, "type": "cycle", "ambiguity": [2]},
            "med_ambiguity": {"size": 5, "rooms": 8, "type": "cycle", "ambiguity": [3]},
            "high_ambiguity": {"size": 5, "rooms": 8, "type": "cycle", "ambiguity": [4]},
            "star": {"size":5, "rooms": 8, "type": "star", "ambiguity": None},
            "ladder": {"size": 5, "rooms": 8, "type": "ladder", "ambiguity": None},
            "path": {"size": 5, "rooms": 8, "type": "path", "ambiguity": None},
        }

        for exp in experiments.keys():
            experiment = self.add_experiment(exp)
            game_id = 0
            size = experiments[exp]["size"]
            rooms = experiments[exp]["rooms"]
            graph_type = experiments[exp]["type"]
            ambiguity = experiments[exp]["ambiguity"]
            for i in range(N):
                ade_map = ADEMap(size, size, rooms, seed=random_seeds[i])
                if graph_type == "cycle":
                    ade_graph = ade_map.create_cycle_graph()
                elif graph_type == "path":
                    ade_graph = ade_map.create_path_graph()
                elif graph_type == "star":
                    ade_graph = ade_map.create_star_graph()
                elif graph_type == "ladder":
                    ade_graph = ade_map.create_ladder_graph()
                else:
                    raise ValueError(f"Invalid graph type! - {graph_type}")

                ade_graph = ade_map.assign_types(ade_graph, ambiguity=ambiguity, use_outdoor_categories=False)
                ade_graph = ade_map.assign_images(ade_graph)

                map_metadata = ade_map.metadata(ade_graph, "indoor", "indoor")
                map_metadata["explorer_prompt"] = EXPL_PROMPT
                map_metadata["guide_prompt"] = GUIDE_PROMPT
                map_metadata["explorer_reprompt"] = EXPL_REPROMPT
                map_metadata["explorer_failed_reprompt"] = EXPL_FAIL_REPROMPT

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
    EscapeRoomInstanceGenerator().generate()
