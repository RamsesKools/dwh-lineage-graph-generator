"""Mermaid diagram generator for data warehouse lineage."""

from typing import Literal, get_args

from lineage.models import Connection, DataLevel, DataType, Node
from lineage.config import CONNECTION_STYLES, DATA_LEVEL_STYLES, NODE_SHAPES

Direction = Literal["LR", "RL", "TB", "BT"]


class MermaidGenerator:
    """Generates Mermaid diagram syntax from lineage data."""

    def __init__(
        self,
        nodes: list[Node],
        connections: list[Connection],
        direction: Direction = "LR",
    ) -> None:
        """Initialize the Mermaid generator.

        Args:
            nodes: List of nodes in the lineage
            connections: List of connections between nodes
            direction: Flow direction (LR=left-right, RL=right-left,
                      TB=top-bottom, BT=bottom-top)
        """
        self.nodes = nodes
        self.connections = connections
        self.direction = direction
        self._node_map = {node.id: node for node in nodes}

    def _sanitize_id(self, node_id: str) -> str:
        """Sanitize node ID for use in Mermaid diagram.

        Args:
            node_id: Original node identifier

        Returns:
            Sanitized identifier safe for Mermaid syntax
        """
        # Replace characters that might cause issues in Mermaid
        return node_id.replace("-", "_").replace(".", "_").replace(" ", "_")

    def _generate_node_definition(self, node: Node) -> str:
        """Generate Mermaid syntax for a single node.

        Args:
            node: Node to generate definition for

        Returns:
            Mermaid node definition string
        """
        safe_id = self._sanitize_id(node.id)
        prefix, suffix = NODE_SHAPES.get(node.data_type, ("[", "]"))
        return f"{safe_id}{prefix}\"{node.label}\"{suffix}"

    def _generate_connection_definition(self, connection: Connection) -> str:
        """Generate Mermaid syntax for a connection.

        Args:
            connection: Connection to generate definition for

        Returns:
            Mermaid connection definition string
        """
        from_id = self._sanitize_id(connection.from_id)
        to_id = self._sanitize_id(connection.to_id)
        arrow = CONNECTION_STYLES.get(connection.connection_type, "-->")
        return f"{from_id} {arrow} {to_id}"

    def _generate_class_definitions(self) -> list[str]:
        """Generate CSS class definitions for all data levels used.

        Returns:
            List of Mermaid classDef statements
        """
        # Collect unique data levels from nodes
        data_levels: set[str] = {node.data_level for node in self.nodes}

        class_defs = []
        for level in sorted(data_levels):
            style = DATA_LEVEL_STYLES.get(level, "unknown")
            if style:
                class_name = f"{level}Style"
                class_defs.append(f"classDef {class_name} {style}")

        return class_defs


    def _generate_class_assignments(self) -> list[str]:
        """Generate class assignments for all nodes.

        Returns:
            List of Mermaid class assignment statements
        """
        # Group nodes by data level
        level_groups: dict[str, list[str]] = {}
        for node in self.nodes:
            level = node.data_level
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(self._sanitize_id(node.id))

        # Generate class assignments
        assignments = []
        for level in sorted(level_groups.keys()):
            class_name = f"{level}Style"
            node_ids = ",".join(level_groups[level])
            assignments.append(f"class {node_ids} {class_name}")

        return assignments

    def generate(self) -> str:
        """Generate complete Mermaid diagram syntax.

        Returns:
            Complete Mermaid diagram as a string
        """
        lines = []

        # Graph header
        lines.append(f"graph {self.direction}")

        # Node definitions (sorted by ID for deterministic output)
        for node in sorted(self.nodes, key=lambda n: n.id):
            lines.append(self._generate_node_definition(node))

        # Add blank line for readability
        lines.append("")

        # Connection definitions (sorted by from_id, then to_id for deterministic output)
        for connection in sorted(self.connections, key=lambda c: (c.from_id, c.to_id)):
            lines.append(self._generate_connection_definition(connection))

        # Add blank line for readability
        lines.append("")

        # Class definitions
        class_defs = self._generate_class_definitions()
        lines.extend(class_defs)

        # Add blank line for readability
        if class_defs:
            lines.append("")

        # Class assignments
        class_assignments = self._generate_class_assignments()
        lines.extend(class_assignments)

        return "\n".join(lines)


def generate_legend() -> str:
    """Generate a legend showing all node types and data levels.

    The legend is structured with subgraphs stacked top to bottom,
    while content within each subgraph flows left to right.

    Returns:
        Complete Mermaid diagram showing all available styles
    """
    lines = []

    # Graph header - LR so subgraphs stack vertically
    lines.append("graph LR")
    lines.append("")

    # Section: Node Shapes by Data Type
    lines.append("subgraph shapes [Node Shapes by Data Type]")
    lines.append("direction TB")

    data_types: tuple[str, ...] = get_args(DataType)
    for idx, data_type in enumerate(data_types):
        node_id = f"shape_{idx}"
        prefix, suffix = NODE_SHAPES[data_type]
        label = data_type.replace("-", " ").title()
        lines.append(f"{node_id}{prefix}\"{label}\"{suffix}")

    lines.append("end")
    lines.append("")

    # Section: Data Levels (Colors)
    lines.append("subgraph levels [Data Levels and Colors]")
    lines.append("direction TB")

    data_levels: tuple[str, ...] = get_args(DataLevel)
    for idx, data_level in enumerate(data_levels):
        node_id = f"level_{idx}"
        label = data_level.capitalize()
        lines.append(f"{node_id}[\"{label}\"]")

    lines.append("end")
    lines.append("")

    # Section: Connection Types
    lines.append("subgraph connections [Connection Types]")
    lines.append("direction TB")

    conn_types = list(CONNECTION_STYLES.keys())
    for idx, conn_type in enumerate(conn_types):
        from_id = f"conn_from_{idx}"
        to_id = f"conn_to_{idx}"
        arrow = CONNECTION_STYLES[conn_type]
        label = conn_type.replace("-", " ").title()

        lines.append(f"{from_id}[\"{label}\"]")
        lines.append(f"{to_id}[\" \"]")
        lines.append(f"{from_id} {arrow} {to_id}")

    lines.append("end")
    lines.append("")

    # Class definitions
    for data_level in data_levels:
        style = DATA_LEVEL_STYLES[data_level]
        class_name = f"{data_level}Style"
        lines.append(f"classDef {class_name} {style}")

    lines.append("")

    # Class assignments for data levels
    for idx, data_level in enumerate(data_levels):
        node_id = f"level_{idx}"
        class_name = f"{data_level}Style"
        lines.append(f"class {node_id} {class_name}")

    return "\n".join(lines)
