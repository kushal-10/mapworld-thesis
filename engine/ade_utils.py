"""
Utils module to handle room type/image assignments to ADE Maps
"""
import json
import numpy as np
import os
from typing import Tuple, Dict, List
from collections import deque, defaultdict

from engine.ade_maps import ADEMap

# Assign the categories from "categories.json" here.
CATEGORY_OUTDOORS = "outdoors"
CATEGORY_TARGETS = "targets"
CATEGORY_DISTRACTORS = "distractors"


def assign_types(ade_graph,
                 json_path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources",
                                               "categories.json"),
                 ambiguity: list[int] = None, use_outdoor_categories: bool = True):
    """
    Assign room categories and images to the nodes in the generated graph.
    Example ade_graph.nodes[room] = {
        'base_type': 'indoor', # or 'outdoor'
        'type': 'k/kitchen',
        'ambiguous': True - for all ambiguous cases or a random room in central area if ambiguity is None - else False
    }

    Args:
        ade_graph: Generated graph. (via BaseMap.create_acyclic_graph()/BaseMap.create_cyclic_graph())
        json_path: Path to a json file containing "targets", "outdoors" and "distractors" categories
        ambiguity: List of integers to control ambiguity. Example: [3,2] means - at
        least two types of potential target categories, and that
        the first will occur three times, and the second twice. Only applies to indoor rooms
        use_outdoor_categories: If true, include `outdoor` room categories

    Raises:
        ValueError: if possible indoor rooms (rooms with more than 1 neighbor) < sum of ambiguity
    """
    # Fixes ambiguity = None case
    if not ambiguity:
        ambiguity = [1]

    outdoor_nodes = []  # Rooms with only one neighbour - Most likely will be used as Entry/Exit points
    indoor_nodes = []  # Most likely will be used as target/distractor rooms
    # Assign nodes based on number of neighbours
    for room in ade_graph.nodes():
        if ade_graph.degree(room) == 1:
            outdoor_nodes.append(room)
        elif ade_graph.degree(room) > 1:
            indoor_nodes.append(room)
        else:
            raise ValueError(f"Check Graph Generation!! Found a node with no neighbors!")

    if len(indoor_nodes) < sum(ambiguity):
        raise ValueError(
            f"Ambiguity passed is {ambiguity}, But number of indoor rooms in the generated graph is {len(indoor_nodes)}"
            f"Try decreasing ambiguity such that sum of ambiguity is <= {len(indoor_nodes)}"
            f"If ambiguity is strictly required and possible with the initialized Map, try generating another random graph.")

    with open(json_path, 'r') as f:
        categories = json.load(f)

    outdoor_nodes_assigned = []
    # Using distractors here, change to "targets" if required
    category_key = CATEGORY_OUTDOORS if use_outdoor_categories else CATEGORY_DISTRACTORS
    for room in outdoor_nodes:
        random_outdoor_room = np.random.choice(categories[category_key])
        while random_outdoor_room in outdoor_nodes_assigned:
            random_outdoor_room = np.random.choice(categories[category_key])

        outdoor_nodes_assigned.append(random_outdoor_room)
        ade_graph.nodes[room]['base_type'] = "outdoor"  # Used as an identifier for rooms with one neighbour
        ade_graph.nodes[room]['type'] = random_outdoor_room
        ade_graph.nodes[room]['ambiguous'] = False

        # TODO: Pass 'type' as argument as well, to pre set certain type of rooms
        # At least 2 home_office and 2 bedrooms, for example

    indoor_nodes_assigned = []
    # Handles cases if outdoor nodes are also randomly drawn from "targets" category
    room_type_assigned = [] if category_key != CATEGORY_TARGETS else outdoor_nodes_assigned

    for amb in ambiguity:
        # Pick a random unique room category from TARGETS for each entry in ambiguity
        random_room_type = np.random.choice(categories[CATEGORY_TARGETS])
        while random_room_type in room_type_assigned:
            random_room_type = np.random.choice(categories[CATEGORY_TARGETS])
        room_type_assigned.append(random_room_type)

        room_count = 1
        for r in range(amb):
            # Pick a random node from the list of indoor nodes and assign the selected room_category
            room = indoor_nodes[np.random.randint(len(indoor_nodes))]
            while room in indoor_nodes_assigned:
                room = indoor_nodes[np.random.randint(len(indoor_nodes))]
            indoor_nodes_assigned.append(room)

            ade_graph.nodes[room]['base_type'] = "indoor"
            # Make the room_type unique
            # (so instead of assigning 'kitchen' to multiple nodes, assign 'kitchen1' and 'kitchen2')
            if amb != 1:
                ade_graph.nodes[room]['type'] = str(random_room_type) + " " + str(room_count)
                room_count += 1
                ade_graph.nodes[room]['ambiguous'] = True  # Set True for all ambiguous rooms
            else:
                ade_graph.nodes[room]['type'] = random_room_type
                ade_graph.nodes[room]['ambiguous'] = False  # Rooms are not ambiguous when ambiguity = [1]

    # Remaining nodes - as distractors
    distractor_rooms = list(set(indoor_nodes) - set(indoor_nodes_assigned))

    # Collect remaining room_types from targets and aa categories["distractors"] to it
    all_targets = set(categories[CATEGORY_TARGETS])
    all_distros = set(categories[CATEGORY_DISTRACTORS])
    chosen_rooms = set(room_type_assigned)
    dist_categories = sorted((all_targets - chosen_rooms) | all_distros)

    distractor_assigned = []
    for room in distractor_rooms:
        random_distractor = np.random.choice(dist_categories)
        while random_distractor in distractor_assigned:
            random_distractor = np.random.choice(dist_categories)

        ade_graph.nodes[room]['base_type'] = "indoor"
        ade_graph.nodes[room]['type'] = random_distractor
        ade_graph.nodes[room]['ambiguous'] = False

    return ade_graph


