"""
Game Master for Escape Room
Implementing a base variant for now...2-player game only
"""

import ast
from clemcore.clemgame import Player, GameMaster, GameBenchmark, DialogueGameMaster, GameScorer, GameSpec
from clemcore.clemgame import metrics as ms
from clemcore.backends import Model
from clemcore.utils import file_utils
from engine.environment import MapWorldEnv
from engine.ade_maps import ADEMap

from typing import List, Dict, Tuple, Union
import os
import numpy as np
import logging

logger = logging.getLogger(__name__)
stdout_logger = logging.getLogger("escaperoom.master")

class Explorer(Player):
    def __init__(self, model: Model):
        super().__init__(model)
        self.response: str = ""
        self.tag: str = "Explorer"

    def _custom_response(self, context: Dict) -> str:
        return "MOVE: North"
    
class Guide(Player):
    def __init__(self, model: Model):
        super().__init__(model)
        self.response: str = ""
        self.tag: str = "Guide"


    def _custom_response(self, context: Dict) -> str:
        return "ANSWER: No"

class EscapeRoom(DialogueGameMaster):

    def __init__(self, name: str, path: str, experiment: Dict, player_models: List[Model]):
        super().__init__(name, path, experiment, player_models)

        # Initialize Experiment/Prompts/Scorer flags
        self.experiment: str = experiment["name"]

        # Scorers
        self.aborted = False
        self.fail = False  # Set when Explorer returns any invalid move
        self.success = False  # Set when Explorer returns - ESCAPE and explorer location == target location

        # Pass Turn
        self.pass_turn = True


    def _on_setup(self, **game_instance):

        # Initialize Game Instance
        self.game_instance = game_instance
        self.m = game_instance["m"]
        self.game_map = MapWorldEnv(render_mode="rgb_array", size=self.m, map_metadata=self.game_instance)

        # Prompts
        self.explorer_prompt: str = self.game_instance["explorer_prompt"]
        self.explorer_reprompt: str = self.game_instance["explorer_reprompt"]
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

        moves = self.game_map.get_next_moves()
        # Name of the room category - bedroom, for example
        self.explorer_room = self.game_instance["node_to_category"][self.explorer_pos]
        # Set possible Moves for Explorer
        # TODO: Do this via API (for each possible direction, get the response and let the explorer build the list)
        self.explorer_prompt = self.explorer_prompt.replace("$DIRECTIONS", moves)
        self.explorer_target = self.game_instance["target_node"]

        # Setup for Guide/Player2
        self.escape_pos = self.game_instance["target_node"]
        self.escape_room = self.game_instance["node_to_category"][self.escape_pos]
        self.guide_image = self.game_instance["node_to_image"][self.escape_pos]

        # Add players
        # NOTE: Player calls will be made in the order below
        self.add_player(self.guide)
        self.add_player(self.explorer)


    def _on_before_game(self):
        """
        Pass initial message - first player (Guide), first turn
        """

        # Add initial prompt to Explorer in (Explorer's) history
        self.set_context_for(self.guide, self.guide_prompt, image=[self.guide_image])
        stdout_logger.info(f"First message for Guide: {self.guide_prompt}")
        stdout_logger.info(f"First Room image path for Guide: {self.guide_image}")

    def _does_game_proceed(self) -> bool:
        """
        Fail cases for each turn, use init_flags/scorers etc...
        """
        if self.aborted or self.current_round==10 or self.success or self.fail:
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
        return response


    def _validate_player_response(self, player, utterance: str) -> bool:
        """
        Check Correct format/ tag etc... in each Player's response
        Args:
            player: Player object - Explorer or Guide type
            utterance: str - response from Player
        Returns:
            True if response format is valid, False otherwise
        """

        stdout_logger.info(f"Player response {player.tag}: {utterance}")
        utterance = self.clean_agent_response(utterance)
        stdout_logger.info(f"Cleaned Player response {player.tag}: {utterance}")

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
            if tag not in valid_tags:
                self.aborted = True
                stdout_logger.info(f"Aborting the Game. Explorer generated invalid tag {tag}")
                stdout_logger.info(f"Invalid utterance: {utterance}")
                self.log_to_self("invalid value", "abort game: explorer")
                return False


            if tag == "move":
                move = splits[1]
                move = move.lower().strip()
                self.pass_turn = False
                efficient_move = self.game_map._is_efficient_move_cycle(move)

                if move not in valid_directions:
                    self.aborted = True
                    stdout_logger.info(f"Aborting the Game. Explorer generated invalid move {move}")
                    stdout_logger.info(f"Invalid utterance: {utterance}")
                    self.log_to_self("invalid value", "abort game: explorer")
                    return False

                if efficient_move:
                    stdout_logger.info(f" Efficient Move : {move}")
                    self.log_to_self("move", "efficient")
                else:
                    stdout_logger.info(f" Efficient Move : {move}")
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

            if tag not in valid_tags:
                self.aborted = True
                stdout_logger.info(f"Invalid Response for Guide: Expected DESCRIPTION/ANSWER tag, got {splits[0]}")
                self.log_to_self("invalid value", "abort game") # Violated request count
                return False

            if tag == "description":
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
        stdout_logger.info(f"Current Round index: {self.current_round}")
        utterance = self.clean_agent_response(utterance)

        if type(player) == Guide:
            if self.current_round==0: # First prompt to Explorer from Guide.
                self.explorer_prompt = self.explorer_prompt.replace("$INIT_DESCRIPTION", utterance)
                stdout_logger.info(f"First prompt for Explorer: {self.explorer_prompt}")
                stdout_logger.info(f"Image for Explorer: {self.explorer_image}")
                # Pass the response from Guide to Explorer
                self.set_context_for(self.explorer, self.explorer_prompt, image=[self.explorer_image])
            else:
                # Pass the response from Guide as is, This should only contain "ANSWER:...."
                # DESCRIPTION: ... is only for the first turn
                stdout_logger.info(f"Set Prompt for Explorer: {self.explorer_prompt}")
                stdout_logger.info(f"Image for Explorer: {self.explorer_image}")
                self.set_context_for(self.explorer, utterance, image=[self.explorer_image])
        else:
            utterance = utterance.lower()
            splits = utterance.split(":")
            tag = splits[0]

            if tag == "move":
                move = splits[1].strip().lower()
                explorer_action = self.game_map._move_to_action[move]
                self.game_map.step(explorer_action) # Update Explorer state
                # Update explorer image
                self.explorer_image = self.game_instance["node_to_image"][str(tuple(self.game_map._agent_location))]
                next_moves = self.game_map.get_next_moves() # Update next possible moves
                self.explorer_reprompt = self.explorer_reprompt.replace("$MOVES", next_moves)
                self.set_context_for(self.explorer, self.explorer_reprompt, image=[self.explorer_image]) # Pass the updated str
                stdout_logger.info(f"Reprompt Explorer: {self.explorer_reprompt}")
                stdout_logger.info(f"Image for Explorer: {self.explorer_image}")
            if tag == "question":
                self.set_context_for(self.guide, utterance) # Pass response as is wo image to Guide
                stdout_logger.info(f"Set Prompt for Guide: {utterance}")
                stdout_logger.info(f"No image passed to Guide")


    def _on_after_game(self):
        # record final results once game episode has ended:
        pass


