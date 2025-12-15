# Data Lineage Python Script

A Python CLI tool that generates Mermaid diagrams for data warehouse lineage visualization.

## Installation

Install dependencies using Poetry:

```bash
poetry install
```

## Usage

### Version Information

Check the tool version:

```bash
python cli.py --version
```

### Generate Lineage Diagram

Generate a Mermaid diagram to stdout:

```bash
python cli.py generate data_warehouse.json
```

Save the generated diagram to a file:

```bash
python cli.py generate data_warehouse.json -o lineage.mmd
```

Change the flow direction (LR=left-right, RL=right-left, TB=top-bottom, BT=bottom-top):

```bash
python cli.py generate data_warehouse.json -d TB
```

Focus on specific nodes using `--focus` (comma-separated for multiple), `--filter-direction` (upstream/downstream/both), `--depth` (max hops), or `--direct-only` (1 hop):

```bash
python cli.py generate data_warehouse.json --focus dim_customer
python cli.py generate data_warehouse.json --focus dim_customer,fact_orders --filter-direction upstream --depth 2
python cli.py generate data_warehouse.json --focus dim_customer --direct-only
```

### Generate Legend

Generate a legend showing all available node types, data levels, and connection styles:

```bash
python cli.py legend
```

Save the legend to a file:

```bash
python cli.py legend -o legend.mmd
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
      "data_type": "dlv1-source",
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
    data_type: dlv1-source
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
- `dlv1-source` → Cylinder: `[(label)]`
- `dlv2-source` → Cylinder: `[(label)]`
- `dlv2-resourcelink` → Hexagon: `{{label}}`
- `dlv1-manual-source` → Trapezoid: `[/label\]`

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
python cli.py generate tests/data/example_lineage.json -o output.mmd
```

### EAH Datamart Lineage

The complete lineage (as of 2025-11-06) of E@H datamart is available in [lineage_data/eah-lineage.yaml](lineage_data/eah-lineage.yaml). This file contains nodes representing the full data pipeline from source systems through staging, base, dimensions, and facts to export views.

Generate the complete EAH lineage diagram:

```bash
poetry run python cli.py generate lineage_data/eah-lineage.yaml -o lineage_data/eah-lineage.mmd
```

The resulting [eah-lineage.mmd](lineage_data/eah-lineage.mmd) can be viewed in any Mermaid-compatible viewer or IDE extension.
It is also possible to insert the mermaid code into lucidchart or draw.io.
For drawio, see how to do it here: <https://www.drawio.com/blog/mermaid-diagrams>

## Code Structure

- [metadata.py](metadata.py): Dataclasses for Node and Connection
- [styles.py](styles.py): Styling configuration (shapes, colors, connection styles)
- [parser.py](parser.py): File parser supporting JSON and YAML formats
- [graph.py](graph.py): LineageGraph class for graph operations (NetworkX-based)
- [generator.py](generator.py): MermaidGenerator class for rendering
- [cli.py](cli.py): Click-based CLI interface
- [tests/](tests/): Test suite with pytest

## Testing

Run the test suite using pytest:

```bash
poetry run pytest
```

Optionally add `-v` for verbose mode adding more output. Or add `--cov` to get a test coverage report.
