"""Unit tests for missing nodes detection."""

from lineage.graph.missing_nodes import (
    extract_referenced_node_ids,
    extract_existing_node_ids,
    find_missing_node_ids,
    create_missing_node,
)


class TestExtractReferencedNodeIds:
    """Test extraction of node IDs from select_from fields."""

    def test_extract_from_string_references(self):
        """Test extraction when select_from contains string references."""
        nodes_data = [
            {"id": "node_a", "select_from": ["node_b", "node_c"]},
        ]
        referenced_ids = extract_referenced_node_ids(nodes_data)
        assert referenced_ids == {"node_b", "node_c"}

    def test_extract_from_multiple_nodes(self):
        """Test extraction from multiple nodes."""
        nodes_data = [
            {"id": "node_a", "select_from": ["node_b"]},
            {"id": "node_c", "select_from": ["node_d", "node_e"]},
        ]
        referenced_ids = extract_referenced_node_ids(nodes_data)
        assert referenced_ids == {"node_b", "node_d", "node_e"}

    def test_extract_with_empty_select_from(self):
        """Test extraction when select_from is empty or None."""
        nodes_data = [
            {"id": "node_a", "select_from": []},
            {"id": "node_b", "select_from": None},
            {"id": "node_c"},  # Missing select_from
        ]
        referenced_ids = extract_referenced_node_ids(nodes_data)
        assert referenced_ids == set()

    def test_extract_ignores_non_dict_nodes(self):
        """Test that non-dict items in nodes list are ignored."""
        nodes_data = [
            {"id": "node_a", "select_from": ["node_b"]},
            "invalid_node",
            None,
        ]
        referenced_ids = extract_referenced_node_ids(nodes_data)
        assert referenced_ids == {"node_b"}


class TestExtractExistingNodeIds:
    """Test extraction of existing node IDs."""

    def test_extract_existing_ids(self):
        """Test basic extraction of existing node IDs."""
        nodes_data = [
            {"id": "node_a"},
            {"id": "node_b"},
            {"id": "node_c"},
        ]
        existing_ids = extract_existing_node_ids(nodes_data)
        assert existing_ids == {"node_a", "node_b", "node_c"}

    def test_extract_with_duplicate_ids(self):
        """Test extraction handles duplicate IDs (set deduplication)."""
        nodes_data = [
            {"id": "node_a"},
            {"id": "node_b"},
            {"id": "node_a"},  # Duplicate
        ]
        existing_ids = extract_existing_node_ids(nodes_data)
        assert existing_ids == {"node_a", "node_b"}

    def test_extract_ignores_missing_id_field(self):
        """Test that nodes without id field are ignored."""
        nodes_data = [
            {"id": "node_a"},
            {"label": "no_id"},
            {"id": "node_b"},
        ]
        existing_ids = extract_existing_node_ids(nodes_data)
        assert existing_ids == {"node_a", "node_b"}

    def test_extract_ignores_non_dict_items(self):
        """Test that non-dict items are ignored."""
        nodes_data = [
            {"id": "node_a"},
            "invalid",
            None,
            {"id": "node_b"},
        ]
        existing_ids = extract_existing_node_ids(nodes_data)
        assert existing_ids == {"node_a", "node_b"}


class TestFindMissingNodeIds:
    """Test finding missing node IDs."""

    def test_find_missing_nodes(self):
        """Test basic missing node detection."""
        nodes_data = [
            {"id": "node_a", "select_from": ["node_b", "node_c"]},
            {"id": "node_b", "select_from": []},
        ]
        missing_ids = find_missing_node_ids(nodes_data)
        assert missing_ids == ["node_c"]

    def test_find_multiple_missing_nodes(self):
        """Test finding multiple missing nodes."""
        nodes_data = [
            {"id": "node_a", "select_from": ["node_b", "node_c"]},
            {"id": "node_d", "select_from": ["node_e"]},
        ]
        missing_ids = find_missing_node_ids(nodes_data)
        assert missing_ids == ["node_b", "node_c", "node_e"]

    def test_exclude_self_references(self):
        """Test that self-references are excluded from missing nodes."""
        nodes_data = [
            {"id": "node_a", "select_from": ["node_a", "node_b"]},
        ]
        missing_ids = find_missing_node_ids(nodes_data)
        assert missing_ids == ["node_b"]

    def test_no_missing_nodes(self):
        """Test when all referenced nodes exist."""
        nodes_data = [
            {"id": "node_a", "select_from": ["node_b"]},
            {"id": "node_b", "select_from": []},
        ]
        missing_ids = find_missing_node_ids(nodes_data)
        assert missing_ids == []

    def test_deterministic_order(self):
        """Test that missing nodes are returned in order of discovery."""
        nodes_data = [
            {"id": "node_a", "select_from": ["node_z", "node_y"]},
            {"id": "node_b", "select_from": ["node_x"]},
        ]
        missing_ids = find_missing_node_ids(nodes_data)
        assert missing_ids == ["node_z", "node_y", "node_x"]

    def test_deduplication_in_order(self):
        """Test that duplicate references are only listed once."""
        nodes_data = [
            {"id": "node_a", "select_from": ["node_missing"]},
            {"id": "node_b", "select_from": ["node_missing"]},
        ]
        missing_ids = find_missing_node_ids(nodes_data)
        assert missing_ids == ["node_missing"]

    def test_real_world_example(self):
        """Test with real-world lineage data structure."""
        nodes_data = [
            {
                "id": "dwh_sales.sv_customers",
                "select_from": [
                    "source_system.sometable",
                    "rl_source_thirdparty.anothertable",
                ],
            },
            {"id": "source_system.sometable", "select_from": []},
        ]
        missing_ids = find_missing_node_ids(nodes_data)
        assert missing_ids == ["rl_source_thirdparty.anothertable"]


class TestCreateMissingNode:
    """Test creation of missing node dictionaries."""

    def test_create_node_structure(self):
        """Test that created node has correct structure and values."""
        node_id = "source_database.orders_table"
        node = create_missing_node(node_id)

        assert node["id"] == node_id
        assert node["label"] == node_id
        assert node["data_level"] is None
        assert node["data_type"] is None
        assert node["select_from"] == []

    def test_create_multiple_nodes(self):
        """Test creating multiple nodes with different IDs."""
        node1 = create_missing_node("node_a")
        node2 = create_missing_node("node_b")

        assert node1["id"] == "node_a"
        assert node2["id"] == "node_b"
