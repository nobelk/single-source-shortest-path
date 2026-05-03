"""Correctness tests for the BMSSP reference implementation."""

from __future__ import annotations

import math
import random

import pytest

from sssp import Graph, sssp

from tests._dijkstra import dijkstra, path_weight, reconstruct_path


# ---------------------------------------------------------------------------
# Graph and sssp contract enforcement
# ---------------------------------------------------------------------------


class TestContract:
    def test_graph_zero_size_rejected(self):
        with pytest.raises(ValueError):
            Graph(0)

    def test_graph_negative_size_rejected(self):
        with pytest.raises(ValueError):
            Graph(-1)

    def test_graph_non_int_size_rejected(self):
        with pytest.raises(TypeError):
            Graph(3.5)  # type: ignore[arg-type]

    def test_add_edge_negative_weight_rejected(self):
        g = Graph(2)
        with pytest.raises(ValueError, match="non-negative"):
            g.add_edge(0, 1, -0.0001)

    def test_add_edge_nan_weight_rejected(self):
        g = Graph(2)
        with pytest.raises(ValueError, match="finite"):
            g.add_edge(0, 1, float("nan"))

    def test_add_edge_inf_weight_rejected(self):
        g = Graph(2)
        with pytest.raises(ValueError, match="finite"):
            g.add_edge(0, 1, float("inf"))

    def test_add_edge_invalid_source_rejected(self):
        g = Graph(2)
        with pytest.raises(ValueError, match="source vertex"):
            g.add_edge(2, 0, 1.0)

    def test_add_edge_invalid_target_rejected(self):
        g = Graph(2)
        with pytest.raises(ValueError, match="target vertex"):
            g.add_edge(0, 2, 1.0)

    def test_sssp_invalid_source_rejected(self):
        g = Graph(3)
        g.add_edge(0, 1, 1.0)
        with pytest.raises(ValueError, match="source out of range"):
            sssp(g, 5)

    def test_sssp_negative_source_rejected(self):
        g = Graph(3)
        with pytest.raises(ValueError):
            sssp(g, -1)

    def test_sssp_non_graph_rejected(self):
        with pytest.raises(TypeError):
            sssp("not a graph", 0)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Hand-crafted topologies
# ---------------------------------------------------------------------------


class TestSmallGraphs:
    def test_single_vertex(self):
        g = Graph(1)
        dist, pred = sssp(g, 0)
        assert dist[0] == 0
        assert pred[0] is None

    def test_disconnected_graph(self):
        g = Graph(4)
        g.add_edge(0, 1, 1)
        dist, _ = sssp(g, 0)
        assert dist == [0, 1, math.inf, math.inf]

    def test_self_loop_is_ignored(self):
        g = Graph(3)
        g.add_edge(0, 0, 5)
        g.add_edge(0, 1, 2)
        g.add_edge(1, 2, 3)
        dist, _ = sssp(g, 0)
        assert dist == [0, 2, 5]

    def test_multiple_paths_same_total(self):
        g = Graph(4)
        g.add_edge(0, 1, 5)
        g.add_edge(0, 2, 5)
        g.add_edge(1, 3, 1)
        g.add_edge(2, 3, 1)
        dist, _ = sssp(g, 0)
        assert dist == [0, 5, 5, 6]

    def test_zero_weight_edges(self):
        g = Graph(3)
        g.add_edge(0, 1, 0)
        g.add_edge(1, 2, 5)
        dist, _ = sssp(g, 0)
        assert dist == [0, 0, 5]

    def test_heavy_vs_light_path(self):
        g = Graph(4)
        g.add_edge(0, 1, 100)
        g.add_edge(0, 2, 1)
        g.add_edge(2, 3, 1)
        g.add_edge(1, 3, 1)
        dist, _ = sssp(g, 0)
        assert dist == [0, 100, 1, 2]

    def test_known_directed_graph(self):
        g = Graph(5)
        g.add_edge(0, 1, 4)
        g.add_edge(0, 2, 2)
        g.add_edge(1, 2, 1)
        g.add_edge(1, 3, 5)
        g.add_edge(2, 3, 8)
        g.add_edge(2, 4, 10)
        g.add_edge(3, 4, 2)
        dist, _ = sssp(g, 0)
        assert dist == [0, 4, 2, 9, 11]


