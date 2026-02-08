"""Resolve orphan relations against the full case entity set.

Orphan relations are relations where the LLM identified a relationship
but the entity matcher couldn't find one or both entities within the
same document's extraction. After all documents are processed and
entities deduplicated, many orphans become resolvable against the
full graph.
"""

import json
import logging
import uuid
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _match_entity_in_graph(
    entity_name: str,
    nodes: list[dict[str, Any]],
) -> str | None:
    """Match an entity name against the full graph node set.

    Uses the same multi-step matching as LLM extraction:
    1. Exact name match (case-insensitive)
    2. Fuzzy match (SequenceMatcher >= 0.75)
    3. Substring containment (min 3 chars)

    Args:
        entity_name: Raw entity name from orphan relation
        nodes: List of graph node dicts with 'id' and 'name'

    Returns:
        Node ID if matched, None otherwise
    """
    normalized = entity_name.lower().strip()

    # Step 1: Exact match
    for node in nodes:
        name = node.get("name", "")
        if name.lower().strip() == normalized:
            return node["id"]

    # Step 2: Fuzzy match
    best_id = None
    best_score = 0.0
    for node in nodes:
        name = node.get("name", "")
        score = SequenceMatcher(None, normalized, name.lower().strip()).ratio()
        if score >= 0.75 and score > best_score:
            best_id = node["id"]
            best_score = score

    if best_id:
        logger.info(f"Fuzzy matched '{entity_name}' (score: {best_score:.2f})")
        return best_id

    # Step 3: Substring containment
    for node in nodes:
        name = node.get("name", "").lower().strip()
        if len(normalized) >= 3 and len(name) >= 3:
            if normalized in name or name in normalized:
                logger.info(f"Substring matched '{entity_name}' → '{node['name']}'")
                return node["id"]

    return None


def resolve_orphans(case_id: str, dry_run: bool = False) -> dict[str, Any]:
    """Resolve orphan relations from extraction JSONs against the full graph.

    Scans all extraction JSONs for unmatched_relations in metadata,
    attempts to match entity names against the full graph node set,
    and adds resolved relations to graph_data.json.

    Args:
        case_id: Case identifier
        dry_run: If True, report what would be resolved without modifying graph

    Returns:
        Dict with resolution stats
    """
    case_dir = Path("cases") / case_id
    graph_path = case_dir / "output" / "graph_data.json"
    extractions_dir = case_dir / "extractions"

    if not graph_path.exists():
        raise FileNotFoundError(f"graph_data.json not found at {graph_path}")
    if not extractions_dir.exists():
        raise FileNotFoundError(f"Extractions not found at {extractions_dir}")

    # Load graph
    graph_data = json.loads(graph_path.read_text(encoding="utf-8"))
    nodes = graph_data.get("nodes", [])
    links = graph_data.get("links", [])

    # Build set of existing relation signatures to avoid duplicates
    existing_rels = set()
    for link in links:
        sig = (link.get("source"), link.get("target"), link.get("relation_type"))
        existing_rels.add(sig)

    # Collect all orphan relations from extractions
    orphans: list[dict[str, Any]] = []
    for f in sorted(extractions_dir.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        metadata = data.get("processing_metadata", {})
        llm_meta = metadata.get("llm_metadata", {})
        unmatched = llm_meta.get("unmatched_relations", [])
        orphans.extend(unmatched)

    if not orphans:
        logger.info("No orphan relations found")
        return {"total_orphans": 0, "resolved": 0, "still_unmatched": 0}

    logger.info(f"Found {len(orphans)} orphan relations to resolve")

    resolved = []
    still_unmatched = []

    for orphan in orphans:
        source_name = orphan["source_entity"]
        target_name = orphan["target_entity"]
        rel_type = orphan["relation_type"]

        source_id = _match_entity_in_graph(source_name, nodes)
        target_id = _match_entity_in_graph(target_name, nodes)

        if source_id and target_id:
            # Check for duplicate
            sig = (source_id, target_id, rel_type)
            if sig in existing_rels:
                logger.info(
                    f"Skipping duplicate: {source_name} --[{rel_type}]--> {target_name}"
                )
                continue

            resolved.append(
                {
                    "source_id": source_id,
                    "target_id": target_id,
                    "relation_type": rel_type,
                    "source_name": source_name,
                    "target_name": target_name,
                    "confidence": orphan.get("confidence", 0.7),
                    "evidence": orphan.get("evidence", ""),
                    "document_id": orphan.get("document_id", ""),
                }
            )
            existing_rels.add(sig)
        else:
            still_unmatched.append(
                {
                    **orphan,
                    "source_resolved": source_id is not None,
                    "target_resolved": target_id is not None,
                }
            )

    # Report
    for r in resolved:
        logger.info(
            f"RESOLVED: {r['source_name']} --[{r['relation_type']}]--> {r['target_name']}"
        )
    for u in still_unmatched:
        src_mark = "?" if not u["source_resolved"] else "ok"
        tgt_mark = "?" if not u["target_resolved"] else "ok"
        logger.warning(
            f"UNRESOLVED: [{src_mark}] {u['source_entity']} "
            f"--[{u['relation_type']}]--> [{tgt_mark}] {u['target_entity']}"
        )

    # Apply to graph if not dry run
    if resolved and not dry_run:
        for r in resolved:
            link = {
                "id": f"orphan_resolved_{uuid.uuid4().hex[:8]}",
                "source": r["source_id"],
                "target": r["target_id"],
                "relation_type": r["relation_type"],
                "document_id": r["document_id"],
                "evidence": r["evidence"],
                "date": None,
                "notes": "Resolved from orphan relation (cross-document match)",
                "verification": {
                    "tier": "TIER_3_AI",
                    "confidence": r["confidence"],
                    "verified_by": None,
                    "verified_at": None,
                    "notes": "Orphan relation resolved against full entity set",
                },
            }
            links.append(link)

        graph_data["links"] = links
        graph_path.write_text(
            json.dumps(graph_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info(f"Added {len(resolved)} relations to graph")

    return {
        "total_orphans": len(orphans),
        "resolved": len(resolved),
        "still_unmatched": len(still_unmatched),
        "details": {
            "resolved": resolved,
            "unmatched": still_unmatched,
        },
    }
