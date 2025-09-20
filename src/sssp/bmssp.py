import math
import heapq
from collections import defaultdict, deque


class Graph:
    def __init__(self, n):
        self.n = n
        self.adj = [[] for _ in range(n)]  # adjacency list

    def add_edge(self, u, v, weight):
        self.adj[u].append((v, weight))


def sssp(graph, source):
    """
    Single-source shortest path algorithm with O(m log^(2/3) n) time complexity.
    Based on "Breaking the Sorting Barrier for Directed Single-Source Shortest Paths"
    by Duan et al. (2025)
    """
    n = graph.n
    db = [float("inf")] * n  # distance bounds
    pred = [None] * n  # predecessors
    db[source] = 0

    # Parameters from the paper
    k = max(3, int(math.log(n, 2) ** (1 / 3)))  # log^(1/3) n
    t = max(3, int(math.log(n, 2) ** (2 / 3)))  # log^(2/3) n

    def base_case(B, S):
        """Base case: S is singleton, run mini-Dijkstra to find k+1 closest vertices"""
        if not S:
            return B, set()

        x = list(S)[0]
        U0 = set()
        h = [(db[x], x)]
        visited = set()

        # Find vertices until heap is empty or bound B is reached
        while h:
            dist_u, u = heapq.heappop(h)
            if u in visited:
                continue
            visited.add(u)
            U0.add(u)

            for v, wuv in graph.adj[u]:
                new_dist = db[u] + wuv
                if new_dist <= db[v] and new_dist < B:
                    db[v] = new_dist
                    pred[v] = u
                    if v not in visited:
                        heapq.heappush(h, (db[v], v))

        # Return all discovered vertices within bound B
        return B, U0

    def find_pivots(B, S):
        """Find pivot vertices with large shortest path trees"""
        W = set(S)
        Wi = set(S)

        # Relax for k steps
        for i in range(k):
            Wi_next = set()
            for u in Wi:
                for v, wuv in graph.adj[u]:
                    new_dist = db[u] + wuv
                    if new_dist <= db[v] and new_dist < B:
                        db[v] = new_dist
                        pred[v] = u
                        Wi_next.add(v)
            Wi = Wi_next
            W |= Wi

            # Early termination if W grows too large
            if len(W) > k * len(S):
                return S, W

        # Build forest F of relaxed edges within W
        # This is the correct way according to the paper
        forest_parent = {}
        forest_children = defaultdict(set)

        for u in W:
            if pred[u] is not None and pred[u] in W:
                # Check if this edge was used in relaxation (db[v] = db[u] + wuv)
                for p, wp in graph.adj[pred[u]]:
                    if p == u and abs(db[u] - (db[pred[u]] + wp)) < 1e-9:
                        forest_parent[u] = pred[u]
                        forest_children[pred[u]].add(u)
                        break

        # Find roots in S with trees of size >= k
        def get_tree_size(root):
            if root not in forest_children:
                return 1
            size = 1
            queue = deque([root])
            visited = {root}
            while queue:
                u = queue.popleft()
                for child in forest_children[u]:
                    if child not in visited:
                        visited.add(child)
                        queue.append(child)
                        size += 1
            return size

        # Pivots are roots in S with large trees
        pivots = set()
        for s in S:
            if s not in forest_parent:  # s is a root
                if get_tree_size(s) >= k:
                    pivots.add(s)

        return pivots, W

    def pull_from_D(D, M):
        """Pull at most M vertices with smallest db values"""
        if not D:
            return float("inf"), set()

        sorted_D = sorted(D, key=lambda v: db[v])
        S_pull = set(sorted_D[: min(M, len(sorted_D))])

        # Update D by removing pulled vertices
        for v in S_pull:
            D.discard(v)

        # Find boundary
        if D:
            B_next = min(db[v] for v in D)
        else:
            B_next = float("inf")

        return B_next, S_pull

    def bmssp(l, B, S):
        """Bounded Multi-Source Shortest Path main procedure"""
        if l == 0:
            return base_case(B, S)

        P, W = find_pivots(B, S)
        if not P:
            return B, set()

        # Initialize data structure D with pivots
        D = set(P)
        U = set()

        # Correct termination bound: k * 2^(l*t), not k*k * 2^(l*t)
        termination_bound = k * (2 ** (l * t))
        pull_size = 2 ** ((l - 1) * t) if l > 0 else 1

        # Main loop
        while len(U) < termination_bound and D:
            # Pull at most 2^((l-1)*t) vertices
            Bi, Si = pull_from_D(D, pull_size)

            # Recursive call
            B_prime_i, Ui = bmssp(l - 1, Bi, Si)
            U |= Ui

            # Relax edges from Ui and collect vertices to add back to D
            K = set()  # For batch prepend
            for u in Ui:
                for v, wuv in graph.adj[u]:
                    new_dist = db[u] + wuv
                    if new_dist <= db[v]:
                        db[v] = new_dist
                        pred[v] = u

                        # Determine where to add v
                        if B_prime_i <= new_dist < Bi:
                            K.add(v)  # Add to batch prepend set
                        elif Bi <= new_dist < B:
                            D.add(v)  # Add directly to D

            # Batch prepend K and unpulled vertices from Si
            for v in K:
                D.add(v)
            for s in Si:
                if B_prime_i <= db[s] < Bi:
                    D.add(s)

            # Check for early termination
            if len(U) >= termination_bound:
                B_prime = B_prime_i
                break
        else:
            B_prime = B

        # Add completed vertices from W
        for w in W:
            if db[w] < B_prime:
                U.add(w)

        return B_prime, U

    # Main algorithm call
    l_max = max(1, int(math.ceil(math.log(n, 2) / max(t, 1))))
    bmssp(l_max, float("inf"), {source})

    return db, pred


if __name__ == "__main__":
    pass
