"""Extract lineage nodes from SQL files."""

from glob import glob as glob_module
from pathlib import Path

import sqlglot
from sqlglot import exp

from lineage.models import Node


def extract_nodes_from_sql_files(pattern: str) -> list[Node]:
    """Extract nodes from SQL files matching glob pattern.

    Args:
        pattern: Glob pattern for SQL files (e.g., "sql/**/*.sql")

    Returns:
        List of Node objects with empty select_from and None data_level
    """
    nodes: dict[str, Node] = {}  # Use dict to deduplicate by id

    # Find all matching SQL files
    sql_files = glob_module(pattern, recursive=True)

    for file_path in sql_files:
        file_nodes = parse_sql_file(Path(file_path))
        for node in file_nodes:
            # Deduplicate: last seen wins
            nodes[node.id] = node

    # Sort by id for deterministic output
    return sorted(nodes.values(), key=lambda n: n.id)


def parse_sql_file(file_path: Path) -> list[Node]:
    """Parse single SQL file and extract CREATE statements.

    Args:
        file_path: Path to SQL file

    Returns:
        List of Node objects
    """
    nodes: list[Node] = []

    try:
        content = file_path.read_text()

        # Parse with Redshift dialect
        statements = sqlglot.parse(content, read="redshift")

        for statement in statements:
            if isinstance(statement, exp.Create):
                node = extract_node_from_create(statement)
                if node:
                    nodes.append(node)

    except Exception as e:
        print(f"Warning: Failed to parse {file_path}: {e}")

    return nodes


def extract_node_from_create(statement: exp.Create) -> Node | None:
    """Extract node info from CREATE statement.

    Args:
        statement: sqlglot CREATE statement

    Returns:
        Node object or None if not a table/view
    """
    # Only handle CREATE TABLE and CREATE VIEW
    if statement.kind not in ("TABLE", "VIEW"):
        return None

    # Extract schema and table name
    if not statement.this:
        return None

    # Handle different sqlglot node types
    table_obj = statement.this

    # Extract table name and schema
    if isinstance(table_obj, exp.Schema):
        # For CREATE TABLE with column definitions
        if not table_obj.this or not isinstance(table_obj.this, exp.Table):
            return None
        table_name = table_obj.this.name
        schema_name = table_obj.this.db
    elif isinstance(table_obj, exp.Table):
        # For CREATE VIEW or CREATE TABLE AS SELECT
        table_name = table_obj.name
        schema_name = table_obj.db
    else:
        return None

    # Only include schema-qualified objects
    if not schema_name or not table_name:
        return None

    # Build fully qualified ID
    node_id = f"{schema_name}.{table_name}"

    # Determine data type
    data_type = "view" if statement.kind == "VIEW" else "table"

    return Node(
        id=node_id,
        label=node_id,
        data_type=data_type,
        data_level=None,
        select_from=[],
    )
