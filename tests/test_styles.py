"""Unit tests for styles module."""

from typing import get_args

from metadata import ConnectionType, DataLevel, DataType
from styles import CONNECTION_STYLES, DATA_LEVEL_STYLES, NODE_SHAPES


class TestNodeShapes:
    """Tests for NODE_SHAPES configuration."""

    def test_node_shapes_contains_all_data_types(self):
        """Test that NODE_SHAPES has an entry for every DataType."""
        data_types = get_args(DataType)

        for data_type in data_types:
            assert (
                data_type in NODE_SHAPES
            ), f"NODE_SHAPES missing entry for {data_type}"

    def test_node_shapes_structure(self):
        """Test that each NODE_SHAPES entry is a tuple of (prefix, suffix)."""
        for data_type, shape in NODE_SHAPES.items():
            assert isinstance(shape, tuple), f"Shape for {data_type} is not a tuple"
            assert len(shape) == 2, f"Shape for {data_type} must have exactly 2 elements"

            prefix, suffix = shape
            assert isinstance(
                prefix, str
            ), f"Prefix for {data_type} must be a string"
            assert isinstance(
                suffix, str
            ), f"Suffix for {data_type} must be a string"

    def test_node_shapes_values_are_valid_mermaid_syntax(self):
        """Test that NODE_SHAPES values are non-empty strings."""
        for data_type, (prefix, suffix) in NODE_SHAPES.items():
            assert len(prefix) > 0, f"Prefix for {data_type} cannot be empty"
            assert len(suffix) > 0, f"Suffix for {data_type} cannot be empty"

    def test_node_shapes_has_no_extra_keys(self):
        """Test that NODE_SHAPES only contains valid DataType keys."""
        data_types = set(get_args(DataType))
        shape_keys = set(NODE_SHAPES.keys())

        extra_keys = shape_keys - data_types
        assert (
            len(extra_keys) == 0
        ), f"NODE_SHAPES contains invalid keys: {extra_keys}"


class TestDataLevelStyles:
    """Tests for DATA_LEVEL_STYLES configuration."""

    def test_data_level_styles_contains_all_data_levels(self):
        """Test that DATA_LEVEL_STYLES has an entry for every DataLevel."""
        data_levels = get_args(DataLevel)

        for level in data_levels:
            assert (
                level in DATA_LEVEL_STYLES
            ), f"DATA_LEVEL_STYLES missing entry for {level}"

    def test_data_level_styles_values_are_strings(self):
        """Test that all DATA_LEVEL_STYLES values are non-empty strings."""
        for level, style in DATA_LEVEL_STYLES.items():
            assert isinstance(
                style, str
            ), f"Style for {level} must be a string"
            assert len(style) > 0, f"Style for {level} cannot be empty"

    def test_data_level_styles_contain_fill_property(self):
        """Test that all styles contain a fill property."""
        for level, style in DATA_LEVEL_STYLES.items():
            assert (
                "fill:" in style
            ), f"Style for {level} must contain 'fill:' property"

    def test_data_level_styles_contain_stroke_property(self):
        """Test that all styles contain a stroke property."""
        for level, style in DATA_LEVEL_STYLES.items():
            assert (
                "stroke:" in style
            ), f"Style for {level} must contain 'stroke:' property"

    def test_data_level_styles_contain_stroke_width(self):
        """Test that all styles contain a stroke-width property."""
        for level, style in DATA_LEVEL_STYLES.items():
            assert (
                "stroke-width:" in style
            ), f"Style for {level} must contain 'stroke-width:' property"

    def test_data_level_styles_has_no_extra_keys(self):
        """Test that DATA_LEVEL_STYLES only contains valid DataLevel keys."""
        data_levels = set(get_args(DataLevel))
        style_keys = set(DATA_LEVEL_STYLES.keys())

        extra_keys = style_keys - data_levels
        assert (
            len(extra_keys) == 0
        ), f"DATA_LEVEL_STYLES contains invalid keys: {extra_keys}"


class TestConnectionStyles:
    """Tests for CONNECTION_STYLES configuration."""

    def test_connection_styles_contains_all_connection_types(self):
        """Test that CONNECTION_STYLES has an entry for every ConnectionType."""
        connection_types = get_args(ConnectionType)

        for conn_type in connection_types:
            assert (
                conn_type in CONNECTION_STYLES
            ), f"CONNECTION_STYLES missing entry for {conn_type}"

    def test_connection_styles_values_are_strings(self):
        """Test that all CONNECTION_STYLES values are non-empty strings."""
        for conn_type, arrow in CONNECTION_STYLES.items():
            assert isinstance(
                arrow, str
            ), f"Arrow for {conn_type} must be a string"
            assert len(arrow) > 0, f"Arrow for {conn_type} cannot be empty"

    def test_connection_styles_contain_arrow_characters(self):
        """Test that all connection styles contain arrow-like characters."""
        for conn_type, arrow in CONNECTION_STYLES.items():
            # All Mermaid arrows contain '>' or '-'
            assert (
                ">" in arrow or "-" in arrow
            ), f"Arrow for {conn_type} should contain arrow characters"

    def test_connection_styles_has_no_extra_keys(self):
        """Test that CONNECTION_STYLES only contains valid ConnectionType keys."""
        connection_types = set(get_args(ConnectionType))
        style_keys = set(CONNECTION_STYLES.keys())

        extra_keys = style_keys - connection_types
        assert (
            len(extra_keys) == 0
        ), f"CONNECTION_STYLES contains invalid keys: {extra_keys}"


class TestStylesIntegrity:
    """Tests for overall styles configuration integrity."""

    def test_all_configs_are_dictionaries(self):
        """Test that all style configurations are dictionaries."""
        assert isinstance(NODE_SHAPES, dict), "NODE_SHAPES must be a dictionary"
        assert isinstance(
            DATA_LEVEL_STYLES, dict
        ), "DATA_LEVEL_STYLES must be a dictionary"
        assert isinstance(
            CONNECTION_STYLES, dict
        ), "CONNECTION_STYLES must be a dictionary"

    def test_all_configs_are_non_empty(self):
        """Test that all style configurations are non-empty."""
        assert len(NODE_SHAPES) > 0, "NODE_SHAPES cannot be empty"
        assert len(DATA_LEVEL_STYLES) > 0, "DATA_LEVEL_STYLES cannot be empty"
        assert len(CONNECTION_STYLES) > 0, "CONNECTION_STYLES cannot be empty"
