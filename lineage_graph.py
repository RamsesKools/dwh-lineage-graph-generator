"""Graph operations for lineage analysis using NetworkX."""

from typing import Literal

import networkx as nx

from metadata import Connection, Node

FilterDirection = Literal["upstream", "downstream", "both"]


class LineageGraph:
    """Graph operations for data lineage analysis.

    Uses NetworkX for efficient graph traversal and filtering operations.
    """

    def __init__(self, nodes: list[Node], connections: list[Connection]) -> None:
        """Initialize lineage graph.

        Args:
            nodes: List of all nodes in the lineage
            connections: List of all connections between nodes
        """
        self.nodes = {node.id: node for node in nodes}
        self.connections = connections
        self.graph = self._build_graph(nodes, connections)

    def _build_graph(
        self, nodes: list[Node], connections: list[Connection]
    ) -> nx.DiGraph:
        """Build NetworkX directed graph from nodes and connections.

        Args:
            nodes: List of nodes
            connections: List of connections

        Returns:
            NetworkX directed graph
        """
        G = nx.DiGraph()

        # Add nodes with their data as attributes
        for node in nodes:
            G.add_node(node.id, node=node)

        # Add edges with connection data as attributes
        for conn in connections:
            G.add_edge(conn.from_id, conn.to_id, connection=conn)

        return G

    def get_upstream_nodes(
        self, node_id: str, max_depth: int | None = None
    ) -> set[str]:
        """Get all upstream node IDs (ancestors).

        Args:
            node_id: The node to find upstream dependencies for
            max_depth: Maximum depth to traverse (None = unlimited)

        Returns:
            Set of upstream node IDs
        """
        if node_id not in self.graph:
            return set()

        if max_depth is None:
            # Use NetworkX built-in for unlimited depth
            return nx.ancestors(self.graph, node_id)

        # BFS with depth limit
        upstream = set()
        visited = {node_id}
        queue = [(node_id, 0)]

        while queue:
            current, depth = queue.pop(0)
            if depth >= max_depth:
                continue

            for predecessor in self.graph.predecessors(current):
                if predecessor not in visited:
                    visited.add(predecessor)
                    upstream.add(predecessor)
                    queue.append((predecessor, depth + 1))

        return upstream

    def get_downstream_nodes(
        self, node_id: str, max_depth: int | None = None
    ) -> set[str]:
        """Get all downstream node IDs (descendants).

        Args:
            node_id: The node to find downstream dependencies for
            max_depth: Maximum depth to traverse (None = unlimited)

        Returns:
            Set of downstream node IDs
        """
        if node_id not in self.graph:
            return set()

        if max_depth is None:
            # Use NetworkX built-in for unlimited depth
            return nx.descendants(self.graph, node_id)

        # BFS with depth limit
        downstream = set()
        visited = {node_id}
        queue = [(node_id, 0)]

        while queue:
            current, depth = queue.pop(0)
            if depth >= max_depth:
                continue

            for successor in self.graph.successors(current):
                if successor not in visited:
                    visited.add(successor)
                    downstream.add(successor)
                    queue.append((successor, depth + 1))

        return downstream

    def get_direct_connections(self, node_id: str) -> set[str]:
        """Get directly connected node IDs (both upstream and downstream).

        Args:
            node_id: The node to find direct connections for

        Returns:
            Set of directly connected node IDs
        """
        if node_id not in self.graph:
            return set()

        upstream = set(self.graph.predecessors(node_id))
        downstream = set(self.graph.successors(node_id))

        return upstream | downstream

    def get_subgraph(
        self,
        focus_node_ids: list[str],
        direction: FilterDirection = "both",
        max_depth: int | None = None,
    ) -> tuple[list[Node], list[Connection]]:
        """Get filtered subgraph based on focus nodes.

        Args:
            focus_node_ids: Node IDs to focus on
            direction: Which direction to traverse ("upstream", "downstream", "both")
            max_depth: Maximum depth to traverse (None = unlimited)

        Returns:
            Tuple of (filtered nodes, filtered connections)
        """
        # Start with focus nodes
        selected_nodes = set(focus_node_ids)

        # Add connected nodes based on direction
        for node_id in focus_node_ids:
            if node_id not in self.graph:
                continue

            if direction in ("upstream", "both"):
                selected_nodes.update(self.get_upstream_nodes(node_id, max_depth))

            if direction in ("downstream", "both"):
                selected_nodes.update(self.get_downstream_nodes(node_id, max_depth))

        # Extract subgraph
        subgraph = self.graph.subgraph(selected_nodes)

        # Convert back to our data types
        nodes = [self.nodes[node_id] for node_id in subgraph.nodes()]
        connections = [
            data["connection"] for _, _, data in subgraph.edges(data=True)
        ]

        return nodes, connections

    def get_direct_subgraph(
        self, focus_node_ids: list[str]
    ) -> tuple[list[Node], list[Connection]]:
        """Get subgraph with only direct connections to focus nodes.

        Args:
            focus_node_ids: Node IDs to focus on

        Returns:
            Tuple of (filtered nodes, filtered connections)
        """
        selected_nodes = set(focus_node_ids)

        # Add directly connected nodes
        for node_id in focus_node_ids:
            if node_id in self.graph:
                selected_nodes.update(self.get_direct_connections(node_id))

        # Extract subgraph
        subgraph = self.graph.subgraph(selected_nodes)

        # Convert back to our data types
        nodes = [self.nodes[node_id] for node_id in subgraph.nodes()]
        connections = [
            data["connection"] for _, _, data in subgraph.edges(data=True)
        ]

        return nodes, connections

    def has_node(self, node_id: str) -> bool:
        """Check if node exists in graph.

        Args:
            node_id: Node ID to check

        Returns:
            True if node exists, False otherwise
        """
        return node_id in self.graph

    def is_acyclic(self) -> bool:
        """Check if the graph is a directed acyclic graph (DAG).

        Returns:
            True if graph is acyclic, False if cycles exist
        """
        return nx.is_directed_acyclic_graph(self.graph)

    def find_cycles(self) -> list[list[str]]:
        """Find all cycles in the graph.

        Returns:
            List of cycles, where each cycle is a list of node IDs
        """
        try:
            cycles = list(nx.simple_cycles(self.graph))
            return cycles
        except nx.NetworkXNoCycle:
            return []

    def get_all_paths(self, from_node_id: str, to_node_id: str) -> list[list[str]]:
        """Get all simple paths between two nodes.

        Args:
            from_node_id: Starting node ID
            to_node_id: Ending node ID

        Returns:
            List of paths, where each path is a list of node IDs
        """
        if from_node_id not in self.graph or to_node_id not in self.graph:
            return []

        try:
            paths = list(nx.all_simple_paths(self.graph, from_node_id, to_node_id))
            return paths
        except nx.NetworkXNoPath:
            return []
