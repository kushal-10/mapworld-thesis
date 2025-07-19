import ast
from typing import List, Tuple, Dict
from collections import deque

metadata = {
                    "game_id": 2,
                    "graph_id": "24s14s34m25c23h15h04k13c",
                    "m": 10,
                    "n": 10,
                    "named_nodes": [
                        "Sewing room",
                        "Sewing room",
                        "Music studio",
                        "Closet",
                        "Home theater",
                        "Hotel room",
                        "Kitchen",
                        "Computer room"
                    ],
                    "unnamed_nodes": [
                        "(2, 4)",
                        "(1, 4)",
                        "(3, 4)",
                        "(2, 5)",
                        "(2, 3)",
                        "(1, 5)",
                        "(0, 4)",
                        "(1, 3)"
                    ],
                    "named_edges": [
                        [
                            "Sewing room",
                            "Sewing room"
                        ],
                        [
                            "Sewing room",
                            "Music studio"
                        ],
                        [
                            "Sewing room",
                            "Closet"
                        ],
                        [
                            "Sewing room",
                            "Home theater"
                        ],
                        [
                            "Sewing room",
                            "Hotel room"
                        ],
                        [
                            "Sewing room",
                            "Kitchen"
                        ],
                        [
                            "Sewing room",
                            "Computer room"
                        ]
                    ],
                    "unnamed_edges": [
                        [
                            "(2, 4)",
                            "(1, 4)"
                        ],
                        [
                            "(2, 4)",
                            "(3, 4)"
                        ],
                        [
                            "(2, 4)",
                            "(2, 5)"
                        ],
                        [
                            "(2, 4)",
                            "(2, 3)"
                        ],
                        [
                            "(1, 4)",
                            "(1, 5)"
                        ],
                        [
                            "(1, 4)",
                            "(0, 4)"
                        ],
                        [
                            "(1, 4)",
                            "(1, 3)"
                        ]
                    ],
                    "node_to_category": {
                        "(2, 4)": "Sewing room",
                        "(1, 4)": "Sewing room",
                        "(3, 4)": "Music studio",
                        "(2, 5)": "Closet",
                        "(2, 3)": "Home theater",
                        "(1, 5)": "Hotel room",
                        "(0, 4)": "Kitchen",
                        "(1, 3)": "Computer room"
                    },
                    "category_to_node": {
                        "Sewing room": "(1, 4)",
                        "Music studio": "(3, 4)",
                        "Closet": "(2, 5)",
                        "Home theater": "(2, 3)",
                        "Hotel room": "(1, 5)",
                        "Kitchen": "(0, 4)",
                        "Computer room": "(1, 3)"
                    },
                    "node_to_image": {
                        "(2, 4)": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/work_place/sewing_room/ADE_train_00016186.jpg",
                        "(1, 4)": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/work_place/sewing_room/ADE_train_00016183.jpg",
                        "(3, 4)": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/cultural/music_studio/ADE_train_00012273.jpg",
                        "(2, 5)": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/home_or_hotel/closet/ADE_train_00005712.jpg",
                        "(2, 3)": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/home_or_hotel/home_theater/ADE_train_00009422.jpg",
                        "(1, 5)": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/home_or_hotel/hotel_room/ADE_train_00009573.jpg",
                        "(0, 4)": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/home_or_hotel/kitchen/ADE_train_00010339.jpg",
                        "(1, 3)": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/work_place/computer_room/ADE_train_00005946.jpg"
                    },
                    "category_to_image": {
                        "Sewing room": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/work_place/sewing_room/ADE_train_00016183.jpg",
                        "Music studio": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/cultural/music_studio/ADE_train_00012273.jpg",
                        "Closet": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/home_or_hotel/closet/ADE_train_00005712.jpg",
                        "Home theater": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/home_or_hotel/home_theater/ADE_train_00009422.jpg",
                        "Hotel room": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/home_or_hotel/hotel_room/ADE_train_00009573.jpg",
                        "Kitchen": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/home_or_hotel/kitchen/ADE_train_00010339.jpg",
                        "Computer room": "https://www.ling.uni-potsdam.de/clembench/adk/images/ADE/training/work_place/computer_room/ADE_train_00005946.jpg"
                    },
                    "start_node": "(3, 4)",
                    "target_node": "(2, 5)",
                    "explorer_prompt": "You are the SEEKER in MapWorld, a network of interconnected rooms.\n\nYour objective is to find and reach the TARGET ROOM.\n\nI have the image of the TARGET ROOM and will describe it to you.\n\nAt each step, you will be shown an image of your current room.\n\nYou may perform only one of the following actions:\n\n1. If the current room exactly matches the TARGET ROOM based on my description, respond strictly with -\nESCAPE\n\n2. If the current room seems similar but you are uncertain, ask me a clarifying question, reply strictly with -\nQUESTION: your question\n\n3. If the current room is definitely not the TARGET ROOM, choose a direction from the available options: $DIRECTIONS$\nreply strictly with -\nMOVE: chosen direction\n\nHere is the description of the TARGET ROOM:\n$INITIAL_DESCRIPTION$\nWhat action do you choose?\n\nYou must follow the above format rules exactly.\nDo not respond in any other format. Do not provide any commentary or clarification.\n\n",
                    "guide_prompt": "You are the GUIDE in MapWorld, a network of interconnected rooms.\n\nYour role is to assist me in reaching the TARGET ROOM.\nYou have access to a single image: the TARGET ROOM.\nI do not know what this room looks like.\nYou do not know the map layout or my current location.\n\nAt each step, you may only respond in one of the following formats:\n\n1. If I ask a question about the TARGET ROOM, reply strictly as:\nANSWER: your answer\n\n2. If I request a description of the TARGET ROOM, reply strictly as:\nDESCRIPTION: your description of the image\n\nDo not respond in any other format. Do not provide any commentary or clarification.\n\nLet’s begin.\n\nPlease describe the TARGET ROOM using:\nDESCRIPTION: your description\n",
                    "explorer_reprompt": "Now you made a move to this room, you can choose one of the following three actions:\n\n1. If the current room exactly matches the TARGET ROOM based on my description, respond strictly with -\nESCAPE\n\n2. If the current room seems similar but you are uncertain, ask me a clarifying question, reply strictly with -\nQUESTION: your question\n\n3. If the current room is definitely not the TARGET ROOM, choose a direction from the available options: $DIRECTIONS$\nreply strictly with -\nMOVE: chosen direction\n\nWhat action do you choose?\n\nYou must follow the above format rules exactly.\nDo not respond in any other format. Do not provide any commentary or clarification.\n\n",
                    "explorer_failed_reprompt": "The move you made is invalid. We remain in the current room. Please carefully review the available directions again.\nYou can now choose one of the following three actions:\n\n1. If the current room exactly matches the TARGET ROOM based on my description, respond strictly with -\nESCAPE\n\n2. If the current room seems similar but you are uncertain, ask me a clarifying question, reply strictly with -\nQUESTION: your question\n\n3. If the current room is definitely not the TARGET ROOM, choose a direction from the available options: $DIRECTIONS$\nreply strictly with -\nMOVE: chosen direction\n\nWhat action do you choose?\n\nYou must follow the above format rules exactly.\nDo not respond in any other format. Do not provide any commentary or clarification.\n\n"
                }

