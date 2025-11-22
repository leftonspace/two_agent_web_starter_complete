"""
Flow Graph Construction

Directed graph representation of flow execution paths with support
for conditional routing, parallel execution, and visualization.
"""

from typing import Dict, List, Set, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque


class NodeType(str, Enum):
    """Types of flow nodes"""
    START = "start"
    STEP = "step"
    ROUTER = "router"
    END = "end"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    JOIN = "join"


@dataclass
class FlowNode:
    """Node in the flow graph"""
    name: str
    type: NodeType
    handler: Optional[Callable] = None
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Connections
    next_nodes: List[str] = field(default_factory=list)
    previous_nodes: List[str] = field(default_factory=list)

    # Conditions for conditional nodes
    conditions: Dict[str, Callable] = field(default_factory=dict)

    # For parallel nodes
    parallel_nodes: List[str] = field(default_factory=list)

    # Configuration
    timeout: Optional[int] = None
    retries: int = 0

    def add_next(self, node_name: str):
        """Add a next node"""
        if node_name not in self.next_nodes:
            self.next_nodes.append(node_name)

    def add_previous(self, node_name: str):
        """Add a previous node"""
        if node_name not in self.previous_nodes:
            self.previous_nodes.append(node_name)

    def remove_next(self, node_name: str):
        """Remove a next node"""
        if node_name in self.next_nodes:
            self.next_nodes.remove(node_name)

    def remove_previous(self, node_name: str):
        """Remove a previous node"""
        if node_name in self.previous_nodes:
            self.previous_nodes.remove(node_name)

    def is_start(self) -> bool:
        """Check if this is a start node"""
        return self.type == NodeType.START or len(self.previous_nodes) == 0

    def is_end(self) -> bool:
        """Check if this is an end node"""
        return self.type == NodeType.END or len(self.next_nodes) == 0

    def is_router(self) -> bool:
        """Check if this is a router node"""
        return self.type in [NodeType.ROUTER, NodeType.CONDITIONAL]

    def is_parallel(self) -> bool:
        """Check if this is a parallel node"""
        return self.type == NodeType.PARALLEL

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary"""
        return {
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "next_nodes": self.next_nodes,
            "previous_nodes": self.previous_nodes,
            "metadata": self.metadata
        }


@dataclass
class FlowEdge:
    """Edge between flow nodes"""
    source: str
    target: str
    condition: Optional[Callable] = None
    label: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert edge to dictionary"""
        return {
            "source": self.source,
            "target": self.target,
            "label": self.label,
            "metadata": self.metadata
        }


