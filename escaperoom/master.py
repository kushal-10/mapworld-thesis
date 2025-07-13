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
import re

from clemcore.clemgame import Player, GameMaster, GameBenchmark, DialogueGameMaster, GameScorer, GameSpec
from clemcore.backends import Model
import numpy as np

from engine.environment import MapWorldEnv
from engine.utils import get_next_node
from escaperoom.scorer import EscapeRoomScorer,is_efficient_move, get_neighbors

logger = logging.getLogger(__name__)
stdout_logger = logging.getLogger("escaperoom.master")
logging.getLogger("huggingface.multimodal.api").disabled = True

lang_config_path = os.path.join(os.path.dirname(__file__), "resources", "language_config.json")
with open(lang_config_path) as f:
    LANG_CFG = json.load(f)

class Explorer(Player):
    def __init__(self, model: Model):
        super().__init__(model)
        self.response: str = ""
        self.tag: str = "Explorer"

    def _custom_response(self, context: Dict) -> str:
        random_direction = np.random.choice(["north", "south", "east", "west"])
        return f"MOVE: {random_direction}"
    
class Guide(Player):
    def __init__(self, model: Model):
        super().__init__(model)
        self.response: str = ""
        self.tag: str = "Guide"


    def _custom_response(self, context: Dict) -> str:
        return "ANSWER: This is a sample description"

