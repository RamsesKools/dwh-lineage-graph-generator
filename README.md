# Data Lineage Graph Generator

[![Check Pre-commit](https://github.com/RamsesKools/dwh-lineage-graph-generator/actions/workflows/check-pre-commit.yml/badge.svg)](https://github.com/RamsesKools/dwh-lineage-graph-generator/actions/workflows/check-pre-commit.yml)
[![CI](https://github.com/RamsesKools/dwh-lineage-graph-generator/actions/workflows/ci.yml/badge.svg)](https://github.com/RamsesKools/dwh-lineage-graph-generator/actions/workflows/ci.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![mypy](https://img.shields.io/badge/mypy-checked-blue)](https://mypy-lang.org/)
[![pytest](https://img.shields.io/badge/pytest-enabled-blue)](https://docs.pytest.org/)
[![coverage](https://img.shields.io/badge/coverage-90%25+-brightgreen)](https://github.com/RamsesKools/dwh-lineage-graph-generator)

A Python CLI tool build with click that generates Mermaid diagrams for data warehouse lineage visualization.
It extracts metadata from SQL files via the sqlglot library.
It stores this lineage information in YAML format and builds a graph of data dependencies using NetworkX, and renders visual diagrams showing how data flows through tables, views, and other data objects.

## Quick Start

### Installation

```bash
poetry install
```

### Basic Usage

```bash
# Generate a lineage diagram from YAML/JSON
lineage generate_mermaid data_warehouse.yaml -o lineage.mmd

# Extract nodes from SQL files
lineage extract_from_sql "sql/**/*.sql" -o lineage.yaml

# Generate a style legend
lineage generate_legend_mermaid -o legend.mmd

# Impute missing nodes referenced in select_from
lineage impute_missing_connecting_nodes lineage.yaml
```

## How to Use

The tool provides four main commands. Use `--help` with any command for detailed options:

```bash
lineage --help
lineage extract_from_sql --help
lineage generate_mermaid --help
lineage generate_legend_mermaid --help
lineage impute_missing_connecting_nodes --help
```

### Common Workflow

1. **Extract nodes from SQL files**:

   ```bash
   lineage extract_from_sql "sql/**/*.sql" -o lineage.yaml
   ```

2. **Impute missing nodes** (optional):

   ```bash
   lineage impute_missing_connecting_nodes lineage.yaml
   ```

3. **Generate diagram**:

   ```bash
   lineage generate_mermaid lineage.yaml -o lineage.mmd
   ```

### Filtering and Focus

Focus on specific nodes to visualize subsets of the lineage:

```bash
# Focus on a single node with all connections
lineage generate_mermaid data.yaml --focus dim_customer

# Focus on multiple nodes, upstream only, max 2 hops
lineage generate_mermaid data.yaml --focus dim_customer,fact_orders --filter-direction upstream --depth 2

# Show only direct connections (1 hop)
lineage generate_mermaid data.yaml --focus dim_customer --direct-only
```

## Lineage File Formats

The tool supports both JSON and YAML input formats. **YAML is recommended** for better readability and inline connection definitions.

### Quick Example (YAML)

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

For detailed format specifications, data types, data levels, and validation rules, see:

**→ [File Format Documentation](docs/file_format.md)**

## Development

This project uses Python 3.12+, Poetry for dependency management, Click for CLI, NetworkX for graph operations, and sqlglot for SQL parsing.

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov
```

For development setup, testing guide, common tasks, and implementation patterns, see:

**→ [Development Guide](docs/development.md)**

## Code Architecture

The tool follows a three-phase pipeline:

1. **Input Phase**: Parse SQL/YAML/JSON → Node and Connection objects
2. **Graph Phase**: Build NetworkX graph → Filter/traverse/analyze
3. **Export Phase**: Render Mermaid diagram syntax

For detailed architecture, design patterns, and extension points, see:

**→ [Code Architecture Documentation](docs/code_architecture.md)**

## File Organization

```text
src/lineage/
├── models.py          # Core dataclasses (Node, Connection)
├── config.py          # Styling configuration
├── cli.py             # Click-based CLI
├── io/                # Input/output (SQL, YAML, JSON parsers)
├── graph/             # Graph operations (NetworkX wrapper)
└── export/            # Output generation (Mermaid)
```

For complete file structure and module responsibilities, see:

**→ [File Organization Documentation](docs/file_organization.md)**

## Examples

### Basic Example

```bash
lineage generate_mermaid tests/data/example_lineage.json -o output.mmd
```

### Real-World Example

The complete lineage of the E@H datamart is available in `lineage_data/eah-lineage.yaml`:

```bash
lineage generate_mermaid lineage_data/eah-lineage.yaml -o lineage_data/eah-lineage.mmd
```

The resulting `.mmd` file can be viewed in any Mermaid-compatible viewer, IDE extension, or imported into Lucidchart/Draw.io. For Draw.io, see: <https://www.drawio.com/blog/mermaid-diagrams>

## Documentation

- **[File Format](docs/file_format.md)** - Lineage file format specification
- **[Development](docs/development.md)** - Development setup and patterns
- **[Architecture](docs/code_architecture.md)** - System architecture and design
- **[File Organization](docs/file_organization.md)** - Codebase structure
- **[Documentation Style](docs/doc_style.md)** - How docs are written and maintained

## License

See [LICENSE](LICENSE) file for details.


## Development backlog

- [x] First working version for creating lineage graph
  - [x] Create nodes based on create statements in SQL files.
  - [x] Create connections based on select from and joins and such in SQL.
  - [x] Generate Mermaid graph
  - [x] Allow filtering: downstream/upstream/focus on connecting nodes etc.
- [x] Add CI + Pre-commit
- [x] Increase pytest test coverage to 90% or higher.
- [x] Add mypy strict checking + fix type errors.
- [ ] Let's try adding parsing lineage data from a SQL database.
  - [ ] SQLite first? Because we can quite easily create a sqlite database for testing purposes.
- [ ] Remove JSON lineage data format.
- [ ] Let's think about adding an interactive front-end?
