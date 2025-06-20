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
        self.distances = [1,2,3]
        self.ambiguities = [1,2]


    def testPathMap(self):
        for n_rooms in range(8,9):
            for st in self.start_types:
                for tt in self.target_types:
                    for dist in self.distances:
                        for amb in self.ambiguities:
                            map = BaseMap(10,10, n_rooms=n_rooms)
                            path_graph = map.create_path_graph()
                            if type(amb) == int:
                                amb = [amb]
                            if sum(amb) <= n_rooms:
                                path_graph = assign_types(path_graph, ambiguity=amb, use_outdoor_categories=True)
                                path_map = assign_images(path_graph)
                                map_metadata = map.metadata(path_map, start_type=st, end_type=tt, distance=dist)
    #
    # def testStarMap(self):
    #     def testPathMap(self):
    #         for n_rooms in range(8, 9):
    #             for st in self.start_types:
    #                 for tt in self.target_types:
    #                     for dist in self.distances:
    #                         for amb in self.ambiguities:
    #                             map = BaseMap(10, 10, n_rooms=n_rooms)
    #                             star_graph = map.create_star_graph()
    #                             if type(amb) == int:
    #                                 amb = [amb]
    #                             if sum(amb) <= n_rooms:
    #                                 star_graph = assign_types(star_graph, ambiguity=amb, use_outdoor_categories=False)
    #                                 star_map = assign_images(star_graph)
    #                                 map_metadata = map.metadata(star_map, start_type=st, end_type=tt, distance=dist)
    #
    # def testLadderMap(self):
    #     for n_rooms in range(10, 12):
    #         for st in self.start_types:
    #             for tt in self.target_types:
    #                 for dist in self.distances:
    #                     for amb in self.ambiguities:
    #                         map = BaseMap(10, 10, n_rooms=n_rooms)
    #                         ladder_graph = map.create_ladder_graph()
    #                         if type(amb) == int:
    #                             amb = [amb]
    #                         if sum(amb) <= n_rooms:
    #                             ladder_graph = assign_types(ladder_graph, ambiguity=amb, use_outdoor_categories=False)
    #                             ladder_map = assign_images(ladder_graph)
    #                             map_metadata = map.metadata(ladder_map, start_type=st, end_type=tt, distance=dist)


if __name__ == '__main__':
    unittest.main()