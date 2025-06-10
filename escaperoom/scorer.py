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
        if dist_to_unexplored is None:
            raise RuntimeError(f"No unexplored rooms reachable from neighbor {nbr}")
        distances.append({"neighbor": nbr, "dist": dist_to_unexplored})

    return distances


def is_efficient_move(curr_room: Tuple[int, int],
                      next_room: Tuple[int, int],
                      neighbors: List[Tuple[int, int]],
                      visited_rooms: List[Tuple[int, int]],
                      move: str,
                      target_observed: bool,
                      map_edges) -> bool:

    """
    Args:
        curr_room: Current position of the Explorer Agent
        next_room: Next position of the Explorer Agent after making move
        neighbors: Neighboring Rooms from the Explorer Agent's current position
        visited_rooms: rooms visited by explorer
        move: Move made by the explorer from curr_room
        target_observed: A flag to indicate whether the target room has already been observed by the explorer
        ade_map: A networkX based graph

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



if __name__ == "__main__":

    ademap = ADEMap(4, 4, 10)
    G = ademap.create_cyclic_graph()
    G = ademap.assign_types(G, ambiguity=[3, 3], use_outdoor_categories=False)
    G = ademap.assign_images(G)
    metadata = ademap.metadata(G)
    print(G.nodes())
    print(G.edges())

    env = MapWorldEnv(render_mode="human", size=4, map_metadata=metadata)
    curr_room = (0,2)
    visited_rooms = [(2,1), (1,1), (1,0), (0,0), (0,1), (0,2), (1,2), (2,2), (2,3)]
    # Not visited - 2,0 and 2,3
    next_room = (0,1)
    neighbors = get_neighbors(curr_room, G.edges())
    move = "temp"
    target_observed = False

    result = is_efficient_move(curr_room, next_room, neighbors, visited_rooms, move, target_observed, G.edges())

    print(result)