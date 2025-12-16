# File Organization

This document describes the structure of the codebase and the purpose of each directory and file.

## Project Structure

```text
dwh-lineage-graph-generator/
├── src/lineage/              # Main source code
├── tests/                    # Test suite
├── docs/                     # Documentation
├── lineage_data/             # Example lineage data (project-specific)
├── pyproject.toml            # Poetry configuration
├── poetry.lock               # Locked dependencies
└── README.md                 # Project overview
```

## Source Code (`src/lineage/`)

```text
src/lineage/
├── __init__.py               # Package initialization, version export
├── models.py                 # Core dataclasses (Node, Connection)
├── config.py                 # Styling configuration (shapes, colors, arrows)
├── cli.py                    # Click-based CLI commands
├── io/                       # Input/output operations
│   ├── __init__.py
│   ├── sql_parser.py         # SQL file extraction
│   ├── sql_lineage_extractor.py  # Extract SELECT dependencies
│   ├── yaml_parser.py        # YAML/JSON loading
│   └── yaml_writer.py        # YAML output with deduplication
├── graph/                    # Graph operations
│   ├── __init__.py
│   ├── lineage_graph.py      # NetworkX wrapper
│   └── missing_nodes.py      # Missing node detection
└── export/                   # Output generation
    ├── __init__.py
    └── mermaid.py            # Mermaid syntax generation
```

### Core Modules

#### `models.py`
Defines the core data structures:
- `Node`: Represents a data object (table, view, source)
- `Connection`: Represents a data flow between nodes

These are immutable dataclasses that serve as the interface between all pipeline phases.

#### `config.py`
Central configuration for visual styling:
- Type definitions: `DataType`, `DataLevel`, `ConnectionType`
- Style mappings: `NODE_SHAPES`, `DATA_LEVEL_STYLES`, `CONNECTION_STYLES`

All styling is defined here to maintain single source of truth.

#### `cli.py`
Command-line interface built with Click:
- Defines all CLI commands
- Handles argument parsing and validation
- Coordinates between modules
- Manages file I/O and error handling

### Input/Output (`io/`)

#### `sql_parser.py`
Extracts lineage from SQL files:
- Uses `sqlglot` library with Redshift dialect
- Parses CREATE TABLE/VIEW statements
- Only extracts schema-qualified objects (`schema.table`)
- Returns list of Node objects

#### `sql_lineage_extractor.py`
Extracts SELECT dependencies from SQL:
- Analyzes FROM clauses in CREATE statements
- Populates `select_from` fields automatically
- Handles complex queries with multiple sources

#### `yaml_parser.py`
Loads lineage from YAML/JSON files:
- Supports both formats
- Converts inline `select_from` to Connection objects
- Returns normalized Node and Connection lists

#### `yaml_writer.py`
Writes nodes to YAML format:
- Uses `ruamel.yaml` to preserve comments
- Handles node deduplication
- Supports append mode for incremental builds

### Graph Operations (`graph/`)

#### `lineage_graph.py`
NetworkX-based graph operations:
- `LineageGraph` class wraps NetworkX DiGraph
- Provides high-level APIs:
  - `get_upstream_nodes()`: Find ancestors
  - `get_downstream_nodes()`: Find descendants
  - `get_subgraph()`: Extract filtered subgraph
  - `get_direct_connections()`: Find immediate neighbors
  - `find_cycles()`: Detect circular dependencies
  - `get_all_paths()`: Find paths between nodes
- Supports depth-limited traversal

#### `missing_nodes.py`
Detects and imputes missing nodes:
- Scans `select_from` fields for referenced IDs
- Identifies nodes that don't exist
- Creates placeholder nodes with null attributes
- Preserves YAML comments during updates

### Export (`export/`)

#### `mermaid.py`
Generates Mermaid diagram syntax:
- `MermaidGenerator` class for diagram generation
- `generate_legend()` function for style reference
- Applies styling based on node attributes
- Sanitizes IDs for Mermaid compatibility
- Produces deterministic output

## Tests (`tests/`)

```text
tests/
├── __init__.py
├── conftest.py                      # Shared fixtures
├── test_cli_integration.py          # CLI integration tests
├── test_extractor_sql_parser.py     # SQL parsing tests
├── test_extractor_yaml_writer.py    # YAML writing tests
├── test_generator.py                # Mermaid generation tests
├── test_graph.py                    # Graph operations tests
├── test_metadata.py                 # Data model tests
├── test_missing_nodes_detector.py   # Missing node detection tests
├── test_sql_lineage_extractor.py    # SQL lineage extraction tests
├── test_styles.py                   # Styling configuration tests
└── data/                            # Test fixtures
    ├── example_lineage.json         # Sample JSON lineage
    ├── example_lineage.yaml         # Sample YAML lineage
    ├── test_extract.sql             # Sample SQL for extraction
    ├── example_full_lineage.mmd     # Expected full diagram
    ├── example_focus_upstream.mmd   # Expected filtered diagram
    └── *.mmd                        # Other expected outputs
```

