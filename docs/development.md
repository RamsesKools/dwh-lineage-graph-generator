# Development Guide

This guide covers development setup, testing, and implementation patterns for the Data Lineage Graph Generator.

## Technology Stack

- **Python**: >=3.12
- **Package Manager**: Poetry
- **CLI Framework**: Click
- **Graph Library**: NetworkX
- **SQL Parser**: sqlglot (Redshift dialect)
- **YAML Parser**: ruamel.yaml (preserves comments)
- **Testing**: pytest

## Setup

### Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd dwh-lineage-graph-generator

# Install dependencies
poetry install
```

### Development Environment

```bash
# Activate virtual environment
poetry shell

# Run CLI directly
python src/lineage/cli.py --help

# Or use the installed entry point
lineage --help
```

## Running the CLI

### Using Poetry Run

```bash
poetry run python src/lineage/cli.py <command>
```

### Using Installed Entry Point

```bash
poetry install
lineage <command>
```

### Available Commands

```bash
lineage extract_from_sql --help
lineage generate_mermaid --help
lineage generate_legend_mermaid --help
lineage impute_missing_connecting_nodes --help
```

## Testing

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run with coverage report
poetry run pytest --cov

# Run specific test file
poetry run pytest tests/test_graph.py

# Run specific test function
poetry run pytest tests/test_graph.py::test_upstream_nodes
```

### Test Organization

Tests are organized by module with fixtures in `tests/data/`:

```text
tests/
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
    ├── example_lineage.json
    ├── example_lineage.yaml
    ├── test_extract.sql
    └── *.mmd                        # Expected output files
```

### Test Coverage

The test suite validates:

- SQL parsing with various CREATE statement formats
- Graph traversal and filtering operations (upstream, downstream, subgraphs)
- Mermaid output formatting and deterministic rendering
- YAML round-trip (read and write with comment preservation)
- Missing node detection and imputation
- CLI integration tests using Click's test utilities

## Key Implementation Patterns

### YAML Format Preference

Use inline `select_from` definitions in YAML for cleaner syntax:

```yaml
nodes:
  - id: schema.table_name
    label: Table Name
    data_type: table
    data_level: dimension
    select_from:
      - schema.source_table
```

This is more concise than separate `connections` arrays.

### Node Deduplication

When extracting from SQL files, nodes are deduplicated by ID (last seen wins):

```python
nodes: dict[str, Node] = {}
for file_path in sql_files:
    file_nodes = parse_sql_file(Path(file_path))
    for node in file_nodes:
        nodes[node.id] = node  # Last seen wins
```

This allows later SQL files to override earlier definitions.

### Missing Node Imputation

The `impute_missing_connecting_nodes` command:

1. Scans all `select_from` fields
2. Identifies referenced node IDs that don't exist
3. Creates placeholder nodes with `null` for `data_level` and `data_type`
4. Appends them to the end of the nodes list
5. Preserves YAML comments and formatting using `ruamel.yaml`

Example:

```python
from lineage.graph.missing_nodes import impute_missing_connecting_nodes

stats = impute_missing_connecting_nodes(
    input_file=Path("lineage.yaml"),
    output_file=Path("lineage.yaml")  # In-place modification
)
```

### Deterministic Output

All node and connection lists are sorted before rendering:

```python
# Sort nodes by ID
for node in sorted(self.nodes, key=lambda n: n.id):
    lines.append(self._generate_node_definition(node))

# Sort connections by from_id, then to_id
for connection in sorted(self.connections, key=lambda c: (c.from_id, c.to_id)):
    lines.append(self._generate_connection_definition(connection))
```

This ensures consistent output for version control and testing.

### ID Sanitization

Node IDs are sanitized for Mermaid output but preserved in data:

```python
def _sanitize_id(self, node_id: str) -> str:
    """Replace characters that might cause issues in Mermaid."""
    return node_id.replace("-", "_").replace(".", "_").replace(" ", "_")
```

Original IDs like `"schema.table"` become `"schema_table"` in Mermaid syntax, but remain `"schema.table"` in the data model.

