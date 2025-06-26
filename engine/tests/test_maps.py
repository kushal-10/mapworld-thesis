import os
import logging
import unittest

from engine.maps import BaseMap
from engine.map_utils import assign_images, assign_types


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename=os.path.join('engine', 'tests', 'test_maps.log'),
                    filemode='w')


class MapGenerationTest(unittest.TestCase):

    def setUp(self):
        self.start_types = ["ambiguous", "indoor", "outdoor", "random"]
        self.target_types = ["ambiguous", "indoor", "outdoor", "random"]
        self.seed = 10

    #
    # def testPathMap(self):
    #     for n_rooms in range(8,9):
    #         for st in self.start_types:
    #             for tt in self.target_types:
    #                 for dist in range(1,5):
    #                     for amb in ([1], [2], [3], [4]):
    #                         for seed in range(1,self.seed+1):
    #                             map = BaseMap(10,10, n_rooms=n_rooms, seed=seed,)
    #                             path_graph = map.create_path_graph()
    #                             if sum(amb) <= n_rooms:
    #                                 path_graph = assign_types(path_graph, ambiguity=amb, use_outdoor_categories=True)
    #                                 path_map = assign_images(path_graph)
    #                                 map_metadata = map.metadata(path_map, start_type=st, end_type=tt, distance=dist)
    #
    #
    # def testStarMap(self):
    #     for n_rooms in range(8,9):
    #         for st in self.start_types:
    #             for tt in self.target_types:
    #                 for dist in range(1,5):
    #                     for amb in ([1], [2], [3], [4]):
    #                         for seed in range(1,self.seed+1):
    #                             map = BaseMap(10,10, n_rooms=n_rooms, seed=seed,)
    #                             path_graph = map.create_path_graph()
    #                             if sum(amb) <= n_rooms:
    #                                 if st == "random" and (tt == "outdoor" or tt == "ambiguous"):
    #                                     path_graph = assign_types(path_graph, ambiguity=amb, use_outdoor_categories=True)
    #                                     path_map = assign_images(path_graph)
    #                                     map_metadata = map.metadata(path_map, start_type=st, end_type=tt, distance=dist)
    #
    def testTreeMap(self):
        for n_rooms in range(8,9):
            for st in self.start_types:
                for tt in self.target_types:
                    for dist in range(1,5):
                        for amb in ([1]):
                            for seed in range(1,self.seed+1):
                                map = BaseMap(10,10, n_rooms=n_rooms, graph_type="tree", seed=seed)
                                map_metadata = map.metadata(start_type=st, end_type=tt, ambiguity=[1], distance=dist)

    # def testCycleMap(self):
    #     for n_rooms in range(8,9):
    #         for st in self.start_types:
    #             for tt in self.target_types:
    #                 for dist in range(1,5):
    #                     for amb in ([1], [2], [3], [4]):
    #                         for seed in range(1,self.seed+1):
    #                             map = BaseMap(10,10, n_rooms=n_rooms, seed=seed,)
    #                             cycle_graph = map.create_cycle_graph()
    #                             if sum(amb) <= n_rooms:
    #                                 if st == "random" and (tt != "outdoor"):
    #                                     cycle_graph = assign_types(cycle_graph, ambiguity=amb, use_outdoor_categories=True)
    #                                     cycle_map = assign_images(cycle_graph)
    #                                     map_metadata = map.metadata(cycle_map, start_type=st, end_type=tt, distance=dist)



if __name__ == '__main__':
    unittest.main()