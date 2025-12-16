"""
Extract lineage (source table dependencies) from SQL statements.

This module provides functionality to extract table references from parsed SQL
statements using sqlglot. It identifies all tables that a query depends on,
including those in FROM clauses, JOINs, and subqueries.
"""

from sqlglot import exp


def extract_lineage_from_statement(statement: exp.Expression) -> list[str]:
    """
    Extract source table references from a SQL statement.

    This function traverses the SQL AST to find all table references in:
    - FROM clauses
    - JOIN clauses
    - Subqueries
    - CTEs (WITH clauses) - resolves through to find external dependencies

    Args:
        statement: A parsed sqlglot Expression (typically a CREATE statement)

    Returns:
        A sorted list of unique schema-qualified table names (e.g., ["schema.table"])
        Only includes schema-qualified names; unqualified references are ignored.

    Example:
        >>> import sqlglot
        >>> sql = "CREATE VIEW my_view AS SELECT * FROM schema1.table1 JOIN schema2.table2"
        >>> parsed = sqlglot.parse_one(sql)
        >>> extract_lineage_from_statement(parsed)
        ['schema1.table1', 'schema2.table2']
    """
    # First, extract all CTEs to identify internal vs external references
    cte_names = _extract_cte_names(statement)

    # Get the target table name (the table/view being created)
    target_table = _extract_target_table(statement)

    # Extract all table references
    table_refs = _extract_table_references(statement)

    # Filter out CTE references (internal), unqualified names, and the target table
    external_refs = {
        ref
        for ref in table_refs
        if ref not in cte_names
        and "." in ref  # Only schema-qualified names
        and ref != target_table  # Exclude the table being created
    }

    # Return sorted list for deterministic output
    return sorted(external_refs)


def _extract_target_table(statement: exp.Expression) -> str | None:
    """
    Extract the target table name from a CREATE statement.

    For CREATE TABLE/VIEW statements, this returns the table/view being created,
    so we can exclude it from the lineage dependencies.

    Args:
        statement: A parsed sqlglot Expression

    Returns:
        The target table name (schema-qualified if available), or None
    """
    # Check if this is a CREATE statement
    if isinstance(statement, exp.Create):
        # Get the table being created
        if statement.this:
            # Handle Schema node (CREATE TABLE with column definitions)
            if isinstance(statement.this, exp.Schema):
                if statement.this.this and isinstance(statement.this.this, exp.Table):
                    return _build_table_name(statement.this.this)
            # Handle Table node directly (CREATE VIEW or CREATE TABLE AS SELECT)
            elif isinstance(statement.this, exp.Table):
                return _build_table_name(statement.this)

    return None


def _extract_cte_names(statement: exp.Expression) -> set[str]:
    """
    Extract CTE (Common Table Expression) names from a statement.

    CTEs are defined in WITH clauses and are internal to the query.
    We need to identify them so we can filter them out from external dependencies.

    Args:
        statement: A parsed sqlglot Expression

    Returns:
        Set of CTE names (aliases)
    """
    cte_names = set()

    # Find all CTE definitions
    for cte in statement.find_all(exp.CTE):
        # The CTE alias is the name of the temporary table
        if cte.alias:
            cte_names.add(cte.alias)

    return cte_names


def _extract_table_references(statement: exp.Expression) -> set[str]:
    """
    Extract all table references from a statement.

    This includes tables in FROM clauses, JOINs, and subqueries.

    Args:
        statement: A parsed sqlglot Expression

    Returns:
        Set of table references (may include both qualified and unqualified names)
    """
    table_refs = set()

    # Find all Table nodes in the AST
    for table in statement.find_all(exp.Table):
        # Build the fully qualified name
        table_name = _build_table_name(table)
        if table_name:
            table_refs.add(table_name)

    return table_refs


def _build_table_name(table: exp.Table) -> str | None:
    """
    Build a qualified table name from a Table expression.

    Args:
        table: A sqlglot Table expression

    Returns:
        Schema-qualified table name (e.g., "schema.table") or unqualified name,
        or None if the table name cannot be determined
    """
    # Get the catalog (database), schema, and table parts
    catalog = table.catalog if hasattr(table, "catalog") else None
    schema = table.db if hasattr(table, "db") else None
    name = table.name if hasattr(table, "name") else None

    if not name:
        return None

    # Build the qualified name based on available parts
    if schema and catalog:
        return f"{catalog}.{schema}.{name}"
    elif schema:
        return f"{schema}.{name}"
    else:
        # Return unqualified name (caller will filter it out if needed)
        return name
