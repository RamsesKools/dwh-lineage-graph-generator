# Data Lineage Graph Generator

A Python CLI tool that generates Mermaid diagrams for data warehouse lineage visualization. It extracts metadata from SQL files or YAML/JSON configuration, builds a graph of data dependencies using NetworkX, and renders visual diagrams showing how data flows through tables, views, and other data objects.

## Quick Start

### Installation

Install dependencies using Poetry:

```bash
poetry install
```

### Basic Usage

```bash
# Generate a lineage diagram from YAML/JSON
python cli.py generate_mermaid data_warehouse.yaml -o lineage.mmd

# Extract nodes from SQL files
python cli.py extract_from_sql "sql/**/*.sql" -o lineage.yaml

# Generate a style legend
python cli.py generate_legend_mermaid -o legend.mmd
```

## CLI Commands

### Generate Lineage Diagram

Generate a Mermaid diagram to stdout:

```bash
python cli.py generate_mermaid data_warehouse.json
```

Save the generated diagram to a file:

```bash
python cli.py generate_mermaid data_warehouse.json -o lineage.mmd
```

Change the flow direction (LR=left-right, RL=right-left, TB=top-bottom, BT=bottom-top):

```bash
python cli.py generate_mermaid data_warehouse.json -d TB
```

Focus on specific nodes using `--focus` (comma-separated for multiple), `--filter-direction` (upstream/downstream/both), `--depth` (max hops), or `--direct-only` (1 hop):

```bash
python cli.py generate_mermaid data_warehouse.json --focus dim_customer
python cli.py generate_mermaid data_warehouse.json --focus dim_customer,fact_orders --filter-direction upstream --depth 2
python cli.py generate_mermaid data_warehouse.json --focus dim_customer --direct-only
```

### Generate Legend

Generate a legend showing all available node types, data levels, and connection styles:

```bash
python cli.py generate_legend_mermaid
```

Save the legend to a file:

```bash
python cli.py generate_legend_mermaid -o legend.mmd
```

The legend displays with subgraphs stacked vertically (top to bottom), while content within each subgraph flows left to right.

### Extract Nodes from SQL

Extract lineage nodes from SQL files (CREATE TABLE/VIEW statements):

```bash
# Recursive extraction (quote pattern to prevent shell expansion)
python cli.py extract_from_sql "sql/**/*.sql" -o lineage.yaml

# Specific directory
python cli.py extract_from_sql "sql/staging/*.sql" -o staging.yaml

# Append to existing file
python cli.py extract_from_sql "sql/base/*.sql" -o lineage.yaml --append
```

**Important:** Always quote glob patterns to prevent shell expansion.

Supports glob patterns (`*.sql`, `**/*.sql`). Only extracts schema-qualified objects (`schema.table`).

### Impute Missing Connecting Nodes

Add nodes that are referenced in `select_from` fields but don't exist in the nodes list:

```bash
# Modify file in-place
python cli.py impute_missing_connecting_nodes lineage.yaml

# Create new output file
python cli.py impute_missing_connecting_nodes lineage.yaml -o lineage_complete.yaml
```

This command scans all `select_from` fields and adds any referenced nodes that are missing. New nodes are created with null `data_level` and `data_type` fields, which can be filled in later.

## Recommended Workflows

### Workflow 1: From SQL Files (Manual)

When building from SQL files without a workflow configuration:

1. **Extract nodes from SQL**: Start by extracting CREATE TABLE/VIEW statements from your SQL files

   ```bash
   python cli.py extract_from_sql "sql/**/*.sql" -o lineage.yaml
   ```

2. **Add select_from relationships**: Manually edit the YAML file to add `select_from` fields by reading the SQL code to understand data dependencies

3. **Impute missing nodes**: Add any nodes that are referenced but not yet defined

   ```bash
   python cli.py impute_missing_connecting_nodes lineage.yaml
   ```

4. **Generate diagram**: Create the final Mermaid visualization

   ```bash
   python cli.py generate_mermaid lineage.yaml -o lineage.mmd
   ```

This workflow ensures a complete and accurate lineage graph with minimal manual effort.

## Input Format

The tool supports both JSON and YAML input formats.

### JSON Format

The input JSON file should contain `nodes` and `connections`:

```json
{
  "nodes": [
    {
      "id": "raw_customers",
      "label": "Raw Customers",
      "data_type": "external-source",
      "data_level": "source"
    },
    {
      "id": "dim_customer",
      "label": "Customer Dimension",
      "data_type": "table",
      "data_level": "dimension"
    }
  ],
  "connections": [
    {"from_id": "raw_customers", "to_id": "dim_customer"}
  ]
}
```

### YAML Format (Recommended)

YAML format is more readable and supports inline connection definitions using `select_from`:

```yaml
nodes:
  - id: raw_customers
    label: Raw Customers
    data_type: external-source
    data_level: source

  - id: dim_customer
    label: Customer Dimension
    data_type: table
    data_level: dimension
    select_from:
      - raw_customers
```

The `select_from` field creates connections from the listed nodes to the current node. You can also use `connected_to` for bidirectional connections.

### Data Types (Shapes)

- `table` → Rectangle: `[label]`
- `view` → Stadium: `([label])`
- `external-source` → Cylinder: `[(label)]`
- `external-resourcelink` → Hexagon: `{{label}}`
- `manual-source` → Trapezoid: `[/label\]`

### Data Levels (Colors)

