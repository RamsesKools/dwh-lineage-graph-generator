# Code Architecture

This document describes the high-level architecture and design patterns of the Data Lineage Graph Generator.

## Three-Phase Pipeline

The tool follows a clean separation of concerns with three independent phases:

```text
Input Phase → Graph Phase → Export Phase
```

Each phase communicates through well-defined dataclass interfaces (`Node` and `Connection`).

### 1. Input Phase ([src/lineage/io/](../src/lineage/io/))

**Purpose**: Parse various input sources and normalize into common data model.

**Key components**:

- **SQL Parser**: Uses `sqlglot` with Redshift dialect to extract CREATE TABLE/VIEW statements
- **SQL Lineage Extractor**: Analyzes SELECT statements to automatically populate `select_from` fields
- **YAML/JSON Parser**: Loads lineage files and converts inline `select_from` to Connection objects
- **YAML Writer**: Uses `ruamel.yaml` to preserve comments and formatting during writes

**Output**: `list[Node]` and `list[Connection]`

### 2. Graph Phase ([src/lineage/graph/](../src/lineage/graph/))

**Purpose**: Build graph representation and perform traversal/filtering operations.

**Key components**:

- **LineageGraph** ([lineage_graph.py](../src/lineage/graph/lineage_graph.py)): Wraps NetworkX DiGraph
  - Graph operations: upstream/downstream traversal, subgraph extraction, cycle detection, path finding
  - Supports depth-limited traversal using BFS
  - Uses NetworkX built-in algorithms for unlimited depth (efficient)

- **Missing Nodes Detector** ([missing_nodes.py](../src/lineage/graph/missing_nodes.py)): Scans `select_from` fields and creates placeholder nodes for missing references

**Output**: Filtered `list[Node]` and `list[Connection]`

### 3. Export Phase ([src/lineage/export/](../src/lineage/export/))

**Purpose**: Render graph data into visual diagram formats.

**Key components**:

- **MermaidGenerator** ([mermaid.py](../src/lineage/export/mermaid.py)):
  - Generates Mermaid syntax from nodes/connections
  - Applies styling based on `data_type` (shape) and `data_level` (color)
  - Sanitizes node IDs for Mermaid compatibility
  - Produces deterministic output (sorted)

- **Legend Generator**: Creates reference diagrams showing all available styles

**Output**: Mermaid diagram string

## Data Model ([src/lineage/models.py](../src/lineage/models.py))

Two immutable dataclasses serve as the interface between all pipeline phases:

**Node**: Represents a data object

- Required: `id`, `label`
- Optional: `data_type` (determines shape), `data_level` (determines color), `select_from` (upstream connections)
- `data_level` can be `null` during extraction

**Connection**: Represents data flow

- Required: `from_id`, `to_id`
- Optional: `connection_type` (determines arrow style, defaults to `"select_from"`)

## Configuration ([src/lineage/config.py](../src/lineage/config.py))

Single source of truth for all visual styling:

- **Type Definitions**: `DataType`, `DataLevel`, `ConnectionType` using Literal types
- **Style Mappings**: Dictionaries mapping types to Mermaid syntax and CSS styles
  - `NODE_SHAPES`: Maps data_type → Mermaid bracket syntax
  - `DATA_LEVEL_STYLES`: Maps data_level → CSS fill/stroke styles
  - `CONNECTION_STYLES`: Maps connection_type → arrow styles

## CLI Structure ([src/lineage/cli.py](../src/lineage/cli.py))

Built with Click framework. Four main commands orchestrate the pipeline:

1. `extract_from_sql`: SQL files → Nodes (YAML output)
2. `generate_mermaid`: Lineage file → Mermaid diagram
3. `generate_legend_mermaid`: Config → Style reference diagram
4. `impute_missing_connecting_nodes`: Scan YAML → Add placeholder nodes

Each command handles I/O and coordinates between pipeline phases.

## Design Patterns

### Separation of Concerns

Phases are independent and communicate only through dataclasses:

```python
# Input → Graph → Export
nodes, connections = load_lineage_file(path)
graph = LineageGraph(nodes, connections)
filtered_nodes, filtered_connections = graph.get_subgraph(focus_ids)
generator = MermaidGenerator(filtered_nodes, filtered_connections)
diagram = generator.generate()
```

### Immutability

Dataclasses are immutable after creation. Graph operations return new filtered lists rather than modifying in place.

### Deterministic Output

All outputs are sorted (nodes by ID, connections by from/to) to ensure:

- Reproducible diagram generation
- Clean version control diffs
- Predictable test assertions

### Fail-Fast Validation

Input validation happens in `__post_init__()` methods to catch errors early.

## Graph Operations

### NetworkX Integration

[LineageGraph](../src/lineage/graph/lineage_graph.py) wraps NetworkX DiGraph:

- Stores Node/Connection objects as graph attributes
- Leverages NetworkX algorithms: `ancestors()`, `descendants()`, `simple_cycles()`, `all_simple_paths()`
- For unlimited depth traversal: uses built-in NetworkX algorithms
- For depth-limited traversal: implements custom BFS

### Filtering Strategies

**Upstream/Downstream**: Uses NetworkX `ancestors()`/`descendants()` for unlimited depth, custom BFS for depth limits

**Subgraph Extraction**: Collects relevant node IDs based on direction (upstream/downstream/both), then extracts subgraph and converts back to Node/Connection lists

See [lineage_graph.py](../src/lineage/graph/lineage_graph.py) for implementation details.

## Extension Points

### Adding New Input Sources

Create a parser in `src/lineage/io/` that returns `tuple[list[Node], list[Connection]]`. Follow the pattern in existing parsers.

### Adding New Export Formats

Create a generator in `src/lineage/export/` with a `generate()` method that returns diagram syntax as string. See `MermaidGenerator` for reference.

### Adding New Graph Operations

Extend `LineageGraph` class with new methods. NetworkX provides many graph algorithms that can be wrapped (shortest paths, centrality measures, community detection, etc.).

### Adding New Data Types/Levels

Update `config.py`:

1. Add to `DataType` or `DataLevel` Literal
2. Add mapping to `NODE_SHAPES` or `DATA_LEVEL_STYLES`

No other code changes needed - styling is centralized.