def unexplored_distance(neighbors: List[Tuple[int, int]],
                        visited_rooms: List[Tuple[int, int]],
                        map_edges: List) -> List[Dict]:
    """
    Args:
        neighbors: Neighbors of Explorer
        visited_rooms: Rooms already visited by the explorer
        map_edges: All edges in the given graph

    Returns:
        dist_to_unexplored: A dict containing the distance to the unexplored rooms from each neighbor of the Explorer
    """

    distances = []
    for nbr in neighbors:
        # BFS from this neighbor
        queue = deque([(nbr, 0)])
        seen = set(nbr)
        dist_to_unexplored = None
        while queue:
            room, d = queue.popleft()
            if room not in visited_rooms:
                dist_to_unexplored = d
                break
            for nxt in get_neighbors(room, map_edges):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append((nxt, d + 1))

        distances.append({"neighbor": nbr, "dist": dist_to_unexplored})

    if not distances:
        raise RuntimeError(f"No unexplored rooms reachable !! Check efficient move method")

    return distances



def get_neighbors(current_node, edges):
    neighbors = []
    for edge in edges:
        node1 = ast.literal_eval(edge[0])
        node2 = ast.literal_eval(edge[1])
        if node1 == current_node:
            if node2 not in neighbors:
                neighbors.append(node2)
        if node2 == current_node:
            if node1 not in neighbors:
                neighbors.append(node1)

    return neighbors

