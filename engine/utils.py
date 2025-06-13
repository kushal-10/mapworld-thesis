"""
Post Processing methods after instances are generated
Util functions for mm_mapworld....
"""
from typing import Dict, Tuple

def get_next_node(start_pos: Tuple, move: str) -> Tuple:
    """
    Get the next node after making move from a given start node
    Args:
        start_pos: current node of the agent inside mapworld
        move: move as a string item

    Returns:
        node: node of the move as a string item
    """
    if move == "north":
        return start_pos[0], start_pos[1] - 1
    elif move == "south":
        return start_pos[0], start_pos[1] + 1
    elif move == "east":
        return start_pos[0] + 1, start_pos[1]
    elif move == "west":
        return start_pos[0] - 1, start_pos[1]
    else:
        raise ValueError("Invalid move! Check the parsed response!")
