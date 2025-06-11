from typing import Tuple, Dict, List
from collections import deque

from engine.environment import MapWorldEnv
from engine.ade_maps import ADEMap


def get_neighbors(agent_room: Tuple, edges: List[Tuple[Tuple[int, int], Tuple[int, int]]]):
    """

    Args:
        agent_room: Current position of Explorer agent
        edges: All edges in the given graph

    Returns:
        A list of neighboring rooms of agent_room in the given graph
    """

    neighbors = []

    for u, v in edges:
        if u == agent_room:
            neighbors.append(v)
        elif v == agent_room:
            neighbors.append(u)

    return neighbors

def unexplored_distance(neighbors: List[Tuple[int, int]],
                        visited_rooms: List[Tuple[int, int]],
                        map_edges: List[Tuple[Tuple[int, int], Tuple[int, int]]]) -> List[Dict]:
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
