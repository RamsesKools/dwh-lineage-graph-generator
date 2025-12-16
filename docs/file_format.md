# Lineage File Format

This document describes the JSON and YAML file formats used to define data warehouse lineage.

## Supported Formats

The tool supports both JSON and YAML input formats. YAML is recommended for better readability and inline connection definitions.

## JSON Format

The JSON format requires explicit `nodes` and `connections` arrays:

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

## YAML Format (Recommended)

YAML format supports inline connection definitions using `select_from`:

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

The `select_from` field creates connections from the listed nodes to the current node.

### Alternative: Bidirectional Connections

You can also use `connected_to` for bidirectional connections:

```yaml
nodes:
  - id: node_a
    label: Node A
    connected_to:
      - node_b  # Creates undirected connection
```

## Node Fields

### Required Fields

- **id** (string): Unique identifier for the node
  - Example: `"raw_customers"` or `"schema.table_name"`
  - For SQL extraction, format is `schema.table`

- **label** (string): Display name shown in the diagram
  - Example: `"Customer Dimension"`

### Optional Fields

- **data_type** (string): Determines the node shape in the diagram
  - Default: `"unknown"`
  - See [Data Types](#data-types-shapes) below

- **data_level** (string): Determines the node color in the diagram
  - Default: `"unknown"`
  - Can be `null` during extraction, must be set before visualization
  - See [Data Levels](#data-levels-colors) below

- **select_from** (array of strings): List of upstream node IDs
  - Creates directed edges from listed nodes to this node
  - Example: `["source_table_1", "source_table_2"]`

- **connected_to** (array of strings): List of bidirectionally connected node IDs
  - Creates undirected edges between nodes
  - Example: `["related_node"]`

## Data Types (Shapes)

The `data_type` field determines the shape of the node in the Mermaid diagram:

| Data Type | Shape | Mermaid Syntax | Visual |
|-----------|-------|----------------|--------|
| `table` | Rectangle | `[label]` | Standard database table |
| `view` | Stadium | `([label])` | Database view |
| `external-source` | Cylinder | `[(label)]` | External data source |
| `external-resourcelink` | Hexagon | `{{label}}` | External resource/API |
| `manual-source` | Trapezoid | `[/label\]` | Manually entered data |
| `unknown` | Rectangle | `[label]` | Default fallback |

## Data Levels (Colors)

The `data_level` field determines the color/fill of the node:

| Data Level | Color | Hex Code | Description |
|------------|-------|----------|-------------|
| `source` | Light blue | #e1f5ff | Raw data sources |
| `staging` | Light orange | #fff3e0 | Staging/landing zone |
| `base` | Light purple | #f3e5f5 | Base/foundation tables |
| `dimension` | Light green | #e8f5e9 | Dimension tables |
| `fact` | Light pink | #fce4ec | Fact tables |
| `export` | Light yellow | #fff9c4 | Export/presentation layer |
| `unknown` | White | #ffffff | Default fallback |

## Connection Types

Connections can be defined in two ways:

### 1. Inline (YAML only)

Using `select_from` or `connected_to` fields within nodes:

```yaml
nodes:
  - id: target
    select_from: [source1, source2]  # Directed: source1 → target, source2 → target
```

### 2. Explicit Connections Array

For JSON or when you need more control:

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

### Connection Types

| Type | Arrow Style | Description |
|------|-------------|-------------|
| `select_from` | `-->` | Solid directed arrow (data flow) |
| `connected_to` | `---` | Dashed undirected line (relationship) |

## Examples

### Example 1: Basic Lineage

```yaml
nodes:
  - id: customers_csv
    label: Customers CSV
    data_type: manual-source
    data_level: source

  - id: stg_customers
    label: Staging Customers
    data_type: table
    data_level: staging
    select_from:
      - customers_csv

  - id: dim_customer
    label: Customer Dimension
    data_type: table
    data_level: dimension
    select_from:
      - stg_customers
```

### Example 2: Complex Multi-Source

```yaml
nodes:
  - id: orders_api
    label: Orders API
    data_type: external-resourcelink
    data_level: source

  - id: customers_db
    label: Customers Database
    data_type: external-source
    data_level: source

  - id: fact_orders
    label: Orders Fact
    data_type: table
    data_level: fact
    select_from:
      - orders_api
      - dim_customer

  - id: dim_customer
    label: Customer Dimension
    data_type: table
    data_level: dimension
    select_from:
      - customers_db
```

### Example 3: Using Explicit Connections (JSON)

```json
{
  "nodes": [
    {"id": "src", "label": "Source", "data_type": "external-source", "data_level": "source"},
    {"id": "tgt", "label": "Target", "data_type": "table", "data_level": "dimension"}
  ],
  "connections": [
    {"from_id": "src", "to_id": "tgt", "connection_type": "select_from"}
  ]
}
```

## Null Values and Missing Nodes

### During SQL Extraction

When extracting nodes from SQL files, `data_level` is set to `null`:

```yaml
nodes:
  - id: schema.table_name
    label: schema.table_name
    data_type: table
    data_level: null  # Must be filled in manually
    select_from: []
```

### Missing Node Imputation

The `impute_missing_connecting_nodes` command adds placeholder nodes for any IDs referenced in `select_from` but not defined:

```yaml
# Before imputation
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
    data_type: null
    data_level: null
    select_from: []
```

## Validation Rules

1. **Node IDs must be unique** - Duplicate IDs will cause the last definition to override earlier ones
2. **Schema qualification for SQL** - Only `schema.table` format is extracted from SQL files
3. **Referenced nodes must exist** - Or use `impute_missing_connecting_nodes` to add them
4. **data_level required for visualization** - Can be null during extraction, but must be set before generating diagrams
5. **Circular references are allowed** - The tool can detect and display cycles
