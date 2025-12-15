"""Unit tests for extractor.sql_parser module."""

from lineage.io.sql_parser import (
    extract_node_from_create,
    extract_nodes_from_sql_files,
    parse_sql_file,
)
from lineage.models import Node


class TestExtractNodeFromCreate:
    """Tests for extract_node_from_create function."""

    def test_extract_view_node(self):
        """Test extracting node from CREATE VIEW statement."""
        import sqlglot

        sql = "CREATE VIEW schema_name.view_name AS SELECT * FROM schema1.table1"
        statements = sqlglot.parse(sql, read="redshift")
        statement = statements[0]

        node = extract_node_from_create(statement)

        assert node is not None
        assert node.id == "schema_name.view_name"
        assert node.label == "schema_name.view_name"
        assert node.data_type == "view"
        assert node.data_level == "unknown"
        assert node.select_from == ["schema1.table1"]

    def test_extract_table_node(self):
        """Test extracting node from CREATE TABLE statement."""
        import sqlglot

        sql = "CREATE TABLE schema_name.table_name (id INT, name VARCHAR)"
        statements = sqlglot.parse(sql, read="redshift")
        statement = statements[0]

        node = extract_node_from_create(statement)

        assert node is not None
        assert node.id == "schema_name.table_name"
        assert node.label == "schema_name.table_name"
        assert node.data_type == "table"
        assert node.data_level == "unknown"
        assert node.select_from == []

    def test_extract_ctas_node(self):
        """Test extracting node from CREATE TABLE AS SELECT."""
        import sqlglot

        sql = "CREATE TABLE schema_name.new_table AS SELECT * FROM schema2.other_table"
        statements = sqlglot.parse(sql, read="redshift")
        statement = statements[0]

        node = extract_node_from_create(statement)

        assert node is not None
        assert node.id == "schema_name.new_table"
        assert node.data_type == "table"
        assert node.select_from == ["schema2.other_table"]

    def test_ignore_non_table_view(self):
        """Test that non-TABLE/VIEW creates are ignored."""
        import sqlglot

        sql = "CREATE INDEX idx_name ON schema_name.table_name (col1)"
        statements = sqlglot.parse(sql, read="redshift")
        statement = statements[0]

        node = extract_node_from_create(statement)

        assert node is None

    def test_ignore_unqualified_name(self):
        """Test that objects without schema qualification are ignored."""
        import sqlglot

        sql = "CREATE TABLE table_name (id INT)"
        statements = sqlglot.parse(sql, read="redshift")
        statement = statements[0]

        node = extract_node_from_create(statement)

        assert node is None

    def test_extract_with_complex_view(self):
        """Test extracting from view with complex SQL (CTEs, joins)."""
        import sqlglot

        sql = """
        CREATE VIEW schema.complex_view AS
        WITH cte AS (
            SELECT * FROM schema.table1
        )
        SELECT c.*, t2.col
        FROM cte c
        JOIN schema.table2 t2 ON c.id = t2.id
        """
        statements = sqlglot.parse(sql, read="redshift")
        statement = statements[0]

        node = extract_node_from_create(statement)

        assert node is not None
        assert node.id == "schema.complex_view"
        assert node.data_type == "view"
        assert node.select_from == ["schema.table1", "schema.table2"]


class TestParseSqlFile:
    """Tests for parse_sql_file function."""

    def test_parse_single_statement(self, tmp_path):
        """Test parsing file with single CREATE statement."""
        sql_file = tmp_path / "single.sql"
        sql_file.write_text("CREATE VIEW schema1.view1 AS SELECT * FROM source_table")

        nodes = parse_sql_file(sql_file)

        assert len(nodes) == 1
        assert nodes[0].id == "schema1.view1"
        assert nodes[0].data_type == "view"

    def test_parse_multiple_statements(self, tmp_path):
        """Test parsing file with multiple CREATE statements."""
        sql_file = tmp_path / "multiple.sql"
        sql_file.write_text(
            """
            CREATE VIEW schema1.view1 AS SELECT * FROM t1;
            CREATE TABLE schema1.table1 (id INT);
            CREATE VIEW schema2.view2 AS SELECT * FROM t2;
            """
        )

        nodes = parse_sql_file(sql_file)

        assert len(nodes) == 3
        assert nodes[0].id == "schema1.view1"
        assert nodes[0].data_type == "view"
        assert nodes[1].id == "schema1.table1"
        assert nodes[1].data_type == "table"
        assert nodes[2].id == "schema2.view2"
        assert nodes[2].data_type == "view"

    def test_parse_mixed_statements(self, tmp_path):
        """Test parsing file with CREATE and non-CREATE statements."""
        sql_file = tmp_path / "mixed.sql"
        sql_file.write_text(
            """
            -- Comment
            CREATE VIEW schema1.view1 AS SELECT * FROM t1;

            INSERT INTO schema1.table1 VALUES (1);

            CREATE TABLE schema1.table2 (id INT);

            DELETE FROM schema1.table1 WHERE id = 1;
            """
        )

        nodes = parse_sql_file(sql_file)

        # Only CREATE TABLE/VIEW should be extracted
        assert len(nodes) == 2
        assert nodes[0].id == "schema1.view1"
        assert nodes[1].id == "schema1.table2"

    def test_parse_file_with_unqualified_names(self, tmp_path):
        """Test that unqualified objects are filtered out."""
        sql_file = tmp_path / "unqualified.sql"
        sql_file.write_text(
            """
            CREATE VIEW view1 AS SELECT * FROM t1;
            CREATE TABLE schema1.table1 (id INT);
            CREATE VIEW view2 AS SELECT * FROM t2;
            """
        )

        nodes = parse_sql_file(sql_file)

        # Only schema-qualified object should be extracted
        assert len(nodes) == 1
        assert nodes[0].id == "schema1.table1"

    def test_parse_empty_file(self, tmp_path):
        """Test parsing empty SQL file."""
        sql_file = tmp_path / "empty.sql"
        sql_file.write_text("")

        nodes = parse_sql_file(sql_file)

        assert len(nodes) == 0

    def test_parse_file_with_only_comments(self, tmp_path):
        """Test parsing file with only comments."""
        sql_file = tmp_path / "comments.sql"
        sql_file.write_text(
            """
            -- This is a comment
            /* Multi-line
               comment */
            """
        )

        nodes = parse_sql_file(sql_file)

        assert len(nodes) == 0


