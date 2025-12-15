"""
Tests for SQL lineage extraction functionality.
"""

import sqlglot
from sqlglot import exp

from src.lineage.io.sql_lineage_extractor import (
    extract_lineage_from_statement,
    _extract_cte_names,
    _extract_table_references,
    _build_table_name,
)


class TestExtractLineageFromStatement:
    """Test the main extract_lineage_from_statement function."""

    def test_simple_select(self):
        """Test extraction from a simple SELECT statement."""
        sql = "CREATE VIEW my_view AS SELECT * FROM schema1.table1"
        parsed = sqlglot.parse_one(sql, dialect="redshift")
        result = extract_lineage_from_statement(parsed)
        assert result == ["schema1.table1"]

    def test_multiple_tables_with_join(self):
        """Test extraction from a query with multiple tables and JOINs."""
        sql = """
        CREATE VIEW my_view AS
        SELECT *
        FROM schema1.table1
        JOIN schema2.table2 ON table1.id = table2.id
        JOIN schema3.table3 ON table2.id = table3.id
        """
        parsed = sqlglot.parse_one(sql, dialect="redshift")
        result = extract_lineage_from_statement(parsed)
        assert result == ["schema1.table1", "schema2.table2", "schema3.table3"]

    def test_subquery(self):
        """Test extraction from a query with subqueries."""
        sql = """
        CREATE VIEW my_view AS
        SELECT *
        FROM schema1.table1
        WHERE id IN (SELECT id FROM schema2.table2)
        """
        parsed = sqlglot.parse_one(sql, dialect="redshift")
        result = extract_lineage_from_statement(parsed)
        assert result == ["schema1.table1", "schema2.table2"]

    def test_cte_filtering(self):
        """Test that CTEs are filtered out from lineage."""
        sql = """
        CREATE VIEW my_view AS
        WITH temp_cte AS (
            SELECT * FROM schema1.source_table
        )
        SELECT * FROM temp_cte
        """
        parsed = sqlglot.parse_one(sql, dialect="redshift")
        result = extract_lineage_from_statement(parsed)
        # Should only include external source, not the CTE
        assert result == ["schema1.source_table"]

    def test_multiple_ctes(self):
        """Test handling of multiple CTEs."""
        sql = """
        CREATE VIEW my_view AS
        WITH
            cte1 AS (SELECT * FROM schema1.table1),
            cte2 AS (SELECT * FROM schema2.table2 JOIN cte1 ON table2.id = cte1.id)
        SELECT * FROM cte2
        """
        parsed = sqlglot.parse_one(sql, dialect="redshift")
        result = extract_lineage_from_statement(parsed)
        # Should include both external sources, but not the CTEs
        assert result == ["schema1.table1", "schema2.table2"]

    def test_nested_subqueries(self):
        """Test extraction from nested subqueries."""
        sql = """
        CREATE VIEW my_view AS
        SELECT *
        FROM (
            SELECT *
            FROM (
                SELECT * FROM schema1.table1
            ) AS sub1
            JOIN schema2.table2 ON sub1.id = table2.id
        ) AS sub2
        """
        parsed = sqlglot.parse_one(sql, dialect="redshift")
        result = extract_lineage_from_statement(parsed)
        assert result == ["schema1.table1", "schema2.table2"]

    def test_unqualified_names_excluded(self):
        """Test that unqualified table names are excluded."""
        sql = """
        CREATE VIEW my_view AS
        SELECT * FROM schema1.table1
        JOIN unqualified_table ON table1.id = unqualified_table.id
        """
        parsed = sqlglot.parse_one(sql, dialect="redshift")
        result = extract_lineage_from_statement(parsed)
        # Should only include schema-qualified name
        assert result == ["schema1.table1"]

    def test_create_table_as_select(self):
        """Test extraction from CREATE TABLE AS SELECT."""
        sql = """
        CREATE TABLE schema1.new_table AS
        SELECT * FROM schema2.source_table
        """
        parsed = sqlglot.parse_one(sql, dialect="redshift")
        result = extract_lineage_from_statement(parsed)
        assert result == ["schema2.source_table"]

    def test_union_queries(self):
        """Test extraction from UNION queries."""
        sql = """
        CREATE VIEW my_view AS
        SELECT * FROM schema1.table1
        UNION ALL
        SELECT * FROM schema2.table2
        """
        parsed = sqlglot.parse_one(sql, dialect="redshift")
        result = extract_lineage_from_statement(parsed)
        assert result == ["schema1.table1", "schema2.table2"]

    def test_empty_result(self):
        """Test that queries without table references return empty list."""
        sql = "CREATE VIEW my_view AS SELECT 1 AS constant"
        parsed = sqlglot.parse_one(sql, dialect="redshift")
        result = extract_lineage_from_statement(parsed)
        assert result == []

    def test_duplicate_references(self):
        """Test that duplicate table references are deduplicated."""
        sql = """
        CREATE VIEW my_view AS
        SELECT *
        FROM schema1.table1 AS t1
        JOIN schema1.table1 AS t2 ON t1.id = t2.parent_id
        """
        parsed = sqlglot.parse_one(sql, dialect="redshift")
        result = extract_lineage_from_statement(parsed)
        # Should only appear once
        assert result == ["schema1.table1"]

    def test_complex_real_world_query(self):
        """Test a complex real-world style query."""
        sql = """
        CREATE VIEW dwh.fact_sales AS
        WITH
            daily_sales AS (
                SELECT
                    date,
                    product_id,
                    SUM(amount) as total_amount
                FROM raw.sales_transactions
                GROUP BY date, product_id
            ),
            enriched_sales AS (
                SELECT
                    ds.*,
                    p.product_name,
                    c.category_name
                FROM daily_sales ds
                JOIN dwh.dim_product p ON ds.product_id = p.id
                JOIN dwh.dim_category c ON p.category_id = c.id
            )
        SELECT
            es.*,
            t.time_period
        FROM enriched_sales es
        JOIN dwh.dim_time t ON es.date = t.date
        """
        parsed = sqlglot.parse_one(sql, dialect="redshift")
        result = extract_lineage_from_statement(parsed)
        # Should include all external tables, not the CTEs
        assert result == [
            "dwh.dim_category",
            "dwh.dim_product",
            "dwh.dim_time",
            "raw.sales_transactions",
        ]


