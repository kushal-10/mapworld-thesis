import unittest
import os
import numpy as np
import logging
import networkx as nx
import ast

from escaperoom.scorer import is_efficient_move, get_neighbors
from engine.ade_maps import ADEMap

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename=os.path.join('tests', 'test_efficient_moves.log'),
                    filemode='w')



class EfficientMovesTest(unittest.TestCase):

    def setUp(self):
        N = 500
        logger.info(f"Setting up random cyclic and random tree graphs for {N} instances")
        self.graphs = []
        for i in range(N):

            # TEST ON RANDOM GRAPHS
            graph_size = np.random.randint(3, 10)
            num_rooms = np.random.randint(6, graph_size*graph_size)
            map = ADEMap(graph_size, graph_size, num_rooms)
            graph = map.create_tree_graph()
            graph = map.assign_types(graph, ambiguity=[1], use_outdoor_categories=False)
            graph = map.assign_images(graph)
            metadata_obj = {
                "graph": graph,
                "metadata": map.metadata(graph, start_type="indoor", end_type="outdoor")
            }
            self.graphs.append(metadata_obj)
            cyclic_graph = map.create_cyclic_graph()
            cyclic_graph = map.assign_types(cyclic_graph, ambiguity=[1], use_outdoor_categories=False)
            cyclic_graph = map.assign_images(cyclic_graph)
            metadata_obj = {
                "graph": cyclic_graph,
                "metadata": map.metadata(cyclic_graph, start_type="indoor", end_type="outdoor")
            }
            self.graphs.append(metadata_obj)

            # TEST ON ESCAPE ROOM GRAPH TYPES
            # 1. CYCLE
            graph_size = np.random.randint(8, 10)
            num_rooms = np.random.randint(6, graph_size * 2)
            if num_rooms%2 !=0:
                num_rooms = num_rooms - 1
            map = ADEMap(graph_size, graph_size, num_rooms)
            cycle_graph = map.create_cycle_graph()
            cycle_graph = map.assign_types(cycle_graph)
            cycle_graph = map.assign_images(cycle_graph)
            metadata_obj = {
                "graph": cycle_graph,
                "metadata": map.metadata(cycle_graph, start_type="indoor", end_type="indoor")
            }
            self.graphs.append(metadata_obj)

            # 2. LADDER
            # Map layout similar to cycle should work
            ladder_graph = map.create_ladder_graph()
            ladder_graph = map.assign_types(ladder_graph)
            ladder_graph = map.assign_images(ladder_graph)
            metadata_obj = {
                "graph": ladder_graph,
                "metadata": map.metadata(ladder_graph, start_type="indoor", end_type="indoor")
            }
            self.graphs.append(metadata_obj)

            # 3. Path Graph - Same params as cycle/ladder should be fine
            path_graph = map.create_path_graph()
            path_graph = map.assign_types(path_graph)
            path_graph = map.assign_images(path_graph)
            metadata_obj = {
                "graph": path_graph,
                "metadata": map.metadata(path_graph, start_type="indoor", end_type="indoor")
            }
            self.graphs.append(metadata_obj)

            # 4. Star
            star_graph = map.create_star_graph()
            star_graph = map.assign_types(star_graph)
            star_graph = map.assign_images(star_graph)
            metadata_obj = {
                "graph": star_graph,
                "metadata": map.metadata(star_graph, start_type="indoor", end_type="indoor")
            }
            self.graphs.append(metadata_obj)


    @staticmethod
    def random_walk(graph_obj):
        """
        Randomly check efficient moves for all nodes at dist == 2 form start node
        Args:
            graph_obj: A dict containing random cyclic/tree graph along with its metadata

        Returns:

        """
        graph = graph_obj["graph"]
        logger.info(f"Random Walk for graph with nodes = {graph.nodes()} and edges = {graph.edges()}")
        visited = set()

        metadata = graph_obj["metadata"]
        start_node = ast.literal_eval(metadata['start_node'])
        visited.add(start_node)
        logger.info(f"Start node = {start_node}")

        # Check degree of the node, should be >=2
        degree = nx.degree(graph, start_node)
        assert degree >= 2 # Atleast 2 neighbors

        neighbors = get_neighbors(start_node, graph.edges())
        logger.info(f"Start Node neighbors = {neighbors}")
        test_nbr = None
        for nbr in neighbors:
            visited.add(nbr)
            degree = nx.degree(graph, nbr)
            if degree >= 2: # Found a neighbor that goes to another room
                test_nbr = nbr

        assert test_nbr is not None # There should be at least one neighbor with degree >= 2
        logger.info(f"Test neighbor = {test_nbr} with neighbors = {get_neighbors(test_nbr, graph.edges())}")

        # Mark all second neighbors except for test_nbr as visited
        for nbr in neighbors:
            if test_nbr != nbr:
                second_nbrs = get_neighbors(nbr, graph.edges())
                logger.info(f"Second neighbors for neighbor {nbr} = {second_nbrs}")
                if second_nbrs:
                    for snbr in second_nbrs:
                        if snbr not in visited:
                            visited.add(snbr)

        logger.info(f"Visited neighbors = {visited}")


        # If common second neighbors - rm from visited, and add that nbr to similar_nbrs
        # This should return True efficient move for all similar_nbrs along with test_nbr
        similar_nbrs = set()
        test_snbrs = get_neighbors(test_nbr, graph.edges())
        found = False
        for snbr in test_snbrs:
            if snbr not in visited:
                found = True

        logger.info(f"Found an unmarked snbr for test nbr? = {found}")

        if not found:
            logger.info(f"Did not find any unexplored neighbors for test nbr, "
                        f"marking one as unexplored and adding that nbr for True Case (Efficient move from two nbrs)")

            for nbr in neighbors:
                if nbr != test_nbr:
                    possible_common_snbrs = get_neighbors(nbr, graph.edges())
                    for pc in possible_common_snbrs:
                        if pc in test_snbrs and pc != start_node:
                            logger.info(f"Found visited snbr for test nbr = {pc}, removing from visited set")
                            visited.remove(pc)
                            similar_nbrs.add(nbr)

        return start_node, test_nbr, neighbors, list(visited), found, list(similar_nbrs)


    def test_efficient_moves(self):
        for graph_obj in self.graphs:
            curr_room, next_room, neighbors, visited_rooms, found, similar_nbrs = self.random_walk(graph_obj)
            target_observed = False
            graph = graph_obj["graph"]
            map_edges = graph.edges()

            true_result = is_efficient_move(next_room, neighbors, visited_rooms,
                                            target_observed, map_edges)

            if found:
                assert true_result == True

            for nbr in neighbors:
                if nbr != next_room and nbr not in similar_nbrs:
                    false_result = is_efficient_move(nbr, neighbors, visited_rooms,
                                                     target_observed, map_edges)

                    assert false_result == False



if __name__ == '__main__':
    unittest.main()







