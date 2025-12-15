"""Write extracted nodes to YAML format."""

from dataclasses import asdict
from pathlib import Path

from ruamel.yaml import YAML

from lineage.models import Node


def _create_yaml_parser() -> YAML:
    """Create a configured YAML parser for writing."""
    yaml = YAML()
    yaml.default_flow_style = False
    yaml.preserve_quotes = True
    return yaml


def write_nodes_to_yaml(
    nodes: list[Node],
    output_path: Path,
    update_nodes: bool = True,
    prevent_file_overwrite: bool = True,
) -> dict[str, int]:
    """Write list of nodes to YAML file.

    Args:
        nodes: List of Node objects to write
        output_path: Path to output YAML file
        update_nodes: If True (default), upsert nodes - add new nodes and update existing
                     ones' null fields. If False, only add new nodes.
        prevent_file_overwrite: If True (default), raise error if file exists and
                               update_nodes=False. If False, overwrite the file.

    Returns:
        Dictionary with statistics: nodes_added, nodes_updated, connections_added

    Raises:
        FileExistsError: If prevent_file_overwrite=True and file exists with update_nodes=False
    """
    stats = {"nodes_added": 0, "nodes_updated": 0, "connections_added": 0}

    if output_path.exists() and prevent_file_overwrite and not update_nodes:
        raise FileExistsError(
            f"File {output_path} already exists. Use prevent_file_overwrite=False to overwrite."
        )

    nodes_dict = [asdict(node) for node in nodes]
    yaml = _create_yaml_parser()

    if output_path.exists() and update_nodes:
        with output_path.open("r") as f:
            data = yaml.load(f)

        existing_nodes = {node["id"]: node for node in data.get("nodes", [])}

        for new_node_dict in nodes_dict:
            node_id = new_node_dict["id"]

            if node_id in existing_nodes:
                existing_node = existing_nodes[node_id]
                updated = False

                if (
                    new_node_dict["data_level"] is not None
                    and existing_node.get("data_level") is None
                ):
                    existing_node["data_level"] = new_node_dict["data_level"]
                    updated = True

                if (
                    new_node_dict["data_type"] is not None
                    and existing_node.get("data_type") is None
                ):
                    existing_node["data_type"] = new_node_dict["data_type"]
                    updated = True

                existing_select_from = existing_node.get("select_from", [])
                if existing_select_from is None:
                    existing_select_from = []

                for source_id in new_node_dict["select_from"]:
                    if source_id not in existing_select_from:
                        existing_select_from.append(source_id)
                        stats["connections_added"] += 1
                        updated = True

                existing_node["select_from"] = existing_select_from

                if updated:
                    stats["nodes_updated"] += 1
            else:
                data["nodes"].append(new_node_dict)
                stats["nodes_added"] += 1

        with output_path.open("w") as f:
            yaml.dump(data, f)
    elif output_path.exists() and not update_nodes:
        with output_path.open("r") as f:
            data = yaml.load(f)

        existing_ids = {node["id"] for node in data.get("nodes", [])}
        new_nodes = [node for node in nodes_dict if node["id"] not in existing_ids]

        for new_node in new_nodes:
            data["nodes"].append(new_node)
            stats["nodes_added"] += 1

        with output_path.open("w") as f:
            yaml.dump(data, f)
    else:
        yaml_data = {"nodes": nodes_dict}
        stats["nodes_added"] = len(nodes_dict)

        with output_path.open("w") as f:
            yaml.dump(yaml_data, f)

    return stats
