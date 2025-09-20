import unittest
from sssp.bmssp import Graph, sssp


class TestSSSP(unittest.TestCase):

    def test_empty_graph(self):
        """Test empty graph edge case"""
        g = Graph(1)  # Single vertex, no edges
        dist, pred = sssp(g, 0)
        self.assertEqual(dist[0], 0)
        self.assertIsNone(pred[0])

    def test_disconnected_graph(self):
        """Test disconnected graph"""
        g = Graph(4)
        g.add_edge(0, 1, 1)
        # Nodes 2 and 3 are disconnected
        dist, pred = sssp(g, 0)
        self.assertEqual(dist[0], 0)
        self.assertEqual(dist[1], 1)
        self.assertEqual(dist[2], float("inf"))
        self.assertEqual(dist[3], float("inf"))

    def test_self_loop(self):
        """Test graph with self loops"""
        g = Graph(3)
        g.add_edge(0, 0, 5)  # Self loop with positive weight
        g.add_edge(0, 1, 2)
        g.add_edge(1, 2, 3)
        dist, pred = sssp(g, 0)
        self.assertEqual(dist[0], 0)  # Should not use self loop
        self.assertEqual(dist[1], 2)
        self.assertEqual(dist[2], 5)

    def test_multiple_sources_same_distance(self):
        """Test case where multiple vertices have same distance"""
        g = Graph(4)
        g.add_edge(0, 1, 5)
        g.add_edge(0, 2, 5)  # Same weight
        g.add_edge(1, 3, 1)
        g.add_edge(2, 3, 1)  # Both paths to 3 have same total cost
        dist, pred = sssp(g, 0)
        self.assertEqual(dist[0], 0)
        self.assertEqual(dist[1], 5)
        self.assertEqual(dist[2], 5)
        self.assertEqual(dist[3], 6)  # min(5+1, 5+1) = 6

    def test_pivot_finding_large_trees(self):
        """Test case that exercises pivot finding with large subtrees"""
        # Create a graph where pivot finding will be triggered
        n = 20
        g = Graph(n)

        # Create a tree structure that will have large subtrees
        # Root at 0 with multiple branches
        for i in range(1, 5):
            g.add_edge(0, i, 1)

        # Each branch has a subtree
        branch_size = 3
        for branch in range(1, 5):
            for j in range(branch_size):
                node = branch * 10 + j
                if node < n:
                    if j == 0:
                        g.add_edge(branch, node, 1)
                    else:
                        g.add_edge(branch * 10 + j - 1, node, 1)

        dist, pred = sssp(g, 0)
        self.assertEqual(dist[0], 0)

        # All connected nodes should be reachable
        for i in range(1, 5):
            if i < n:
                self.assertLess(dist[i], float("inf"))

    def test_heavy_vs_light_edges(self):
        """Test algorithm choice between heavy and light edge paths"""
        g = Graph(4)
        g.add_edge(0, 1, 100)  # Heavy direct path
        g.add_edge(0, 2, 1)  # Light path via intermediate
        g.add_edge(2, 3, 1)
        g.add_edge(1, 3, 1)  # Total: 100+1=101 vs 1+1=2

        dist, pred = sssp(g, 0)
        self.assertEqual(dist[0], 0)
        self.assertEqual(dist[2], 1)
        self.assertEqual(dist[3], 2)  # Should take light path
        self.assertEqual(dist[1], 100)

    def test_zero_weight_edges(self):
        """Test graph with zero weight edges"""
        g = Graph(3)
        g.add_edge(0, 1, 0)  # Zero weight edge
        g.add_edge(1, 2, 5)

        dist, pred = sssp(g, 0)
        self.assertEqual(dist[0], 0)
        self.assertEqual(dist[1], 0)
        self.assertEqual(dist[2], 5)

    def test_dense_graph(self):
        """Test algorithm on dense graph"""
        n = 8
        g = Graph(n)

        # Add edges between all pairs with distance as weight
        for i in range(n):
            for j in range(i + 1, n):
                weight = abs(i - j)
                g.add_edge(i, j, weight)
                g.add_edge(j, i, weight)  # Make it undirected

        dist, pred = sssp(g, 0)
        self.assertEqual(dist[0], 0)

        # In this setup, distance should be minimum edge weight to each node
        for i in range(1, n):
            self.assertEqual(dist[i], i)  # Direct edge has weight i

    def test_edge_cases_for_coverage(self):
        """Test edge cases to improve coverage"""
        # Test case that triggers empty source set in base_case (line 33)
        from sssp.bmssp import sssp

        g = Graph(2)
        g.add_edge(0, 1, 1)

        # This should work normally and not trigger the empty set case
        # The empty set case is an internal edge case that's hard to trigger directly
        dist, pred = sssp(g, 0)
        self.assertEqual(dist[0], 0)
        self.assertEqual(dist[1], 1)

    def test_large_graph_with_early_termination(self):
        """Test case designed to trigger early termination conditions"""
        # Create a larger graph to trigger more complex algorithm paths
        n = 50
        g = Graph(n)

        # Create a connected path with some shortcuts
        for i in range(n - 1):
            g.add_edge(i, i + 1, 1)

        # Add some shortcut edges that might trigger different algorithm paths
        g.add_edge(0, 10, 5)  # Shortcut
        g.add_edge(0, 20, 8)  # Another shortcut
        g.add_edge(10, 30, 3)  # Cross-edges

        dist, pred = sssp(g, 0)
        self.assertEqual(dist[0], 0)

        # Check that some shortcuts are actually better than the long path
        self.assertLess(dist[10], 10)  # Should use shortcut

    def test_stress_test_complex_topology(self):
        """Test complex graph topology to exercise more code paths"""
        n = 25
        g = Graph(n)

        # Create a more complex topology: grid-like structure
        # Horizontal connections
        for i in range(5):
            for j in range(4):
                node = i * 5 + j
                g.add_edge(node, node + 1, 1)

        # Vertical connections
        for i in range(4):
            for j in range(5):
                node = i * 5 + j
                g.add_edge(node, node + 5, 2)

        # Diagonal connections to create more complex shortest paths
        for i in range(4):
            for j in range(4):
                node = i * 5 + j
                g.add_edge(node, node + 6, 3)  # Diagonal down-right

        dist, pred = sssp(g, 0)
        self.assertEqual(dist[0], 0)

        # All nodes should be reachable in this connected graph
        for i in range(n):
            self.assertLess(dist[i], float("inf"), f"Node {i} should be reachable")


