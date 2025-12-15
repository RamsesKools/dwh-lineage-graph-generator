"""Unit tests for generator module."""

from typing import get_args

import pytest

from lineage.export.mermaid import MermaidGenerator, generate_legend
from lineage.models import Connection, DataLevel, DataType, Node
from lineage.config import CONNECTION_STYLES, DATA_LEVEL_STYLES, NODE_SHAPES


class TestMermaidGenerator:
    """Tests for MermaidGenerator class."""

    @pytest.fixture
    def simple_nodes(self):
        """Provide simple test nodes."""
        return [
            Node(
                id="node1",
                label="Node 1",
                data_type="table",
                data_level="base",
            ),
            Node(
                id="node2",
                label="Node 2",
                data_type="view",
                data_level="staging",
            ),
        ]

    @pytest.fixture
    def simple_connections(self):
        """Provide simple test connections."""
        return [Connection(from_id="node1", to_id="node2")]

    def test_generator_initialization(self, simple_nodes, simple_connections):
        """Test MermaidGenerator initialization."""
        gen = MermaidGenerator(
            nodes=simple_nodes, connections=simple_connections, direction="LR"
        )

        assert gen.nodes == simple_nodes
        assert gen.connections == simple_connections
        assert gen.direction == "LR"
        assert len(gen._node_map) == 2

    def test_generator_default_direction(self, simple_nodes, simple_connections):
        """Test MermaidGenerator uses LR as default direction."""
        gen = MermaidGenerator(nodes=simple_nodes, connections=simple_connections)

        assert gen.direction == "LR"

    def test_sanitize_id(self, simple_nodes, simple_connections):
        """Test ID sanitization."""
        gen = MermaidGenerator(nodes=simple_nodes, connections=simple_connections)

        assert gen._sanitize_id("simple_id") == "simple_id"
        assert gen._sanitize_id("id-with-dashes") == "id_with_dashes"
        assert gen._sanitize_id("id.with.dots") == "id_with_dots"
        assert gen._sanitize_id("id with spaces") == "id_with_spaces"
        assert gen._sanitize_id("complex-id.with spaces") == "complex_id_with_spaces"

    def test_generate_node_definition_uses_correct_shapes(
        self, simple_nodes, simple_connections
    ):
        """Test that node definitions use shapes from NODE_SHAPES config."""
        gen = MermaidGenerator(nodes=simple_nodes, connections=simple_connections)

        for data_type, (prefix, suffix) in NODE_SHAPES.items():
            node = Node(
                id="test",
                label="Test Label",
                data_type=data_type,  # type: ignore
                data_level="base",
            )
            result = gen._generate_node_definition(node)

            # Verify the prefix and suffix are used correctly
            assert result.startswith(f"test{prefix}")
            assert result.endswith(f"{suffix}")
            assert "Test Label" in result

    def test_generate_connection_definition_uses_correct_arrows(
        self, simple_nodes, simple_connections
    ):
        """Test that connections use arrows from CONNECTION_STYLES config."""
        gen = MermaidGenerator(nodes=simple_nodes, connections=simple_connections)

        for conn_type, arrow in CONNECTION_STYLES.items():
            conn = Connection(
                from_id="node1", to_id="node2", connection_type=conn_type  # type: ignore
            )
            result = gen._generate_connection_definition(conn)

            assert result == f"node1 {arrow} node2"

    def test_generate_class_definitions_uses_data_level_styles(
        self, simple_nodes, simple_connections
    ):
        """Test that class definitions use styles from DATA_LEVEL_STYLES config."""
        gen = MermaidGenerator(nodes=simple_nodes, connections=simple_connections)

        result = gen._generate_class_definitions()

        # Should have one class definition per unique data level in nodes
        assert len(result) == 2  # Two unique data levels in simple_nodes

        # Verify each class definition uses the correct style
        for line in result:
            if "baseStyle" in line:
                assert DATA_LEVEL_STYLES["base"] in line
            elif "stagingStyle" in line:
                assert DATA_LEVEL_STYLES["staging"] in line

    def test_generate_class_assignments(self, simple_nodes, simple_connections):
        """Test class assignment generation."""
        gen = MermaidGenerator(nodes=simple_nodes, connections=simple_connections)

        result = gen._generate_class_assignments()

        # Should have one assignment per unique data level
        assert len(result) == 2

        # Verify assignments reference correct nodes and styles
        assert any("node1" in line and "baseStyle" in line for line in result)
        assert any("node2" in line and "stagingStyle" in line for line in result)

    def test_generate_complete_diagram(self, simple_nodes, simple_connections):
        """Test complete diagram generation."""
        gen = MermaidGenerator(
            nodes=simple_nodes, connections=simple_connections, direction="TB"
        )

        result = gen.generate()

        # Check header
        assert "graph TB" in result

        # Check nodes are present
        assert "node1" in result
        assert "node2" in result
        assert "Node 1" in result
        assert "Node 2" in result

        # Check connections
        assert "node1 --> node2" in result

        # Check classes are defined and assigned
        assert "classDef" in result
        assert "class node1" in result or "class node2" in result

    def test_generate_with_all_directions(self, simple_nodes, simple_connections):
        """Test diagram generation with all valid directions."""
        # Test with all valid direction values
        for direction in ["LR", "RL", "TB", "BT"]:
            gen = MermaidGenerator(
                nodes=simple_nodes,
                connections=simple_connections,
                direction=direction,  # type: ignore
            )
            result = gen.generate()

            assert f"graph {direction}" in result

    def test_generate_with_all_node_types(self):
        """Test generation with all node types from DataType."""
        data_types = get_args(DataType)
        nodes = [
            Node(
                id=f"node_{i}",
                label=f"Node {i}",
                data_type=dt,  # type: ignore
                data_level="base",
            )
            for i, dt in enumerate(data_types)
        ]

        gen = MermaidGenerator(nodes=nodes, connections=[])
        result = gen.generate()

        # Verify all nodes are in output
        for i in range(len(data_types)):
            assert f"node_{i}" in result

    def test_generate_with_all_data_levels(self):
        """Test generation with all data levels from DataLevel."""
        data_levels = get_args(DataLevel)
        nodes = [
            Node(
                id=f"node_{i}",
                label=f"Node {i}",
                data_type="table",
                data_level=dl,  # type: ignore
            )
            for i, dl in enumerate(data_levels)
        ]

        gen = MermaidGenerator(nodes=nodes, connections=[])
        result = gen.generate()

        # Verify all data level styles are defined
        for level in data_levels:
            assert f"{level}Style" in result


