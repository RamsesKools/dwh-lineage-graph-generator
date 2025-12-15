# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python CLI tool that generates Mermaid diagrams for data warehouse lineage visualization. It extracts metadata from SQL files or YAML/JSON configuration, builds a graph of data dependencies using NetworkX, and renders visual diagrams showing how data flows through tables, views, and other data objects.

## Development Commands

### Setup
```bash
poetry install
```

### Testing
```bash
# Run all tests
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run with coverage report
poetry run pytest --cov
```

### Running the CLI
```bash
# Using poetry run
poetry run python src/lineage/cli.py <command>

# Or install and use the entry point
poetry install
lineage <command>
```

## Core Architecture

### Three-Phase Pipeline

1. **Input Phase** (`src/lineage/io/`)
   - **SQL Parsing**: Uses `sqlglot` to extract CREATE TABLE/VIEW statements from SQL files
   - **YAML/JSON Parsing**: Loads lineage configuration files with nodes and connections
   - Outputs: List of `Node` objects and `Connection` objects

2. **Graph Phase** (`src/lineage/graph/`)
   - **LineageGraph**: Wraps NetworkX DiGraph for traversal operations (ancestors, descendants, path finding)
   - **Missing Nodes**: Detects and imputes nodes referenced in `select_from` but not defined
   - Core operations: upstream/downstream filtering, subgraph extraction, cycle detection

3. **Export Phase** (`src/lineage/export/`)
   - **MermaidGenerator**: Renders Mermaid diagram syntax with proper node shapes and colors
   - Applies styling based on `data_type` (shapes) and `data_level` (colors)

### Data Model (`src/lineage/models.py`)

- **Node**: Represents a data object (table, view, source)
  - `id`: Unique identifier (e.g., "schema.table")
  - `label`: Display name
  - `data_type`: Determines shape (table→rectangle, view→stadium, etc.)
  - `data_level`: Determines color (source, staging, base, dimension, fact, export)
  - `select_from`: List of upstream node IDs (creates connections)

- **Connection**: Data flow between nodes
  - `from_id`, `to_id`: Node identifiers
  - `connection_type`: Arrow style (select_from→solid, connected_to→dashed)

### Configuration (`src/lineage/config.py`)

Defines all visual styling:
- `NODE_SHAPES`: Maps data_type to Mermaid syntax (brackets, parentheses, etc.)
- `DATA_LEVEL_STYLES`: Maps data_level to CSS fill/stroke styles
- `CONNECTION_STYLES`: Maps connection_type to arrow styles

### CLI Structure (`src/lineage/cli.py`)

Four main commands implemented with Click:
1. `extract_from_sql`: Parse SQL files → YAML nodes
2. `generate_mermaid`: YAML/JSON → Mermaid diagram
3. `generate_legend_mermaid`: Create style reference diagram
4. `impute_missing_connecting_nodes`: Add missing nodes referenced in select_from

### SQL Parsing Details (`src/lineage/io/sql_parser.py`)

- Uses sqlglot with Redshift dialect
- Extracts CREATE TABLE/VIEW statements
- Only processes schema-qualified objects (must have `schema.table` format)
- Automatically extracts lineage from SELECT statements via `sql_lineage_extractor.py`
- Stores extracted dependencies in `select_from` field

### Graph Operations (`src/lineage/graph/lineage_graph.py`)

NetworkX-based operations for:
- **Filtering**: Focus on specific nodes with depth limits and direction (upstream/downstream/both)
- **Traversal**: BFS with configurable depth for finding related nodes
- **Analysis**: Cycle detection, path finding, DAG validation
- **Subgraphs**: Extract portions of the graph for focused visualization

## Key Implementation Patterns

### YAML Format (Preferred)

Nodes can define connections inline using `select_from`:
```yaml
nodes:
  - id: schema.table_name
    label: Table Name
    data_type: table
    data_level: dimension
    select_from:
      - schema.source_table
```

This is more concise than separate `connections` list and is the recommended format.

### Node Deduplication

When extracting from SQL files, nodes are deduplicated by ID (last seen wins). This allows later SQL files to override earlier definitions.

### Missing Node Imputation

The `impute_missing_connecting_nodes` command scans all `select_from` fields and creates placeholder nodes for any referenced IDs that don't exist. New nodes get `null` for `data_level` and `data_type`, which must be filled in manually.

### Deterministic Output

All node and connection lists are sorted before rendering to ensure consistent output for version control and testing.

## File Organization

```
src/lineage/
├── models.py           # Core dataclasses (Node, Connection)
├── config.py           # Styling configuration (shapes, colors, arrows)
├── cli.py              # Click-based CLI commands
├── io/                 # Input parsing
│   ├── sql_parser.py           # SQL file extraction
│   ├── sql_lineage_extractor.py # Extract SELECT dependencies
│   ├── yaml_parser.py          # YAML/JSON loading
│   └── yaml_writer.py          # YAML output with deduplication
├── graph/              # Graph operations
│   ├── lineage_graph.py        # NetworkX wrapper
│   └── missing_nodes.py        # Missing node detection
└── export/             # Output generation
    └── mermaid.py              # Mermaid syntax generation

tests/
├── test_*.py           # Unit tests matching src/ structure
└── data/               # Test fixtures (SQL, YAML, expected outputs)
```

## Testing Strategy

Tests are organized by module with fixtures in `tests/data/`. The test suite validates:
- SQL parsing with various CREATE statement formats
- Graph traversal and filtering operations
- Mermaid output formatting
- YAML round-trip (read and write)
- Missing node detection and imputation
- CLI integration tests using Click's test utilities

## Common Gotchas

1. **Glob patterns must be quoted** when passed to shell: `"sql/**/*.sql"` not `sql/**/*.sql`
2. **Schema qualification is required**: Only objects with `schema.table` format are extracted from SQL
3. **Node IDs are sanitized** in Mermaid output (dots/dashes → underscores) but preserved in data
4. **YAML preserves comments** when using `ruamel.yaml` for imputation operations
5. **data_level can be None/null** during extraction, must be set before final visualization
