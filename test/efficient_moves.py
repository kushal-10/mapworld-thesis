import unittest
import os
import numpy as np
import logging
import networkx as nx
import ast
from networkx.drawing.nx_pydot import to_pydot

from escaperoom.scorer import is_efficient_move, get_neighbors
from engine.ade_maps import ADEMap

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename=os.path.join('test', 'test_efficient_moves.log'),
                    filemode='w')



class EfficientMovesTest(unittest.TestCase):

    def setUp(self):
        N = 5000
        logger.info(f"Setting up random cyclic and random tree graphs for {N} instances")
        self.graphs = []
        for i in range(N):
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

        # If common second neighbors - skip the test
        snbrs = get_neighbors(test_nbr, graph.edges())
        found = False
        for snbr in snbrs:
            if snbr not in visited:
                found = True

        logger.info(f"Found an unmarked snbr for test nbr? = {found}")

        return start_node, test_nbr, neighbors, list(visited), found


    def test_efficient_moves(self):
        for graph_obj in self.graphs:
            curr_room, next_room, neighbors, visited_rooms, found = self.random_walk(graph_obj)
            target_observed = False
            move = "random"
            graph = graph_obj["graph"]
            map_edges = graph.edges()

            true_result = is_efficient_move(curr_room, next_room, neighbors, visited_rooms,
                                            move, target_observed, map_edges)

            if found:
                assert true_result == True

            # for nbr in neighbors:
            #     if nbr != next_room:
            #         false_result = is_efficient_move(curr_room, nbr, neighbors, visited_rooms,
            #                                 move, target_observed, map_edges)
            #
            #         assert false_result == False



if __name__ == '__main__':
    unittest.main()







