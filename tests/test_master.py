import json
import os

from clemcore.backends import Model

"""
Game Master for Escape Room
Implementing a base variant for now...2-player game only
"""
import ast
# TODO : Add max number of images - If it reaches limit remove images from beginning
# TODO : Add this value as a variable.

from typing import List, Dict, Union
import logging
import os
import json

from clemcore.clemgame import Player, GameMaster, GameBenchmark, DialogueGameMaster, GameScorer, GameSpec
from clemcore.backends import Model
import numpy as np

from engine.environment import MapWorldEnv
from engine.utils import get_next_node
from escaperoom.scorer import EscapeRoomScorer, is_efficient_move, get_neighbors

logger = logging.getLogger(__name__)
stdout_logger = logging.getLogger("escaperoom.master")

lang_config_path = os.path.join("escaperoom", "resources", "language_config.json")
with open(lang_config_path) as f:
    LANG_CFG = json.load(f)

class Explorer():
    def __init__(self):
        self.response: str = ""
        self.tag: str = "Explorer"

    def _custom_response(self, context: Dict) -> str:
        random_direction = np.random.choice(["north", "south", "east", "west"])
        return f"MOVE: {random_direction}"


class Guide():
    def __init__(self):
        self.response: str = ""
        self.tag: str = "Guide"

    def _custom_response(self, context: Dict) -> str:
        return "ANSWER: This is a sample description"