class EscapeRoom(DialogueGameMaster):

    def __init__(self, name: str, path: str, experiment: Dict, player_models: List[Model]):
        super().__init__(name, path, experiment, player_models)

        # Initialize Experiment/Prompts/Scorer flags
        self.experiment: str = experiment["name"]

        # Scorers
        self.aborted = False
        self.fail = False  # Set when Explorer returns any invalid move
        self.success = False  # Set when Explorer returns - ESCAPE and explorer location == target location
        self.reprompt_fail = False  # Set when Explorer returns a move to an invalid room

        # Pass Turn
        self.pass_turn = True

    def _on_setup(self, **game_instance):

        # Initialize Game Instance
        self.game_instance = game_instance
        self.m = game_instance["m"]
        self.game_map = MapWorldEnv(render_mode="rgb_array", size=self.m, map_metadata=self.game_instance)

        # Prompts
        self.explorer_base_prompt: str = self.game_instance["explorer_prompt"]
        self.explorer_base_reprompt: str = self.game_instance["explorer_reprompt"]
        self.explorer_base_failed_reprompt: str = self.game_instance["explorer_failed_reprompt"]
        self.guide_prompt: str = self.game_instance["guide_prompt"]

        # Initialize Players
        # Player 1 (Explorer) is in the mapworld
        # Player 2 (Guide) is outside the world
        self.explorer = Explorer(self.player_models[0])
        self.guide = Guide(self.player_models[1])

        # Setup for Explorer/Player1
        self.explorer_pos = self.game_instance["start_node"]
        self.explorer_image = self.game_instance["node_to_image"][self.explorer_pos]
        # Keep the nodes and edges as str in master (straightforward mapping) but pass as Tuples to the mapworld engine

        self.max_explorer_retries = 1 # At max, Let the explorer make 1 wrong move continuously from the same room
        self.current_explorer_try = 0 # reset try after every explorer move (to another room)
        self.total_explorer_moves = 0 # log all explorer moves valid+invalid here.
        # Check against a max value for aborting


        # Name of the room category - bedroom, for example
        self.explorer_room = self.game_instance["node_to_category"][self.explorer_pos]
        self.initial_description_tag = LANG_CFG["initial_description_tag"]
        self.directions_tag = LANG_CFG["directions_tag"]

        self.explorer_target = self.game_instance["target_node"]

        # Setup for Guide/Player2
        self.escape_pos = self.game_instance["target_node"]
        self.escape_room = self.game_instance["node_to_category"][self.escape_pos]
        self.guide_image = self.game_instance["node_to_image"][self.escape_pos]

        # Add players
        # NOTE: Player calls will be made in the order below
        self.add_player(self.guide)
        self.add_player(self.explorer)

        # Question Flag to keep track of - when explorer asks the questions, and if guide responds with answer
        self.question_flag = 0

    def _on_before_game(self):
        """
        Pass initial message - first player (Guide), first turn
        """

        # Add initial prompt to Explorer in (Explorer's) history
        self.set_context_for(self.guide, self.guide_prompt, image=[self.guide_image])
        self.log_to_self("image", {"image": [self.guide_image]})
        stdout_logger.info(f"First message for Guide: {self.guide_prompt}")
        stdout_logger.info(f"First Room image path for Guide: {self.guide_image}")

    def _does_game_proceed(self) -> bool:
        """
        Fail cases for each turn, use init_flags/scorers etc...
        """
        if self.aborted or self.current_round==25 or self.success or self.fail:
            return False
        else:
            return True

    def _should_pass_turn(self):
        return self.pass_turn

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
    def clean_thinking_text(response: str) -> str:
        # Try to extract between <answer>...</answer>
        match = re.search(r"<answer>(.*?)</answer>", response, re.DOTALL)
        if match:
            content = match.group(1).strip()
            if content:  # Not empty
                return content
            # If empty, keep looking

        # Try to extract between <\|begin_of_box\|>...\|end_of_box\|>
        box_match = re.search(r"<\|begin_of_box\|>(.*?)<\|end_of_box\|>", response, re.DOTALL)
        if box_match:
            return box_match.group(1).strip()

        # If neither found
        print(f"No answer content found in response from GLM Thinking! - {response}")
        return None


    def _validate_player_response(self, player, utterance: str) -> bool:
        """
        Check Correct format/ tag etc... in each Player's response
        Args:
            player: Player object - Explorer or Guide type
            utterance: str - response from Player
        Returns:
            True if response format is valid, False otherwise
        """
        stdout_logger.info(f"Generated player response: {utterance}")
        utterance = self.clean_agent_response(utterance)
        utterance = self.clean_thinking_text(utterance)
        stdout_logger.info(f"Cleaned Player response {player.tag}: {utterance}")

        if not utterance:
            self.aborted = True
            stdout_logger.info(f"Aborting the Game. Could not parse response from Player.")
            stdout_logger.info(f"Invalid utterance: {utterance}")
            self.log_to_self("invalid value", "abort game: explorer")
            return False


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
            self.question_flag = 0

            if tag not in valid_tags:
                self.aborted = True
                stdout_logger.info(f"Aborting the Game. Explorer generated invalid tag {tag}")
                stdout_logger.info(f"Invalid utterance: {utterance}")
                self.log_to_self("invalid value", "abort game: explorer")
                return False


            if tag == "move":
                self.total_explorer_moves += 1
                stdout_logger.info(f"Current explorer move: {self.total_explorer_moves}")
                if self.total_explorer_moves >= 14:
                    self.fail = True
                    self.log_to_self("turns exceeded", "failed game: explorer")

                stdout_logger.info(f"Move made from location - {self.game_map._agent_location}")
                move = splits[1]
                move = move.lower().strip()
                self.pass_turn = False

                next_node = get_next_node(tuple(self.game_map._agent_location), move)
                next_node = tuple(next_node)

                stdout_logger.info(f"Move: {move}")
                stdout_logger.info(f"Next node: {next_node}")
                # FIXME: add str/tuple typecheck
                current_node = str(tuple(self.game_map._agent_location))
                next_node_str = str(next_node)
                edge = [current_node, next_node_str]
                reverse_edge = [next_node_str, current_node]

                if edge not in self.game_map.map_metadata["unnamed_edges"] and reverse_edge not in \
                        self.game_map.map_metadata["unnamed_edges"]:
                    stdout_logger.info(f"Invalid move from {current_node} to {next_node_str}")
                    self.log_to_self("move", "invalid")
                    self.reprompt_fail = True
                    self.current_explorer_try += 1
                    invalid_move = True
                    if self.current_explorer_try == self.max_explorer_retries:
                        self.fail = True
                        self.log_to_self("turns exceeded", "failed game: explorer")
                else:
                    stdout_logger.info(f"Valid move: {move}")
                    # self.log_to_self("move", "valid")
                    self.current_explorer_try = 0 # Reset explorer tries

                edges = self.game_map.map_metadata["unnamed_edges"]
                tuple_edges = []
                for edge in edges:
                    tuple_edges.append((tuple(ast.literal_eval(edge[0])), tuple(ast.literal_eval(edge[1]))))

                neighbors = get_neighbors(next_node, tuple_edges)
                efficient_move = is_efficient_move(next_room=next_node, neighbors=neighbors, visited_rooms=self.game_map.visited,
                                                   target_observed=self.game_map.reached_target, map_edges=tuple_edges)

                if move not in valid_directions:
                    self.aborted = True
                    stdout_logger.info(f"Aborting the Game. Explorer generated invalid move {move}")
                    stdout_logger.info(f"Invalid utterance: {utterance}")
                    self.log_to_self("invalid value", "abort game: explorer")
                    return False

                if not invalid_move:
                    if efficient_move:
                        stdout_logger.info(f" Efficient Move : {move}")
                        self.log_to_self("move", "efficient")
                    else:
                        stdout_logger.info(f" Inefficient Move : {move}")
                        self.log_to_self("move", "inefficient")
                return True

            # Episodic Success case
            elif tag == "escape":
                stdout_logger.info(f"Agent Location - {str(tuple(self.game_map._agent_location))}")
                stdout_logger.info(f"Target Location - {self.game_instance['target_node']}")
                if str(tuple(self.game_map._agent_location)) == self.game_instance["target_node"]:
                    stdout_logger.info(f"Escape room {self.escape_room} - Reached, Explorer successfully escaped!")
                    self.log_to_self("escape", "success")
                    self.success = True
                    return True
                else:
                    stdout_logger.info(f"Explorer tried to Escape from a wrong room!")
                    self.log_to_self("escape", "failed")
                    self.fail = True
                    return True

            # tag == "question"
            else:
                self.question_flag = 1
                self.pass_turn = True
                stdout_logger.info(f"Explorer asked Question - {utterance}")
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

            if "description:" in utterance and "answer:" in utterance:
                self.aborted = True
                stdout_logger.info(f"Invalid Response for Guide: Expected DESCRIPTION/ANSWER tag, got both - {utterance}")
                self.log_to_self("invalid value", "abort game: guide")  # Violated request count
                return False

            if tag not in valid_tags:
                self.aborted = True
                stdout_logger.info(f"Invalid Response for Guide: Expected DESCRIPTION/ANSWER tag, got {splits[0]}")
                self.log_to_self("invalid value", "abort game: guide") # Violated request count
                return False

            if tag == "description":
                if self.question_flag == 1:
                    self.fail = True
                    self.log_to_self("description", "wrong response")
                    stdout_logger.info(f"Description by Guide, but Explorer asked a Question: {utterance}")

                stdout_logger.info(f"Description by Guide: {utterance}")
                self.log_to_self("description", "guide")
                return True
            else:
                stdout_logger.info(f"Answer by Guide: {utterance}")
                self.log_to_self("answer", "guide")
                return True


    def _parse_response(self, player: Union[Explorer, Guide], utterance: str) -> str:
        """
        Modify the response from Guide and send it to the Explorer
        Args:
            player: Player object - Explorer or Guide type
            utterance: str - response from current Player

        NOTE: _validate_player_response is called before _parse_response in step()
        """
        # TODO: If player is guide - pass the reprompt version with rooms to Guide - Do this in parse resp
        # FIXME: Does not seem to be required, Is the utterance stored before or after this call
        # FIXME: If after, then the utterance can be overridden here as reprompt for explorer
        # if type(player) == Explorer:
        #     # Return utterance as is, and forward to Guide
        #     return utterance
        # elif type(player) == Guide:
        #     move_dict = ast.literal_eval(utterance)
        #     move = move_dict['move']
        #     self.explorer_image = get_next_image(self.game_instance, self.explorer_pos, move)
        #     next_node = get_node(ast.literal_eval(self.explorer_pos), move)
        #     next_moves = get_next_moves(self.game_instance, next_node)
        #     self.explorer_reprompt = self.explorer_reprompt.replace("$ROOMS", next_moves)
        return utterance

    def _on_valid_player_response(self, player: Union[Explorer, Guide], utterance: str):
        """
        Send Explorer's response to Guide and vice versa

        Args:
            player: Player object - Explorer or Guide type
            utterance: str - response from current Player
        """

        # First explorer turn is done, the response from explorer always goes into guide, unchanged
        # The guide response never goes into the Explorer, rather the reprompt of explorer is fixed
        # and the next possible moves are interpreted based on the guide's response
        stdout_logger.info(f"Current Round index: {self.current_round}. Current player: {player}")
        utterance = self.clean_agent_response(utterance)
        utterance = self.clean_thinking_text(utterance)

        if type(player) == Guide:
            if self.current_round==0: # First prompt to Explorer from Guide.
                moves = self.game_map.get_next_moves()
                self.explorer_prompt = self.explorer_base_prompt.replace(self.initial_description_tag, utterance)
                self.explorer_prompt = self.explorer_prompt.replace(self.directions_tag, moves)
                stdout_logger.info(f"First prompt for Explorer: {self.explorer_prompt}")
                stdout_logger.info(f"Image for Explorer: {self.explorer_image}")
                # Pass the response from Guide to Explorer
                self.set_context_for(self.explorer, self.explorer_prompt, image=[self.explorer_image])
                self.log_to_self("image", {"image": [self.explorer_image]})
            else:
                # Pass the response from Guide as is, This should only contain "ANSWER:...."
                # DESCRIPTION: ... is only for the first turn
                stdout_logger.info(f"Set Prompt for Explorer: {utterance}")
                stdout_logger.info(f"Image for Explorer: {self.explorer_image}")
                self.set_context_for(self.explorer, utterance, image=[self.explorer_image])
                self.log_to_self("image", {"image": [self.explorer_image]})
        else:
            utterance = utterance.lower()
            splits = utterance.split(":")
            tag = splits[0]

            if tag == "move" and not self.fail:
                if self.reprompt_fail:
                    # Skip updating environment, pass same image,moves, but different reprompt
                    next_moves = self.game_map.get_next_moves()  # Update next possible moves
                    stdout_logger.info(f"Next Moves: {next_moves}")
                    self.explorer_failed_reprompt = self.explorer_base_failed_reprompt.replace(self.directions_tag,
                                                                                          next_moves)
                    self.set_context_for(self.explorer, self.explorer_failed_reprompt,
                                         image=[self.explorer_image])  # Pass the updated str
                    self.log_to_self("image", {"image": [self.explorer_image]})
                    stdout_logger.info(f"Reprompt Explorer: {self.explorer_failed_reprompt}")
                    stdout_logger.info(f"Image for Explorer: {self.explorer_image}")
                    stdout_logger.info(f"Resetting reprompt_fail flag")
                    self.reprompt_fail = False
                else:
                    move = splits[1].strip().lower()
                    explorer_action = self.game_map._move_to_action[move]
                    self.game_map.step(explorer_action) # Update Explorer state
                    # Update explorer image
                    self.explorer_image = self.game_instance["node_to_image"][str(tuple(self.game_map._agent_location))]
                    next_moves = self.game_map.get_next_moves() # Update next possible moves
                    stdout_logger.info(f"Next Moves: {next_moves}")
                    self.explorer_reprompt = self.explorer_base_reprompt.replace(self.directions_tag, next_moves)
                    # Pass the updated str
                    self.set_context_for(self.explorer, self.explorer_reprompt, image=[self.explorer_image])
                    self.log_to_self("image", {"image": [self.explorer_image]})
                    stdout_logger.info(f"Reprompt Explorer: {self.explorer_reprompt}")
                    stdout_logger.info(f"Image for Explorer: {self.explorer_image}")
            if tag == "question":
                self.set_context_for(self.guide, utterance, image=[self.guide_image])
                self.log_to_self("image", {"image": [self.guide_image]})
                stdout_logger.info(f"Set Prompt for Guide: {utterance}")
                stdout_logger.info(f"Image for Guide: {self.guide_image}")

    def _on_after_game(self):
        # record final results once game episode has ended:
        pass


class EscapeRoomBenchmark(GameBenchmark):
    """Integrate this game in the overall benchmark runs"""

    def __init__(self, game_spec: GameSpec):
        super().__init__(game_spec)

    def create_game_master(self, experiment: Dict, player_models: List[Model]) -> GameMaster:
        return EscapeRoom(self.game_name, self.game_path, experiment, player_models)

    def create_game_scorer(self, experiment: Dict, game_instance: Dict) -> GameScorer:
        return EscapeRoomScorer(self.game_name, experiment, game_instance)