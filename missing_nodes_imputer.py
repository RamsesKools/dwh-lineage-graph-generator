"""
Missing Nodes Imputation Module using ruamel.yaml.

This module provides functions to impute missing connecting nodes in YAML lineage files
while preserving comments, order, and formatting.
"""

from pathlib import Path
from typing import Any
from ruamel.yaml import YAML

from missing_nodes_detector import find_missing_node_ids, create_missing_node


class ImputationStats:
    """Track statistics about missing node imputation operations."""

    def __init__(self):
        self.nodes_added = 0
        self.missing_node_ids: list[str] = []

    def __str__(self):
        result = f"Imputation Summary:\n  - Missing nodes added: {self.nodes_added}"
        if self.missing_node_ids:
            result += "\n  - Added node IDs:"
            for node_id in self.missing_node_ids:
                result += f"\n    * {node_id}"
        return result


def impute_missing_connecting_nodes(
    input_path: Path, output_path: Path
) -> ImputationStats:
    """
    Impute missing connecting nodes in a YAML lineage file.

    This function reads a YAML file, identifies nodes that are referenced in
    select_from fields but not present in the nodes list, and appends them
    to the end of the nodes list with null values for data_level and data_type.

    Args:
        input_path: Path to the input YAML file
        output_path: Path to the output YAML file (can be same as input for in-place)

    Returns:
        ImputationStats object with counts and IDs of added nodes
    """
    # Initialize YAML with round-trip mode to preserve comments and formatting
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = None

    # Load the YAML file
    with open(input_path, "r") as f:
        data = yaml.load(f)

    # Track statistics
    stats = ImputationStats()

    # Check if nodes exist
    if "nodes" not in data or not data["nodes"]:
        return stats

    # Find missing node IDs
    missing_ids = find_missing_node_ids(data["nodes"])

    # Create and append missing nodes
    for node_id in missing_ids:
        new_node = create_missing_node(node_id)
        data["nodes"].append(new_node)
        stats.nodes_added += 1
        stats.missing_node_ids.append(node_id)

    # Write the result
    with open(output_path, "w") as f:
        yaml.dump(data, f)

    return stats
