"""Unit tests for metadata module."""

from typing import cast
from lineage.models import Connection, Node, ConnectionType
from lineage.config import CONNECTION_STYLES, DEFAULT_CONNECTION_TYPE


class TestNode:
    """Tests for Node dataclass."""

    def test_node_creation_with_valid_data(self):
        """Test creating a Node with valid data."""
        node = Node(
            id="test_node",
            label="Test Node",
            data_type="table",
            data_level="base",
        )

        assert node.id == "test_node"
        assert node.label == "Test Node"
        assert node.data_type == "table"
        assert node.data_level == "base"

    def test_node_creation_with_all_data_types(self):
        """Test creating nodes with all valid data types."""
        data_types = [
            "table",
            "view",
            "dlv1-source",
            "dlv2-source",
            "dlv2-resourcelink",
            "dlv1-manual-source",
        ]

        for data_type in data_types:
            node = Node(
                id=f"node_{data_type}",
                label=f"Node {data_type}",
                data_type=data_type,  # type: ignore
                data_level="base",
            )
            assert node.data_type == data_type

    def test_node_creation_with_all_data_levels(self):
        """Test creating nodes with all valid data levels."""
        data_levels = ["source", "staging", "base", "dimension", "fact", "export"]

        for data_level in data_levels:
            node = Node(
                id=f"node_{data_level}",
                label=f"Node {data_level}",
                data_type="table",
                data_level=data_level,  # type: ignore
            )
            assert node.data_level == data_level

    def test_node_equality(self):
        """Test that two nodes with same data are equal."""
        node1 = Node(
            id="test",
            label="Test",
            data_type="table",
            data_level="base",
        )
        node2 = Node(
            id="test",
            label="Test",
            data_type="table",
            data_level="base",
        )

        assert node1 == node2

    def test_node_inequality(self):
        """Test that two nodes with different data are not equal."""
        node1 = Node(
            id="test1",
            label="Test 1",
            data_type="table",
            data_level="base",
        )
        node2 = Node(
            id="test2",
            label="Test 2",
            data_type="view",
            data_level="staging",
        )

        assert node1 != node2


class TestConnection:
    """Tests for Connection dataclass."""

    def test_connection_creation_with_default_type(self):
        """Test creating a Connection with default connection type."""
        conn = Connection(from_id="node1", to_id="node2")

        assert conn.from_id == "node1"
        assert conn.to_id == "node2"
        assert conn.connection_type == DEFAULT_CONNECTION_TYPE

    def test_connection_creation_with_explicit_type(self):
        """Test creating a Connection with explicit connection type."""
        # Use the second connection type (not the default)
        non_default_type = cast(ConnectionType, list(CONNECTION_STYLES.keys())[1])
        conn = Connection(
            from_id="node1", to_id="node2", connection_type=non_default_type
        )

        assert conn.from_id == "node1"
        assert conn.to_id == "node2"
        assert conn.connection_type == non_default_type

    def test_connection_creation_with_all_types(self):
        """Test creating connections with all valid connection types."""
        connection_types = list(CONNECTION_STYLES.keys())

        for conn_type in connection_types:
            conn = Connection(
                from_id="node1",
                to_id="node2",
                connection_type=conn_type,  # type: ignore
            )
            assert conn.connection_type == conn_type

    def test_connection_equality(self):
        """Test that two connections with same data are equal."""
        # Use second connection type for testing equality
        test_type = cast(ConnectionType, list(CONNECTION_STYLES.keys())[1])
        conn1 = Connection(from_id="node1", to_id="node2", connection_type=test_type)
        conn2 = Connection(from_id="node1", to_id="node2", connection_type=test_type)

        assert conn1 == conn2

    def test_connection_inequality(self):
        """Test that two connections with different data are not equal."""
        conn1 = Connection(from_id="node1", to_id="node2")
        conn2 = Connection(from_id="node2", to_id="node3")

        assert conn1 != conn2
