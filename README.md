[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

# single-source-shortest-path

This repository is a Python implementation of the deterministic O(m log^(2/3) n) algorithm for Single Source Shortest Paths (SSSP) in directed graphs with non-negative real weights, as described in the paper:

>[!Note] "Breaking the Sorting Barrier for Directed Single-Source Shortest Paths" Ran Duan, Jiayi Mao, Xiao Mao, Xinkai Shu, Longhui Yin (2025)

This approach is the first deterministic SSSP algorithm for directed real-weighted graphs to break the famous O(m + n log n) time bound of Dijkstra's algorithm, using recursive partitioning and partial Bellman-Ford expansions to reduce the "frontier" size at each step.

## Algorithm Overview
Dijkstra's Limitation: Dijkstra's algorithm repeatedly selects the closest incomplete vertex, requiring sorting via heap/priority queue that leads to the O(n log n) factor.

>[!Important] Key Insight: It's possible to avoid sorting all vertices by partitioning the graph recursively and compressing the "frontier" to a much smaller set (size reduced by a log-factor) at each step using a hybrid of Bellman-Ford and Dijkstra.


Recursive Decomposition: At each recursion level, the algorithm:
- Finds Pivots: Via a limited number of relaxation steps, finds pivot vertices whose "subtree" is large.
- Partitions Work: Recursively solves smaller bounded multi-source SSSP from pivots.
- Batch Relaxation: Aggressively batch processes vertices with similar distance estimates to amortize sorting cost.
- Overall: The algorithm uses advanced partitioning and frontier-management to ensure that the total time spent per vertex is much less than log(n), achieving the improved bound.


## Requirements

- **Python**: 3.13.4+
- **Build Tool**: [uv](https://docs.astral.sh/uv/) - A fast Python package installer and resolver
- **Dependencies**: pytest, coverage (automatically managed by uv)

## Installation

This project uses [uv](https://docs.astral.sh/uv/) for dependency management. First, install uv:

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then install the project dependencies:

```bash
uv sync
```

## Project Structure

```
src/
├── sssp/
│   ├── __init__.py
│   ├── bmssp.py          # Main SSSP algorithm implementation
│   └── main.py           # Entry point module
tests/
├── __init__.py
├── test_bmssp.py         # Comprehensive unit tests
└── test_main.py          # Main module tests
```

## Usage

### Basic Example

```python
from sssp.bmssp import Graph, sssp

# Create a simple line graph: 0->1->2->3->4, all edge weights 1
g = Graph(5)
for i in range(4):
    g.add_edge(i, i+1, 1)  # Edge from i to i+1 with weight 1

# Run SSSP from node 0
distances, predecessors = sssp(g, 0)
print(distances)        # Output: [0, 1, 2, 3, 4]
print(predecessors)     # Output: [None, 0, 1, 2, 3]
```
### Advanced Example

```python
from sssp.bmssp import Graph, sssp

# Create a more complex directed weighted graph
g = Graph(4)
g.add_edge(0, 1, 2)
g.add_edge(0, 2, 5)
g.add_edge(1, 2, 1)  # Shorter path to node 2
g.add_edge(2, 3, 3)

distances, predecessors = sssp(g, 0)
print(distances)      # Output: [0, 2, 3, 6]
print(predecessors)   # Output: [None, 0, 1, 2]
```

## Development

### Running Tests

Run all tests:
```bash
uv run pytest tests/
```

Run tests with verbose output:
```bash
uv run pytest tests/ -v
```

Run a specific test file:
```bash
uv run pytest tests/test_bmssp.py -v
```

### Test Coverage

Generate and view test coverage report:
```bash
# Run tests with coverage
uv run coverage run --source=src -m pytest tests/

# Generate coverage report
uv run coverage report

# Generate HTML coverage report
uv run coverage html
# Open htmlcov/index.html in your browser
```

Current test coverage: **94%**

### Building

Build the package:
```bash
uv build
```

### Running the Package

Run the main module:
```bash
uv run python -m sssp.main
```

## Limitations and Notes
Input Graphs: Assumes vertices are labeled 0..n-1.
Non-negative weights: The implementation (like the original paper) assumes all edge weights are non-negative.
Edge Cases: Handles disconnected graphs by returning float('inf') for unreachable nodes.
Performance: The algorithm is meant to be of theoretical interest; for practical graphs, Dijkstra's may be faster in Python due to simpler structure, but this code demonstrates the core techniques from the 2025 paper.
## References

- **Breaking the Sorting Barrier for Directed Single-Source Shortest Paths** - Ran Duan, Jiayi Mao, Xiao Mao, Xinkai Shu, Longhui Yin (2025)
- Classical references as cited in the original paper: Dijkstra (1959), Bellman-Ford, and others.

## Contributing

This implementation includes comprehensive unit tests covering edge cases, disconnected graphs, complex topologies, and performance scenarios. When contributing:

1. Ensure all tests pass: `uv run pytest tests/`
2. Maintain test coverage above 90%: `uv run coverage run --source=src -m pytest tests/`
3. Follow the existing code style and documentation patterns

## License

This project is provided for educational and research purposes, implementing the theoretical algorithm described in the 2025 paper by Duan et al.