def get_next_node(current_node, edges, move):
    next_node = None
    if move == 'north':
        next_node = (current_node[0], current_node[1]-1)
    elif move == 'south':
        next_node = (current_node[0], current_node[1]+1)
    elif move == 'east':
        next_node = (current_node[0]+1, current_node[1])
    elif move == 'west':
        next_node = (current_node[0]-1, current_node[1])
    else:
        print("Invalid move! - Expected - north, south, east, west, got - {}".format(move))

    return next_node

def is_efficient_move(next_room: Tuple[int, int],
                      neighbors: List[Tuple[int, int]],
                      visited_rooms: List[Tuple[int, int]],
                      target_observed: bool,
                      map_edges) -> bool:

    """
    Args:
        next_room: Next position of the Explorer Agent after making move
        neighbors: Neighboring Rooms from the Explorer Agent's current position
        visited_rooms: rooms visited by explorer
        target_observed: A flag to indicate whether the target room has already been observed by the explorer
        map_edges: Edges of a networkX based graph

    NOTE: Presupposes that after making 'move' the agent ends up in one of the rooms in 'neighbors'
    TODO: Handle re-prompting when move made is to an invalid neighbor
    Returns:
        True if the move mase is efficient, False otherwise
    """

    # Check 1: Any move made after reaching target_room is inefficient
    # The agent, once reaching the target room, should ask questions and escape
    if target_observed:
        return False

    # Check 2: Any move made from a room with degree=1 is efficient
    # Only possible move
    if len(neighbors) == 1:
        return True

    # Check 3.a: Any move to an unexplored room is efficient
    if next_room not in visited_rooms:
        return True

    # Check 3.b: If any neighbor is unexplored, choosing a visited one is inefficient
    for nbr in neighbors:
        if nbr not in visited_rooms:
            return False


    # Check 4: Among visited neighbors, pick the one closest to any unexplored room
    dists = unexplored_distance(neighbors, visited_rooms, map_edges)
    # find minimal distance
    min_dist = min(d['dist'] for d in dists)
    # check if chosen next_room achieves that minimal
    for entry in dists:
        if entry['neighbor'] == next_room and entry['dist'] == min_dist:
            return True
    return False

def get_efficient_moves(moves_made):
    # metadata = get_metadata(instances, exp_name, game_id)
    unnamed_edges = metadata["unnamed_edges"]
    start_node = ast.literal_eval(metadata["start_node"])
    current_node = start_node
    target_observed = False

    visited_rooms = []
    for move in moves_made:
        next_node = get_next_node(current_node, unnamed_edges, move)
        neighbors = get_neighbors(current_node, unnamed_edges)
        eff_move = is_efficient_move(next_node, neighbors, visited_rooms, target_observed, unnamed_edges)
        if str(next_node) == metadata["target_node"]:
            target_observed = True
        current_node = next_node
        if next_node not in visited_rooms:
            visited_rooms.append(next_node)



if __name__ == "__main__":
    moves_made = ["west", "north", "south", "west", "south", "north", "west", "east", "north", "south", "south"]
    get_efficient_moves(moves_made)