class TestExtractCteNames:
    """Test the _extract_cte_names helper function."""

    def test_single_cte(self):
        """Test extraction of a single CTE name."""
        sql = """
        WITH temp AS (SELECT * FROM schema1.table1)
        SELECT * FROM temp
        """
        parsed = sqlglot.parse_one(sql, dialect="redshift")
        result = _extract_cte_names(parsed)
        assert result == {"temp"}

    def test_multiple_ctes(self):
        """Test extraction of multiple CTE names."""
        sql = """
        WITH
            cte1 AS (SELECT * FROM schema1.table1),
            cte2 AS (SELECT * FROM schema2.table2),
            cte3 AS (SELECT * FROM cte1 JOIN cte2)
        SELECT * FROM cte3
        """
        parsed = sqlglot.parse_one(sql, dialect="redshift")
        result = _extract_cte_names(parsed)
        assert result == {"cte1", "cte2", "cte3"}

    def test_no_ctes(self):
        """Test query without CTEs."""
        sql = "SELECT * FROM schema1.table1"
        parsed = sqlglot.parse_one(sql, dialect="redshift")
        result = _extract_cte_names(parsed)
        assert result == set()


class TestExtractTableReferences:
    """Test the _extract_table_references helper function."""

    def test_single_table(self):
        """Test extraction from single table."""
        sql = "SELECT * FROM schema1.table1"
        parsed = sqlglot.parse_one(sql, dialect="redshift")
        result = _extract_table_references(parsed)
        assert result == {"schema1.table1"}

    def test_multiple_tables(self):
        """Test extraction from multiple tables."""
        sql = """
        SELECT *
        FROM schema1.table1
        JOIN schema2.table2
        """
        parsed = sqlglot.parse_one(sql, dialect="redshift")
        result = _extract_table_references(parsed)
        assert result == {"schema1.table1", "schema2.table2"}

    def test_includes_unqualified(self):
        """Test that unqualified names are included (filtering happens later)."""
        sql = "SELECT * FROM unqualified_table"
        parsed = sqlglot.parse_one(sql, dialect="redshift")
        result = _extract_table_references(parsed)
        assert result == {"unqualified_table"}


class TestBuildTableName:
    """Test the _build_table_name helper function."""

    def test_qualified_table(self):
        """Test building name for schema-qualified table."""
        sql = "SELECT * FROM schema1.table1"
        parsed = sqlglot.parse_one(sql, dialect="redshift")
        table = parsed.find(exp.Table)
        result = _build_table_name(table)
        assert result == "schema1.table1"

    def test_unqualified_table(self):
        """Test building name for unqualified table."""
        sql = "SELECT * FROM table1"
        parsed = sqlglot.parse_one(sql, dialect="redshift")
        table = parsed.find(exp.Table)
        result = _build_table_name(table)
        assert result == "table1"
