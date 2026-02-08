"""Generate per-entity descriptions using Haiku for cheap, fast prose summaries."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from farmer_factory.config.settings import settings
from farmer_factory.extract.api_client import ClaudeAPIClient

if TYPE_CHECKING:
    from farmer_factory.intake.manifest import CaseFocus

logger = logging.getLogger(__name__)

ENTITY_DESCRIPTION_PROMPT = """You are a forensic research analyst writing a brief profile for a person, property, organization, or location found in historical documents related to property restitution.

**CRITICAL CONSTRAINTS:**
1. State ONLY what the documents show — never infer or speculate
2. NEVER make legal conclusions about ownership, validity, or case strength
3. Write in past tense, 2-3 sentences maximum
4. Be specific: use names, dates, and document references when available
5. This is AI-generated research context, not a verified record

**Entity:**
- Name: {name}
- Type: {entity_type}
{metadata_section}

**Connections:**
{connections_section}

**Source Documents:** {source_doc_count} document(s)

Write a 2-3 sentence description of this entity based solely on what the documents reveal. Focus on who/what they are, their role in the documentary record, and key relationships. Be concise and factual."""


def _build_metadata_section(entity: dict[str, Any]) -> str:
    """Build metadata lines from entity fields."""
    skip_keys = {
        "id", "name", "entity_type", "verification", "extracted_from",
        "processing_metadata", "description", "roleLabel",
    }
    lines = []
    for key, value in entity.items():
        if key in skip_keys or value is None or value == "":
            continue
        label = key.replace("_", " ").title()
        lines.append(f"- {label}: {value}")
    return "\n".join(lines) if lines else "- No additional metadata"


def _build_connections_section(
    entity_id: str, links: list[dict[str, Any]], nodes_by_id: dict[str, dict[str, Any]]
) -> str:
    """Build connections context from graph links."""
    connections = []
    for link in links:
        if link["source"] == entity_id:
            target = nodes_by_id.get(link["target"], {})
            connections.append(
                f"- {link.get('relation_type', '?')} → {target.get('name', link['target'])} ({target.get('entity_type', '?')})"
            )
        elif link["target"] == entity_id:
            source = nodes_by_id.get(link["source"], {})
            connections.append(
                f"- {source.get('name', link['source'])} ({source.get('entity_type', '?')}) → {link.get('relation_type', '?')} → this entity"
            )
    return "\n".join(connections[:15]) if connections else "No connections found"


def generate_entity_descriptions(
    case_id: str,
    max_cost: float = 0.50,
    case_focus: CaseFocus | None = None,
) -> Path:
    """Generate descriptions for all non-DOCUMENT entities, saved to entity_descriptions.json.

    Reads graph_data.json for entity metadata and connections, generates prose
    descriptions via Haiku, and writes a separate {entity_id: description} map.
    Survives rebuild-graph and apply-merges since it's a separate file.

    Args:
        case_id: Case identifier
        max_cost: Cost ceiling in USD (default $0.50 — generous for Haiku)
        case_focus: Optional case-level focus configuration

    Returns:
        Path to entity_descriptions.json
    """
    output_dir = Path("cases") / case_id / "output"
    graph_path = output_dir / "graph_data.json"
    descriptions_path = output_dir / "entity_descriptions.json"

    if not graph_path.exists():
        raise FileNotFoundError(f"graph_data.json not found: {graph_path}")

    graph_data = json.loads(graph_path.read_text(encoding="utf-8"))
    nodes = graph_data.get("nodes", [])
    links = graph_data.get("links", [])

    nodes_by_id = {n["id"]: n for n in nodes}

    # Load existing descriptions to skip already-generated ones
    existing: dict[str, str] = {}
    if descriptions_path.exists():
        existing = json.loads(descriptions_path.read_text(encoding="utf-8"))

    # Filter to non-DOCUMENT entities without an existing description
    targets = [
        n for n in nodes
        if n.get("entity_type") != "DOCUMENT" and n["id"] not in existing
    ]

    if not targets:
        logger.info("All entities already have descriptions, nothing to generate")
        return descriptions_path

    logger.info(f"Generating descriptions for {len(targets)} entities using Haiku")

    client = ClaudeAPIClient()
    total_cost = 0.0
    generated = 0

    for entity in targets:
        if total_cost >= max_cost:
            logger.warning(f"Cost ceiling reached (${total_cost:.4f}/${max_cost:.2f}), stopping")
            break

        entity_id = entity["id"]
        name = entity.get("name", entity_id)
        entity_type = entity.get("entity_type", "UNKNOWN")

        metadata_section = _build_metadata_section(entity)
        connections_section = _build_connections_section(entity_id, links, nodes_by_id)

        source_docs = entity.get("extracted_from", "")
        source_doc_count = len([s for s in source_docs.split(",") if s.strip()]) if source_docs else 0

        focus_section = ""
        if case_focus is not None:
            focus_text = case_focus.to_prompt_section()
            if focus_text:
                focus_section = f"\n{focus_text}\n"

        prompt = f"{focus_section}{ENTITY_DESCRIPTION_PROMPT}".format(
            name=name,
            entity_type=entity_type,
            metadata_section=metadata_section,
            connections_section=connections_section,
            source_doc_count=source_doc_count,
        )

        try:
            response = client.call_standard(
                prompt=prompt,
                model=settings.claude_model,  # Haiku
                max_retries=2,
                api_timeout=30,
            )

            description = response.strip().strip('"')
            existing[entity_id] = description
            generated += 1

            cost = ClaudeAPIClient._compute_cost(
                settings.claude_model,
                int(len(prompt.split()) * 1.3),
                int(len(description.split()) * 1.3),
            )
            total_cost += cost

            logger.info(f"  [{generated}/{len(targets)}] {name} — ${cost:.4f}")

        except Exception as e:
            logger.warning(f"Failed to generate description for {name}: {e}")
            continue

    # Write descriptions map
    descriptions_path.write_text(
        json.dumps(existing, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    logger.info(
        f"Done: {generated}/{len(targets)} descriptions generated, "
        f"total cost ${total_cost:.4f}"
    )
    return descriptions_path
