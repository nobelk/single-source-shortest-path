"""Reference implementation of the BMSSP recursive partitioning algorithm.

This module is a Python *reference / prototype* of the algorithmic structure
introduced in:

    Duan, R., Mao, J., Mao, X., Shu, X., and Yin, L. (2025).
    "Breaking the Sorting Barrier for Directed Single-Source Shortest Paths."

The paper proves a deterministic ``O(m log^(2/3) n)`` time bound. Faithfully
matching that bound requires specialized frontier and pivot-forest data
structures. This module instead uses simpler Python substitutes (a heap with
lazy deletion for the frontier, dict-based bookkeeping for the pivot forest)
that preserve correctness but do not reproduce the paper's asymptotic
guarantee. See README for the practical/theoretical gap.
"""

from __future__ import annotations

import heapq
import math
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

Vertex = int
Weight = float
Edge = tuple[Vertex, Weight]


class Graph:
    """Directed graph with non-negative real edge weights."""

    __slots__ = ("n", "adj")

    def __init__(self, n: int) -> None:
        if not isinstance(n, int):
            raise TypeError(f"n must be an int, got {type(n).__name__}")
        if n <= 0:
            raise ValueError(f"n must be positive, got {n}")
        self.n: int = n
        self.adj: list[list[Edge]] = [[] for _ in range(n)]

    def add_edge(self, u: Vertex, v: Vertex, weight: Weight) -> None:
        if not (0 <= u < self.n):
            raise ValueError(f"source vertex out of range: u={u} not in [0, {self.n})")
        if not (0 <= v < self.n):
            raise ValueError(f"target vertex out of range: v={v} not in [0, {self.n})")
        # Reject NaN, +/-inf, and negative weights up front.
        if not isinstance(weight, (int, float)) or isinstance(weight, bool):
            raise TypeError(
                f"weight must be a real number, got {type(weight).__name__}"
            )
        w = float(weight)
        if not math.isfinite(w):
            raise ValueError(f"weight must be finite, got {weight}")
        if w < 0:
            raise ValueError(f"weight must be non-negative, got {weight}")
        self.adj[u].append((v, w))


@dataclass
class _BMSSPState:
    """Mutable state shared across recursive BMSSP calls.

    Decoupling state from the recursive function lets us unit-test individual
    phases and swap frontier or pivot-forest implementations without rewriting
    the whole driver.
    """

    graph: Graph
    db: list[Weight]
    pred: list[Vertex | None]
    # pred_weight[v] is the weight of the edge (pred[v], v) that produced db[v].
    # Recording it at relaxation time avoids re-discovering the relaxed edge with
    # a floating-point equality check later.
    pred_weight: list[Weight | None]
    k: int
    t: int

    @classmethod
    def initial(cls, graph: Graph, source: Vertex) -> "_BMSSPState":
        n = graph.n
        # max(3, ...) guards small n where log^(1/3) n collapses to 0/1 and
        # would make the recursion degenerate.
        log_n = math.log(max(n, 2), 2)
        k = max(3, int(log_n ** (1 / 3)))
        t = max(3, int(log_n ** (2 / 3)))
        db: list[Weight] = [math.inf] * n
        pred: list[Vertex | None] = [None] * n
        pred_weight: list[Weight | None] = [None] * n
        db[source] = 0.0
        return cls(
            graph=graph,
            db=db,
            pred=pred,
            pred_weight=pred_weight,
            k=k,
            t=t,
        )

    def relax(self, u: Vertex, v: Vertex, w: Weight) -> bool:
        """Try to relax edge (u, v, w). Returns True iff db[v] strictly improved."""
        new_dist = self.db[u] + w
        if new_dist < self.db[v]:
            self.db[v] = new_dist
            self.pred[v] = u
            self.pred_weight[v] = w
            return True
        return False


