"""Parser for lineage data files in JSON or YAML format."""

import json
from pathlib import Path
from typing import Any

import yaml

from metadata import Connection, Node
from styles import DEFAULT_CONNECTION_TYPE


def load_lineage_file(file_path: str | Path) -> tuple[list[Node], list[Connection]]:
    """Load lineage data from JSON or YAML file.

    Args:
        file_path: Path to the lineage data file

    Returns:
        Tuple of (nodes, connections)

    Raises:
        ValueError: If file format is unsupported or data is invalid
    """
    file_path = Path(file_path)

    # Load file based on extension
    if file_path.suffix.lower() == ".json":
        with open(file_path) as f:
            data = json.load(f)
    elif file_path.suffix.lower() in (".yaml", ".yml"):
        with open(file_path) as f:
            data = yaml.safe_load(f)
    else:
        raise ValueError(
            f"Unsupported file format: {file_path.suffix}. "
            "Supported formats: .json, .yaml, .yml"
        )

    # Normalize and parse the data
    nodes_data, connections_data = _normalize_format(data)

    # Convert to dataclass objects
    nodes = _parse_nodes(nodes_data)
    connections = _parse_connections(connections_data)

    return nodes, connections


def _normalize_format(data: dict[str, Any]) -> tuple[list[dict], list[dict]]:
    """Normalize lineage data to common format.

    Supports two formats:
    1. Old format: {"nodes": [...], "connections": [...]}
    2. New format: {"nodes": [...]} with select_from/connected_to fields

    Args:
        data: Raw loaded data dictionary

    Returns:
        Tuple of (normalized_nodes_data, normalized_connections_data)
    """
    if "nodes" not in data:
        raise ValueError("Missing required 'nodes' key in lineage data")

    nodes_data = data["nodes"]

    # Check if old format (has explicit connections array)
    if "connections" in data:
        # Old format: use connections as-is
        connections_data = data["connections"]
    else:
        # New format: extract connections from node fields
        connections_data = _extract_connections_from_nodes(nodes_data)

    return nodes_data, connections_data


def _extract_connections_from_nodes(nodes_data: list[dict]) -> list[dict]:
    """Extract connections from node select_from/connected_to fields.

    Args:
        nodes_data: List of node dictionaries with optional connection fields

    Returns:
        List of connection dictionaries
    """
    connections = []

    for node in nodes_data:
        node_id = node["id"]

        # Handle select_from connections (directed: from -> to)
        if "select_from" in node:
            select_from = node["select_from"]
            if select_from is not None:
                # Handle single string or list
                if isinstance(select_from, str):
                    select_from = [select_from]

                for source_id in select_from:
                    # Handle both string format and dict format (e.g., {'id': 'node_id'})
                    if isinstance(source_id, dict):
                        source_id = source_id.get("id", source_id)

                    connections.append({
                        "from_id": source_id,
                        "to_id": node_id,
                        "connection_type": "select_from",
                    })

        # Handle connected_to connections (undirected line)
        if "connected_to" in node:
            connected_to = node["connected_to"]
            if connected_to is not None:
                # Handle single string or list
                if isinstance(connected_to, str):
                    connected_to = [connected_to]

                for connected_id in connected_to:
                    # Handle both string format and dict format (e.g., {'id': 'node_id'})
                    if isinstance(connected_id, dict):
                        connected_id = connected_id.get("id", connected_id)

                    connections.append({
                        "from_id": node_id,
                        "to_id": connected_id,
                        "connection_type": "connected_to",
                    })

    return connections


def _parse_nodes(nodes_data: list[dict]) -> list[Node]:
    """Parse node dictionaries into Node objects.

    Args:
        nodes_data: List of node dictionaries

    Returns:
        List of Node objects

    Raises:
        ValueError: If node data is invalid
    """
    nodes = []

    for node_dict in nodes_data:
        try:
            node = Node(
                id=node_dict["id"],
                label=node_dict["label"],
                data_type=node_dict["data_type"],
                data_level=node_dict["data_level"],
            )
            nodes.append(node)
        except KeyError as e:
            raise ValueError(
                f"Missing required field {e} in node: {node_dict.get('id', 'unknown')}"
            )
        except TypeError as e:
            raise ValueError(
                f"Invalid data type in node {node_dict.get('id', 'unknown')}: {e}"
            )

    return nodes


def _parse_connections(connections_data: list[dict]) -> list[Connection]:
    """Parse connection dictionaries into Connection objects.

    Args:
        connections_data: List of connection dictionaries

    Returns:
        List of Connection objects

    Raises:
        ValueError: If connection data is invalid
    """
    connections = []

    for conn_dict in connections_data:
        try:
            connection = Connection(
                from_id=conn_dict["from_id"],
                to_id=conn_dict["to_id"],
                connection_type=conn_dict.get("connection_type", DEFAULT_CONNECTION_TYPE),
            )
            connections.append(connection)
        except KeyError as e:
            raise ValueError(
                f"Missing required field {e} in connection: {conn_dict}"
            )
        except TypeError as e:
            raise ValueError(f"Invalid data type in connection: {e}")

    return connections
