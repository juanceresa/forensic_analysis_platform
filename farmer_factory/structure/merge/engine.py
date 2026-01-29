"""Apply entity merges to rebuild graph_data.json without OCR or LLM calls.

Reads the current graph_data.json and confirmed merge groups, then produces
a new graph with entities merged, relations rewritten, and LLM-enriched
fields preserved.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .reader import (
    get_all_entity_groups,
    get_confirmed_merges,
    read_cross_type_relations,
)
from .writer import _compute_extractions_hash

logger = logging.getLogger(__name__)


def apply_merges(
    case_dir: Path,
    include_drafts: bool = False,
    output_path: Optional[Path] = None,
) -> Path:
    """Apply confirmed merges to graph_data.json.

    Reads the current graph, merges entities according to confirmed (or draft)
    merge groups, rewrites relations, and writes the result.

    This is idempotent — running twice produces the same result.
    No OCR, no extraction, no LLM calls — graph surgery only.

    Note: The graph_data.json already contains dedupe merges from processing.
    This function applies *additional* analyst-driven merges on top. If a merge
    references an entity already merged by dedupe, the missing ID is logged and
    skipped (not an error).

    Args:
        case_dir: Path to case directory (e.g., cases/CASE-ID).
        include_drafts: If True, also apply DRAFT merges (for preview).
        output_path: Override output path. Defaults to case output/graph_data.json.

    Returns:
        Path to the written graph_data.json.
    """
    if output_path is None:
        output_path = case_dir / "output" / "graph_data.json"

    # Load current graph
    graph_data = _load_graph(output_path)
    if graph_data is None:
        raise FileNotFoundError(f"No graph_data.json found at {output_path}")

    nodes: List[Dict[str, Any]] = graph_data.get("nodes", [])
    links: List[Dict[str, Any]] = graph_data.get("links", [])
    metadata: Dict[str, Any] = graph_data.get("metadata", {})

    # Check staleness
    current_hash = _compute_extractions_hash(case_dir)
    _check_staleness(case_dir, current_hash)

    # Build merge map: member_id → canonical_id
    merge_map = get_confirmed_merges(case_dir, include_drafts=include_drafts)

    merged_node_ids: Set[str] = set()

    if merge_map:
        logger.info(f"Applying {len(merge_map)} entity merges (include_drafts={include_drafts})")

        # Build node lookup
        node_by_id: Dict[str, Dict[str, Any]] = {n["id"]: n for n in nodes}

        # Validate merge references
        missing = {mid for mid in merge_map if mid not in node_by_id}
        if missing:
            logger.warning(f"Merge references {len(missing)} entity IDs not in graph, skipping: {missing}")
            merge_map = {k: v for k, v in merge_map.items() if k not in missing}

        missing_canonicals = {cid for cid in merge_map.values() if cid not in node_by_id}
        if missing_canonicals:
            logger.warning(
                f"Canonical IDs not in graph, skipping their merges: {missing_canonicals}"
            )
            merge_map = {k: v for k, v in merge_map.items() if v not in missing_canonicals}

        # Merge entity nodes
        for member_id, canonical_id in merge_map.items():
            member_node = node_by_id.get(member_id)
            canonical_node = node_by_id.get(canonical_id)
            if member_node and canonical_node:
                _merge_node_fields(canonical_node, member_node)
                merged_node_ids.add(member_id)

        # Remove merged nodes
        nodes = [n for n in nodes if n["id"] not in merged_node_ids]

        # Rewrite relations
        links = _rewrite_relations(links, merge_map)
    else:
        logger.info("No entity merges to apply")

    # Apply cross-type relation corrections (always, even without entity merges)
    links = _apply_cross_type_relations(case_dir, links, include_drafts)

    # Recompute metadata to reflect merged state
    metadata = _recompute_metadata(metadata, nodes, links)

    # Write result
    graph_data["nodes"] = nodes
    graph_data["links"] = links
    graph_data["metadata"] = metadata

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(graph_data, f, indent=2, ensure_ascii=False)

    logger.info(
        f"Wrote merged graph: {len(nodes)} nodes, {len(links)} links "
        f"({len(merged_node_ids)} entities merged)"
    )
    return output_path


def _load_graph(path: Path) -> Optional[Dict[str, Any]]:
    """Load graph_data.json if it exists."""
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def _check_staleness(case_dir: Path, current_hash: str) -> None:
    """Warn if any merge file has a stale extractions_hash."""
    for entity_type, entity_file in get_all_entity_groups(case_dir):
        if entity_file.extractions_hash and entity_file.extractions_hash != current_hash:
            logger.warning(
                f"{entity_type} merge file has stale extractions_hash "
                f"(file={entity_file.extractions_hash}, current={current_hash}). "
                f"Proceeding anyway."
            )


def _merge_node_fields(
    canonical: Dict[str, Any], member: Dict[str, Any]
) -> None:
    """Merge member node fields into canonical node.

    Canonical fields take precedence. Missing fields are filled from member.
    extracted_from is combined as comma-separated union.
    """
    # Combine extracted_from
    canonical_sources = set(
        s.strip()
        for s in canonical.get("extracted_from", "").split(",")
        if s.strip()
    )
    member_sources = set(
        s.strip()
        for s in member.get("extracted_from", "").split(",")
        if s.strip()
    )
    combined = canonical_sources | member_sources
    if combined:
        canonical["extracted_from"] = ",".join(sorted(combined))

    # Fill missing fields from member (canonical takes precedence)
    skip_fields = {"id", "entity_type", "extracted_from", "created_at", "updated_at"}
    for key, value in member.items():
        if key in skip_fields:
            continue
        if key not in canonical or canonical[key] is None:
            canonical[key] = value


def _rewrite_relations(
    links: List[Dict[str, Any]], merge_map: Dict[str, str]
) -> List[Dict[str, Any]]:
    """Rewrite relation endpoints to canonical IDs, dedup, drop self-loops."""
    rewritten: List[Dict[str, Any]] = []

    for link in links:
        source = merge_map.get(link["source"], link["source"])
        target = merge_map.get(link["target"], link["target"])

        # Drop self-loops
        if source == target:
            logger.debug(
                f"Dropping self-loop: {link['source']}→{link['target']} "
                f"(type={link.get('relation_type', '?')})"
            )
            continue

        link = {**link, "source": source, "target": target}
        rewritten.append(link)

    # Deduplicate: same (source, target, relation_type) → keep higher confidence
    seen: Dict[tuple, int] = {}
    for i, link in enumerate(rewritten):
        key = (link["source"], link["target"], link.get("relation_type", ""))
        if key in seen:
            existing_idx = seen[key]
            existing_conf = _get_link_confidence(rewritten[existing_idx])
            new_conf = _get_link_confidence(link)
            if new_conf > existing_conf:
                seen[key] = i
        else:
            seen[key] = i

    deduped = [rewritten[i] for i in sorted(seen.values())]
    dropped = len(rewritten) - len(deduped)
    if dropped:
        logger.info(f"Deduplicated {dropped} relations after merge rewriting")

    return deduped


def _get_link_confidence(link: Dict[str, Any]) -> float:
    """Extract confidence from a link dict."""
    verification = link.get("verification", {})
    if isinstance(verification, dict):
        return verification.get("confidence", 0.0)
    return 0.0


def _apply_cross_type_relations(
    case_dir: Path,
    links: List[Dict[str, Any]],
    include_drafts: bool,
) -> List[Dict[str, Any]]:
    """Add/update relations from cross_type_relations.yaml."""
    cross_file = read_cross_type_relations(case_dir)
    if cross_file is None:
        return links

    for rel in cross_file.relations:
        if rel.status == "DRAFT" and not include_drafts:
            continue

        # Check if this relation already exists
        exists = any(
            l["source"] == rel.source_id
            and l["target"] == rel.target_id
            and l.get("relation_type") == rel.relation_type
            for l in links
        )
        if not exists:
            links.append({
                "source": rel.source_id,
                "target": rel.target_id,
                "relation_type": rel.relation_type,
                "date": rel.date,
                "source_authority": rel.source,
            })

    return links


def _recompute_metadata(
    metadata: Dict[str, Any],
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Recompute metadata counts to reflect the post-merge graph state."""
    from collections import Counter

    metadata = dict(metadata)  # shallow copy

    metadata["entity_count"] = len(nodes)
    metadata["relation_count"] = len(links)

    type_counts: Counter = Counter()
    for node in nodes:
        etype = node.get("entity_type")
        if etype:
            type_counts[etype] += 1
    metadata["entity_type_summary"] = dict(type_counts)

    verification_dist: Counter = Counter()
    for node in nodes:
        tier = node.get("verification", {})
        if isinstance(tier, dict):
            tier = tier.get("tier", "TIER_3_AI")
        else:
            tier = "TIER_3_AI"
        verification_dist[tier] += 1
    metadata["verification_distribution"] = dict(verification_dist)

    return metadata
