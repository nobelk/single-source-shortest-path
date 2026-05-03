"""Reference implementation of the BMSSP recursive partitioning SSSP algorithm.

Public API:

    >>> from sssp import Graph, sssp
    >>> g = Graph(3)
    >>> g.add_edge(0, 1, 1.0)
    >>> g.add_edge(1, 2, 2.5)
    >>> distances, predecessors = sssp(g, 0)
"""

from sssp.bmssp import Graph, sssp

__all__ = ["Graph", "sssp"]
