"""Graph post-processing for redundancy removal.

Implements edge cleanup based on Chilean KG paper recommendations:
- Remove transitive redundant edges (e.g., A->B->C implies A->C)
- Remove self-loops
- Clean up organization/location disambiguation
"""

import logging
from typing import Dict, Set, Tuple, List, TYPE_CHECKING

import networkx as nx

if TYPE_CHECKING:
    from ..graph import KnowledgeGraph

logger = logging.getLogger(__name__)


# Relation types that are transitive (strict, safe subset)
TRANSITIVE_RELATIONS = {
    "LOCATED_IN",  # If A in B, B in C, then A in C
    # Avoid EMPLOYED_BY transitivity (not always valid)
}


class GraphPostProcessor:
    """
    Post-processes knowledge graphs to remove redundant information.

    Based on Chilean KG paper (arXiv:2408.11975) graph cleanup rules.
    """

    def remove_redundant_edges(
        self, graph: "KnowledgeGraph", dry_run: bool = False
    ) -> Dict[str, int]:
        """
        Remove edges that can be inferred from existing paths.

        Args:
            graph: KnowledgeGraph to process (modified in place)
            dry_run: If True, report stats but don't modify graph

        Returns:
            Stats dict with counts of removed edges
        """
        stats = {
            "edges_removed": 0,
            "self_loops_removed": 0,
            "transitive_removed": 0,
        }

        # First pass: remove self-loops
        self_loops = list(nx.selfloop_edges(graph.graph, keys=True))
        for u, v, key in self_loops:
            if not dry_run:
                graph.graph.remove_edge(u, v, key=key)
            stats["self_loops_removed"] += 1
            stats["edges_removed"] += 1
            logger.debug(f"Removed self-loop on {u}")

        # Second pass: remove transitive redundancies
        edges_to_remove = self._find_transitive_redundancies(graph)

        for source, target, key in edges_to_remove:
            try:
                if not dry_run:
                    graph.graph.remove_edge(source, target, key=key)
                stats["transitive_removed"] += 1
                stats["edges_removed"] += 1
                logger.debug(f"Removed transitive edge {source} -> {target}")
            except nx.NetworkXError:
                pass  # Edge already removed

        logger.info(
            f"Post-processing complete: {stats['edges_removed']} edges removed "
            f"({stats['self_loops_removed']} self-loops, "
            f"{stats['transitive_removed']} transitive)"
        )

        return stats

    def _find_transitive_redundancies(
        self, graph: "KnowledgeGraph"
    ) -> List[Tuple[str, str, str]]:
        """
        Find edges that are redundant due to transitivity.

        For each transitive relation type, if A->B->C exists,
        then A->C is redundant and can be removed.
        """
        redundant = []

        for rel_type in TRANSITIVE_RELATIONS:
            # Get all edges of this type
            typed_edges = [
                (u, v, k, d)
                for u, v, k, d in graph.graph.edges(data=True, keys=True)
                if d.get("relation_type") == rel_type
            ]

            # Build adjacency for this relation type
            adjacency: Dict[str, Set[str]] = {}
            for u, v, k, d in typed_edges:
                if u not in adjacency:
                    adjacency[u] = set()
                adjacency[u].add(v)

            # For each edge A->C, check if path A->B->C exists
            for source, target, key, data in typed_edges:
                # Check if there's an intermediate node B where A->B and B->C
                if self._has_intermediate_path(source, target, adjacency):
                    redundant.append((source, target, key))

        return redundant

    def _has_intermediate_path(
        self, source: str, target: str, adjacency: Dict[str, Set[str]]
    ) -> bool:
        """
        Check if there's a path from source to target through an intermediate.

        Returns True if exists B where source->B and B->target.
        """
        if source not in adjacency:
            return False

        # Get all nodes reachable from source in one hop
        intermediates = adjacency.get(source, set())

        # Check if any intermediate can reach target
        for intermediate in intermediates:
            if intermediate == target:
                continue  # Skip direct edge
            if target in adjacency.get(intermediate, set()):
                return True

        return False

    def validate_location_hierarchy(
        self, graph: "KnowledgeGraph"
    ) -> List[Dict[str, str]]:
        """
        Validate LOCATED_IN relations form a proper hierarchy.

        Checks for:
        1. Self-references (A LOCATED_IN A)
        2. Cycles (A -> B -> C -> A)
        3. Hierarchy violations (country LOCATED_IN city)

        Args:
            graph: KnowledgeGraph to validate

        Returns:
            List of warning dicts with issue details
        """
        warnings: List[Dict[str, str]] = []

        # Get all LOCATED_IN edges
        located_in_edges = [
            (u, v, k, d)
            for u, v, k, d in graph.graph.edges(data=True, keys=True)
            if d.get("relation_type") == "LOCATED_IN"
        ]

        # Check 1: Self-references
        for source, target, key, data in located_in_edges:
            if source == target:
                warnings.append({
                    "issue": "self_reference",
                    "source_id": source,
                    "target_id": target,
                    "relation_id": key,
                    "message": f"Location {source} is LOCATED_IN itself",
                })

        # Build subgraph of LOCATED_IN relations for cycle detection
        location_subgraph = nx.DiGraph()
        for source, target, key, data in located_in_edges:
            if source != target:  # Skip self-loops for cycle check
                location_subgraph.add_edge(source, target)

        # Check 2: Cycles
        try:
            cycles = list(nx.simple_cycles(location_subgraph))
            for cycle in cycles:
                warnings.append({
                    "issue": "cycle",
                    "source_id": cycle[0] if cycle else "",
                    "target_id": cycle[-1] if cycle else "",
                    "message": f"Cycle detected in LOCATED_IN: {' -> '.join(cycle)}",
                })
        except nx.NetworkXError:
            pass  # No cycles

        # Check 3: Hierarchy violations using location_type
        location_type_rank = {
            "country": 1,
            "province": 2,
            "state": 2,
            "department": 2,
            "region": 2,
            "municipality": 3,
            "city": 3,
            "town": 3,
            "district": 4,
            "neighborhood": 5,
            "barrio": 5,
            "address": 6,
            "property": 6,
            "sugar_mill": 6,
            "finca": 6,
        }

        for source, target, key, data in located_in_edges:
            source_node = graph.graph.nodes.get(source, {})
            target_node = graph.graph.nodes.get(target, {})

            source_type = source_node.get("location_type", "").lower()
            target_type = target_node.get("location_type", "").lower()

            source_rank = location_type_rank.get(source_type, 0)
            target_rank = location_type_rank.get(target_type, 0)

            # If both have known types and source is higher rank (smaller number) than target
            if source_rank > 0 and target_rank > 0 and source_rank < target_rank:
                warnings.append({
                    "issue": "hierarchy_violation",
                    "source_id": source,
                    "target_id": target,
                    "relation_id": key,
                    "source_type": source_type,
                    "target_type": target_type,
                    "message": (
                        f"Hierarchy violation: {source_type} ({source}) "
                        f"cannot be LOCATED_IN {target_type} ({target})"
                    ),
                })

        if warnings:
            logger.warning(
                f"Location hierarchy validation found {len(warnings)} issues"
            )
        else:
            logger.info("Location hierarchy validation passed")

        return warnings