## Common Development Tasks

### Adding a New Data Type

1. Add the type to `DataType` in [src/lineage/config.py](../src/lineage/config.py):

```python
DataType = Literal[
    "table",
    "view",
    "new-type",  # Add here
    # ...
]
```

2. Add the shape mapping to `NODE_SHAPES`:

```python
NODE_SHAPES: dict[str, tuple[str, str]] = {
    "table": ("[", "]"),
    "new-type": ("((", "))"),  # Double parentheses = circle
    # ...
}
```

3. Update [docs/file_format.md](file_format.md) with the new type

### Adding a New Data Level

1. Add the level to `DataLevel` in [src/lineage/config.py](../src/lineage/config.py):

```python
DataLevel = Literal[
    "source",
    "new-level",  # Add here
    # ...
]
```

2. Add the color style to `DATA_LEVEL_STYLES`:

```python
DATA_LEVEL_STYLES: dict[str, str] = {
    "source": "fill:#e1f5ff,stroke:#01579b,stroke-width:2px",
    "new-level": "fill:#custom,stroke:#color,stroke-width:2px",
    # ...
}
```

3. Update [docs/file_format.md](file_format.md) with the new level

### Adding a New CLI Command

1. Define the command in [src/lineage/cli.py](../src/lineage/cli.py):

```python
@click.command(
    name="my_command",
    help="Description of the command"
)
@click.argument("input_file", type=click.Path(exists=True))
def my_command(input_file: Path) -> None:
    """Command implementation."""
    pass
```

2. Register it with the CLI group:

```python
cli.add_command(my_command)
```

3. Add integration tests in `tests/test_cli_integration.py`

### Extending Graph Operations

Add new graph operations to [src/lineage/graph/lineage_graph.py](../src/lineage/graph/lineage_graph.py):

```python
def get_shortest_path(self, from_node_id: str, to_node_id: str) -> list[str]:
    """Get shortest path between two nodes."""
    try:
        return nx.shortest_path(self.graph, from_node_id, to_node_id)
    except nx.NetworkXNoPath:
        return []
```

NetworkX provides many built-in graph algorithms that can be wrapped.

## Common Gotchas

1. **Glob patterns must be quoted** when passed to shell:
   ```bash
   python cli.py extract_from_sql "sql/**/*.sql"  # Correct
   python cli.py extract_from_sql sql/**/*.sql     # Wrong - shell expands it
   ```

2. **Schema qualification is required**: Only objects with `schema.table` format are extracted from SQL

3. **Node IDs are sanitized** in Mermaid output (dots/dashes → underscores) but preserved in data

4. **YAML preserves comments** when using `ruamel.yaml` for imputation operations

5. **data_level can be None/null** during extraction, must be set before final visualization

6. **Self-references are excluded**: A node cannot reference itself in `select_from`

7. **Last definition wins**: When extracting from multiple SQL files with duplicate IDs, the last file wins

## Code Style

- Follow PEP 8 conventions
- Use type hints for all function signatures
- Write docstrings for public functions and classes
- Keep functions focused and single-purpose
- Use dataclasses for data structures
- Prefer explicit over implicit

## Adding Dependencies

```bash
# Add runtime dependency
poetry add package-name

# Add development dependency
poetry add --group dev package-name

# Update lock file
poetry lock
```

## Debugging

### Enable Verbose Output

```bash
# Use -v flag in pytest
poetry run pytest -v

# Use -s to see print statements
poetry run pytest -s
```

### Inspect Generated Mermaid

```bash
# Output to stdout for inspection
python cli.py generate_mermaid lineage.yaml

# Compare with expected output
diff <(python cli.py generate_mermaid lineage.yaml) expected.mmd
```

### Debug SQL Parsing

```python
import sqlglot

sql = "CREATE TABLE schema.table AS SELECT * FROM source"
statements = sqlglot.parse(sql, read="redshift")
print(statements[0].sql())  # Pretty-print parsed SQL
```
