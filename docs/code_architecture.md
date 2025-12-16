# Code Architecture

This document describes the high-level architecture and design patterns of the Data Lineage Graph Generator.

## Overview

The tool follows a **three-phase pipeline** architecture:

```text
Input Phase → Graph Phase → Export Phase
```

Each phase is cleanly separated with well-defined interfaces using Python dataclasses.

## Three-Phase Pipeline

### 1. Input Phase ([src/lineage/io/](../src/lineage/io/))

**Purpose**: Parse various input sources and normalize them into a common data model.

**Components**:

- **SQL Parser** ([sql_parser.py](../src/lineage/io/sql_parser.py))
  - Uses `sqlglot` library with Redshift dialect
  - Extracts CREATE TABLE/VIEW statements from SQL files
  - Supports glob patterns for file discovery
  - Only processes schema-qualified objects (`schema.table` format)

- **SQL Lineage Extractor** ([sql_lineage_extractor.py](../src/lineage/io/sql_lineage_extractor.py))
  - Extracts SELECT dependencies from CREATE statements
  - Automatically populates `select_from` fields
  - Handles complex queries with multiple FROM clauses

- **YAML/JSON Parser** ([yaml_parser.py](../src/lineage/io/yaml_parser.py))
  - Loads lineage configuration files
  - Supports both JSON and YAML formats
  - Converts inline `select_from` to explicit Connection objects

- **YAML Writer** ([yaml_writer.py](../src/lineage/io/yaml_writer.py))
  - Uses `ruamel.yaml` to preserve comments and formatting
  - Handles node deduplication during writes
  - Supports append mode for incremental builds

**Output**: `list[Node]` and `list[Connection]`

### 2. Graph Phase ([src/lineage/graph/](../src/lineage/graph/))

**Purpose**: Build a graph representation and perform traversal/filtering operations.

**Components**:

- **LineageGraph** ([lineage_graph.py](../src/lineage/graph/lineage_graph.py))
  - Wraps NetworkX DiGraph for graph operations
  - Provides high-level APIs for common operations:
    - `get_upstream_nodes()`: Find all ancestors
    - `get_downstream_nodes()`: Find all descendants
    - `get_subgraph()`: Extract filtered subgraph
    - `find_cycles()`: Detect circular dependencies
    - `get_all_paths()`: Find paths between nodes
  - Supports depth-limited traversal using BFS
  - Efficiently handles large graphs (100s-1000s of nodes)

- **Missing Nodes Detector** ([missing_nodes.py](../src/lineage/graph/missing_nodes.py))
  - Scans `select_from` fields for referenced node IDs
  - Identifies nodes that don't exist in the nodes list
  - Creates placeholder nodes with null `data_level` and `data_type`
  - Uses `ruamel.yaml` to preserve comments during file updates

**Output**: Filtered `list[Node]` and `list[Connection]` based on user criteria

### 3. Export Phase ([src/lineage/export/](../src/lineage/export/))

**Purpose**: Render the graph data into visual diagram formats.

**Components**:

- **MermaidGenerator** ([mermaid.py](../src/lineage/export/mermaid.py))
  - Generates Mermaid diagram syntax from nodes and connections
  - Applies visual styling based on node attributes:
    - `data_type` → Node shape (rectangle, stadium, cylinder, etc.)
    - `data_level` → Node color (source=blue, dimension=green, etc.)
    - `connection_type` → Arrow style (solid, dashed)
  - Sanitizes node IDs for Mermaid compatibility
  - Produces deterministic output (sorted nodes/connections)

- **Legend Generator** ([mermaid.py](../src/lineage/export/mermaid.py))
  - Creates reference diagrams showing all available styles
  - Uses subgraphs to organize by category
  - Automatically includes all defined types and levels

**Output**: Mermaid diagram as string

## Data Model ([src/lineage/models.py](../src/lineage/models.py))

### Node

Represents a data object in the warehouse lineage.

```python
@dataclass
class Node:
    id: str                    # Unique identifier (e.g., "schema.table")
    label: str                 # Display name
    data_type: DataType        # Determines shape
    data_level: DataLevel      # Determines color
    select_from: list[str]     # Upstream node IDs
```

**Key Properties**:
- IDs must be unique across all nodes
- `data_level` can be `None` during extraction
- `select_from` creates connections automatically in YAML format

### Connection

Represents a data flow connection between nodes.

```python
@dataclass
class Connection:
    from_id: str               # Source node identifier
    to_id: str                 # Target node identifier
    connection_type: ConnectionType  # Arrow style
```

**Key Properties**:
- `from_id` and `to_id` must reference existing nodes
- `connection_type` defaults to `"select_from"` (solid arrow)

## Configuration ([src/lineage/config.py](../src/lineage/config.py))

Central configuration for all visual styling.

### Type Definitions

```python
DataType = Literal["table", "view", "external-source", ...]
DataLevel = Literal["source", "staging", "base", "dimension", "fact", "export", ...]
ConnectionType = Literal["select_from", "connected_to"]
```

### Style Mappings

- **NODE_SHAPES**: Maps `data_type` to Mermaid syntax
  - Example: `"table": ("[", "]")` → `[label]`

- **DATA_LEVEL_STYLES**: Maps `data_level` to CSS styles
  - Example: `"dimension": "fill:#e8f5e9,stroke:#1b5e20,stroke-width:3px"`

- **CONNECTION_STYLES**: Maps `connection_type` to arrow styles
  - Example: `"select_from": "-->"`

## CLI Structure ([src/lineage/cli.py](../src/lineage/cli.py))

Built with Click framework for command-line interface.

### Command Organization