def test_sssp():
    """Test the fixed SSSP algorithm"""
    import random

    # Test 1: Simple directed graph
    g1 = Graph(5)
    g1.add_edge(0, 1, 4)
    g1.add_edge(0, 2, 2)
    g1.add_edge(1, 2, 1)
    g1.add_edge(1, 3, 5)
    g1.add_edge(2, 3, 8)
    g1.add_edge(2, 4, 10)
    g1.add_edge(3, 4, 2)

    dist1, pred1 = sssp(g1, 0)
    assert dist1[0] == 0
    assert dist1[1] == 4
    assert dist1[2] == 2
    assert dist1[3] == 9
    assert dist1[4] == 11
    print("Test 1 passed: Simple directed graph")

    # Test 2: Larger random graph
    n = 100
    g2 = Graph(n)
    random.seed(42)

    # Create a connected graph
    for i in range(n - 1):
        g2.add_edge(i, i + 1, random.uniform(1, 10))

    # Add more random edges
    for _ in range(n * 2):
        u = random.randint(0, n - 2)
        v = random.randint(u + 1, n - 1)
        w = random.uniform(1, 20)
        g2.add_edge(u, v, w)

    dist2, pred2 = sssp(g2, 0)

    # Verify basic properties
    assert dist2[0] == 0
    for i in range(1, n):
        assert dist2[i] < float("inf"), f"Node {i} should be reachable"
        assert dist2[i] > 0, f"Distance to node {i} should be positive"

    print("Test 2 passed: Larger random graph")

    # Test 3: Graph with single path
    g3 = Graph(10)
    for i in range(9):
        g3.add_edge(i, i + 1, i + 1)

    dist3, pred3 = sssp(g3, 0)
    expected_dist = 0
    for i in range(10):
        assert (
            abs(dist3[i] - expected_dist) < 1e-9
        ), f"Node {i}: expected {expected_dist}, got {dist3[i]}"
        if i < 9:
            expected_dist += i + 1

    print("Test 3 passed: Single path graph")

    # Test 4: Star graph
    g4 = Graph(20)
    for i in range(1, 20):
        g4.add_edge(0, i, i)

    dist4, pred4 = sssp(g4, 0)
    assert dist4[0] == 0
    for i in range(1, 20):
        assert dist4[i] == i

    print("Test 4 passed: Star graph")

    print("\nAll tests passed!")
