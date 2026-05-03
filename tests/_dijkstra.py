"""Reference Dijkstra implementation, shared by multiple test modules."""

from __future__ import annotations

import heapq

from sssp import Graph


def dijkstra(graph: Graph, source: int) -> tuple[list[float], list[int | None]]:
    """Reference shortest-path implementation. Returns (distances, predecessors)."""
    n = graph.n
    dist: list[float] = [float("inf")] * n
    pred: list[int | None] = [None] * n
    dist[source] = 0.0
    heap: list[tuple[float, int]] = [(0.0, source)]
    visited: set[int] = set()
    while heap:
        d, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)
        for v, w in graph.adj[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                pred[v] = u
                heapq.heappush(heap, (nd, v))
    return dist, pred


def reconstruct_path(pred: list[int | None], target: int) -> list[int]:
    """Walk the predecessor chain from `target` back to a root, returning [root, ..., target]."""
    path: list[int] = []
    cur: int | None = target
    seen: set[int] = set()
    while cur is not None:
        if cur in seen:
            raise AssertionError(f"cycle in predecessor chain at vertex {cur}")
        seen.add(cur)
        path.append(cur)
        cur = pred[cur]
    path.reverse()
    return path


def path_weight(graph: Graph, path: list[int]) -> float:
    """Sum of the smallest-weight edges along `path`.

    Graphs may contain parallel edges; the relaxed predecessor edge is by
    definition the one with the smallest weight among (u, v) edges, so we
    take the minimum here. Raises if any consecutive pair lacks an edge.
    """
    total = 0.0
    for u, v in zip(path, path[1:]):
        candidates = [w for nbr, w in graph.adj[u] if nbr == v]
        if not candidates:
            raise AssertionError(f"no edge {u}->{v} in graph")
        total += min(candidates)
    return total