class _LazyHeapFrontier:
    """Heap-with-lazy-deletion frontier for the BMSSP D set.

    Supports add(v) and pull(M) which returns at most M vertices with the
    smallest current ``db[v]`` plus the next boundary value (smallest db
    remaining in the frontier, or +inf if empty).

    The heap stores ``(db_at_push, vertex)``. When popped, an entry is treated
    as stale if either (a) the vertex is no longer in the frontier (already
    pulled or removed) or (b) db[v] has decreased since the entry was pushed.
    """

    __slots__ = ("_db", "_heap", "_in_set")

    def __init__(self, db: list[Weight], initial: Iterable[Vertex] = ()) -> None:
        self._db = db
        self._heap: list[tuple[Weight, Vertex]] = []
        self._in_set: set[Vertex] = set()
        for v in initial:
            self.add(v)

    def __bool__(self) -> bool:
        return self._peek_live() is not None

    def add(self, v: Vertex) -> None:
        # We always push, even if v is already in the set with an older
        # (larger) key; the older entry will be skipped when popped.
        self._in_set.add(v)
        heapq.heappush(self._heap, (self._db[v], v))

    def _peek_live(self) -> tuple[Weight, Vertex] | None:
        while self._heap:
            d, v = self._heap[0]
            if v in self._in_set and d == self._db[v]:
                return d, v
            heapq.heappop(self._heap)
        return None

    def pull(self, m: int) -> tuple[Weight, set[Vertex]]:
        """Pop up to m smallest-db vertices; return (next_boundary, pulled set)."""
        pulled: set[Vertex] = set()
        while len(pulled) < m:
            top = self._peek_live()
            if top is None:
                break
            _, v = top
            heapq.heappop(self._heap)
            self._in_set.discard(v)
            pulled.add(v)
        next_top = self._peek_live()
        next_boundary = next_top[0] if next_top is not None else math.inf
        return next_boundary, pulled


def _base_case(
    state: _BMSSPState, B: Weight, S: set[Vertex]
) -> tuple[Weight, set[Vertex]]:
    """Singleton-source mini-Dijkstra bounded by B. S is non-empty."""
    # S is a non-empty singleton at l == 0, drained from the frontier above.
    x = next(iter(S))
    discovered: set[Vertex] = set()
    heap: list[tuple[Weight, Vertex]] = [(state.db[x], x)]
    visited: set[Vertex] = set()

    while heap:
        _, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)
        discovered.add(u)
        for v, w in state.graph.adj[u]:
            new_dist = state.db[u] + w
            if new_dist <= state.db[v] and new_dist < B:
                state.db[v] = new_dist
                state.pred[v] = u
                state.pred_weight[v] = w
                if v not in visited:
                    heapq.heappush(heap, (state.db[v], v))

    return B, discovered


def _find_pivots(
    state: _BMSSPState, B: Weight, S: set[Vertex]
) -> tuple[set[Vertex], set[Vertex]]:
    """Run k bounded relaxation rounds from S, then identify pivots whose
    relaxed-forest subtrees have size >= k."""
    k = state.k
    db = state.db
    adj = state.graph.adj

    W: set[Vertex] = set(S)
    Wi: set[Vertex] = set(S)
    # Track which vertex's pred was assigned during this find_pivots call so we
    # can build the relaxed forest from authoritative parent pointers without
    # re-scanning adjacency lists later.
    relaxed_parent: dict[Vertex, Vertex] = {}

    for _ in range(k):
        Wi_next: set[Vertex] = set()
        for u in Wi:
            for v, w in adj[u]:
                new_dist = db[u] + w
                if new_dist <= db[v] and new_dist < B:
                    db[v] = new_dist
                    state.pred[v] = u
                    state.pred_weight[v] = w
                    relaxed_parent[v] = u
                    Wi_next.add(v)
        Wi = Wi_next
        W |= Wi
        if len(W) > k * len(S):
            return set(S), W

    # Build the relaxed-forest restricted to W by walking parent pointers we
    # recorded above. This avoids the previous code's "rescan adjacency to
    # match db with float tolerance" pattern.
    forest_children: dict[Vertex, set[Vertex]] = defaultdict(set)
    forest_has_parent: set[Vertex] = set()
    for v, parent in relaxed_parent.items():
        if v in W and parent in W:
            forest_children[parent].add(v)
            forest_has_parent.add(v)

    def subtree_size(root: Vertex) -> int:
        # Iterative DFS over forest_children. Trees are by construction acyclic
        # (relaxation only lowers db, so no cycle in the parent map within W).
        size = 0
        stack = [root]
        while stack:
            u = stack.pop()
            size += 1
            if size >= k:
                # Early exit; we only need to know whether the subtree reaches k.
                return size
            stack.extend(forest_children.get(u, ()))
        return size

    pivots: set[Vertex] = set()
    for s in S:
        if s in forest_has_parent:
            continue
        if subtree_size(s) >= k:
            pivots.add(s)
    return pivots, W


