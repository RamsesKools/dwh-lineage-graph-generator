"""
Missing Nodes Detection and Imputation Module.

This module provides functions to detect and impute nodes that are referenced in
select_from fields but are not present in the nodes list. It preserves comments,
order, and formatting when modifying YAML files.
"""

from pathlib import Path
from typing import Any
from ruamel.yaml import YAML


# ============================================================================
# Detection Functions
# ============================================================================


def extract_referenced_node_ids(nodes_data: list[dict[str, Any]]) -> set[str]:
    """
    Extract all node IDs referenced in select_from fields.

    Args:
        nodes_data: List of node dictionaries from YAML

    Returns:
        Set of node IDs that are referenced in select_from fields
    """
    referenced_ids = set()

    for node in nodes_data:
        if not isinstance(node, dict):
            continue

        select_from = node.get("select_from")
        if not select_from:
            continue

        # Handle list of node references (string format only)
        if isinstance(select_from, list):
            for ref in select_from:
                if isinstance(ref, str):
                    referenced_ids.add(ref)

    return referenced_ids


def extract_existing_node_ids(nodes_data: list[dict[str, Any]]) -> set[str]:
    """
    Extract all existing node IDs from the nodes list.

    Args:
        nodes_data: List of node dictionaries from YAML

    Returns:
        Set of node IDs that exist in the nodes list
    """
    existing_ids = set()

    for node in nodes_data:
        if isinstance(node, dict) and "id" in node:
            existing_ids.add(node["id"])

    return existing_ids


def find_missing_node_ids(nodes_data: list[dict[str, Any]]) -> list[str]:
    """
    Find node IDs that are referenced but not present in the nodes list.

    This function identifies nodes that are referenced in select_from fields
    but do not exist in the nodes list. Self-references (where a node references
    itself) are excluded.

    Args:
        nodes_data: List of node dictionaries from YAML

    Returns:
        List of missing node IDs in order of discovery (deterministic)
    """
    existing_ids = extract_existing_node_ids(nodes_data)
    referenced_ids = extract_referenced_node_ids(nodes_data)

    # Find missing nodes (referenced but not existing)
    missing_ids = referenced_ids - existing_ids

    # Return in deterministic order (maintain order of discovery)
    missing_in_order = []
    seen = set()

    for node in nodes_data:
        if not isinstance(node, dict):
            continue

        select_from = node.get("select_from")
        if not select_from or not isinstance(select_from, list):
            continue

        for ref in select_from:
            # Only process string references
            if isinstance(ref, str) and ref in missing_ids and ref not in seen:
                missing_in_order.append(ref)
                seen.add(ref)

    return missing_in_order


def create_missing_node(node_id: str) -> dict[str, Any]:
    """
    Create a new node dictionary with null values for data_level and data_type.

    Args:
        node_id: The ID of the missing node to create

    Returns:
        Dictionary representing the new node with null values
    """
    return {
        "id": node_id,
        "label": node_id,
        "data_level": None,
        "data_type": None,
        "select_from": [],
    }


# ============================================================================
# Imputation Functions
# ============================================================================


class ImputationStats:
    """Track statistics about missing node imputation operations."""

    def __init__(self) -> None:
        self.nodes_added = 0
        self.missing_node_ids: list[str] = []

    def __str__(self) -> str:
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
