# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository implements the deterministic O(m log^(2/3) n) algorithm for Single Source Shortest Paths (SSSP) in directed graphs with non-negative real weights from the 2025 paper "Breaking the Sorting Barrier for Directed Single-Source Shortest Paths" by Duan, Mao, Shu, and Yin.

## Commands

### Running Tests
```bash
python -m pytest tests/
# or for specific test
python -m pytest tests/test_bmssp.py
```

### Running the Algorithm
The main algorithm can be imported and used:
```python
from src.sssp.bmssp import Graph, sssp
```

## Architecture

### Core Components

- **`src/sssp/bmssp.py`**: Main algorithm implementation
  - `Graph` class: Simple adjacency list representation
  - `sssp(graph, source)`: Main SSSP function implementing the recursive partitioning algorithm
  - `bmssp()`: Core recursive function that partitions work and manages frontiers
  - `find_pivots()`: Identifies pivot vertices for recursive decomposition
  - `base_case()`: Handles small subproblems with Dijkstra-like approach

- **`tests/test_bmssp.py`**: Unit tests with Dijkstra comparison for correctness verification

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