def _bmssp(
    state: _BMSSPState, level: int, B: Weight, S: set[Vertex]
) -> tuple[Weight, set[Vertex]]:
    """Bounded multi-source SSSP: process sources S within bound B at recursion level `level`."""
    if level == 0:
        return _base_case(state, B, S)

    P, W = _find_pivots(state, B, S)
    if not P:
        return B, set()

    frontier = _LazyHeapFrontier(state.db, initial=P)
    U: set[Vertex] = set()

    k, t = state.k, state.t
    termination_bound = k * (2 ** (level * t))
    pull_size = 2 ** ((level - 1) * t)

    B_prime = B
    while len(U) < termination_bound and frontier:
        Bi, Si = frontier.pull(pull_size)
        B_prime_i, Ui = _bmssp(state, level - 1, Bi, Si)
        U |= Ui

        # Relax edges from Ui; route newly relaxed vertices to either the
        # batch-prepend set (K) or back into the frontier depending on which
        # range their new distance falls in.
        K: set[Vertex] = set()
        for u in Ui:
            for v, w in state.graph.adj[u]:
                if state.relax(u, v, w):
                    new_dist = state.db[v]
                    if B_prime_i <= new_dist < Bi:
                        K.add(v)
                    elif Bi <= new_dist < B:
                        frontier.add(v)

        for v in K:
            frontier.add(v)
        for s in Si:
            if B_prime_i <= state.db[s] < Bi:
                frontier.add(s)

        if len(U) >= termination_bound:
            B_prime = B_prime_i
            break
    else:
        B_prime = B

    for w in W:
        if state.db[w] < B_prime:
            U.add(w)

    return B_prime, U


def sssp(graph: Graph, source: Vertex) -> tuple[list[Weight], list[Vertex | None]]:
    """Single-source shortest paths from ``source`` in ``graph``.

    Reference / prototype implementation of the recursive partitioning structure
    from Duan et al. (2025). Returns ``(distances, predecessors)`` where
    ``distances[i]`` is the shortest distance from ``source`` to vertex ``i``
    (``inf`` if unreachable) and ``predecessors[i]`` is the previous vertex on
    that shortest path (``None`` for the source or unreachable vertices).
    """
    if not isinstance(graph, Graph):
        raise TypeError(f"graph must be a Graph, got {type(graph).__name__}")
    if not isinstance(source, int) or isinstance(source, bool):
        raise TypeError(f"source must be an int, got {type(source).__name__}")
    if not (0 <= source < graph.n):
        raise ValueError(f"source out of range: source={source} not in [0, {graph.n})")

    state = _BMSSPState.initial(graph, source)

    # Recursion depth: ceil(log_2(n) / t). max(...) guards small n.
    log_n = math.log(max(graph.n, 2), 2)
    l_max = max(1, math.ceil(log_n / state.t))
    _bmssp(state, l_max, math.inf, {source})
    return state.db, state.pred


if __name__ == "__main__":
    pass