class TestEscapeRoom:
    def __init__(self, m, game_instance):
        self.game_instance = game_instance
        self.game_map = MapWorldEnv(render_mode="rgb_array", size=m, map_metadata=game_instance)
        self.max_explorer_retries = 2  # At max, Let the explorer make 2 wrong moves continuously from the same room
        self.current_explorer_try = 0  # reset try after every explorer move (to another room)
        self.total_explorer_moves = 0  # log all explorer moves valid+invalid here.

        self.explorer_prompt_base: str = self.game_instance["explorer_prompt"]
        self.explorer_reprompt_base: str = self.game_instance["explorer_reprompt"]
        self.explorer_failed_reprompt_base: str = self.game_instance["explorer_failed_reprompt"]
        self.guide_prompt_base: str = self.game_instance["guide_prompt"]

        self.explorer_pos = self.game_instance["start_node"]
        self.explorer_image = self.game_instance["node_to_image"][self.explorer_pos]

        moves = self.game_map.get_next_moves()
        self.explorer_room = self.game_instance["node_to_category"][self.explorer_pos]
        self.initial_description_tag = LANG_CFG["initial_description_tag"]
        self.directions_tag = LANG_CFG["directions_tag"]
        # Set possible Moves for Explorer
        self.explorer_prompt = self.explorer_prompt_base.replace(self.directions_tag, moves)
        self.explorer_target = self.game_instance["target_node"]

        # Setup for Guide/Player2
        self.escape_pos = self.game_instance["target_node"]
        self.escape_room = self.game_instance["node_to_category"][self.escape_pos]
        self.guide_image = self.game_instance["node_to_image"][self.escape_pos]

        # Scorers
        self.aborted = False
        self.fail = False  # Set when Explorer returns any invalid move
        self.success = False  # Set when Explorer returns - ESCAPE and explorer location == target location
        self.reprompt_fail = False  # Set when Explorer returns a move to an invalid room

        # Pass Turn
        self.pass_turn = True
        self.start_next_round = False

    @staticmethod
    def clean_agent_response(response: str) -> str:
        """
        Remove leading and trailing markdown wrappers from response
        """
        response = response.strip()
        response = response.replace("```json", "")
        response = response.replace("```", "")
        if response.endswith("."):
            response = response[:-1]
        return response.lower()

    @staticmethod
    def log_to_self(v1, v2):
        print(v1, v2)

    def _validate_player_response(self, player, utterance: str) -> bool:
        """
        Check Correct format/ tag etc... in each Player's response
        Args:
            player: Player object - Explorer or Guide type
            utterance: str - response from Player
        Returns:
            True if response format is valid, False otherwise
        """

        utterance = self.clean_agent_response(utterance)
        print(f"Cleaned Player response {player.tag}: {utterance}")
        print(type(player))
        if type(player) == Explorer:
            """
            Explorer should respond only in one of the following format
            1) MOVE: North
            2) ESCAPE
            3) QUESTION: 
            Check for each tag

            Abort - If explorer responds in invalid format, or invalid keys
            """
            valid_tags = ["move", "escape", "question"]
            valid_directions = ["north", "east", "south", "west"]
            utterance = utterance.lower()
            splits = utterance.split(":")
            tag = splits[0]
            invalid_move = False

            if tag not in valid_tags:
                self.aborted = True
                print(f"Aborting the Game. Explorer generated invalid tag {tag}")
                print(f"Invalid utterance: {utterance}")
                self.log_to_self("invalid value", "abort game: explorer")
                return False

            if tag == "move":
                self.total_explorer_moves += 1
                print(f"Current explorer move: {self.total_explorer_moves}")
                if self.total_explorer_moves >= 14:
                    self.aborted = True
                    self.log_to_self("turns exceeded", "abort game: explorer")

                print(f"Move made from location - {self.game_map._agent_location}")
                move = splits[1]
                move = move.lower().strip()
                self.pass_turn = False

                next_node = get_next_node(tuple(self.game_map._agent_location), move)
                next_node = tuple(next_node)

                print(f"Move: {move}")
                print(f"Next node: {next_node}")
                # FIXME: add str/tuple typecheck
                current_node = str(tuple(self.game_map._agent_location))
                next_node_str = str(next_node)
                edge = [current_node, next_node_str]
                reverse_edge = [next_node_str, current_node]

                if edge not in self.game_map.map_metadata["unnamed_edges"] and reverse_edge not in \
                        self.game_map.map_metadata["unnamed_edges"]:
                    print(f"Invalid move from {current_node} to {next_node_str}")
                    self.log_to_self("move", "invalid")
                    self.reprompt_fail = True
                    self.current_explorer_try += 1
                    invalid_move = True
                    if self.current_explorer_try == self.max_explorer_retries:
                        self.aborted = True
                        self.log_to_self("turns exceeded", "abort game: explorer")
                else:
                    print(f"Valid move: {move}")
                    # self.log_to_self("move", "valid")
                    self.current_explorer_try = 0  # Reset explorer tries

                edges = self.game_map.map_metadata["unnamed_edges"]
                tuple_edges = []
                for edge in edges:
                    tuple_edges.append((tuple(ast.literal_eval(edge[0])), tuple(ast.literal_eval(edge[1]))))

                neighbors = get_neighbors(next_node, tuple_edges)
                efficient_move = is_efficient_move(next_room=next_node, neighbors=neighbors,
                                                   visited_rooms=self.game_map.visited,
                                                   target_observed=self.game_map.reached_target, map_edges=tuple_edges)

                if move not in valid_directions:
                    self.aborted = True
                    print(f"Aborting the Game. Explorer generated invalid move {move}")
                    print(f"Invalid utterance: {utterance}")
                    self.log_to_self("invalid value", "abort game: explorer")
                    return False

                if not invalid_move:
                    if efficient_move:
                        print(f" Efficient Move : {move}")
                        self.log_to_self("move", "efficient")
                    else:
                        print(f" Inefficient Move : {move}")
                        self.log_to_self("move", "inefficient")
                return True

            # Episodic Success case
            elif tag == "escape":
                print(f"Agent Location - {str(tuple(self.game_map._agent_location))}")
                print(f"Target Location - {self.game_instance['target_node']}")
                if str(tuple(self.game_map._agent_location)) == self.game_instance["target_node"]:
                    print(f"Escape room {self.escape_room} - Reached, Explorer successfully escaped!")
                    self.log_to_self("escape", "success")
                    self.success = True
                    return True
                else:
                    print(f"Explorer tried to Escape from a wrong room!")
                    self.log_to_self("escape", "failed")
                    self.fail = True
                    return True

            # tag == "question"
            else:
                self.pass_turn = True
                print(f"Explorer asked Question - {utterance}")
                self.log_to_self("question", "explorer")
                return True

        else:
            """
            Guide should respond only in one of the following format
            1) DESCRIPTION: 
            2) ANSWER:
            """

            utterance = utterance.lower()
            splits = utterance.split(":")
            tag = splits[0]
            valid_tags = ["description", "answer"]

            if tag not in valid_tags:
                self.aborted = True
                print(f"Invalid Response for Guide: Expected DESCRIPTION/ANSWER tag, got {splits[0]}")
                self.log_to_self("invalid value", "abort game: guide")  # Violated request count
                return False

            if tag == "description":
                print(f"Description by Guide: {utterance}")
                self.log_to_self("description", "guide")
                return True
            else:
                print(f"Answer by Guide: {utterance}")
                self.log_to_self("answer", "guide")
                return True

    def _on_valid_player_response(self, player, utterance: str, current_round):
        """
        Send Explorer's response to Guide and vice versa

        Args:
            player: Player object - Explorer or Guide type
            utterance: str - response from current Player
        """
        self.current_round = current_round

        utterance = self.clean_agent_response(utterance)
        self.start_next_round = True
        if type(player) == Guide:
            if self.current_round==0: # First prompt to Explorer from Guide.
                self.explorer_prompt = self.explorer_prompt_base.replace(self.initial_description_tag, utterance)
                print(f"First prompt for Explorer: {self.explorer_prompt}")
                print(f"Image for Explorer: {self.explorer_image}")
                # Pass the response from Guide to Explorer
                self.log_to_self("image", {"image": [self.explorer_image]})

            else:
                # Pass the response from Guide as is, This should only contain "ANSWER:...."
                # DESCRIPTION: ... is only for the first turn
                print(f"Set Prompt for Explorer: {utterance}")
                print(f"Image for Explorer: {self.explorer_image}")
                self.log_to_self("image", {"image": [self.explorer_image]})
        else:
            utterance = utterance.lower()
            splits = utterance.split(":")
            tag = splits[0]

            if tag == "move" and not self.fail:
                if self.reprompt_fail:
                    # Skip updating environment, pass same image,moves, but different reprompt
                    next_moves = self.game_map.get_next_moves()  # Update next possible moves
                    print(f"Next Moves: {next_moves}")
                    self.explorer_failed_reprompt = self.explorer_failed_reprompt_base.replace(self.directions_tag,
                                                                                          next_moves)
                    self.log_to_self("image", {"image": [self.explorer_image]})
                    print(f"Reprompt (Failed) Explorer: {self.explorer_failed_reprompt}")
                    print(f"Image for Explorer: {self.explorer_image}")
                    print(f"Resetting reprompt_fail flag")
                    self.reprompt_fail = False
                else:
                    move = splits[1].strip().lower()
                    explorer_action = self.game_map._move_to_action[move]
                    self.game_map.step(explorer_action) # Update Explorer state
                    # Update explorer image
                    self.explorer_image = self.game_instance["node_to_image"][str(tuple(self.game_map._agent_location))]
                    next_moves = self.game_map.get_next_moves() # Update next possible moves
                    print(f"Next Moves: {next_moves}")
                    self.explorer_reprompt = self.explorer_reprompt_base.replace(self.directions_tag, next_moves)
                    # Pass the updated str
                    self.log_to_self("image", {"image": [self.explorer_image]})
                    print(f"Reprompt Explorer: {self.explorer_reprompt}")
                    print(f"Image for Explorer: {self.explorer_image}")
            if tag == "question":
                self.log_to_self("image", {"image": [self.guide_image]})
                print(f"Set Prompt for Guide: {utterance}")
                print(f"Image for Guide: {self.guide_image}")


if __name__ == "__main__":
    instance_path = os.path.join("escaperoom", "in", "instances.json")
    with open(instance_path) as json_data:
        instances = json.load(json_data)

    instance = instances["experiments"][0]["game_instances"][1]
    m = instance["m"]
    escape_room = TestEscapeRoom(m, instance)
    guide = Guide()
    explorer = Explorer()

    escape_room._validate_player_response(guide, "DESCRIPTION: Test Description")
    escape_room._on_valid_player_response(guide, "DESCRIPTION: Test Description", 0)
    escape_room._validate_player_response(explorer, "MOVE: NORTH")
    escape_room._on_valid_player_response(explorer, "MOVE: NORTH", current_round=0)
    escape_room._validate_player_response(explorer, "MOVE: SOUTH")
    escape_room._on_valid_player_response(explorer, "MOVE: SOUTH", current_round=0)
    escape_room._validate_player_response(explorer, "MOVE: SOUTH")
    escape_room._on_valid_player_response(explorer, "MOVE: SOUTH", current_round=0)
    escape_room._validate_player_response(explorer, "MOVE: WEST")
    escape_room._on_valid_player_response(explorer, "MOVE: WEST", current_round=0)