### Test Organization

- **Unit tests**: Test individual functions and classes in isolation
- **Integration tests**: Test CLI commands end-to-end
- **Fixtures**: Shared test data in `tests/data/`
- **Naming**: `test_<module>.py` matches `src/lineage/<module>.py`

### Test Fixtures (`tests/data/`)

- **Input fixtures**: Example lineage files for testing parsers
- **Expected outputs**: Mermaid diagrams for comparison
- **SQL samples**: Various CREATE statement formats for parser testing

## Documentation (`docs/`)

```text
docs/
├── file_format.md           # Lineage file format specification
├── development.md           # Development setup and patterns
├── code_architecture.md     # Architecture and design decisions
└── file_organization.md     # This file
```

### Documentation Purpose

- **file_format.md**: Reference for users creating lineage files
- **development.md**: Guide for contributors and developers
- **code_architecture.md**: High-level design for understanding the system
- **file_organization.md**: Map of the codebase structure

## Configuration Files

### `pyproject.toml`
Poetry configuration file:
- Package metadata (name, version, authors)
- Dependencies (runtime and dev)
- Build system configuration
- Entry point definition (`lineage` command)

### `poetry.lock`
Locked dependency versions:
- Ensures reproducible builds
- Generated automatically by Poetry
- Should be committed to version control

## Example Data (`lineage_data/`)

Project-specific example data (not part of the package):
- `eah-lineage.yaml`: Complete E@H datamart lineage
- `eah-lineage.mmd`: Generated diagram from above

## Import Paths

### From External Code

```python
from lineage.models import Node, Connection
from lineage.graph.lineage_graph import LineageGraph
from lineage.export.mermaid import MermaidGenerator
```

### Internal Imports (within src/lineage/)

```python
# Relative imports
from .models import Node, Connection
from .config import NODE_SHAPES, DATA_LEVEL_STYLES

# Absolute imports
from lineage.io.yaml_parser import load_lineage_file
from lineage.graph.lineage_graph import LineageGraph
```

## Entry Points

### CLI Entry Point

Defined in `pyproject.toml`:

```toml
[tool.poetry.scripts]
lineage = "lineage.cli:cli"
```

This creates the `lineage` command when installed with Poetry.

### Main Module

`src/lineage/cli.py` contains the main entry point:

```python
if __name__ == "__main__":
    cli()
```

Can be run directly: `python src/lineage/cli.py`

## Adding New Files

### Adding a New Module

1. Create file in appropriate directory under `src/lineage/`
2. Add corresponding test file in `tests/test_<module>.py`
3. Update this documentation if it introduces new concepts

### Adding a New Command

1. Add command function to `src/lineage/cli.py`
2. Register with `cli.add_command()`
3. Add integration tests to `tests/test_cli_integration.py`
4. Update `README.md` if user-facing

### Adding a New Test Fixture

1. Add file to `tests/data/`
2. Document expected behavior in test file
3. Use descriptive filename (e.g., `example_<scenario>.yaml`)

## File Naming Conventions

- **Source files**: Snake case (e.g., `lineage_graph.py`)
- **Test files**: `test_<module>.py` matching source
- **Data files**: Descriptive names (e.g., `example_lineage.yaml`)
- **Documentation**: Lowercase with underscores (e.g., `file_format.md`)

## Directory Responsibilities

| Directory | Responsibility | Dependencies |
|-----------|---------------|--------------|
| `src/lineage/` | Core package code | External libraries only |
| `src/lineage/io/` | Input/output operations | `models`, `config` |
| `src/lineage/graph/` | Graph operations | `models`, NetworkX |
| `src/lineage/export/` | Output generation | `models`, `config` |
| `tests/` | Test suite | `src/lineage/`, pytest |
| `docs/` | Documentation | None |

## Dependency Flow

```text
cli.py
  ├─→ io/ (parsers)
  │    └─→ models
  ├─→ graph/
  │    └─→ models
  └─→ export/
       └─→ models, config

models ←─ (used by all modules)
config ←─ (used by export, cli)
```

This organization maintains clear separation of concerns and prevents circular dependencies.