```python
@click.group()
def cli():
    """Main CLI group"""
    pass

cli.add_command(extract_from_sql_command)
cli.add_command(mmd_generate_command)
cli.add_command(mmd_legend_command)
cli.add_command(impute_missing_connecting_nodes_command)
```

### Four Main Commands

1. **extract_from_sql**
   - Input: Glob pattern for SQL files
   - Output: YAML file with extracted nodes
   - Process: SQL → sqlglot → Node objects → YAML

2. **generate_mermaid**
   - Input: JSON/YAML lineage file
   - Output: Mermaid diagram (.mmd)
   - Process: File → Nodes/Connections → LineageGraph → MermaidGenerator

3. **generate_legend_mermaid**
   - Input: None (uses config)
   - Output: Mermaid legend diagram
   - Process: Config → Legend generator → Mermaid

4. **impute_missing_connecting_nodes**
   - Input: YAML lineage file
   - Output: Updated YAML with placeholder nodes
   - Process: YAML → Scan select_from → Add missing → YAML

## Design Patterns

### Separation of Concerns

Each phase is independent and communicates through well-defined data structures:

```python
# Input Phase
nodes, connections = load_lineage_file(path)

# Graph Phase
graph = LineageGraph(nodes, connections)
filtered_nodes, filtered_connections = graph.get_subgraph(focus_ids)

# Export Phase
generator = MermaidGenerator(filtered_nodes, filtered_connections)
diagram = generator.generate()
```

### Dependency Injection

Configuration is centralized and injected where needed:

```python
from lineage.config import NODE_SHAPES, DATA_LEVEL_STYLES

class MermaidGenerator:
    def __init__(self, nodes, connections, direction="LR"):
        self.nodes = nodes
        self.direction = direction
        # Uses imported config dictionaries
```

### Immutability

Data structures are designed to be immutable after creation:

```python
@dataclass
class Node:
    # Fields are set at initialization
    # No methods that modify state
```

Graph operations return new filtered lists rather than modifying in place.

### Fail-Fast Validation

Input validation happens early in the pipeline:

```python
def __post_init__(self):
    """Validate field values after initialization."""
    if not isinstance(self.id, str) or not self.id:
        raise ValueError("id must be a non-empty string")
```

### Deterministic Output

All outputs are sorted to ensure consistency:

```python
# Sort nodes by ID
for node in sorted(self.nodes, key=lambda n: n.id):
    process(node)

# Sort connections by from_id, then to_id
for conn in sorted(self.connections, key=lambda c: (c.from_id, c.to_id)):
    process(conn)
```

This ensures:
- Reproducible diagram generation
- Clean version control diffs
- Predictable test assertions

## Graph Operations Deep Dive

### NetworkX Integration

The tool wraps NetworkX's DiGraph for efficiency:

```python
class LineageGraph:
    def __init__(self, nodes, connections):
        self.graph = nx.DiGraph()

        # Store node objects as attributes
        for node in nodes:
            self.graph.add_node(node.id, node=node)

        # Store connection objects as attributes
        for conn in connections:
            self.graph.add_edge(conn.from_id, conn.to_id, connection=conn)
```

**Benefits**:
- O(1) node/edge lookup
- Efficient graph traversal algorithms (BFS, DFS)
- Built-in cycle detection
- Path finding algorithms

### Filtering Strategies

**Upstream Filtering** (ancestors):
```python
def get_upstream_nodes(self, node_id, max_depth=None):
    if max_depth is None:
        return nx.ancestors(self.graph, node_id)
    else:
        # BFS with depth limit
        return custom_bfs(node_id, predecessors, max_depth)
```

**Downstream Filtering** (descendants):
```python
def get_downstream_nodes(self, node_id, max_depth=None):
    if max_depth is None:
        return nx.descendants(self.graph, node_id)
    else:
        # BFS with depth limit
        return custom_bfs(node_id, successors, max_depth)
```

**Subgraph Extraction**:
```python
def get_subgraph(self, focus_nodes, direction="both", max_depth=None):
    # Collect all relevant node IDs
    selected = set(focus_nodes)
    for node_id in focus_nodes:
        if direction in ("upstream", "both"):
            selected.update(get_upstream_nodes(node_id, max_depth))
        if direction in ("downstream", "both"):
            selected.update(get_downstream_nodes(node_id, max_depth))

    # Extract subgraph and convert back to data structures
    subgraph = self.graph.subgraph(selected)
    return convert_to_nodes_and_connections(subgraph)
```

## Extension Points

### Adding New Input Sources

Create a new parser in `src/lineage/io/`:

```python
def parse_custom_format(file_path: Path) -> tuple[list[Node], list[Connection]]:
    """Parse custom format and return normalized data."""
    # Implementation
    return nodes, connections
```

### Adding New Export Formats

Create a new generator in `src/lineage/export/`:

```python
class GraphvizGenerator:
    def __init__(self, nodes, connections):
        self.nodes = nodes
        self.connections = connections

    def generate(self) -> str:
        """Generate Graphviz DOT syntax."""
        # Implementation
        return dot_syntax
```

### Adding New Graph Operations

Extend `LineageGraph` class:

```python
def get_longest_path(self) -> list[str]:
    """Find longest path in DAG."""
    return nx.dag_longest_path(self.graph)
```

## Performance Considerations

- **Graph Construction**: O(N + E) where N=nodes, E=edges
- **Upstream/Downstream**: O(N + E) for unlimited depth, O(D × B) for depth-limited (D=depth, B=branching factor)
- **Subgraph Extraction**: O(K × (N + E)) where K=number of focus nodes
- **Mermaid Generation**: O(N + E) with sorting overhead

The tool efficiently handles graphs with hundreds to thousands of nodes on standard hardware.