class TestGenerateLegend:
    """Tests for generate_legend function."""

    def test_generate_legend_structure(self):
        """Test that legend has correct structure."""
        result = generate_legend()

        # Check main direction
        assert "graph LR" in result

        # Check subgraphs exist
        assert "subgraph shapes" in result
        assert "subgraph levels" in result
        assert "subgraph connections" in result

        # Check subgraph directions
        assert result.count("direction TB") >= 3

    def test_generate_legend_contains_all_node_types(self):
        """Test that legend contains all node types from DataType."""
        result = generate_legend()
        data_types = get_args(DataType)

        # Each data type should appear in the legend
        for data_type in data_types:
            # The label is generated from data_type with title case
            # e.g., "dlv1-source" becomes "Dlv1 Source"
            assert data_type.replace("-", " ").title() in result or data_type in result

    def test_generate_legend_contains_all_data_levels(self):
        """Test that legend contains all data levels from DataLevel."""
        result = generate_legend()
        data_levels = get_args(DataLevel)

        for level in data_levels:
            # Capitalized version should appear
            assert level.capitalize() in result

    def test_generate_legend_contains_all_connection_types(self):
        """Test that legend contains all connection types from CONNECTION_STYLES."""
        result = generate_legend()

        for conn_type, arrow in CONNECTION_STYLES.items():
            # Connection type label should appear
            assert conn_type.replace("-", " ").title() in result
            # Arrow symbol should appear
            assert arrow in result

    def test_generate_legend_defines_all_data_level_styles(self):
        """Test that legend defines all data level styles."""
        result = generate_legend()
        data_levels = get_args(DataLevel)

        for level in data_levels:
            style_name = f"{level}Style"
            style_def = DATA_LEVEL_STYLES[level]

            # Class definition should exist
            assert f"classDef {style_name}" in result
            # Style definition should be included
            assert style_def in result

    def test_generate_legend_assigns_styles_to_level_nodes(self):
        """Test that legend assigns styles to data level nodes."""
        result = generate_legend()
        data_levels = get_args(DataLevel)

        for level in data_levels:
            style_name = f"{level}Style"
            # Class assignment should exist for this level
            assert style_name in result
            assert "class level_" in result
