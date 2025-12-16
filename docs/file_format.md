# Lineage File Format

This document describes the JSON and YAML file formats used to define data warehouse lineage.

## Format Overview

The tool supports both JSON and YAML input formats. **YAML is recommended** for better readability and inline connection definitions using `select_from`.

### JSON Format

Requires explicit `nodes` and `connections` arrays:

```json
{
  "nodes": [
    {
      "id": "raw_customers",
      "label": "Raw Customers",
      "data_type": "external-source",
      "data_level": "source"
    }
  ],
  "connections": [
    {"from_id": "raw_customers", "to_id": "dim_customer"}
  ]
}
```

### YAML Format (Recommended)

Supports inline connection definitions:

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
      - raw_customers  # Creates connection: raw_customers → dim_customer
```

## Node Fields

### Required Fields

- **id** (string): Unique identifier
  - Example: `"raw_customers"` or `"schema.table_name"`
  - For SQL extraction, must use `schema.table` format

- **label** (string): Display name shown in diagram

### Optional Fields

- **data_type** (string): Determines node shape in diagram
  - Default: `"unknown"`
  - Available types: `table`, `view`, `external-source`, `external-resourcelink`, `manual-source`
  - Run `lineage generate_legend_mermaid` to see all shapes

- **data_level** (string): Determines node color in diagram
  - Default: `"unknown"`
  - Can be `null` during extraction, must be set before visualization
  - Available levels: `source`, `staging`, `base`, `dimension`, `fact`, `export`
  - Run `lineage generate_legend_mermaid` to see all colors

- **select_from** (array of strings): List of upstream node IDs
  - Creates directed edges from listed nodes to this node
  - Example: `["source_table_1", "source_table_2"]`

- **connected_to** (array of strings): List of bidirectionally connected node IDs
  - Creates undirected edges between nodes
  - Less common than `select_from`

## Connection Definitions

### Inline (YAML only - Recommended)

```yaml
nodes:
  - id: target
    select_from: [source1, source2]  # Creates: source1 → target, source2 → target
```

### Explicit Array (JSON or YAML)

```json
{
  "connections": [
    {
      "from_id": "source1",
      "to_id": "target",
      "connection_type": "select_from"
    }
  ]
}
```

Connection types:

- `select_from`: Directed arrow (data flow)
- `connected_to`: Undirected line (relationship)

## SQL Extraction Behavior

When extracting from SQL files (`extract_from_sql` command):

- Only schema-qualified objects extracted: `schema.table`
- `data_type` is automatically set based on CREATE TABLE/VIEW
- `data_level` is set to `null` (must be filled in manually)
- `select_from` is automatically populated from SELECT statements

Example extracted node:

```yaml
nodes:
  - id: schema.table_name
    label: schema.table_name
    data_type: table
    data_level: null  # Fill this in
    select_from: []   # Or populated from SELECT
```

## Missing Node Imputation

The `impute_missing_connecting_nodes` command:

1. Scans all `select_from` fields for referenced node IDs
2. Adds placeholder nodes for any IDs not defined
3. Sets `data_type` and `data_level` to `null` (must be filled in manually)

Example:

```yaml
# Before
nodes:
  - id: dim_customer
    select_from:
      - raw_customers  # This node doesn't exist!

# After imputation
nodes:
  - id: dim_customer
    select_from:
      - raw_customers
  - id: raw_customers  # Added automatically
    label: raw_customers
    data_type: null    # Fill in manually
    data_level: null   # Fill in manually
    select_from: []
```

## Validation Rules

1. **Node IDs must be unique** - Duplicates will override (last wins)
2. **Schema qualification for SQL extraction** - Only `schema.table` format extracted
3. **Referenced nodes must exist** - Or use `impute_missing_connecting_nodes`
4. **data_level required for visualization** - Can be null during extraction
5. **Circular references allowed** - Tool can detect and display cycles

## Examples

See `tests/data/` for example lineage files:

- `example_lineage.json` - Basic JSON format
- `example_lineage.yaml` - Basic YAML format with inline connections
- `test_extract.sql` - SQL file for extraction testing