- `source`: Light blue (#e1f5ff)
- `staging`: Light orange (#fff3e0)
- `base`: Light purple (#f3e5f5)
- `dimension`: Light green (#e8f5e9)
- `fact`: Light pink (#fce4ec)
- `export`: Light yellow (#fff9c4)

## Examples

### Basic Example

A basic example lineage file is provided in [tests/data/example_lineage.json](tests/data/example_lineage.json). Run:

```bash
python cli.py generate_mermaid tests/data/example_lineage.json -o output.mmd
```

### EAH Datamart Lineage

The complete lineage (as of 2025-11-06) of E@H datamart is available in [lineage_data/eah-lineage.yaml](lineage_data/eah-lineage.yaml). This file contains nodes representing the full data pipeline from source systems through staging, base, dimensions, and facts to export views.

Generate the complete EAH lineage diagram:

```bash
poetry run python cli.py generate_mermaid lineage_data/eah-lineage.yaml -o lineage_data/eah-lineage.mmd
```

The resulting [eah-lineage.mmd](lineage_data/eah-lineage.mmd) can be viewed in any Mermaid-compatible viewer or IDE extension.
It is also possible to insert the mermaid code into lucidchart or draw.io.
For drawio, see how to do it here: <https://www.drawio.com/blog/mermaid-diagrams>

## Development

### Running the CLI

```bash
# Using poetry run
poetry run python src/lineage/cli.py <command>

# Or install and use the entry point
poetry install
lineage <command>
```

### Testing

Run the test suite using pytest:

```bash
# Run all tests
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run with coverage report
poetry run pytest --cov
```

Tests are organized by module with fixtures in `tests/data/`. The test suite validates:

- SQL parsing with various CREATE statement formats
- Graph traversal and filtering operations
- Mermaid output formatting
- YAML round-trip (read and write)
- Missing node detection and imputation
- CLI integration tests using Click's test utilities

## Architecture

### Three-Phase Pipeline

1. **Input Phase** ([src/lineage/io/](src/lineage/io/))
   - **SQL Parsing**: Uses `sqlglot` to extract CREATE TABLE/VIEW statements from SQL files
   - **YAML/JSON Parsing**: Loads lineage configuration files with nodes and connections
   - Outputs: List of `Node` objects and `Connection` objects

2. **Graph Phase** ([src/lineage/graph/](src/lineage/graph/))
   - **LineageGraph**: Wraps NetworkX DiGraph for traversal operations (ancestors, descendants, path finding)
   - **Missing Nodes**: Detects and imputes nodes referenced in `select_from` but not defined
   - Core operations: upstream/downstream filtering, subgraph extraction, cycle detection

3. **Export Phase** ([src/lineage/export/](src/lineage/export/))
   - **MermaidGenerator**: Renders Mermaid diagram syntax with proper node shapes and colors
   - Applies styling based on `data_type` (shapes) and `data_level` (colors)

### Data Model ([src/lineage/models.py](src/lineage/models.py))

- **Node**: Represents a data object (table, view, source)
  - `id`: Unique identifier (e.g., "schema.table")
  - `label`: Display name
  - `data_type`: Determines shape (table→rectangle, view→stadium, etc.)
  - `data_level`: Determines color (source, staging, base, dimension, fact, export)
  - `select_from`: List of upstream node IDs (creates connections)

- **Connection**: Data flow between nodes
  - `from_id`, `to_id`: Node identifiers
  - `connection_type`: Arrow style (select_from→solid, connected_to→dashed)

### Configuration ([src/lineage/config.py](src/lineage/config.py))

Defines all visual styling:
- `NODE_SHAPES`: Maps data_type to Mermaid syntax (brackets, parentheses, etc.)
- `DATA_LEVEL_STYLES`: Maps data_level to CSS fill/stroke styles
- `CONNECTION_STYLES`: Maps connection_type to arrow styles

### CLI Structure ([src/lineage/cli.py](src/lineage/cli.py))

Four main commands implemented with Click:
1. `extract_from_sql`: Parse SQL files → YAML nodes
2. `generate_mermaid`: YAML/JSON → Mermaid diagram
3. `generate_legend_mermaid`: Create style reference diagram
4. `impute_missing_connecting_nodes`: Add missing nodes referenced in select_from

### SQL Parsing Details ([src/lineage/io/sql_parser.py](src/lineage/io/sql_parser.py))

- Uses sqlglot with Redshift dialect
- Extracts CREATE TABLE/VIEW statements
- Only processes schema-qualified objects (must have `schema.table` format)
- Automatically extracts lineage from SELECT statements via `sql_lineage_extractor.py`
- Stores extracted dependencies in `select_from` field

### Graph Operations ([src/lineage/graph/lineage_graph.py](src/lineage/graph/lineage_graph.py))

NetworkX-based operations for:
- **Filtering**: Focus on specific nodes with depth limits and direction (upstream/downstream/both)
- **Traversal**: BFS with configurable depth for finding related nodes
- **Analysis**: Cycle detection, path finding, DAG validation
- **Subgraphs**: Extract portions of the graph for focused visualization

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

## Common Gotchas

1. **Glob patterns must be quoted** when passed to shell: `"sql/**/*.sql"` not `sql/**/*.sql`
2. **Schema qualification is required**: Only objects with `schema.table` format are extracted from SQL
3. **Node IDs are sanitized** in Mermaid output (dots/dashes → underscores) but preserved in data
4. **YAML preserves comments** when using `ruamel.yaml` for imputation operations
5. **data_level can be None/null** during extraction, must be set before final visualization
