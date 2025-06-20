"""
Utils module to handle room type/image assignments to Graphs
"""
import json
import numpy as np
import os
from typing import Tuple, Dict, List
from collections import deque, defaultdict

# Assign the categories from "categories.json" here.
CATEGORY_OUTDOORS = "outdoors"
CATEGORY_TARGETS = "targets"
CATEGORY_DISTRACTORS = "distractors"


def assign_types(nx_graph,
                 json_path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources",
                                               "categories.json"),
                 ambiguity: list[int] = None, use_outdoor_categories: bool = True):
    """
    Assign room categories and images to the nodes in the generated graph.
    Example nx_graph.nodes[room] = {
        'base_type': 'indoor' or 'outdoor' depending on degree of the room
        'type': 'k/kitchen',
        'ambiguous': True - for all ambiguous cases | a random room if ambiguity is None([1]) - else False
    }

    Args:
        nx_graph: Generated graph. (via BaseGraph methods)
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

    outdoor_rooms = []  # Rooms with only one neighbour - Degree = 1
    indoor_rooms = []  # Internal rooms, with Degree > 1
    # Assign rooms based on number of neighbours
    for room in nx_graph.nodes():
        if nx_graph.degree(room) == 1:
            outdoor_rooms.append(room)
        elif nx_graph.degree(room) > 1:
            indoor_rooms.append(room)
        else:
            raise ValueError(f"Check Graph Generation methods in BaseGraph!! Found a node with no neighbors!")

    if len(indoor_rooms) < sum(ambiguity):
        raise ValueError(
            f"Ambiguity passed is {ambiguity}, But number of indoor rooms in the generated graph is {len(indoor_rooms)}"
            f"\nTry decreasing ambiguity such that sum of ambiguity is <= {len(indoor_rooms)}"
            f"\nIf ambiguity is strictly required and possible with the initialized Map, try generating another random graph.")

    with open(json_path, 'r') as f:
        categories = json.load(f)

    outdoor_rooms_assigned = []
    # Using distractors here, change to "targets" if required
    category_key = CATEGORY_OUTDOORS if use_outdoor_categories else CATEGORY_DISTRACTORS
    for room in outdoor_rooms:
        random_outdoor_room = np.random.choice(categories[category_key])
        while random_outdoor_room in outdoor_rooms_assigned:
            random_outdoor_room = np.random.choice(categories[category_key])

        outdoor_rooms_assigned.append(random_outdoor_room)
        nx_graph.nodes[room]['base_type'] = "outdoor"  # Used as an identifier for rooms with one neighbour
        nx_graph.nodes[room]['type'] = random_outdoor_room
        nx_graph.nodes[room]['ambiguous'] = False

    indoor_rooms_assigned = []
    # Handles cases if outdoor nodes are also randomly drawn from "targets" category
    room_type_assigned = [] if category_key != CATEGORY_TARGETS else outdoor_rooms_assigned

    for amb in ambiguity:
        # Pick a random unique room category from TARGETS for each entry in ambiguity
        random_room_type = np.random.choice(categories[CATEGORY_TARGETS])
        while random_room_type in room_type_assigned:
            random_room_type = np.random.choice(categories[CATEGORY_TARGETS])
        room_type_assigned.append(random_room_type)

        room_count = 1
        for r in range(amb):
            # Pick a random node from the list of indoor nodes and assign the selected room_category
            room = indoor_rooms[np.random.randint(len(indoor_rooms))]
            while room in indoor_rooms_assigned:
                room = indoor_rooms[np.random.randint(len(indoor_rooms))]
            indoor_rooms_assigned.append(room)

            nx_graph.nodes[room]['base_type'] = "indoor"
            # Make the room_type unique
            # (so instead of assigning 'kitchen' to multiple nodes, assign 'kitchen1' and 'kitchen2')
            if amb != 1:
                nx_graph.nodes[room]['type'] = str(random_room_type) + " " + str(room_count)
                room_count += 1
                nx_graph.nodes[room]['ambiguous'] = True  # Set True for all ambiguous rooms
            else:
                nx_graph.nodes[room]['type'] = random_room_type
                nx_graph.nodes[room]['ambiguous'] = False  # Rooms are not ambiguous when ambiguity = [1]

    # Remaining nodes - as distractors
    distractor_rooms = list(set(indoor_rooms) - set(indoor_rooms_assigned))

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

        nx_graph.nodes[room]['base_type'] = "indoor"
        nx_graph.nodes[room]['type'] = random_distractor
        nx_graph.nodes[room]['ambiguous'] = False

    return nx_graph


def assign_images(nx_graph, json_path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources",
                                                   "images.json")):
    """
    Assign Images from ADE20k dataset to a graph whose nodes have already been assigned a specific room type

    Args:
        nx_graph: networkx type graph containing node info - {type, base_type, target}
        json_path: Path to a jsonn file containing mapping of room_types to various images

    Return:
        nx_graph: Graph with updated nodes with randomly assigned image of a specific room_type
    """

    with open(json_path, 'r') as f:
        json_data = json.load(f)

    images_assigned = []
    for node in nx_graph.nodes():
        room_type = nx_graph.nodes[node]['type']
        room_type = room_type.split(" ")[0]  # For ambiguous cases - remove assigned number
        random_image = np.random.choice(json_data[room_type])
        while random_image in images_assigned:
            random_image = np.random.choice(json_data[room_type])
        images_assigned.append(random_image)
        nx_graph.nodes[node]['image'] = random_image

    return nx_graph


def print_mapping(nx_graph):
    """
    Print a mapping of node: room_type - image_url for all nodes in the graph
    """
    for this_node in nx_graph.nodes():
        print('{}: {} - {:>50}'.format(this_node,
                                       nx_graph.nodes[this_node]['type'],
                                       nx_graph.nodes[this_node]['image']))


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

