from clemcore.clemgame import GameInstanceGenerator
from engine.ade_maps import ADEMap

import os
import numpy as np
from typing import Tuple

# TODO: Move this to initial_prompt.template under resources
EXPL_PROMPT = """You are stuck in a mapworld environment containing several rooms. 
Your task is to explore this world and reach an escape room.
You are always given an image of the current room you are in. 
I have an image of the Escape Room, this is an initial description of my image - $INIT_DESCRIPTION.

Based on my description and the image given, you now have three options

First Option - If you think that the description of my image matches the image you have, i.e.
you are in the escape room then respond with one word - ESCAPE.

Second Option - If you think you need more details from my image - respond in the following format
QUESTION: Ask details about the image I have to verify if we have the same image or not

Third Option - If you think you are in a different room than what I have, i.e we are seeing different images,
then you can make a move in following Directions - $DIRECTIONS. Respond in the following format
MOVE: direction - Here direction can be one of {north, south, east, west}
"""

EXPL_REPROMPT = """
Now you made a move to this room, and you can either ESCAPE, ask me a QUESTION or MOVE in one of these directions 
$MOVES
"""

# TODO: change $MOVES to $DIRECTIONS

GUIDE_PROMPT = """I need your help, I am stuck in a mapworld environment. 
Your task is to help me reach an escape room. I do not know what the escape room looks like. 
But fortunately, you have an image of the escape room with you. I will explore each room here and ask you a few QUESTIONS
to verify if we have the same image or not, thus verifying if I am in the Escape Room or not.

First start by describing the image that you have, Respond in the following format
DESCRIPTION: your description of the image that you have

Then if I ask a QUESTION, the respond appropriately based on your image in the following format
ANSWER: your Answer
"""


N = 10 # Number of instances per experiment
np.random.seed(42)
random_seeds = [np.random.randint(1,1000) for i in range(N)]
print(random_seeds)


class EscapeRoomInstanceGenerator(GameInstanceGenerator):
    def __init__(self):
        super().__init__(os.path.dirname(os.path.abspath(__file__)))


    def on_generate(self):
        experiments = {
            "[2]": {"size": 6, "rooms":8, "type": "cycle", "ambiguity": [2]},
            "[3]": {"size": 6, "rooms": 8, "type": "cycle", "ambiguity": [3]},
            "[2,3]": {"size":6, "rooms": 8, "type": "cycle", "ambiguity": [2,3]}
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

                map_metadata = ade_map.metadata(ade_graph, "indoor", "ambiguous")
                map_metadata["explorer_prompt"] = EXPL_PROMPT
                map_metadata["guide_prompt"] = GUIDE_PROMPT
                map_metadata["explorer_reprompt"] = EXPL_REPROMPT

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
