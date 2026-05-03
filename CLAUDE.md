# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository is a Python *reference / prototype* of the recursive partitioning structure in the deterministic O(m log^(2/3) n) algorithm for Single Source Shortest Paths (SSSP) in directed graphs with non-negative real weights, from the 2025 paper "Breaking the Sorting Barrier for Directed Single-Source Shortest Paths" by Duan, Mao, Mao, Shu, and Yin. It does not match the paper's asymptotic bound — see `README.md` for the practical/theoretical gap.

## Commands

### Running Tests
```bash
uv run pytest tests/
# or for a specific test
uv run pytest tests/test_bmssp.py
```

### Running the Algorithm
The main algorithm is re-exported from the package root:
```python
from sssp import Graph, sssp
```

## Architecture

### Core Components

- **`src/sssp/__init__.py`**: Public API surface. Re-exports `Graph` and `sssp`.
- **`src/sssp/bmssp.py`**: Main algorithm implementation
  - `Graph` class: Simple adjacency list representation; validates inputs (non-negative finite weights, in-range vertices).
  - `sssp(graph, source)`: Main SSSP function implementing the recursive partitioning algorithm.
  - `_bmssp()`: Core recursive function that partitions work and manages frontiers (private).
  - `_find_pivots()`: Identifies pivot vertices for recursive decomposition (private).
  - `_base_case()`: Handles small subproblems with Dijkstra-like approach (private).
  - `_BMSSPState`: Mutable state shared across recursive calls (db, pred, pred_weight, k, t).
  - `_LazyHeapFrontier`: Heap with lazy deletion replacing the previous full-sort frontier.
- **`src/sssp/main.py`**: CLI entry point (`sssp = "sssp.main:main"`).
- **`tests/test_bmssp.py`**: Unit tests with Dijkstra comparison and predecessor-tree invariants.
- **`tests/test_main.py`**: CLI behavior tests.
- **`tests/_dijkstra.py`**: Shared reference Dijkstra and path-reconstruction helpers.
- **`benchmarks/run_benchmarks.py`**: Reproducible wall-clock comparison against heapq Dijkstra.

### Algorithm Structure

The implementation uses recursive partitioning with three key phases:
1. **Pivot Finding**: Identifies vertices whose subtrees are large enough for recursive decomposition
2. **Recursive Decomposition**: Solves smaller bounded multi-source SSSP problems from pivots
3. **Batch Processing**: Groups vertices with similar distance estimates to amortize sorting costs

Key parameters:
- `k = log(n)^(1/3)`: Controls frontier compression
- `t = log(n)^(2/3)`: Controls batch sizes
- `l_max`: Maximum recursion depth

### Important Notes

- Vertices must be labeled 0..n-1
- All edge weights must be non-negative
- Returns `(distances, predecessors)` where distances[i] is shortest distance to vertex i
- Unreachable vertices have distance `float('inf')`
- The algorithm is primarily of theoretical interest; for practical graphs Dijkstra may be faster in Python