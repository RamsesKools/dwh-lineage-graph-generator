# Development Guide

## Technology Stack

- Python >=3.12
- Poetry (package management)
- Click (CLI framework)
- NetworkX (graph operations)
- sqlglot (SQL parsing, Redshift dialect)
- ruamel.yaml (preserves comments)
- pytest (testing)

## Setup

```bash
poetry install
```

## Running Tests

```bash
# All tests
poetry run pytest

# With coverage
poetry run pytest --cov

# Specific test
poetry run pytest tests/test_graph.py::test_upstream_nodes
```

## Key Implementation Patterns

### Node Deduplication

When extracting from SQL files, nodes are deduplicated by ID (last seen wins). This allows later SQL files to override earlier definitions.

### Missing Node Imputation

The `impute_missing_connecting_nodes` command scans `select_from` fields and creates placeholder nodes (with `null` data_type/data_level) for any referenced IDs that don't exist. Uses `ruamel.yaml` to preserve comments.

### Deterministic Output

All nodes and connections are sorted before rendering to ensure consistent output for version control and testing.

### ID Sanitization

Node IDs are sanitized for Mermaid output (dots/dashes → underscores) but preserved in the data model.

## Common Development Tasks

### Adding a New Data Type

1. Add to `DataType` in [src/lineage/config.py](../src/lineage/config.py)
2. Add mapping to `NODE_SHAPES`
3. No other changes needed - styling is centralized

### Adding a New Data Level

1. Add to `DataLevel` in [src/lineage/config.py](../src/lineage/config.py)
2. Add mapping to `DATA_LEVEL_STYLES`
3. No other changes needed - styling is centralized

### Adding a New CLI Command

1. Define command in [src/lineage/cli.py](../src/lineage/cli.py) using `@click.command`
2. Register with `cli.add_command()`
3. Add integration tests in `tests/test_cli_integration.py`

### Adding a New Module

1. Create file in appropriate directory under `src/lineage/`
2. Add corresponding test file `tests/test_<module>.py`
3. Update docs if it introduces new concepts

### Extending Graph Operations

Add methods to `LineageGraph` class in [src/lineage/graph/lineage_graph.py](../src/lineage/graph/lineage_graph.py). NetworkX provides many algorithms that can be wrapped (shortest paths, centrality, community detection, etc.).

## Common Gotchas

1. **Quote glob patterns** when passed to shell: `"sql/**/*.sql"` not `sql/**/*.sql`
2. **Schema qualification required**: Only `schema.table` format extracted from SQL
3. **Node IDs sanitized** in Mermaid output but preserved in data
4. **data_level can be null** during extraction, must be set before visualization
5. **Self-references excluded**: Node cannot reference itself in `select_from`
6. **Last definition wins**: Duplicate IDs from multiple SQL files

## Code Style

### Python Conventions

- Follow PEP 8
- Use type hints for all function signatures
- Write docstrings for public functions and classes
- Keep functions focused and single-purpose
- Use dataclasses for data structures
- Prefer explicit over implicit

### Import Style

Use absolute imports from `lineage` package:

```python
from lineage.models import Node, Connection
from lineage.graph.lineage_graph import LineageGraph
```
