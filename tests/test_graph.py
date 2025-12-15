"""Unit tests for graph module."""

import pytest

from lineage.graph.lineage_graph import LineageGraph
from lineage.models import Connection, Node


class TestLineageGraph:
    """Tests for LineageGraph class."""

    @pytest.fixture
    def sample_nodes(self):
        """Provide sample nodes for testing.

        Uses generic data_type and data_level values since graph operations
        don't depend on specific styles.
        """
        return [
            Node(id="node_a", label="Node A", data_type="table", data_level="level1"),
            Node(id="node_b", label="Node B", data_type="table", data_level="level1"),
            Node(id="node_c", label="Node C", data_type="view", data_level="level2"),
            Node(id="node_d", label="Node D", data_type="table", data_level="level3"),
            Node(id="node_e", label="Node E", data_type="table", data_level="level4"),
            Node(id="node_f", label="Node F", data_type="table", data_level="level5"),
            Node(id="node_g", label="Node G", data_type="view", data_level="level6"),
        ]

    @pytest.fixture
    def sample_connections(self):
        """Provide sample connections for testing.

        Graph structure:
        node_a ──> node_c ──> node_d ──> node_e ──> node_f ──> node_g
        node_b ──>             │                     ↑
                               └──────────────────────┘
        """
        return [
            Connection(from_id="node_a", to_id="node_c"),
            Connection(from_id="node_b", to_id="node_c"),
            Connection(from_id="node_c", to_id="node_d"),
            Connection(from_id="node_d", to_id="node_e"),
            Connection(from_id="node_d", to_id="node_f"),
            Connection(from_id="node_e", to_id="node_f"),
            Connection(from_id="node_f", to_id="node_g"),
        ]

    @pytest.fixture
    def lineage_graph(self, sample_nodes, sample_connections):
        """Provide a LineageGraph instance for testing."""
        return LineageGraph(sample_nodes, sample_connections)

    def test_initialization(self, sample_nodes, sample_connections):
        """Test LineageGraph initialization."""
        graph = LineageGraph(sample_nodes, sample_connections)

        assert len(graph.nodes) == 7
        assert len(graph.connections) == 7
        assert graph.graph.number_of_nodes() == 7
        assert graph.graph.number_of_edges() == 7

    def test_has_node(self, lineage_graph):
        """Test has_node method."""
        assert lineage_graph.has_node("node_a") is True
        assert lineage_graph.has_node("node_e") is True
        assert lineage_graph.has_node("nonexistent") is False

    def test_get_upstream_nodes_unlimited_depth(self, lineage_graph):
        """Test getting all upstream nodes with unlimited depth."""
        upstream = lineage_graph.get_upstream_nodes("node_f")

        # node_f has upstream: node_e, node_d, node_c, node_a, node_b
        assert upstream == {"node_e", "node_d", "node_c", "node_a", "node_b"}

    def test_get_upstream_nodes_with_depth_limit(self, lineage_graph):
        """Test getting upstream nodes with depth limit."""
        # Depth 1: only direct predecessors
        upstream = lineage_graph.get_upstream_nodes("node_f", max_depth=1)
        assert upstream == {"node_e", "node_d"}

        # Depth 2: up to 2 hops
        upstream = lineage_graph.get_upstream_nodes("node_f", max_depth=2)
        assert upstream == {"node_e", "node_d", "node_c"}

    def test_get_upstream_nodes_nonexistent(self, lineage_graph):
        """Test getting upstream nodes for nonexistent node."""
        upstream = lineage_graph.get_upstream_nodes("nonexistent")
        assert upstream == set()

    def test_get_downstream_nodes_unlimited_depth(self, lineage_graph):
        """Test getting all downstream nodes with unlimited depth."""
        downstream = lineage_graph.get_downstream_nodes("node_d")

        # node_d has downstream: node_e, node_f, node_g
        assert downstream == {"node_e", "node_f", "node_g"}

    def test_get_downstream_nodes_with_depth_limit(self, lineage_graph):
        """Test getting downstream nodes with depth limit."""
        # Depth 1: only direct successors
        downstream = lineage_graph.get_downstream_nodes("node_d", max_depth=1)
        assert downstream == {"node_e", "node_f"}

        # Depth 2: up to 2 hops
        downstream = lineage_graph.get_downstream_nodes("node_d", max_depth=2)
        assert downstream == {"node_e", "node_f", "node_g"}

    def test_get_downstream_nodes_nonexistent(self, lineage_graph):
        """Test getting downstream nodes for nonexistent node."""
        downstream = lineage_graph.get_downstream_nodes("nonexistent")
        assert downstream == set()

    def test_get_direct_connections(self, lineage_graph):
        """Test getting directly connected nodes."""
        direct = lineage_graph.get_direct_connections("node_d")

        # node_d has upstream: node_c, downstream: node_e, node_f
        assert direct == {"node_c", "node_e", "node_f"}

    def test_get_direct_connections_source_node(self, lineage_graph):
        """Test getting direct connections for source node."""
        direct = lineage_graph.get_direct_connections("node_a")

        # node_a has only downstream: node_c
        assert direct == {"node_c"}

    def test_get_direct_connections_sink_node(self, lineage_graph):
        """Test getting direct connections for sink node."""
        direct = lineage_graph.get_direct_connections("node_g")

        # node_g has only upstream: node_f
        assert direct == {"node_f"}

    def test_get_subgraph_both_directions(self, lineage_graph):
        """Test getting subgraph with both upstream and downstream."""
        nodes, connections = lineage_graph.get_subgraph(["node_e"])

        # Should include all upstream and all downstream of node_e
        node_ids = {node.id for node in nodes}
        assert "node_e" in node_ids
        assert "node_d" in node_ids  # upstream
        assert "node_c" in node_ids  # upstream
        assert "node_a" in node_ids  # upstream
        assert "node_b" in node_ids  # upstream
        assert "node_f" in node_ids  # downstream
        assert "node_g" in node_ids  # downstream

    def test_get_subgraph_upstream_only(self, lineage_graph):
        """Test getting subgraph with upstream only."""
        nodes, _connections = lineage_graph.get_subgraph(
            ["node_e"], direction="upstream"
        )

        node_ids = {node.id for node in nodes}
        assert "node_e" in node_ids
        assert "node_d" in node_ids
        assert "node_c" in node_ids
        assert "node_a" in node_ids
        assert "node_b" in node_ids
        # Should NOT include downstream
        assert "node_f" not in node_ids
        assert "node_g" not in node_ids

    def test_get_subgraph_downstream_only(self, lineage_graph):
        """Test getting subgraph with downstream only."""
        nodes, _connections = lineage_graph.get_subgraph(
            ["node_d"], direction="downstream"
        )

        node_ids = {node.id for node in nodes}
        assert "node_d" in node_ids
        assert "node_e" in node_ids
        assert "node_f" in node_ids
        assert "node_g" in node_ids
        # Should NOT include upstream
        assert "node_c" not in node_ids
        assert "node_a" not in node_ids
        assert "node_b" not in node_ids

    def test_get_subgraph_with_depth_limit(self, lineage_graph):
        """Test getting subgraph with depth limit."""
        nodes, _connections = lineage_graph.get_subgraph(
            ["node_d"], direction="both", max_depth=1
        )

        node_ids = {node.id for node in nodes}
        assert "node_d" in node_ids
        assert "node_c" in node_ids  # 1 hop upstream
        assert "node_e" in node_ids  # 1 hop downstream
        assert "node_f" in node_ids  # 1 hop downstream
        # Should NOT include nodes beyond depth 1
        assert "node_a" not in node_ids
        assert "node_b" not in node_ids
        assert "node_g" not in node_ids

    def test_get_subgraph_multiple_focus_nodes(self, lineage_graph):
        """Test getting subgraph with multiple focus nodes."""
        nodes, _connections = lineage_graph.get_subgraph(
            ["node_a", "node_g"], direction="both"
        )

        node_ids = {node.id for node in nodes}
        # Should include all nodes in paths between node_a and node_g
        assert len(node_ids) == 7  # All nodes

    def test_get_direct_subgraph(self, lineage_graph):
        """Test getting subgraph with only direct connections."""
        nodes, _connections = lineage_graph.get_direct_subgraph(["node_d"])

        node_ids = {node.id for node in nodes}
        assert "node_d" in node_ids
        assert "node_c" in node_ids  # direct upstream
        assert "node_e" in node_ids  # direct downstream
        assert "node_f" in node_ids  # direct downstream
        # Should NOT include indirect connections
        assert "node_a" not in node_ids
        assert "node_b" not in node_ids
        assert "node_g" not in node_ids

    def test_get_direct_subgraph_multiple_nodes(self, lineage_graph):
        """Test getting direct subgraph with multiple focus nodes."""
        nodes, _connections = lineage_graph.get_direct_subgraph(["node_d", "node_e"])

        node_ids = {node.id for node in nodes}
        assert "node_d" in node_ids
        assert "node_e" in node_ids
        assert "node_c" in node_ids  # direct to node_d
        assert "node_f" in node_ids  # direct to both node_d and node_e
        assert "node_g" not in node_ids  # not direct to either

    def test_is_acyclic(self, lineage_graph):
        """Test checking if graph is acyclic."""
        assert lineage_graph.is_acyclic() is True

    def test_is_acyclic_with_cycle(self, sample_nodes):
        """Test checking if graph with cycle is not acyclic."""
        connections_with_cycle = [
            Connection(from_id="node_a", to_id="node_c"),
            Connection(from_id="node_c", to_id="node_d"),
            Connection(from_id="node_d", to_id="node_c"),  # Creates cycle
        ]

        graph = LineageGraph(sample_nodes, connections_with_cycle)
        assert graph.is_acyclic() is False

    def test_find_cycles_no_cycles(self, lineage_graph):
        """Test finding cycles in acyclic graph."""
        cycles = lineage_graph.find_cycles()
        assert cycles == []

    def test_find_cycles_with_cycle(self, sample_nodes):
        """Test finding cycles in graph with cycles."""
        connections_with_cycle = [
            Connection(from_id="node_a", to_id="node_c"),
            Connection(from_id="node_c", to_id="node_d"),
            Connection(from_id="node_d", to_id="node_c"),  # Creates cycle
        ]

        graph = LineageGraph(sample_nodes, connections_with_cycle)
        cycles = graph.find_cycles()

        assert len(cycles) > 0
        # Should find the node_c-node_d cycle
        assert any("node_c" in cycle and "node_d" in cycle for cycle in cycles)

    def test_get_all_paths(self, lineage_graph):
        """Test getting all paths between two nodes."""
        paths = lineage_graph.get_all_paths("node_a", "node_f")

        # There should be multiple paths from node_a to node_f
        assert len(paths) > 0

        # All paths should start with node_a and end with node_f
        for path in paths:
            assert path[0] == "node_a"
            assert path[-1] == "node_f"

    def test_get_all_paths_direct(self, lineage_graph):
        """Test getting paths with direct connection."""
        paths = lineage_graph.get_all_paths("node_a", "node_c")

        assert len(paths) == 1
        assert paths[0] == ["node_a", "node_c"]

    def test_get_all_paths_no_path(self, lineage_graph):
        """Test getting paths when no path exists."""
        # No path from node_g back to node_a (wrong direction)
        paths = lineage_graph.get_all_paths("node_g", "node_a")

        assert paths == []

    def test_get_all_paths_nonexistent_nodes(self, lineage_graph):
        """Test getting paths with nonexistent nodes."""
        paths = lineage_graph.get_all_paths("nonexistent1", "nonexistent2")

        assert paths == []

    def test_subgraph_preserves_connections(self, lineage_graph):
        """Test that subgraph preserves connection objects."""
        _nodes, connections = lineage_graph.get_subgraph(["node_d"])

        # Check that connections have correct attributes
        for conn in connections:
            assert hasattr(conn, "from_id")
            assert hasattr(conn, "to_id")
            assert hasattr(conn, "connection_type")

    def test_subgraph_with_nonexistent_focus_node(self, lineage_graph):
        """Test subgraph with nonexistent focus node."""
        nodes, connections = lineage_graph.get_subgraph(["nonexistent"])

        # Should return empty results
        assert len(nodes) == 0
        assert len(connections) == 0
