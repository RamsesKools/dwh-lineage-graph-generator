"""Unit tests for extractor.yaml_writer module."""

from pathlib import Path

import pytest
from ruamel.yaml import YAML

from extractor.yaml_writer import write_nodes_to_yaml
from metadata import Node


class TestWriteNodesToYaml:
    """Tests for write_nodes_to_yaml function."""

    def test_write_nodes_with_placeholders(self, tmp_path):
        """Test writing nodes with None/empty fields output as unknown or empty list."""
        output_file = tmp_path / "output.yaml"
        nodes = [
            Node(
                id="schema1.table1",
                label="schema1.table1",
                data_type="table",
                data_level=None,
                select_from=[],
            ),
            Node(
                id="schema1.view1",
                label="schema1.view1",
                data_type="view",
                data_level=None,
                select_from=[],
            ),
        ]

        write_nodes_to_yaml(nodes, output_file)

        with output_file.open("r") as f:
            data = YAML().load(f)

        assert len(data["nodes"]) == 2
        assert data["nodes"][0]["id"] == "schema1.table1"
        assert data["nodes"][0]["data_level"] == "unknown"
        assert data["nodes"][0]["select_from"] == []
        assert data["nodes"][1]["id"] == "schema1.view1"
        assert data["nodes"][1]["data_type"] == "view"

    def test_preserve_populated_fields(self, tmp_path):
        """Test that populated data_level and select_from are preserved."""
        output_file = tmp_path / "output.yaml"
        nodes = [
            Node(
                id="schema1.table1",
                label="schema1.table1",
                data_type="table",
                data_level="dimension",
                select_from=["schema1.source1", "schema1.source2"],
            )
        ]

        write_nodes_to_yaml(nodes, output_file)

        with output_file.open("r") as f:
            data = YAML().load(f)

        assert data["nodes"][0]["data_level"] == "dimension"
        assert data["nodes"][0]["select_from"] == [
            "schema1.source1",
            "schema1.source2",
        ]

    def test_write_empty_node_list(self, tmp_path):
        """Test writing empty list of nodes."""
        output_file = tmp_path / "output.yaml"
        nodes = []

        write_nodes_to_yaml(nodes, output_file)

        with output_file.open("r") as f:
            data = YAML().load(f)

        assert data["nodes"] == []

    def test_preserve_node_order(self, tmp_path):
        """Test that node order is preserved in YAML output."""
        output_file = tmp_path / "output.yaml"
        nodes = [
            Node(
                id="schema1.zulu",
                label="schema1.zulu",
                data_type="table",
                data_level=None,
                select_from=[],
            ),
            Node(
                id="schema1.alpha",
                label="schema1.alpha",
                data_type="view",
                data_level=None,
                select_from=[],
            ),
        ]

        write_nodes_to_yaml(nodes, output_file)

        with output_file.open("r") as f:
            data = YAML().load(f)

        # Verify order is preserved (not sorted)
        assert data["nodes"][0]["id"] == "schema1.zulu"
        assert data["nodes"][1]["id"] == "schema1.alpha"

    def test_append_mode_adds_new_nodes(self, tmp_path):
        """Test append mode adds only new nodes to end of file."""
        output_file = tmp_path / "output.yaml"

        # Write initial nodes
        initial_nodes = [
            Node(
                id="schema1.table1",
                label="schema1.table1",
                data_type="table",
                data_level=None,
                select_from=[],
            ),
            Node(
                id="schema1.table2",
                label="schema1.table2",
                data_type="table",
                data_level=None,
                select_from=[],
            ),
        ]
        write_nodes_to_yaml(initial_nodes, output_file)

        # Append new nodes (one duplicate, one new)
        new_nodes = [
            Node(
                id="schema1.table2",
                label="schema1.table2",
                data_type="table",
                data_level=None,
                select_from=[],
            ),
            Node(
                id="schema1.table3",
                label="schema1.table3",
                data_type="view",
                data_level=None,
                select_from=[],
            ),
        ]
        write_nodes_to_yaml(
            new_nodes, output_file, update_nodes=False, prevent_file_overwrite=False
        )

        # Verify result
        with output_file.open("r") as f:
            data = YAML().load(f)

        assert len(data["nodes"]) == 3
        # Order should be preserved: table1, table2 (original), then table3 (appended)
        assert data["nodes"][0]["id"] == "schema1.table1"
        assert data["nodes"][1]["id"] == "schema1.table2"
        assert data["nodes"][2]["id"] == "schema1.table3"

    def test_append_mode_preserves_existing_values(self, tmp_path):
        """Test append mode keeps existing node values (doesn't override)."""
        output_file = tmp_path / "output.yaml"

        # Write initial node with populated fields
        initial_nodes = [
            Node(
                id="schema1.table1",
                label="Original Label",
                data_type="table",
                data_level="dimension",
                select_from=["schema1.source1"],
            ),
        ]
        write_nodes_to_yaml(initial_nodes, output_file)

        # Try to append same node with different values
        new_nodes = [
            Node(
                id="schema1.table1",
                label="New Label",
                data_type="view",
                data_level="fact",
                select_from=["schema1.source2"],
            ),
        ]
        write_nodes_to_yaml(
            new_nodes, output_file, update_nodes=False, prevent_file_overwrite=False
        )

        # Verify original values are preserved
        with output_file.open("r") as f:
            data = YAML().load(f)

        assert len(data["nodes"]) == 1
        assert data["nodes"][0]["id"] == "schema1.table1"
        assert data["nodes"][0]["label"] == "Original Label"
        assert data["nodes"][0]["data_type"] == "table"
        assert data["nodes"][0]["data_level"] == "dimension"
        assert data["nodes"][0]["select_from"] == ["schema1.source1"]

    def test_append_mode_with_nonexistent_file(self, tmp_path):
        """Test append mode works like normal write when file doesn't exist."""
        output_file = tmp_path / "output.yaml"

        nodes = [
            Node(
                id="schema1.table1",
                label="schema1.table1",
                data_type="table",
                data_level=None,
                select_from=[],
            ),
        ]
        write_nodes_to_yaml(
            nodes, output_file, update_nodes=False, prevent_file_overwrite=False
        )

        with output_file.open("r") as f:
            data = YAML().load(f)

        assert len(data["nodes"]) == 1
        assert data["nodes"][0]["id"] == "schema1.table1"

    def test_append_mode_preserves_comments(self, tmp_path):
        """Test append mode preserves comments in existing file."""
        output_file = tmp_path / "output.yaml"

        # Write initial file with comments
        initial_content = """# This is a comment at the top
nodes:
- id: schema1.table1
  label: schema1.table1
  data_type: table
  data_level: dimension  # inline comment
  select_from: ???
  # Another comment
- id: schema1.table2
  label: schema1.table2
  data_type: view
  data_level: ???
  select_from: ???
# Final comment
"""
        output_file.write_text(initial_content)

        # Append new node
        new_nodes = [
            Node(
                id="schema1.table3",
                label="schema1.table3",
                data_type="table",
                data_level=None,
                select_from=[],
            ),
        ]
        write_nodes_to_yaml(
            new_nodes, output_file, update_nodes=False, prevent_file_overwrite=False
        )

        # Read the entire file content
        content = output_file.read_text()

        # Verify comments are preserved
        assert "# This is a comment at the top" in content
        assert "# inline comment" in content
        assert "# Another comment" in content
        assert "# Final comment" in content

        # Verify new node was appended
        assert "schema1.table3" in content

        # Verify nodes are still parseable
        with output_file.open("r") as f:
            data = YAML().load(f)
        assert len(data["nodes"]) == 3
