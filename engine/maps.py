import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import random

# TODO: Write Tests for each map variant.

class BaseMap:

    def __init__(self, m: int = 3, n: int = 3, n_nodes: int = 9):
        """
        Set up a base 2-D graph, assign cycles in the graph if required

        Args:
            m: Number of rows in the graph.
            n: Number of columns in the graph
            n_nodes: Required number of nodes. Should be less than n*m

        Raises:
            ValueError: If any value is unset
            AssertionError: If `n_nodes` > `n*m`
        """
        if not m or not n or not n_nodes:
            raise ValueError(
                f"One of the values passed - m : {m}, n: {n}, n_nodes: {n_nodes} is not set. (n,m,n_nodes) >= 1")
        assert n_nodes <= m * n, "Number of nodes cannot exceed grid size"

        self.m = m
        self.n = n
        self.n_nodes = n_nodes

    @staticmethod
    def get_valid_neighbors(current_pos: np.array = [0, 0], visited: list = [], m: int = 3, n: int = 3):
        """
        Get a list of valid nodes, to which a step can be taken from the current node
        """

        possible_moves = [[0, 1], [0, -1], [1, 0], [-1, 0]]
        valid_neighbors = []
        for move in possible_moves:
            next_pos = [current_pos[0] + move[0], current_pos[1] + move[1]]

            if 0 <= next_pos[0] < m and 0 <= next_pos[1] < n and tuple(next_pos) not in visited:
                valid_neighbors.append(next_pos)

        return valid_neighbors

    def create_tree_graph(self, current_node=None):
        """
        Create an Acyclic graph

        Returns:
            G: A networkx acyclic graph with (n_nodes-1) edges
        """
        G = nx.Graph()
        visited = set()
        tracker = []

        # Pick a random node from the grid
        if not current_node:
            current_node = (np.random.randint(self.m), np.random.randint(self.n))

        tracker.append(current_node)
        visited.add(tuple(current_node))
        G.add_node(tuple(current_node))

        while len(visited) < self.n_nodes:
            current_node = tracker[-1]
            neighbors = self.get_valid_neighbors(current_node, visited, self.m, self.n)
            if neighbors:
                # Traverse in random (valid) directions until no possible neighbor nodes from current node are found
                random_index = np.random.choice(len(neighbors))
                next_node = neighbors[random_index]
                visited.add(tuple(next_node))
                G.add_node(tuple(next_node))
                G.add_edge(tuple(current_node), tuple(next_node))
                tracker.append(next_node)
            else:
                # Then track back to the last node from which a move can be made to a node that has not been visited
                tracker.pop()

        return G

    def create_cyclic_graph(self, n_loops: int = 1):
        """
        Create a cyclic graph with a specified number of loops.

        Args:
            n_loops: Number of loops (cycles) required in the graph.

        Returns:
            loop_graph: A networkx graph containing n_loops cycles.

        Raises:
            ValueError: If parameters are invalid or a valid configuration cannot be found.
        """
        if n_loops < 1:
            raise ValueError(f"Please set n_loops to at least 1 to form a cycle. Passed value: {n_loops}")

        if self.m == 1 or self.n == 1:
            raise ValueError(
                "1-D graph is being passed. Please use a 2-D grid with m, n >= 2 to create a cyclic graph."
            )

        if self.n_nodes < n_loops + 3:
            raise ValueError(
                f"At least {n_loops + 3} nodes are required to form {n_loops} loops."
                f" nodes provided: {self.n_nodes}. Increase n_nodes or reduce n_loops."
            )

        max_attempts = 10
        attempt = 0

        while attempt < max_attempts:
            attempt += 1
            possible_starts = set()

            # Pick a unique random starting node
            current_node = [np.random.randint(self.m), np.random.randint(self.n)]
            while tuple(current_node) in possible_starts:
                current_node = [np.random.randint(self.m), np.random.randint(self.n)]
            possible_starts.add(tuple(current_node))

            # Create acyclic graph from the starting node
            G = self.create_tree_graph(current_node)

            # Collect all possible additional edges that could be added to form loops
            nodes = G.nodes()
            existing_edges = set(G.edges())
            possible_edges = []

            for node in nodes:
                neighbors = self.get_valid_neighbors(node, [], self.m, self.n)
                for neighbor in neighbors:
                    if tuple(neighbor) in nodes:
                        edge = tuple(sorted((tuple(node), tuple(neighbor))))
                        if edge not in existing_edges and edge not in possible_edges:
                            possible_edges.append(edge)

            # Try to add edges to form desired number of loops
            np.random.shuffle(possible_edges)
            loop_graph = G.copy()
            cycles = nx.cycle_basis(loop_graph)

            while len(cycles) < n_loops and possible_edges:
                edge = possible_edges.pop()
                loop_graph.add_edge(*edge)
                cycles = nx.cycle_basis(loop_graph)

            if len(cycles) >= n_loops:
                return loop_graph

            print(f"[Attempt {attempt}] Could only form {len(cycles)} cycles. Retrying...")

        # If after max attempts, no valid config is found...
        raise ValueError(
            f"Could not find a valid configuration to form {n_loops} loops after {max_attempts} attempts."
            f" Try reducing n_loops or increasing grid size (m x n)."
        )

    def create_star_graph(self):
        """
        Create a “star” configuration:
          - Pick one central node at random.
          - Add its 4 orthogonal neighbors.
          - If n_nodes > 5, iteratively attach the remaining nodes by
            choosing one of the 4 “arm” endpoints at random and extending
            to an unvisited neighbor.

        Returns:
            star_graph: networkx Graph with exactly self.n_nodes nodes.

        Raises:
            ValueError: If the grid or n_nodes aren’t compatible.
        """
        # Basic checks
        if self.m < 3 or self.n < 3:
            raise ValueError(f"Grid must be at least 3×3 for a star (got {self.m}×{self.n}).")
        if self.n_nodes < 5:
            raise ValueError(f"Need at least 5 nodes for a star (got {self.n_nodes}).")
        if self.n_nodes > self.m * self.n:
            raise ValueError(f"Cannot place {self.n_nodes} nodes in a {self.m}×{self.n} grid.")

        G = nx.Graph()
        visited = set()

        # 1) Pick central node
        center = (np.random.randint(1, self.m), np.random.randint(1, self.n))
        G.add_node(center)
        visited.add(center)

        # 2) Add the 4 orthogonal neighbors
        arms = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nb = (center[0] + dx, center[1] + dy)
            if 0 <= nb[0] < self.m and 0 <= nb[1] < self.n:
                G.add_node(nb)
                G.add_edge(center, nb)
                visited.add(nb)
                arms.append(nb)
        if len(arms) < 4:
            raise ValueError("Center chosen too close to the border—cannot form 4 arms. Try larger grid.")

        # 3) If more nodes remain, attach them one by one
        while len(visited) < self.n_nodes:
            # pick a random endpoint from the current arms
            endpoint = random.choice(arms)
            # find its valid unvisited neighbors
            cands = [tuple(p) for p in self.get_valid_neighbors(endpoint, visited, self.m, self.n)]
            if not cands:
                # if this arm is stuck, remove it from arms and continue
                arms.remove(endpoint)
                if not arms:
                    raise ValueError("No more possible extensions; cannot place all nodes.")
                continue
            new_node = random.choice(cands)
            G.add_node(new_node)
            G.add_edge(endpoint, new_node)
            visited.add(new_node)
            arms.append(new_node)

        return G

    def create_ladder_graph(self):
        """
        Create a 2-row “ladder” configuration with n_cols = n_nodes/2 rungs:
          - Only works if n_nodes is even, and grid has at least 2 rows and n_cols columns.
          - Nodes occupy positions (0..1, 0..n_cols-1).
          - Edges along each row plus vertical “rungs” between rows.

        Returns:
            ladder_graph: networkx Graph with exactly self.n_nodes nodes.

        Raises:
            ValueError: If parameters are invalid.
        """
        if self.n_nodes % 2 != 0:
            raise ValueError(f"n_nodes must be even for a ladder (got {self.n_nodes}).")
        n_cols = self.n_nodes // 2
        if self.m < 2 or self.n < n_cols:
            raise ValueError(
                f"Grid must be at least 2×{n_cols} to fit the ladder "
                f"(got {self.m}×{self.n})."
            )

        G = nx.Graph()
        visited = set()

        # Add all nodes in the 2×n_cols block at top-left
        for i in (0, 1):
            for j in range(n_cols):
                G.add_node((i, j))
                visited.add((i, j))

        # Add horizontal edges on each row
        for i in (0, 1):
            for j in range(n_cols - 1):
                G.add_edge((i, j), (i, j + 1))

        # Add vertical rungs between the two rows
        for j in range(n_cols):
            G.add_edge((0, j), (1, j))

        return G

    def create_cycle_graph(self):
        """
        Create a single simple cycle of length self.n_nodes, placed at a random
        2×(n_nodes/2) rectangle within the m×n grid.

        Requirements:
          - self.n_nodes must be even and >= 4.
          - The grid must have at least 2 rows and at least self.n_nodes/2 columns.

        Returns:
            A networkx Graph whose nodes form a single closed loop somewhere
            in the grid, in random orientation and starting point.
        Raises:
            ValueError: if parameters don’t allow embedding such a cycle.
        """
        # sanity checks
        if self.n_nodes < 4 or self.n_nodes % 2 != 0:
            raise ValueError(f"Need an even number of nodes ≥ 4 for a single cycle (got {self.n_nodes}).")
        n_cols = self.n_nodes // 2
        if self.m < 2 or self.n < n_cols:
            raise ValueError(
                f"Grid must be at least 2×{n_cols} to fit a cycle of length {self.n_nodes} "
                f"(got {self.m}×{self.n})."
            )

        # choose a random pair of adjacent rows
        row0 = random.randrange(self.m - 1)
        row1 = row0 + 1

        # choose a random horizontal offset so we fit n_cols across
        max_offset = self.n - n_cols
        col0 = random.randrange(max_offset + 1)

        # build the two “sides” of the rectangle
        top_row = [(row0, col0 + j) for j in range(n_cols)]
        bottom_row = [(row1, col0 + j) for j in range(n_cols)][::-1]

        # randomly flip orientation (top↔bottom) half the time
        if random.choice([True, False]):
            top_row, bottom_row = bottom_row, top_row

        cycle_nodes = top_row + bottom_row

        # rotate the cycle so it doesn’t always start at index 0
        k = random.randrange(len(cycle_nodes))
        cycle_nodes = cycle_nodes[k:] + cycle_nodes[:k]

        # assemble graph
        G = nx.Graph()
        G.add_nodes_from(cycle_nodes)
        for u, v in zip(cycle_nodes, cycle_nodes[1:] + cycle_nodes[:1]):
            G.add_edge(u, v)

        return G


    def create_path_graph(self):
        """
        Create a simple path (chain) of self.n_nodes nodes on the grid.

        Requirements:
          - self.n_nodes ≥ 1
          - self.n_nodes ≤ self.m * self.n
          - The grid must allow a non-branching walk of length n_nodes.

        Returns:
          A networkx Graph whose nodes form a single chain.

        Raises:
          ValueError: if it gets stuck before placing all nodes.
        """
        if self.n_nodes < 1:
            raise ValueError(f"Need at least 1 node for a path (got {self.n_nodes}).")
        if self.n_nodes > self.m * self.n:
            raise ValueError(f"Cannot place {self.n_nodes} nodes in a {self.m}×{self.n} grid.")

        G = nx.Graph()
        visited = []
        # start somewhere random
        start = (random.randrange(self.m), random.randrange(self.n))
        visited.append(start)
        G.add_node(start)

        while len(visited) < self.n_nodes:
            curr = visited[-1]
            # orthogonal moves into unvisited
            nbrs = [tuple(nb) for nb in self.get_valid_neighbors(curr, visited, self.m, self.n)]
            if not nbrs:
                raise ValueError(
                    f"Stuck at {curr} after {len(visited)} nodes; cannot extend to {self.n_nodes}."
                )
            nxt = random.choice(nbrs)
            visited.append(nxt)
            G.add_node(nxt)
            G.add_edge(curr, nxt)

        return G


    def plot_graph(self, G):
        nx.draw_networkx(G, pos={n: n for n in G.nodes()})
        plt.show()

    def __repr__(self) -> str:
        return f"<BaseMap({self.m}, {self.n}, {self.n_nodes})>"


if __name__ == '__main__':
    map = BaseMap(4, 4, 6)
    G = map.create_cycle_graph()
    map.plot_graph(G)

    print(G.nodes())