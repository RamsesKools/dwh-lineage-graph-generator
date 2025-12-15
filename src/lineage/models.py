"""Data structures for representing data warehouse lineage."""

from dataclasses import dataclass, field
from typing import cast

from lineage.config import DEFAULT_CONNECTION_TYPE, DataType, DataLevel, ConnectionType


@dataclass
class Node:
    """Represents a data object in the warehouse lineage.

    Attributes:
        id: Unique identifier for the node
        label: Display name for the node
        data_type: Type of data object (determines shape in diagram)
        data_level: Level in data architecture (determines color/fill), optional during extraction
        select_from: List of node IDs this node selects from
    """

    id: str
    label: str
    data_type: DataType = field(default="unknown")
    data_level: DataLevel = field(default="unknown")
    select_from: list[str] = field(default_factory=list[str])

    def __post_init__(self):
        """Validate and normalize field values after initialization."""
        if not isinstance(self.id, str) or not self.id:
            raise ValueError("id must be a non-empty string")

        if not isinstance(self.label, str) or not self.label:
            raise ValueError("label must be a non-empty string")

        if self.data_type is None or self.data_type == "":
            self.data_type = "unknown"

        if self.data_level is None or self.data_level == "":
            self.data_level = "unknown"

        if not isinstance(self.select_from, list):
            raise ValueError("select_from must be a list")
        if not all(isinstance(item, str) for item in self.select_from):
            raise ValueError("select_from must contain only strings")


@dataclass
class Connection:
    """Represents a data flow connection between nodes.

    Attributes:
        from_id: Source node identifier
        to_id: Target node identifier
        connection_type: Type of connection (determines arrow style)
    """

    from_id: str
    to_id: str
    connection_type: ConnectionType = cast(ConnectionType, DEFAULT_CONNECTION_TYPE)
