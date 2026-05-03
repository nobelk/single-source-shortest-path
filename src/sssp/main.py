"""Command-line interface for the SSSP reference implementation.

Reads a graph in a simple edge-list format and prints shortest-path distances
(or full distances+predecessors as JSON) from a chosen source vertex.

Input format::

    n source
    u1 v1 w1
    u2 v2 w2
    ...

Lines starting with ``#`` and blank lines are ignored. Vertices must be
integers in ``[0, n)``; weights must be non-negative finite reals.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import IO

from sssp import Graph, sssp


def _parse_graph(stream: IO[str]) -> tuple[Graph, int]:
    header: tuple[int, int] | None = None
    edges: list[tuple[int, int, float]] = []
    for raw in stream:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if header is None:
            if len(parts) != 2:
                raise ValueError(f"expected 'n source' header, got: {raw.rstrip()!r}")
            header = (int(parts[0]), int(parts[1]))
            continue
        if len(parts) != 3:
            raise ValueError(f"expected 'u v w' edge line, got: {raw.rstrip()!r}")
        edges.append((int(parts[0]), int(parts[1]), float(parts[2])))

    if header is None:
        raise ValueError("input did not contain an 'n source' header line")

    n, source = header
    g = Graph(n)
    for u, v, w in edges:
        g.add_edge(u, v, w)
    return g, source


def _format_distance(d: float) -> float | str:
    return "inf" if math.isinf(d) else d


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sssp",
        description="Compute single-source shortest paths from an edge-list graph.",
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help="Path to input file, or '-' for stdin (default: '-').",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text).",
    )
    args = parser.parse_args(argv)

    try:
        if args.input == "-":
            graph, source = _parse_graph(sys.stdin)
        else:
            with open(args.input, "r", encoding="utf-8") as fh:
                graph, source = _parse_graph(fh)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        distances, predecessors = sssp(graph, source)
    except (TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        payload = {
            "source": source,
            "distances": [_format_distance(d) for d in distances],
            "predecessors": predecessors,
        }
        json.dump(payload, sys.stdout)
        sys.stdout.write("\n")
    else:
        for v, d in enumerate(distances):
            pred = predecessors[v]
            pred_str = "-" if pred is None else str(pred)
            d_str = "inf" if math.isinf(d) else f"{d:g}"
            print(f"{v}\t{d_str}\t{pred_str}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
