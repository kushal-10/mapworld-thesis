from engine.maps import BaseMap

import random
import os
import json
import numpy as np
from typing import Tuple, Any

class ADEMap(BaseMap):

    def __init__(self, m: int = 3, n: int = 3, n_rooms: int = 9, seed: int = 42):
        """
        Set up a base 2-D graph whose nodes are based on ADE20k dataset.

        Args:
            m: Number of rows in the graph.
            n: Number of columns in the graph
            n_rooms: Required number of rooms. Should be less than n*m

        Raises:
            ValueError: If any value is unset
            AssertionError: If `n_rooms` > `n*m`
        """
        random.seed(seed)
        np.random.seed(seed)
        super().__init__(m, n, n_rooms)


    def set_positions(self, ambiguous_rooms: list, indoor_rooms: list, outdoor_rooms: list, start_type: str = "random",
                      end_type: str = "random", distance: int = 2) -> Any | None:
        """
        Set agent position/target position.
        Based on the list of rooms provided and required area for the node

        Args:
            ambiguous_rooms: List of rooms assigned as ambiguous
            indoor_rooms: List of rooms assigned as indoor
            outdoor_rooms: List of rooms assigned as outdoor
            start_type: Type of room that needs to be assigned - indoor/outdoor/random/ambiguous to agents start position
            end_type: Type of room that needs to be assigned to the target room
            distance: Distance between start and target node.

        Return:
            start_pos, target_pos - in position/node: (x, y)
        """

        # TODO - Find Nodes at Manhattan distance for each node, and group by category, the search for valid pairs

        return (0,0), (0,0)



    def metadata(self, G, start_type: str = "outdoor", end_type: str = "outdoor", distance: int = 2) -> dict:
        """
        Generate metadata for the Graph incl. start/end points
        Args:

            G: networkx type graph
            start_type: "outdoor"/"indoor"/"random"/"ambiguous" - Defining agent start position
            end_type: "outdoor"/"indoor"/"random"/"ambiguous" - Defining target room position
            distance: Distance between start and target node.
        """

        # Metadata values
        graph_id = ""
        named_nodes = []
        unnamed_nodes = []
        named_edges = []
        unnamed_edges = []
        node_to_category = {}
        category_to_node = {}
        node_to_image = {}
        category_to_image = {}

        # Additional values
        ambiguous_rooms = []
        indoor_rooms = []
        outdoor_rooms = []

        # Nodes Metadata
        for node in G.nodes():
            # Clean Node name
            node_name = G.nodes[node]['type']
            node_name = " ".join(node_name.split("__"))
            node_name = " ".join(node_name.split("_"))
            node_name = node_name.capitalize()

            # Create a graph id based on node position and node category
            graph_id += str(list(node)[0]) + str(list(node)[1]) + node_name[0].lower()

            named_nodes.append(node_name)
            unnamed_nodes.append(node)

            node_to_category[str(node)] = node_name
            category_to_node[node_name] = node
            node_to_image[str(node)] = G.nodes[node]['image']
            category_to_image[node_name] = G.nodes[node]['image']

            # Additional info
            if G.nodes[node]['type'] == "indoor":
                if G.nodes[node]['ambiguous']:
                    ambiguous_rooms.append(node)
                else:
                    indoor_rooms.append(node)
            else:
                outdoor_rooms.append(node)

        # Edge Metadata
        for edge in G.edges():
            named_edge = []
            for e in edge:
                named_edge.append(node_to_category[str(e)])
            named_edges.append(tuple(named_edge))
            unnamed_edges.append(edge)

        # Set Random start and Target positions
        # Can be overridden by the environment if required
        start_pos, target_pos = self.set_positions(ambiguous_rooms=ambiguous_rooms, indoor_rooms=indoor_rooms, outdoor_rooms=outdoor_rooms,
                                                   start_type=start_type, end_type=end_type, distance=distance)

        graph_metadata = {
            "graph_id": graph_id,
            "m": self.m,
            "n": self.n,
            "named_nodes": named_nodes,
            "unnamed_nodes": unnamed_nodes,
            "named_edges": named_edges,
            "unnamed_edges": unnamed_edges,
            "node_to_category": node_to_category,
            "category_to_node": category_to_node,
            "node_to_image": node_to_image,
            "category_to_image": category_to_image,
            "start_node": str(start_pos),
            "target_node": str(target_pos),
        }

        return graph_metadata


if __name__ == '__main__':
    ademap = ADEMap(4, 4, 10)
    G = ademap.create_cyclic_graph()
    G = ademap.assign_types(G, ambiguity=[3,3], use_outdoor_categories=False)
    G = ademap.assign_images(G)
    metadata = ademap.metadata(G)

    print(metadata)