# ---------------------------------------------------------------------------
# Pivot finding and recursive descent stress
# ---------------------------------------------------------------------------


class TestStressTopologies:
    def test_grid_graph_all_reachable(self):
        n = 25
        g = Graph(n)
        for i in range(5):
            for j in range(4):
                node = i * 5 + j
                g.add_edge(node, node + 1, 1)
        for i in range(4):
            for j in range(5):
                node = i * 5 + j
                g.add_edge(node, node + 5, 2)
        for i in range(4):
            for j in range(4):
                node = i * 5 + j
                g.add_edge(node, node + 6, 3)
        dist, _ = sssp(g, 0)
        for v in range(n):
            assert dist[v] < math.inf, f"vertex {v} should be reachable"

    def test_long_path_with_shortcuts(self):
        """Designed to push the recursive algorithm into deeper levels."""
        n = 50
        g = Graph(n)
        for i in range(n - 1):
            g.add_edge(i, i + 1, 1)
        g.add_edge(0, 10, 5)
        g.add_edge(0, 20, 8)
        g.add_edge(10, 30, 3)
        dist, _ = sssp(g, 0)
        ref, _ = dijkstra(g, 0)
        assert dist == ref


# ---------------------------------------------------------------------------
# Comparison against reference Dijkstra
# ---------------------------------------------------------------------------


class TestDijkstraEquivalence:
    def test_simple(self):
        g = Graph(5)
        g.add_edge(0, 1, 4)
        g.add_edge(0, 2, 2)
        g.add_edge(1, 2, 1)
        g.add_edge(1, 3, 5)
        g.add_edge(2, 3, 8)
        g.add_edge(2, 4, 10)
        g.add_edge(3, 4, 2)
        dist, _ = sssp(g, 0)
        ref, _ = dijkstra(g, 0)
        assert dist == pytest.approx(ref)

    def test_star_graph(self):
        g = Graph(20)
        for i in range(1, 20):
            g.add_edge(0, i, float(i))
        dist, _ = sssp(g, 0)
        ref, _ = dijkstra(g, 0)
        assert dist == pytest.approx(ref)

    def test_path_graph(self):
        g = Graph(10)
        for i in range(9):
            g.add_edge(i, i + 1, float(i + 1))
        dist, _ = sssp(g, 0)
        ref, _ = dijkstra(g, 0)
        assert dist == pytest.approx(ref)

    @pytest.mark.parametrize("seed", list(range(10)))
    def test_random_sparse(self, seed):
        rng = random.Random(seed)
        n = rng.randint(5, 30)
        g = Graph(n)
        for i in range(n - 1):
            g.add_edge(i, i + 1, rng.uniform(0.5, 10.0))
        for _ in range(n * 2):
            u, v = rng.randint(0, n - 1), rng.randint(0, n - 1)
            if u != v:
                g.add_edge(u, v, rng.uniform(0.1, 20.0))
        source = rng.randint(0, n - 1)
        dist, _ = sssp(g, source)
        ref, _ = dijkstra(g, source)
        assert dist == pytest.approx(ref)

    @pytest.mark.parametrize("seed", list(range(5)))
    def test_random_dense(self, seed):
        rng = random.Random(42 + seed)
        n = rng.randint(10, 20)
        g = Graph(n)
        for i in range(n):
            for j in range(n):
                if i != j and rng.random() < 0.6:
                    g.add_edge(i, j, rng.uniform(0.1, 15.0))
        dist, _ = sssp(g, 0)
        ref, _ = dijkstra(g, 0)
        assert dist == pytest.approx(ref)

    def test_large_random_graph_triggers_deep_recursion(self):
        """A larger graph forces the recursive bmssp into multiple levels and
        exercises both the K reinsertion path (B'_i <= new_dist < B_i) and the
        direct frontier insertion path (B_i <= new_dist < B)."""
        rng = random.Random(2025)
        n = 200
        g = Graph(n)
        for i in range(n - 1):
            g.add_edge(i, i + 1, rng.uniform(0.5, 5.0))
        for _ in range(n * 4):
            u, v = rng.randint(0, n - 1), rng.randint(0, n - 1)
            if u != v:
                g.add_edge(u, v, rng.uniform(0.1, 30.0))
        dist, _ = sssp(g, 0)
        ref, _ = dijkstra(g, 0)
        assert dist == pytest.approx(ref)