class FlowGraph:
    """Directed graph representing a flow"""

    def __init__(self, name: str = "flow"):
        self.name = name
        self.nodes: Dict[str, FlowNode] = {}
        self.edges: List[FlowEdge] = []
        self._start_node: Optional[str] = None
        self._end_nodes: Set[str] = set()

    def add_node(self, node: FlowNode) -> 'FlowGraph':
        """Add a node to the graph"""
        self.nodes[node.name] = node

        if node.type == NodeType.START:
            self._start_node = node.name
        elif node.type == NodeType.END:
            self._end_nodes.add(node.name)

        return self

    def remove_node(self, node_name: str) -> 'FlowGraph':
        """Remove a node from the graph"""
        if node_name not in self.nodes:
            return self

        node = self.nodes[node_name]

        # Remove edges
        self.edges = [e for e in self.edges if e.source != node_name and e.target != node_name]

        # Update connections in other nodes
        for other_name, other_node in self.nodes.items():
            other_node.remove_next(node_name)
            other_node.remove_previous(node_name)

        # Remove from special sets
        if node_name == self._start_node:
            self._start_node = None
        self._end_nodes.discard(node_name)

        del self.nodes[node_name]
        return self

    def add_edge(self, source: str, target: str, condition: Optional[Callable] = None, label: str = "") -> 'FlowGraph':
        """Add an edge between nodes"""
        if source not in self.nodes:
            raise ValueError(f"Source node '{source}' not found")
        if target not in self.nodes:
            raise ValueError(f"Target node '{target}' not found")

        edge = FlowEdge(source, target, condition, label)
        self.edges.append(edge)

        # Update node connections
        self.nodes[source].add_next(target)
        self.nodes[target].add_previous(source)

        return self

    def remove_edge(self, source: str, target: str) -> 'FlowGraph':
        """Remove an edge between nodes"""
        self.edges = [e for e in self.edges if not (e.source == source and e.target == target)]

        if source in self.nodes and target in self.nodes:
            self.nodes[source].remove_next(target)
            self.nodes[target].remove_previous(source)

        return self

    def add_parallel(self, source: str, parallel_nodes: List[str], join_node: str) -> 'FlowGraph':
        """Add parallel execution paths"""
        # Create parallel split node
        split_node = FlowNode(
            name=f"{source}_parallel_split",
            type=NodeType.PARALLEL,
            parallel_nodes=parallel_nodes
        )
        self.add_node(split_node)
        self.add_edge(source, split_node.name)

        # Connect to parallel nodes
        for node in parallel_nodes:
            if node in self.nodes:
                self.add_edge(split_node.name, node)

        # Create join node
        join = FlowNode(
            name=f"{source}_parallel_join",
            type=NodeType.JOIN
        )
        self.add_node(join)

        # Connect parallel nodes to join
        for node in parallel_nodes:
            if node in self.nodes:
                self.add_edge(node, join.name)

        # Connect join to next
        if join_node in self.nodes:
            self.add_edge(join.name, join_node)

        return self

    def add_conditional(self, source: str, conditions: Dict[str, str], default: Optional[str] = None) -> 'FlowGraph':
        """Add conditional branching"""
        cond_node = FlowNode(
            name=f"{source}_conditional",
            type=NodeType.CONDITIONAL
        )
        self.add_node(cond_node)
        self.add_edge(source, cond_node.name)

        # Add conditional edges
        for condition_name, target in conditions.items():
            if target in self.nodes:
                self.add_edge(
                    cond_node.name,
                    target,
                    label=condition_name
                )

        # Add default edge if specified
        if default and default in self.nodes:
            self.add_edge(cond_node.name, default, label="default")

        return self

    def get_node(self, node_name: str) -> Optional[FlowNode]:
        """Get a node by name"""
        return self.nodes.get(node_name)

    def get_start_node(self) -> Optional[FlowNode]:
        """Get the start node"""
        if self._start_node:
            return self.nodes.get(self._start_node)

        # Find nodes with no predecessors
        for node in self.nodes.values():
            if node.is_start():
                return node

        return None

    def get_end_nodes(self) -> List[FlowNode]:
        """Get all end nodes"""
        end_nodes = []
        for node in self.nodes.values():
            if node.is_end():
                end_nodes.append(node)
        return end_nodes

    def get_next_nodes(self, node_name: str) -> List[FlowNode]:
        """Get next nodes for a given node"""
        if node_name not in self.nodes:
            return []

        node = self.nodes[node_name]
        return [self.nodes[name] for name in node.next_nodes if name in self.nodes]

    def get_previous_nodes(self, node_name: str) -> List[FlowNode]:
        """Get previous nodes for a given node"""
        if node_name not in self.nodes:
            return []

        node = self.nodes[node_name]
        return [self.nodes[name] for name in node.previous_nodes if name in self.nodes]

    def get_edge(self, source: str, target: str) -> Optional[FlowEdge]:
        """Get edge between two nodes"""
        for edge in self.edges:
            if edge.source == source and edge.target == target:
                return edge
        return None

    def get_path(self, start: str, end: str) -> Optional[List[str]]:
        """Find a path between two nodes using BFS"""
        if start not in self.nodes or end not in self.nodes:
            return None

        queue = deque([(start, [start])])
        visited = set()

        while queue:
            current, path = queue.popleft()

            if current == end:
                return path

            if current in visited:
                continue

            visited.add(current)

            for next_node in self.nodes[current].next_nodes:
                if next_node not in visited:
                    queue.append((next_node, path + [next_node]))

        return None

    def get_all_paths(self, start: str, end: str) -> List[List[str]]:
        """Find all paths between two nodes"""
        if start not in self.nodes or end not in self.nodes:
            return []

        all_paths = []

        def dfs(current: str, path: List[str], visited: Set[str]):
            if current == end:
                all_paths.append(path[:])
                return

            for next_node in self.nodes[current].next_nodes:
                if next_node not in visited:
                    visited.add(next_node)
                    path.append(next_node)
                    dfs(next_node, path, visited)
                    path.pop()
                    visited.remove(next_node)

        dfs(start, [start], {start})
        return all_paths

    def validate(self) -> List[str]:
        """Validate the graph structure"""
        errors = []

        # Check for start node
        if not self.get_start_node():
            errors.append("No start node found")

        # Check for unreachable nodes
        reachable = self._get_reachable_nodes()
        unreachable = set(self.nodes.keys()) - reachable
        if unreachable:
            errors.append(f"Unreachable nodes: {unreachable}")

        # Check for cycles (warning, not always an error)
        if self._has_cycle():
            errors.append("Graph contains cycles")

        # Check for dead ends (except end nodes)
        for node_name, node in self.nodes.items():
            if not node.is_end() and node.type != NodeType.END and len(node.next_nodes) == 0:
                errors.append(f"Dead end node (no next): {node_name}")

        # Check edge consistency
        for edge in self.edges:
            if edge.source not in self.nodes:
                errors.append(f"Edge references unknown source: {edge.source}")
            if edge.target not in self.nodes:
                errors.append(f"Edge references unknown target: {edge.target}")

        return errors

    def _get_reachable_nodes(self) -> Set[str]:
        """Get all nodes reachable from start"""
        start = self.get_start_node()
        if not start:
            return set()

        visited = set()
        stack = [start.name]

        while stack:
            current = stack.pop()
            if current in visited:
                continue

            visited.add(current)
            if current in self.nodes:
                stack.extend(self.nodes[current].next_nodes)

        return visited

    def _has_cycle(self) -> bool:
        """Check if graph has cycles using DFS"""
        visited = set()
        rec_stack = set()

        def visit(node_name: str) -> bool:
            visited.add(node_name)
            rec_stack.add(node_name)

            for next_node in self.nodes[node_name].next_nodes:
                if next_node not in visited:
                    if visit(next_node):
                        return True
                elif next_node in rec_stack:
                    return True

            rec_stack.remove(node_name)
            return False

        for node_name in self.nodes:
            if node_name not in visited:
                if visit(node_name):
                    return True

        return False

    def get_topological_order(self) -> List[str]:
        """Get nodes in topological order"""
        in_degree = {name: 0 for name in self.nodes}

        for node in self.nodes.values():
            for next_node in node.next_nodes:
                if next_node in in_degree:
                    in_degree[next_node] += 1

        queue = deque([name for name, degree in in_degree.items() if degree == 0])
        result = []

        while queue:
            current = queue.popleft()
            result.append(current)

            for next_node in self.nodes[current].next_nodes:
                if next_node in in_degree:
                    in_degree[next_node] -= 1
                    if in_degree[next_node] == 0:
                        queue.append(next_node)

        return result

    def visualize(self, format: str = "ascii") -> str:
        """Generate visualization of the graph"""
        if format == "ascii":
            return self._visualize_ascii()
        elif format == "dot":
            return self._visualize_dot()
        elif format == "mermaid":
            return self._visualize_mermaid()
        else:
            raise ValueError(f"Unknown format: {format}")

    def _visualize_ascii(self) -> str:
        """Generate ASCII art visualization"""
        lines = [f"Flow: {self.name}", "=" * 40]

        # Start from start node and traverse
        start = self.get_start_node()
        if not start:
            return "No start node found"

        visited = set()

        def traverse(node_name: str, indent: int = 0):
            if node_name in visited:
                lines.append(" " * indent + f"-> (see {node_name} above)")
                return

            visited.add(node_name)
            node = self.nodes[node_name]

            prefix = " " * indent + "-> " if indent > 0 else ""
            type_indicator = f"[{node.type.value}]" if node.type != NodeType.STEP else ""
            lines.append(f"{prefix}{node.name} {type_indicator}")

            for next_node in node.next_nodes:
                traverse(next_node, indent + 2)

        traverse(start.name)

        return "\n".join(lines)

    def _visualize_dot(self) -> str:
        """Generate Graphviz DOT format"""
        lines = ["digraph flow {", '  rankdir="TB";', '  node [shape=box];']

        # Add nodes
        for name, node in self.nodes.items():
            shape = {
                NodeType.START: "ellipse",
                NodeType.END: "ellipse",
                NodeType.ROUTER: "diamond",
                NodeType.CONDITIONAL: "diamond",
                NodeType.PARALLEL: "trapezium",
                NodeType.JOIN: "invtrapezium",
                NodeType.STEP: "box"
            }.get(node.type, "box")

            style = "filled" if node.type in [NodeType.START, NodeType.END] else ""
            color = {
                NodeType.START: "lightgreen",
                NodeType.END: "lightcoral",
                NodeType.ROUTER: "lightyellow",
                NodeType.CONDITIONAL: "lightyellow",
                NodeType.PARALLEL: "lightblue",
            }.get(node.type, "white")

            lines.append(f'  "{name}" [shape={shape}, style="{style}", fillcolor="{color}"];')

        # Add edges
        for edge in self.edges:
            label = f' [label="{edge.label}"]' if edge.label else ""
            lines.append(f'  "{edge.source}" -> "{edge.target}"{label};')

        lines.append("}")
        return "\n".join(lines)

    def _visualize_mermaid(self) -> str:
        """Generate Mermaid diagram format"""
        lines = ["graph TD"]

        # Add nodes with styling
        for name, node in self.nodes.items():
            shape_start, shape_end = {
                NodeType.START: ("([", "])"),
                NodeType.END: ("([", "])"),
                NodeType.ROUTER: ("{", "}"),
                NodeType.CONDITIONAL: ("{", "}"),
                NodeType.PARALLEL: ("[[", "]]"),
                NodeType.JOIN: ("[[", "]]"),
                NodeType.STEP: ("[", "]"),
            }.get(node.type, ("[", "]"))

            lines.append(f"    {name}{shape_start}{name}{shape_end}")

        # Add edges
        for edge in self.edges:
            if edge.label:
                lines.append(f"    {edge.source} -->|{edge.label}| {edge.target}")
            else:
                lines.append(f"    {edge.source} --> {edge.target}")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary"""
        return {
            "name": self.name,
            "nodes": {name: node.to_dict() for name, node in self.nodes.items()},
            "edges": [edge.to_dict() for edge in self.edges],
            "start_node": self._start_node,
            "end_nodes": list(self._end_nodes)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FlowGraph':
        """Create graph from dictionary"""
        graph = cls(name=data.get("name", "flow"))

        for name, node_data in data.get("nodes", {}).items():
            node = FlowNode(
                name=node_data["name"],
                type=NodeType(node_data["type"]),
                description=node_data.get("description", ""),
                next_nodes=node_data.get("next_nodes", []),
                previous_nodes=node_data.get("previous_nodes", []),
                metadata=node_data.get("metadata", {})
            )
            graph.nodes[name] = node

        for edge_data in data.get("edges", []):
            edge = FlowEdge(
                source=edge_data["source"],
                target=edge_data["target"],
                label=edge_data.get("label", ""),
                metadata=edge_data.get("metadata", {})
            )
            graph.edges.append(edge)

        graph._start_node = data.get("start_node")
        graph._end_nodes = set(data.get("end_nodes", []))

        return graph