def assign_images(ade_graph, json_path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources",
                                                   "images.json")):
    """
    Assign Images from ADE20k dataset to a graph whose nodes have already been assigned a specific room type

    Args:
        ade_graph: networkx type graph containing node info - {type, base_type, target}
        json_path: Path to a jsonn file containing mapping of room_types to various images

    Return:
        ade_graph: Graph with updated nodes with randomly assigned image of a specific room_type
    """

    with open(json_path, 'r') as f:
        json_data = json.load(f)

    images_assigned = []
    for node in ade_graph.nodes():
        room_type = ade_graph.nodes[node]['type']
        room_type = room_type.split(" ")[0]  # For ambiguous cases - remove assigned number
        random_image = np.random.choice(json_data[room_type])
        while random_image in images_assigned:
            random_image = np.random.choice(json_data[room_type])
        images_assigned.append(random_image)
        ade_graph.nodes[node]['image'] = random_image

    return ade_graph


def print_mapping(ade_graph):
    """
    Print a mapping of node: room_type - image_url for all nodes in the graph
    """
    for this_node in ade_graph.nodes():
        print('{}: {} - {:>50}'.format(this_node,
                                       ade_graph.nodes[this_node]['type'],
                                       ade_graph.nodes[this_node]['image']))


def select_random_room(available_rooms: list, occupied: Tuple | None):
    """
    Pick a random room from a list of (available rooms - occupied)
    Args:
        available_rooms: List of available nodes that can be assigned a room
        occupied: A node that already has been assigned a room

    Returns:
        A random room chosen
    """

    if occupied in available_rooms:
        available_rooms.remove(occupied)
    return available_rooms[np.random.choice(len(available_rooms))]


def find_distance(edges: List[Tuple], nodes: List) -> Dict:
    """
    Given the edges and nodes of a graph, generate distances between every node using BFS.

    Args:
        edges: List of tuples representing edges in the graph.
        nodes: List of nodes in the graph.

    Returns:
        A dictionary where distances[start][end] gives the shortest distance from start to end.
    """
    # Build adjacency list
    graph = defaultdict(list)
    for u, v in edges:
        graph[u].append(v)
        graph[v].append(u)

    # Dictionary to hold distances between all node pairs
    distances = {}

    # BFS from each node
    for start in nodes:
        queue = deque([(start, 0)])
        visited = set()
        dist_map = {}

        while queue:
            current, dist = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            dist_map[current] = dist

            for neighbor in graph[current]:
                if neighbor not in visited:
                    queue.append((neighbor, dist + 1))

        distances[start] = dist_map

    return distances

if __name__ == "__main__":
    ade_map = ADEMap(3,3,5)
    ade_gr = ade_map.create_tree_graph()
    distances = find_distance(ade_gr.edges(), ade_gr.nodes())
    print(distances)
    ade_map.plot_graph(ade_gr)