class TestExtractNodesFromSqlFiles:
    """Tests for extract_nodes_from_sql_files function."""

    def test_extract_from_single_file(self, tmp_path):
        """Test extracting from single SQL file."""
        sql_file = tmp_path / "test.sql"
        sql_file.write_text(
            """
            CREATE VIEW schema1.view1 AS SELECT * FROM t1;
            CREATE TABLE schema1.table1 (id INT);
            """
        )

        pattern = str(sql_file)
        nodes = extract_nodes_from_sql_files(pattern)

        assert len(nodes) == 2
        assert nodes[0].id == "schema1.table1"  # Sorted alphabetically
        assert nodes[1].id == "schema1.view1"

    def test_extract_from_multiple_files(self, tmp_path):
        """Test extracting from multiple SQL files using glob pattern."""
        # Create multiple SQL files
        (tmp_path / "file1.sql").write_text(
            "CREATE VIEW schema1.view1 AS SELECT * FROM t1"
        )
        (tmp_path / "file2.sql").write_text("CREATE TABLE schema1.table1 (id INT)")
        (tmp_path / "file3.sql").write_text(
            "CREATE VIEW schema2.view2 AS SELECT * FROM t2"
        )

        pattern = str(tmp_path / "*.sql")
        nodes = extract_nodes_from_sql_files(pattern)

        assert len(nodes) == 3
        # Should be sorted by id
        assert nodes[0].id == "schema1.table1"
        assert nodes[1].id == "schema1.view1"
        assert nodes[2].id == "schema2.view2"

    def test_extract_with_recursive_glob(self, tmp_path):
        """Test extracting with recursive glob pattern."""
        # Create nested directory structure
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        (tmp_path / "root.sql").write_text(
            "CREATE VIEW schema1.root_view AS SELECT * FROM t1"
        )
        (subdir / "nested.sql").write_text("CREATE TABLE schema1.nested_table (id INT)")

        pattern = str(tmp_path / "**/*.sql")
        nodes = extract_nodes_from_sql_files(pattern)

        assert len(nodes) == 2
        ids = [node.id for node in nodes]
        assert "schema1.root_view" in ids
        assert "schema1.nested_table" in ids

    def test_extract_deduplication(self, tmp_path):
        """Test that duplicate node IDs are deduplicated (last seen wins)."""
        (tmp_path / "file1.sql").write_text(
            "CREATE VIEW schema1.view1 AS SELECT col1 FROM t1"
        )
        (tmp_path / "file2.sql").write_text(
            "CREATE VIEW schema1.view1 AS SELECT col2 FROM t2"
        )

        pattern = str(tmp_path / "*.sql")
        nodes = extract_nodes_from_sql_files(pattern)

        # Should have only one node (deduplicated)
        assert len(nodes) == 1
        assert nodes[0].id == "schema1.view1"

    def test_extract_with_no_matches(self, tmp_path):
        """Test extracting with pattern that matches no files."""
        pattern = str(tmp_path / "nonexistent*.sql")
        nodes = extract_nodes_from_sql_files(pattern)

        assert len(nodes) == 0

    def test_extract_sorted_output(self, tmp_path):
        """Test that output is sorted alphabetically by node ID."""
        sql_file = tmp_path / "test.sql"
        sql_file.write_text(
            """
            CREATE VIEW schema1.zulu AS SELECT * FROM t1;
            CREATE TABLE schema1.alpha (id INT);
            CREATE VIEW schema1.bravo AS SELECT * FROM t2;
            CREATE TABLE schema2.charlie (id INT);
            """
        )

        pattern = str(sql_file)
        nodes = extract_nodes_from_sql_files(pattern)

        # Verify alphabetical order
        assert len(nodes) == 4
        assert nodes[0].id == "schema1.alpha"
        assert nodes[1].id == "schema1.bravo"
        assert nodes[2].id == "schema1.zulu"
        assert nodes[3].id == "schema2.charlie"

    def test_extract_node_structure(self, tmp_path):
        """Test that extracted nodes have correct structure."""
        sql_file = tmp_path / "test.sql"
        sql_file.write_text(
            "CREATE VIEW schema1.test_view AS SELECT * FROM schema2.source_table"
        )

        pattern = str(sql_file)
        nodes = extract_nodes_from_sql_files(pattern)

        assert len(nodes) == 1
        node = nodes[0]

        # Verify all Node fields
        assert isinstance(node, Node)
        assert node.id == "schema1.test_view"
        assert node.label == "schema1.test_view"
        assert node.data_type == "view"
        assert node.data_level == "unknown"
        assert node.select_from == ["schema2.source_table"]