# ---------------------------------------------------------------------------
# Predecessor-tree invariants
# ---------------------------------------------------------------------------


class TestPredecessorInvariants:
    """Verifies the predecessor array reconstructs a valid shortest-path tree."""

    @staticmethod
    def _check_pred_tree(g: Graph, source: int):
        dist, pred = sssp(g, source)
        ref_dist, _ = dijkstra(g, source)
        for v in range(g.n):
            if math.isinf(dist[v]):
                assert math.isinf(ref_dist[v])
                assert pred[v] is None
                continue
            # Walking pred from v should reach the source through real edges
            # whose total weight equals dist[v].
            path = reconstruct_path(pred, v)
            assert path[0] == source, f"pred chain for {v} did not reach source"
            assert path[-1] == v
            assert path_weight(g, path) == pytest.approx(dist[v])
            assert dist[v] == pytest.approx(ref_dist[v])

    def test_pred_tree_simple_directed(self):
        g = Graph(5)
        g.add_edge(0, 1, 4)
        g.add_edge(0, 2, 2)
        g.add_edge(1, 2, 1)
        g.add_edge(1, 3, 5)
        g.add_edge(2, 3, 8)
        g.add_edge(2, 4, 10)
        g.add_edge(3, 4, 2)
        self._check_pred_tree(g, 0)

    def test_pred_tree_disconnected(self):
        g = Graph(4)
        g.add_edge(0, 1, 1)
        self._check_pred_tree(g, 0)

    @pytest.mark.parametrize("seed", list(range(5)))
    def test_pred_tree_random(self, seed):
        rng = random.Random(seed * 17 + 1)
        n = rng.randint(8, 25)
        g = Graph(n)
        for i in range(n - 1):
            g.add_edge(i, i + 1, rng.uniform(0.5, 5.0))
        for _ in range(n * 3):
            u, v = rng.randint(0, n - 1), rng.randint(0, n - 1)
            if u != v:
                g.add_edge(u, v, rng.uniform(0.1, 10.0))
        self._check_pred_tree(g, 0)


# ---------------------------------------------------------------------------
# Numeric robustness
# ---------------------------------------------------------------------------


class TestNumericScales:
    """Verifies the algorithm copes with weight scales that would have broken
    the previous fixed 1e-9 absolute-tolerance forest test."""

    def test_very_small_weights(self):
        g = Graph(4)
        g.add_edge(0, 1, 1e-15)
        g.add_edge(1, 2, 2e-15)
        g.add_edge(2, 3, 3e-15)
        dist, _ = sssp(g, 0)
        ref, _ = dijkstra(g, 0)
        assert dist == pytest.approx(ref, rel=1e-9, abs=1e-30)

    def test_very_large_weights(self):
        g = Graph(4)
        g.add_edge(0, 1, 1e15)
        g.add_edge(1, 2, 2e15)
        g.add_edge(2, 3, 3e15)
        dist, _ = sssp(g, 0)
        ref, _ = dijkstra(g, 0)
        assert dist == pytest.approx(ref)

    def test_mixed_weight_scales(self):
        g = Graph(5)
        g.add_edge(0, 1, 1e-12)
        g.add_edge(1, 2, 1e12)
        g.add_edge(0, 3, 1.0)
        g.add_edge(3, 4, 1.0)
        g.add_edge(2, 4, 1e-12)
        dist, _ = sssp(g, 0)
        ref, _ = dijkstra(g, 0)
        for v in range(g.n):
            assert dist[v] == pytest.approx(ref[v], rel=1e-9)
