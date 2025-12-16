"""Unit tests for extractor.yaml_writer module."""

import pytest
from ruamel.yaml import YAML

from lineage.io.yaml_writer import write_nodes_to_yaml
from lineage.models import Node


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
                select_from=[],
            ),
            Node(
                id="schema1.view1",
                label="schema1.view1",
                data_type="view",
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
        nodes: list[Node] = []

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
                select_from=[],
            ),
            Node(
                id="schema1.alpha",
                label="schema1.alpha",
                data_type="view",
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
                select_from=[],
            ),
            Node(
                id="schema1.table2",
                label="schema1.table2",
                data_type="table",
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
                select_from=[],
            ),
            Node(
                id="schema1.table3",
                label="schema1.table3",
                data_type="view",
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


class TestUpdateNodesMode:
    """Tests for update_nodes=True mode."""

    def test_update_mode_adds_data_level_to_existing_node(self, tmp_path):
        """Test update mode fills in null data_level field."""
        output_file = tmp_path / "output.yaml"

        # Manually create YAML with null data_level
        yaml_content = """nodes:
- id: schema1.table1
  label: schema1.table1
  data_type: table
  data_level: null
  select_from: []
"""
        output_file.write_text(yaml_content)

        # Update with populated data_level
        updated_nodes = [
            Node(
                id="schema1.table1",
                label="schema1.table1",
                data_type="table",
                data_level="dimension",
                select_from=[],
            )
        ]
        stats = write_nodes_to_yaml(updated_nodes, output_file, update_nodes=True)

        # Verify stats
        assert stats["nodes_updated"] == 1
        assert stats["nodes_added"] == 0

        # Verify data_level was updated
        with output_file.open("r") as f:
            data = YAML().load(f)

        assert data["nodes"][0]["data_level"] == "dimension"

    def test_update_mode_adds_data_type_to_existing_node(self, tmp_path):
        """Test update mode fills in null data_type field."""
        output_file = tmp_path / "output.yaml"

        # Manually create YAML with null data_type
        yaml_content = """nodes:
- id: schema1.table1
  label: schema1.table1
  data_type: null
  data_level: base
  select_from: []
"""
        output_file.write_text(yaml_content)

        # Update with populated data_type
        updated_nodes = [
            Node(
                id="schema1.table1",
                label="schema1.table1",
                data_type="table",
                data_level="base",
                select_from=[],
            )
        ]
        stats = write_nodes_to_yaml(updated_nodes, output_file, update_nodes=True)

        # Verify stats
        assert stats["nodes_updated"] == 1
        assert stats["nodes_added"] == 0

        # Verify data_type was updated
        with output_file.open("r") as f:
            data = YAML().load(f)

        assert data["nodes"][0]["data_type"] == "table"

    def test_update_mode_adds_connections(self, tmp_path):
        """Test update mode adds new connections to existing node."""
        output_file = tmp_path / "output.yaml"

        # Write initial node with one connection
        initial_nodes = [
            Node(
                id="schema1.table1",
                label="schema1.table1",
                data_type="table",
                data_level="dimension",
                select_from=["schema1.source1"],
            )
        ]
        write_nodes_to_yaml(initial_nodes, output_file)

        # Update with additional connection
        updated_nodes = [
            Node(
                id="schema1.table1",
                label="schema1.table1",
                data_type="table",
                data_level="dimension",
                select_from=["schema1.source1", "schema1.source2"],
            )
        ]
        stats = write_nodes_to_yaml(updated_nodes, output_file, update_nodes=True)

        # Verify stats
        assert stats["nodes_updated"] == 1
        assert stats["connections_added"] == 1

        # Verify connection was added
        with output_file.open("r") as f:
            data = YAML().load(f)

        assert set(data["nodes"][0]["select_from"]) == {
            "schema1.source1",
            "schema1.source2",
        }

    def test_update_mode_handles_null_existing_select_from(self, tmp_path):
        """Test update mode handles existing nodes with null select_from."""
        output_file = tmp_path / "output.yaml"

        # Manually create YAML with null select_from
        yaml_content = """nodes:
- id: schema1.table1
  label: schema1.table1
  data_type: table
  data_level: dimension
  select_from: null
"""
        output_file.write_text(yaml_content)

        # Update with connections
        updated_nodes = [
            Node(
                id="schema1.table1",
                label="schema1.table1",
                data_type="table",
                data_level="dimension",
                select_from=["schema1.source1"],
            )
        ]
        stats = write_nodes_to_yaml(updated_nodes, output_file, update_nodes=True)

        # Verify connection was added
        with output_file.open("r") as f:
            data = YAML().load(f)

        assert data["nodes"][0]["select_from"] == ["schema1.source1"]
        assert stats["connections_added"] == 1

    def test_update_mode_adds_new_nodes_and_updates_existing(self, tmp_path):
        """Test update mode can both add new nodes and update existing ones."""
        output_file = tmp_path / "output.yaml"

        # Manually create YAML with null data_level
        yaml_content = """nodes:
- id: schema1.table1
  label: schema1.table1
  data_type: table
  data_level: null
  select_from: []
"""
        output_file.write_text(yaml_content)

        # Update existing and add new
        updated_nodes = [
            Node(
                id="schema1.table1",
                label="schema1.table1",
                data_type="table",
                data_level="dimension",
                select_from=["schema1.source1"],
            ),
            Node(
                id="schema1.table2",
                label="schema1.table2",
                data_type="view",
                data_level="fact",
                select_from=[],
            ),
        ]
        stats = write_nodes_to_yaml(updated_nodes, output_file, update_nodes=True)

        # Verify stats
        assert stats["nodes_updated"] == 1
        assert stats["nodes_added"] == 1
        assert stats["connections_added"] == 1

        # Verify both nodes exist
        with output_file.open("r") as f:
            data = YAML().load(f)

        assert len(data["nodes"]) == 2
        assert data["nodes"][0]["data_level"] == "dimension"
        assert data["nodes"][0]["select_from"] == ["schema1.source1"]
        assert data["nodes"][1]["id"] == "schema1.table2"

    def test_update_mode_does_not_overwrite_existing_values(self, tmp_path):
        """Test update mode preserves existing non-null values."""
        output_file = tmp_path / "output.yaml"

        # Write initial node with populated fields
        initial_nodes = [
            Node(
                id="schema1.table1",
                label="schema1.table1",
                data_type="table",
                data_level="dimension",
                select_from=["schema1.source1"],
            )
        ]
        write_nodes_to_yaml(initial_nodes, output_file)

        # Try to update with different values
        updated_nodes = [
            Node(
                id="schema1.table1",
                label="schema1.table1",
                data_type="view",  # Different
                data_level="fact",  # Different
                select_from=["schema1.source1"],  # Same
            )
        ]
        stats = write_nodes_to_yaml(updated_nodes, output_file, update_nodes=True)

        # Verify original values are preserved
        with output_file.open("r") as f:
            data = YAML().load(f)

        assert stats["nodes_updated"] == 0  # Nothing updated
        assert data["nodes"][0]["data_type"] == "table"  # Original
        assert data["nodes"][0]["data_level"] == "dimension"  # Original

    def test_prevent_file_overwrite_raises_error(self, tmp_path):
        """Test prevent_file_overwrite=True raises error when file exists."""
        output_file = tmp_path / "output.yaml"

        # Write initial file
        initial_nodes = [
            Node(
                id="schema1.table1",
                label="schema1.table1",
                data_type="table",
                select_from=[],
            )
        ]
        write_nodes_to_yaml(initial_nodes, output_file)

        # Try to write again with prevent_file_overwrite=True and update_nodes=False
        new_nodes = [
            Node(
                id="schema1.table2",
                label="schema1.table2",
                data_type="view",
                select_from=[],
            )
        ]

        with pytest.raises(
            FileExistsError, match="File .* already exists. Use prevent_file_overwrite"
        ):
            write_nodes_to_yaml(
                new_nodes, output_file, update_nodes=False, prevent_file_overwrite=True
            )