class EscapeRoomScorer(GameScorer):
    """
    Scorer class for Escape Room Game
    """

    def __init__(self, game_name:str, experiment:Dict, game_instance: Dict):
        super().__init__(game_name, experiment, game_instance)

    def compute_scores(self, episode_interactions: Dict) -> None:
        """
        Temp method to compute scores for Escape Room Game - Binary success rate
        """

        success = False
        # # skip player specific eval for now
        # success_explorer = False
        # success_guide = False
        all_turn_scores = []
        for turn_idx, turn in enumerate(episode_interactions["turns"]):
            turn_score_dict = {
                "request_count": 0,
                "violated_request_count": 0,
                "parsed_request_count": 0,
            }

            # Walk through log_to_self items from DGM
            for event in turn:
                action = event["action"]
                turn_score_dict["request_count"] += 1
                if action["type"] == "invalid format":
                    turn_score_dict["violated_request_count"] += 1
                elif action["type"] == "invalid value":
                    turn_score_dict["parsed_request_count"] += 1
                elif action["type"] == "success":
                    turn_score_dict["parsed_request_count"] += 1
                    if action["content"] == "episode":
                        success = True

            # log turn request scores
            self.log_turn_score(turn_idx, ms.METRIC_REQUEST_COUNT_VIOLATED, turn_score_dict["violated_request_count"])
            self.log_turn_score(turn_idx, ms.METRIC_REQUEST_COUNT_PARSED, turn_score_dict["parsed_request_count"])
            self.log_turn_score(turn_idx, ms.METRIC_REQUEST_COUNT, turn_score_dict["request_count"])
            all_turn_scores.append(turn_score_dict)

        # Log episodic scores
        ep_request_count = 0
        ep_violated_request_count = 0
        ep_parsed_request_count = 0
        for s in all_turn_scores:
            ep_request_count += s["request_count"]
            ep_violated_request_count += s["violated_request_count"]
            ep_parsed_request_count += s["parsed_request_count"]

        self.log_episode_score(ms.METRIC_REQUEST_COUNT, ep_request_count)
        self.log_episode_score(ms.METRIC_REQUEST_COUNT_VIOLATED, ep_violated_request_count)
        self.log_episode_score(ms.METRIC_REQUEST_COUNT_PARSED, ep_parsed_request_count)

        if not success:
            self.log_episode_score(ms.METRIC_ABORTED, 1)
            self.log_episode_score(ms.METRIC_SUCCESS, 0)
            self.log_episode_score(ms.METRIC_LOSE, 0)
            # Game-specific metrics
            self.log_episode_score(ms.BENCH_SCORE, np.nan)  # metric not applicable
            self.log_episode_score("Player Score", np.nan)
        else:
            self.log_episode_score(ms.METRIC_ABORTED, 0)
            self.log_episode_score(ms.METRIC_SUCCESS, 1)
            self.log_episode_score(ms.METRIC_LOSE, 0)
            self.log_episode_score(ms.BENCH_SCORE, 100)
            self.log_episode_score("Player Score", 100)


class EscapeRoomBenchmark(GameBenchmark):
    """
    Integrate this game in the overall benchmark runs
    """

    def __init__(self, game_spec: GameSpec):
        super().__init__(game_spec)

    def create_game_master(self, experiment: Dict, player_models: List[Model]) -> GameMaster:
        return EscapeRoom(self.game_name, self.game_path, experiment, player_models)

    def create_game_scorer(self, experiment: Dict, game_instance: Dict) -> GameScorer:
        return EscapeRoomScorer(self.game_name, experiment, game_instance)