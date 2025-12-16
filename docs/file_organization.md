# File Organization

This document describes the directory structure and organization principles of the codebase.

## Directory Structure

```text
dwh-lineage-graph-generator/
├── src/lineage/              # Main source code
├── tests/                    # Test suite
├── docs/                     # Documentation
├── pyproject.toml            # Poetry configuration
└── README.md                 # Project overview
```

## Source Code (`src/lineage/`)

```text
src/lineage/
├── models.py                 # Core data structures shared across all modules
├── config.py                 # Styling configuration (single source of truth)
├── cli.py                    # CLI commands and orchestration
├── io/                       # Input/output operations
├── graph/                    # Graph operations (NetworkX wrapper)
└── export/                   # Output generation
```

### Directory Responsibilities

| Directory | Purpose | Key Dependencies |
|-----------|---------|------------------|
| `src/lineage/` | Core package with shared data structures | External libraries only |
| `src/lineage/io/` | Parse SQL/YAML/JSON files into Node/Connection objects | `models`, `config` |
| `src/lineage/graph/` | Graph traversal, filtering, analysis using NetworkX | `models`, NetworkX |
| `src/lineage/export/` | Render diagrams (currently Mermaid) | `models`, `config` |
| `tests/` | Unit and integration tests | `src/lineage/`, pytest |
| `docs/` | Project documentation | None |

### Core Modules

- **models.py**: Immutable dataclasses (`Node`, `Connection`) that serve as the interface between pipeline phases
- **config.py**: All visual styling configuration in one place to maintain single source of truth
- **cli.py**: Click-based CLI that orchestrates the three-phase pipeline (input → graph → export)

## Tests (`tests/`)

### Test Organization

- **Naming convention**: `test_<module>.py` matches source files in `src/lineage/<module>.py`
- **Unit tests**: Test individual functions/classes in isolation
- **Integration tests**: Test CLI commands end-to-end (see `test_cli_integration.py`)
- **Fixtures**: Shared test data in `tests/data/` (input files and expected outputs)

### Test Data

Test fixtures include:

- Input files (JSON, YAML, SQL) for parser testing
- Expected output files (`.mmd`) for comparison
- Various CREATE statement formats to validate SQL parsing

## Documentation (`docs/`)

Our documentation follows a "write once" principle:

- **README.md**: Quick start and overview with links to detailed docs
- **docs/**: In-depth documentation for concepts not clear from code alone

Documentation guidelines:

- Only document conventions, design decisions, and non-obvious patterns
- Don't duplicate information available in docstrings
- Don't list files or structure that changes frequently
- Focus on: conventions, way of working, how-tos, guides, explanations, architectural decisions

Current docs:

- `file_format.md`: Lineage file format specification
- `development.md`: Development setup, testing, patterns, coding style
- `code_architecture.md`: High-level design and extension points
- `file_organization.md`: This file

## Naming Conventions

- **Source files**: Snake case (`lineage_graph.py`)
- **Test files**: `test_<module>.py` matching the source module
- **Data files**: Descriptive names (`example_lineage.yaml`, `example_focus_upstream.mmd`)
- **Documentation**: Lowercase with underscores (`file_format.md`)

## Dependency Flow

```text
cli.py
  ├─→ io/        (parsers)  ──→ models
  ├─→ graph/     (analysis) ──→ models
  └─→ export/    (render)   ──→ models, config

models  ←─  Used by all modules
config  ←─  Used by export, cli
```

This maintains clear separation of concerns and prevents circular dependencies.

## Entry Points

**CLI entry point** (defined in `pyproject.toml`):

```toml
[tool.poetry.scripts]
lineage = "lineage.cli:cli"
```

**Direct execution**:

```bash
python src/lineage/cli.py <command>
```

## Adding New Components

See [Development Guide](development.md) for details on:

- Adding new modules
- Adding new CLI commands
- Adding test fixtures
- Code style and import conventions
