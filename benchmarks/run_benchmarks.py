"""Reproducible benchmark suite for the SSSP reference implementation.

Compares ``sssp.sssp`` against a reference ``heapq``-based Dijkstra across four
fixed-seed graph workloads (sparse random, dense random, path, star). Prints
n, m, both wall-clock times, and the slowdown ratio.

Run with::

    uv run python benchmarks/run_benchmarks.py
    uv run python benchmarks/run_benchmarks.py --sizes 100 500 1000

The README warns that Dijkstra will usually win in Python; the point of these
numbers is to make that quantitative and comparable across changes.
"""

from __future__ import annotations

import argparse
import heapq
import random
import time
from collections.abc import Callable

from sssp import Graph, sssp


def reference_dijkstra(graph: Graph, source: int) -> list[float]:
    n = graph.n
    dist = [float("inf")] * n
    dist[source] = 0.0
    heap: list[tuple[float, int]] = [(0.0, source)]
    visited = [False] * n
    while heap:
        d, u = heapq.heappop(heap)
        if visited[u]:
            continue
        visited[u] = True
        for v, w in graph.adj[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return dist


def make_sparse(n: int, seed: int) -> Graph:
    rng = random.Random(seed)
    g = Graph(n)
    for i in range(n - 1):
        g.add_edge(i, i + 1, rng.uniform(0.5, 5.0))
    for _ in range(n * 3):
        u, v = rng.randint(0, n - 1), rng.randint(0, n - 1)
        if u != v:
            g.add_edge(u, v, rng.uniform(0.1, 10.0))
    return g


def make_dense(n: int, seed: int) -> Graph:
    rng = random.Random(seed)
    g = Graph(n)
    for u in range(n):
        for v in range(n):
            if u != v and rng.random() < 0.5:
                g.add_edge(u, v, rng.uniform(0.1, 10.0))
    return g


def make_path(n: int, seed: int) -> Graph:
    rng = random.Random(seed)
    g = Graph(n)
    for i in range(n - 1):
        g.add_edge(i, i + 1, rng.uniform(0.5, 5.0))
    return g


def make_star(n: int, seed: int) -> Graph:
    rng = random.Random(seed)
    g = Graph(n)
    for v in range(1, n):
        g.add_edge(0, v, rng.uniform(0.5, 10.0))
    return g


WORKLOADS: dict[str, Callable[[int, int], Graph]] = {
    "sparse": make_sparse,
    "dense": make_dense,
    "path": make_path,
    "star": make_star,
}


def edge_count(g: Graph) -> int:
    return sum(len(adj) for adj in g.adj)


def time_run(fn: Callable[[], object], repeat: int) -> float:
    """Best-of-`repeat` wall-clock seconds, to dampen noise."""
    best = float("inf")
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn()
        elapsed = time.perf_counter() - t0
        if elapsed < best:
            best = elapsed
    return best


def run_one(name: str, n: int, builder: Callable[[int, int], Graph], repeat: int):
    g = builder(n, seed=42)
    m = edge_count(g)
    sssp_time = time_run(lambda: sssp(g, 0), repeat)
    dij_time = time_run(lambda: reference_dijkstra(g, 0), repeat)
    ratio = sssp_time / dij_time if dij_time > 0 else float("inf")
    print(
        f"  {name:<8} n={n:<5d} m={m:<6d}  sssp={sssp_time*1000:7.2f} ms"
        f"  dijkstra={dij_time*1000:7.2f} ms  ratio={ratio:5.2f}x"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark sssp() against heapq Dijkstra on fixed-seed graphs."
    )
    parser.add_argument(
        "--sizes",
        type=int,
        nargs="+",
        default=[100, 300, 800],
        help="Vertex counts to benchmark (default: 100 300 800).",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=3,
        help="Best-of-N timing repetitions (default: 3).",
    )
    parser.add_argument(
        "--workloads",
        nargs="+",
        choices=sorted(WORKLOADS.keys()),
        default=sorted(WORKLOADS.keys()),
        help="Which workloads to run (default: all).",
    )
    args = parser.parse_args()

    print(
        "Benchmark: sssp() vs heapq Dijkstra (best-of-{} timings)".format(args.repeat)
    )
    print(f"{'-' * 78}")
    for name in args.workloads:
        builder = WORKLOADS[name]
        for n in args.sizes:
            run_one(name, n, builder, args.repeat)
    print(f"{'-' * 78}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
