[![Python 3.13.4+](https://img.shields.io/badge/python-3.13.4%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# Single-Source Shortest Path — Reference Implementation of the BMSSP Algorithm

A Python *reference / prototype* implementation of the recursive partitioning structure introduced in the deterministic O(m log^(2/3) n) algorithm for Single-Source Shortest Paths (SSSP) in directed graphs with non-negative real weights:

> "Breaking the Sorting Barrier for Directed Single-Source Shortest Paths"
> Ran Duan, Jiayi Mao, Xiao Mao, Xinkai Shu, Longhui Yin (2025)

This repository implements the algorithmic *structure* — recursive partitioning, pivot finding, and bounded multi-source SSSP — with simpler Python substitutes for the paper's specialized data structures. It is suitable for understanding, teaching, and experimenting with the algorithm. It does **not** reproduce the paper's asymptotic O(m log^(2/3) n) bound, because:

- The frontier `D` is implemented as a heap with lazy deletion rather than the paper's batched data structure, and does not match the amortized-pull cost.
- The pivot-forest is built and traversed with simple dict/DFS bookkeeping rather than the paper's specialized structure.
- Python overhead dominates for any practical input size.

For asymptotic-fidelity work, treat this as a starting point and a correctness oracle, not as a benchmark of the paper's bound.

## Motivation

For decades, Dijkstra's algorithm with a Fibonacci heap has been the best known deterministic algorithm for SSSP in directed graphs with real non-negative weights, running in O(m + n log n) time. The O(n log n) term arises from sorting vertices by distance — processing each vertex requires extracting the minimum from a priority structure, which requires comparison-based sorting.

This 2025 paper by Duan et al. is the first deterministic algorithm to break this sorting barrier for directed real-weighted graphs, achieving O(m log^(2/3) n). The improvement is asymptotically significant: for large graphs, log^(2/3) n grows substantially slower than log n. As a concrete example, for n = 10^6, log n ≈ 20 while log^(2/3) n ≈ 7.4.

Prior improvements (including Fibonacci heaps) reduced constant factors but could not eliminate the log n term from the n log n component. This algorithm is the first deterministic result to do so, making it a landmark theoretical breakthrough in the study of shortest path algorithms.

This repository provides a Python reference implementation demonstrating the algorithm's structure and correctness. It is intended for educational and research purposes — for practical graphs, Dijkstra's algorithm will be faster due to simpler structure and lower constant factors.

## Algorithm Overview

### The Core Idea

Dijkstra's algorithm processes vertices one at a time in order of increasing distance, requiring a global sort of all n vertices. The key insight of this algorithm is that full global sorting is unnecessary: by recursively partitioning the graph and compressing the active frontier to a smaller representative set, the total sorting work is reduced from O(n log n) to O(m log^(2/3) n).

The algorithm achieves this through three coordinated phases at each level of a shallow recursion tree.

### Key Parameters

All parameters are derived from n (the number of vertices):

| Parameter | Formula | Role |
|-----------|---------|------|
| `k` | `max(3, floor(log2(n)^(1/3)))` | Controls frontier compression; sets the pivot tree size threshold and number of relaxation steps |
| `t` | `max(3, floor(log2(n)^(2/3)))` | Controls batch sizes at each recursion level; the 2/3 exponent is central to the complexity result |
| `l_max` | `ceil(log2(n) / t)` | Maximum recursion depth; equals O(log^(1/3) n), so the recursion is shallow |

### Phase 1 — Pivot Finding

Given a frontier S (a set of source vertices) and a distance bound B, the algorithm runs k relaxation steps outward from each vertex in S. Vertices whose shortest-path subtree (within k steps) has size at least k are designated as **pivots**.

Pivots represent vertices that will generate substantial downstream work. Identifying them allows the algorithm to assign large subproblems to recursive calls rather than processing everything at once. If the frontier grows beyond k * |S| vertices during relaxation, the algorithm returns early — the frontier is already large enough that pivot selection is unnecessary.

### Phase 2 — Recursive Decomposition (bmssp)

The core recursive function `bmssp(l, B, S)` processes sources S within distance bound B at recursion level l:

1. Find pivots P in S using Phase 1.
2. Initialize a priority set D from the pivots.
3. Repeatedly pull batches of at most `2^((l-1)*t)` vertices from D (those with the smallest current distance bounds).
4. Recursively solve SSSP for each pulled batch at level l-1.
5. After each recursive call, relax edges from the discovered vertices, routing newly reached vertices back into D or the next batch.
6. Terminate when enough vertices are processed (`k * 2^(l*t)`) or D is empty.

Batch sizes grow geometrically with recursion level: at level l, batches have size `2^((l-1)*t)`. This geometric growth amortizes sorting cost — instead of sorting all n vertices once, the algorithm sorts geometrically smaller sub-batches at each level.

### Phase 3 — Base Case

When `l == 0`, the algorithm falls back to a standard Dijkstra-style heap relaxation from a single source vertex x, respecting the distance bound B. This is the leaf of the recursion tree.

### State Management

Two arrays are shared across all recursive calls:
- `db[v]`: Current best distance bound for vertex v (upper bound on true shortest distance).
- `pred[v]`: Predecessor vertex on the shortest path to v.

Both arrays are mutated in-place. The invariant that `db[v]` is always an upper bound on the true shortest distance is maintained throughout, and relaxations only decrease it.

## Requirements

- **Python**: 3.13.4+
- **Build Tool**: [uv](https://docs.astral.sh/uv/) — a fast Python package installer and resolver
- **Dependencies**: pytest, coverage, black (automatically managed by uv)

## Installation

This project uses [uv](https://docs.astral.sh/uv/) for dependency management. First, install uv if you have not already:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then install the project dependencies:

```bash
uv sync
```

## Usage

### Basic Example

```python
from sssp import Graph, sssp

# Create a simple line graph: 0->1->2->3->4, all edge weights 1
g = Graph(5)
for i in range(4):
    g.add_edge(i, i+1, 1)

# Run SSSP from node 0
distances, predecessors = sssp(g, 0)
print(distances)     # Output: [0, 1, 2, 3, 4]
print(predecessors)  # Output: [None, 0, 1, 2, 3]
```

### Advanced Example

```python
from sssp import Graph, sssp

# Create a directed weighted graph with a non-obvious shortest path
g = Graph(4)
g.add_edge(0, 1, 2)
g.add_edge(0, 2, 5)
g.add_edge(1, 2, 1)  # Path 0->1->2 has total weight 3, shorter than direct 0->2 (weight 5)
g.add_edge(2, 3, 3)

distances, predecessors = sssp(g, 0)
print(distances)     # Output: [0, 2, 3, 6]
print(predecessors)  # Output: [None, 0, 1, 2]
```

### Command-Line Interface

```bash
echo "3 0
0 1 2.0
1 2 3.0" | uv run sssp -

# Output (vertex<TAB>distance<TAB>predecessor):
# 0    0    -
# 1    2    0
# 2    5    1
```

Use `--format json` to emit machine-readable output:

```bash
echo "3 0
0 1 1.5" | uv run sssp - --format json
```

### API Reference

```python
g = Graph(n)                # Create a graph with n vertices labeled 0..n-1
g.add_edge(u, v, weight)    # Add a directed edge from u to v with the given non-negative weight
distances, predecessors = sssp(g, source)
```

- `distances[i]`: Shortest distance from `source` to vertex `i`. Returns `float('inf')` if vertex `i` is unreachable.
- `predecessors[i]`: Predecessor of vertex `i` on the shortest path. Returns `None` if `i` is the source or unreachable.

**Constraints:**
- Vertices must be labeled 0..n-1 (contiguous integers starting from 0).
- All edge weights must be non-negative real numbers.
- The graph is directed. For undirected graphs, add edges in both directions.

## Project Structure

```
src/
  sssp/
    __init__.py
    bmssp.py       # Main algorithm implementation (Graph, sssp, bmssp, find_pivots, base_case)
    main.py        # Entry point module
tests/
  __init__.py
  test_bmssp.py   # Comprehensive unit tests with Dijkstra comparison
  test_main.py    # Main module tests
```

## Development

### Running Tests

```bash
# Run all tests
uv run pytest tests/

# Run with verbose output
uv run pytest tests/ -v

# Run a specific test file
uv run pytest tests/test_bmssp.py -v
```

### Test Coverage

The test suite uses several verification strategies:
- **Contract tests**: Verify that invalid inputs (negative weights, out-of-range vertices, non-finite weights) are rejected with clear errors.
- **Known-value tests**: Hand-crafted graphs with pre-computed expected distances.
- **Dijkstra comparison tests**: Random sparse and dense graphs where `sssp()` output is compared against a reference Dijkstra implementation.
- **Predecessor-tree invariants**: Walk the `predecessors` chain back to the source and verify the summed edge weights equal the reported distance.
- **Numeric scale tests**: Verify correctness across very small (`1e-15`) and very large (`1e15`) weight magnitudes.

```bash
# Run tests with coverage measurement
uv run coverage run --source=src -m pytest tests/

# Print coverage report
uv run coverage report

# Generate HTML coverage report (open htmlcov/index.html)
uv run coverage html
```

### Building

```bash
uv build
```

### Running the Package

```bash
# As an installed console script (preferred):
uv run sssp path/to/graph.txt

# Or as a module:
uv run python -m sssp.main path/to/graph.txt
```

### Benchmarks

Compare this implementation against a reference `heapq` Dijkstra on fixed-seed
synthetic workloads:

```bash
uv run python benchmarks/run_benchmarks.py
```

## Limitations and Notes

- **Input vertices**: Vertices must be labeled 0..n-1 as contiguous integers.
- **Non-negative weights**: Both this implementation and the original paper require all edge weights to be non-negative.
- **Disconnected graphs**: Unreachable vertices return `float('inf')` for distance and `None` for predecessor.
- **Practical performance**: This algorithm is primarily of theoretical interest. For practical graphs, Dijkstra's algorithm will be faster in Python due to its simpler structure and much lower constant factors. The O(m log^(2/3) n) bound is asymptotic; hidden constants and Python overhead make this implementation slower than a well-tuned Dijkstra for any realistic graph size.
- **Directed graphs only**: The algorithm is designed for directed graphs. Undirected graphs can be represented by adding an edge in each direction.
- **Small graphs**: For small n, `k` and `t` are floored to 3, so the algorithm's behavior on small inputs differs from the theoretical model.

## References

- Duan, R., Mao, J., Mao, X., Shu, X., and Yin, L. (2025). **Breaking the Sorting Barrier for Directed Single-Source Shortest Paths**.
- Dijkstra, E. W. (1959). A note on two problems in connexion with graphs. *Numerische Mathematik*, 1(1), 269-271.
- Fredman, M. L., and Tarjan, R. E. (1987). Fibonacci heaps and their uses in improved network optimization algorithms. *Journal of the ACM*, 34(3), 596-615.

## Contributing

When contributing to this repository:

1. Ensure all tests pass: `uv run pytest tests/`
2. Maintain test coverage above 90%: `uv run coverage run --source=src -m pytest tests/`
3. Follow the existing code style (formatted with [Black](https://github.com/psf/black)): `uv run black src/ tests/`

## License

This project is licensed under the [Apache License 2.0](LICENSE).

This implementation is provided for educational and research purposes, demonstrating the algorithm from Duan et al. (2025).
