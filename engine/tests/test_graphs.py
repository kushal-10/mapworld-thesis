import unittest
import os
import logging
import numpy as np

from engine.graphs import BaseGraph

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename=os.path.join('engine', 'tests', 'test_graphs.log'),
                    filemode='w')

IMG_PTH = os.path.join('engine', 'tests', 'graph_images')
os.makedirs(IMG_PTH, exist_ok=True)

class GraphGenerationTest(unittest.TestCase):

    def setUp(self):
        self.grid_size_small = 4
        self.grid_size_big = 5
        self.num_rooms_small = 4
        self.num_rooms_big = 8


    def test_graph_generation(self):
        for i in range(self.grid_size_small, self.grid_size_big + 1):
            for n_rooms in range(self.num_rooms_small, self.num_rooms_big+ 1):
                base_graph = BaseGraph(i, i, n_rooms)
                tree_graph = base_graph.create_tree_graph()
                path_graph = base_graph.create_path_graph()
                if n_rooms%2==0:
                    cycle_graph = base_graph.create_cycle_graph()
                    ladder_graph = base_graph.create_ladder_graph()
                if n_rooms >= 5:
                    star_graph = base_graph.create_star_graph()

                tree_img_path = os.path.join(IMG_PTH,
                                            f'tree_{i}_{i}_{n_rooms}.jpg')
                base_graph.save_graph(tree_graph, tree_img_path)
                path_img_path = os.path.join(IMG_PTH,
                                             f'path_{i}_{i}_{n_rooms}.jpg')
                base_graph.save_graph(path_graph, path_img_path)
                if n_rooms%2==0:
                    cycle_img_path = os.path.join(IMG_PTH,
                                                  f'cycle_{i}_{i}_{n_rooms}.jpg')
                    base_graph.save_graph(cycle_graph, cycle_img_path)
                    ladder_img_path = os.path.join(IMG_PTH,
                                                  f'ladder_{i}_{i}_{n_rooms}.jpg')
                    base_graph.save_graph(ladder_graph, ladder_img_path)
                if n_rooms >= 5:
                    star_img_path = os.path.join(IMG_PTH,
                                                 f'star_{i}_{i}_{n_rooms}.jpg')
                    base_graph.save_graph(star_graph, star_img_path)
                logger.info(f"Saved graphs with grid=({i}x{i}), rooms={n_rooms}")


if __name__ == '__main__':
    unittest.main()







