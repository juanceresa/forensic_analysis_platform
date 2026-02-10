"""Write entity merge authority YAML files from dedupe results.

Generates DRAFT merge files from dedupe clusters, preserving existing
CONFIRMED entries when updating.
"""

import hashlib
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

from .models import (
    CrossTypeRelation,
    CrossTypeRelationsFile,
    EntityGroupFile,
    MergeGroup,
    MergeGroupMember,
    SameTypeRelation,
    UnmergedEntity,
)

logger = logging.getLogger(__name__)

# Entity type to filename mapping
ENTITY_TYPE_FILES = {
    "PERSON": "person_groups.yaml",
    "PROPERTY": "property_groups.yaml",
    "ORGANIZATION": "organization_groups.yaml",
    "LOCATION": "location_groups.yaml",
}


def _compute_extractions_hash(case_dir: Path) -> str:
    """Compute SHA-256 prefix of the extractions directory file listing."""
    extractions_dir = case_dir / "extractions"
    if not extractions_dir.exists():
        return ""
    files = sorted(f.name for f in extractions_dir.iterdir() if f.is_file())
    content = "\n".join(files)
    return hashlib.sha256(content.encode()).hexdigest()[:12]


def _entity_groups_dir(case_dir: Path) -> Path:
    """Get or create the entity_groups directory for a case."""
    groups_dir = case_dir / "entity_groups"
    groups_dir.mkdir(exist_ok=True)
    return groups_dir


def _load_existing_file(path: Path) -> Optional[EntityGroupFile]:
    """Load existing entity group file, returning None if missing."""
    if not path.exists():
        return None
    with open(path) as f:
        data = yaml.safe_load(f)
    if data is None:
        return None
    return EntityGroupFile.model_validate(data)


def write_entity_groups(
    case_dir: Path,
    entity_type: str,
    clusters: List[List[Tuple[str, str, float]]],
    singletons: List[Tuple[str, str]],
    relations: Optional[List[Dict]] = None,
) -> Path:
    """Write entity merge groups to YAML, preserving CONFIRMED entries.

    Args:
        case_dir: Path to case directory (e.g., cases/CASE-ID)
        entity_type: Entity type key (PERSON, PROPERTY, etc.)
        clusters: List of clusters. Each cluster is a list of
            (entity_id, entity_name, confidence) tuples.
            First item in each cluster is the canonical entity.
        singletons: List of (entity_id, entity_name) not in any cluster.
        relations: Optional same-type relations as dicts with keys:
            source_id, target_id, relation_type, date.

    Returns:
        Path to written YAML file.
    """
    filename = ENTITY_TYPE_FILES.get(entity_type)
    if filename is None:
        raise ValueError(f"Unknown entity type: {entity_type}")

    groups_dir = _entity_groups_dir(case_dir)
    filepath = groups_dir / filename
    extractions_hash = _compute_extractions_hash(case_dir)

    # Load existing file to preserve CONFIRMED entries
    existing = _load_existing_file(filepath)
    confirmed_group_ids: set[str] = set()
    confirmed_groups: list[MergeGroup] = []
    confirmed_member_ids: set[str] = set()
    confirmed_relations: list[SameTypeRelation] = []

    if existing:
        for group in existing.groups:
            if group.status == "CONFIRMED":
                confirmed_groups.append(group)
                confirmed_group_ids.add(group.canonical_id)
                for member in group.members:
                    confirmed_member_ids.add(member.id)
        for rel in existing.relations:
            if rel.status == "CONFIRMED":
                confirmed_relations.append(rel)

    # Build new DRAFT groups from clusters, skipping entities already in CONFIRMED groups
    # Work on a copy to avoid mutating the caller's list
    working_singletons: list[Tuple[str, str]] = list(singletons)
    draft_groups: list[MergeGroup] = []
    for cluster in clusters:
        # Filter out members already in confirmed groups
        filtered = [
            (eid, name, conf)
            for eid, name, conf in cluster
            if eid not in confirmed_member_ids
        ]
        if len(filtered) < 2:
            # Not enough members for a merge after filtering
            for eid, name, _ in filtered:
                if eid not in confirmed_member_ids:
                    working_singletons.append((eid, name))
            continue

        canonical_id, canonical_name, _ = filtered[0]
        members = [
            MergeGroupMember(id=eid, name=name, source="dedupe", confidence=conf)
            for eid, name, conf in filtered
        ]
        draft_groups.append(
            MergeGroup(
                canonical_id=canonical_id,
                canonical_name=canonical_name,
                status="DRAFT",
                members=members,
            )
        )

    # Build unmerged list (singletons not in any confirmed group)
    unmerged = [
        UnmergedEntity(id=eid, name=name)
        for eid, name in working_singletons
        if eid not in confirmed_member_ids
    ]

    # Build relations list (deduplicated)
    draft_relations: list[SameTypeRelation] = []
    if relations:
        confirmed_rel_keys = {
            (r.source_id, r.target_id, r.relation_type) for r in confirmed_relations
        }
        seen_rel_keys: set[tuple[str, str, str]] = set()
        for rel_dict in relations:
            key = (
                rel_dict["source_id"],
                rel_dict["target_id"],
                rel_dict["relation_type"],
            )
            if key in seen_rel_keys or key in confirmed_rel_keys:
                continue
            seen_rel_keys.add(key)
            draft_relations.append(
                SameTypeRelation(
                    source_id=rel_dict["source_id"],
                    target_id=rel_dict["target_id"],
                    relation_type=rel_dict["relation_type"],
                    date=rel_dict.get("date"),
                    source="extraction",
                    status="DRAFT",
                )
            )

    all_groups = confirmed_groups + draft_groups
    all_relations = confirmed_relations + draft_relations

    # Determine top-level status
    has_draft = any(g.status == "DRAFT" for g in all_groups) or any(
        r.status == "DRAFT" for r in all_relations
    )
    top_status = "DRAFT" if has_draft else "CONFIRMED"

    entity_file = EntityGroupFile(
        status=top_status,
        extractions_hash=extractions_hash,
        groups=all_groups,
        relations=all_relations,
        unmerged=unmerged,
    )

    # Write YAML
    _write_yaml(filepath, entity_file.model_dump())
    logger.info(
        f"Wrote {entity_type} merge file: {len(confirmed_groups)} confirmed, "
        f"{len(draft_groups)} draft groups, {len(unmerged)} unmerged"
    )
    return filepath


def write_cross_type_relations(
    case_dir: Path,
    relations: List[Dict],
) -> Path:
    """Write cross-type relations to YAML, preserving CONFIRMED entries.

    Args:
        case_dir: Path to case directory.
        relations: List of relation dicts with keys:
            source_id, target_id, relation_type, date.

    Returns:
        Path to written YAML file.
    """
    groups_dir = _entity_groups_dir(case_dir)
    filepath = groups_dir / "cross_type_relations.yaml"
    extractions_hash = _compute_extractions_hash(case_dir)

    # Load existing to preserve CONFIRMED
    confirmed_relations: list[CrossTypeRelation] = []
    if filepath.exists():
        with open(filepath) as f:
            data = yaml.safe_load(f)
        if data:
            existing = CrossTypeRelationsFile.model_validate(data)
            confirmed_relations = [
                r for r in existing.relations if r.status == "CONFIRMED"
            ]

    confirmed_keys = {
        (r.source_id, r.target_id, r.relation_type) for r in confirmed_relations
    }

    # Deduplicate incoming relations by (source_id, target_id, relation_type),
    # keeping the first occurrence (which preserves date/name from earliest extraction)
    seen_keys: set[tuple[str, str, str]] = set()
    deduped_relations: list[dict] = []
    for rel_dict in relations:
        key = (rel_dict["source_id"], rel_dict["target_id"], rel_dict["relation_type"])
        if key not in seen_keys:
            seen_keys.add(key)
            deduped_relations.append(rel_dict)

    dupes_removed = len(relations) - len(deduped_relations)
    if dupes_removed:
        logger.info(f"Deduplicated {dupes_removed} cross-type relations")

    draft_relations = []
    for rel_dict in deduped_relations:
        key = (rel_dict["source_id"], rel_dict["target_id"], rel_dict["relation_type"])
        if key not in confirmed_keys:
            draft_relations.append(
                CrossTypeRelation(
                    source_id=rel_dict["source_id"],
                    source_name=rel_dict.get("source_name", ""),
                    target_id=rel_dict["target_id"],
                    target_name=rel_dict.get("target_name", ""),
                    relation_type=rel_dict["relation_type"],
                    date=rel_dict.get("date"),
                    source=rel_dict.get("source", "extraction"),
                    status="DRAFT",
                )
            )

    all_relations = confirmed_relations + draft_relations
    has_draft = any(r.status == "DRAFT" for r in all_relations)

    cross_file = CrossTypeRelationsFile(
        status="DRAFT" if has_draft else "CONFIRMED",
        extractions_hash=extractions_hash,
        relations=all_relations,
    )

    _write_yaml_with_spaced_list(
        filepath, cross_file.model_dump(), list_key="relations"
    )
    logger.info(
        f"Wrote cross-type relations: {len(confirmed_relations)} confirmed, "
        f"{len(draft_relations)} draft"
    )
    return filepath


def add_analyst_merge(
    case_dir: Path,
    entity_type: str,
    canonical_id: str,
    canonical_name: str,
    member_id: str,
    member_name: str,
) -> Path:
    """Add an analyst-confirmed merge to the appropriate entity groups file.

    Used by the merge-entities CLI command.

    Args:
        case_dir: Path to case directory.
        entity_type: Entity type key (PERSON, etc.)
        canonical_id: The entity to merge into.
        canonical_name: Name of the canonical entity.
        member_id: The entity being merged.
        member_name: Name of the entity being merged.

    Returns:
        Path to updated YAML file.
    """
    filename = ENTITY_TYPE_FILES.get(entity_type)
    if filename is None:
        raise ValueError(f"Unknown entity type: {entity_type}")

    groups_dir = _entity_groups_dir(case_dir)
    filepath = groups_dir / filename
    extractions_hash = _compute_extractions_hash(case_dir)

    existing = _load_existing_file(filepath)
    if existing is None:
        existing = EntityGroupFile(extractions_hash=extractions_hash)

    # Find any existing group that contains either entity (as canonical or member)
    canonical_group: Optional[MergeGroup] = None
    member_group: Optional[MergeGroup] = None
    for group in existing.groups:
        member_ids = {m.id for m in group.members}
        if canonical_id in member_ids:
            canonical_group = group
        if member_id in member_ids:
            member_group = group

    new_member = MergeGroupMember(
        id=member_id, name=member_name, source="analyst", confidence=1.0
    )
    canonical_as_member = MergeGroupMember(
        id=canonical_id, name=canonical_name, source="analyst", confidence=1.0
    )

    if canonical_group and member_group and canonical_group is member_group:
        # Already in the same group — just confirm it
        canonical_group.status = "CONFIRMED"
    elif canonical_group and member_group:
        # Both in different groups — merge the member's group into canonical's group
        for m in member_group.members:
            if not any(existing_m.id == m.id for existing_m in canonical_group.members):
                canonical_group.members.append(m)
        existing.groups.remove(member_group)
        canonical_group.status = "CONFIRMED"
    elif canonical_group:
        # Canonical has a group, member doesn't — add member to it
        if not any(m.id == member_id for m in canonical_group.members):
            canonical_group.members.append(new_member)
        canonical_group.status = "CONFIRMED"
    elif member_group:
        # Member has a group, canonical doesn't — add canonical and make it the canonical
        if not any(m.id == canonical_id for m in member_group.members):
            member_group.members.insert(0, canonical_as_member)
        else:
            # Move canonical to front
            member_group.members = [
                m for m in member_group.members if m.id != canonical_id
            ]
            member_group.members.insert(0, canonical_as_member)
        member_group.canonical_id = canonical_id
        member_group.canonical_name = canonical_name
        member_group.status = "CONFIRMED"
    else:
        # Neither in a group — create new group
        new_group = MergeGroup(
            canonical_id=canonical_id,
            canonical_name=canonical_name,
            status="CONFIRMED",
            members=[canonical_as_member, new_member],
        )
        existing.groups.append(new_group)

    # Remove both member and canonical from unmerged if present
    existing.unmerged = [
        u for u in existing.unmerged if u.id not in (member_id, canonical_id)
    ]

    # Recompute top-level status
    has_draft = any(g.status == "DRAFT" for g in existing.groups) or any(
        r.status == "DRAFT" for r in existing.relations
    )
    existing.status = "DRAFT" if has_draft else "CONFIRMED"
    existing.extractions_hash = extractions_hash

    _write_yaml(filepath, existing.model_dump())
    logger.info(f"Added analyst merge: {member_id} → {canonical_id}")
    return filepath


def save_entity_group_file(
    case_dir: Path, entity_type: str, entity_file: EntityGroupFile
) -> Path:
    """Save a modified EntityGroupFile directly to YAML.

    Recomputes top-level status and extractions_hash before writing.

    Args:
        case_dir: Path to case directory.
        entity_type: Entity type key (PERSON, PROPERTY, etc.)
        entity_file: The modified EntityGroupFile to save.

    Returns:
        Path to written YAML file.
    """
    filename = ENTITY_TYPE_FILES.get(entity_type)
    if filename is None:
        raise ValueError(f"Unknown entity type: {entity_type}")

    groups_dir = _entity_groups_dir(case_dir)
    filepath = groups_dir / filename

    # Recompute extractions_hash
    entity_file.extractions_hash = _compute_extractions_hash(case_dir)

    # Recompute top-level status
    has_draft = any(g.status == "DRAFT" for g in entity_file.groups) or any(
        r.status == "DRAFT" for r in entity_file.relations
    )
    entity_file.status = "DRAFT" if has_draft else "CONFIRMED"

    _write_yaml(filepath, entity_file.model_dump())
    logger.info(f"Saved {entity_type} merge file: {filepath}")
    return filepath


def write_relation_review(
    case_dir: Path,
    flagged_relations: List[Dict],
) -> Path:
    """Write flagged relations for analyst review, preserving prior decisions.

    Args:
        case_dir: Path to case directory.
        flagged_relations: List of relation dicts with keys:
            source_id, source_name, target_id, target_name, relation_type,
            date, document_id, evidence.

    Returns:
        Path to written YAML file.
    """
    from .models import RelationReviewEntry, RelationReviewFile

    groups_dir = _entity_groups_dir(case_dir)
    filepath = groups_dir / "relation_review.yaml"
    extractions_hash = _compute_extractions_hash(case_dir)

    # Load existing to preserve CONFIRMED and conditionally preserve REJECTED
    preserved: list[RelationReviewEntry] = []
    preserved_keys: set[tuple[str, str, str]] = set()
    hash_changed = False

    if filepath.exists():
        with open(filepath) as f:
            data = yaml.safe_load(f)
        if data:
            existing = RelationReviewFile.model_validate(data)
            hash_changed = existing.extractions_hash != extractions_hash

            for entry in existing.relations:
                if entry.status == "CONFIRMED":
                    preserved.append(entry)
                    preserved_keys.add(
                        (entry.source_id, entry.target_id, entry.relation_type)
                    )
                elif entry.status == "REJECTED":
                    if hash_changed:
                        demoted = entry.model_copy(update={"status": "DRAFT"})
                        preserved.append(demoted)
                    else:
                        preserved.append(entry)
                    preserved_keys.add(
                        (entry.source_id, entry.target_id, entry.relation_type)
                    )

    # Add new DRAFT entries for flagged relations not already reviewed
    draft_entries: list[RelationReviewEntry] = []
    for rel in flagged_relations:
        key = (rel["source_id"], rel["target_id"], rel["relation_type"])
        if key not in preserved_keys:
            preserved_keys.add(key)
            draft_entries.append(
                RelationReviewEntry(
                    source_id=rel["source_id"],
                    source_name=rel.get("source_name", ""),
                    target_id=rel["target_id"],
                    target_name=rel.get("target_name", ""),
                    relation_type=rel["relation_type"],
                    date=rel.get("date"),
                    document_id=rel.get("document_id", ""),
                    evidence=rel.get("evidence", ""),
                    status="DRAFT",
                    review_reason="Family relation requires analyst verification",
                )
            )

    all_entries = preserved + draft_entries
    has_draft = any(e.status == "DRAFT" for e in all_entries)

    review_file = RelationReviewFile(
        status="DRAFT" if has_draft else "CONFIRMED",
        extractions_hash=extractions_hash,
        relations=all_entries,
    )

    _write_yaml_with_spaced_list(
        filepath, review_file.model_dump(), list_key="relations"
    )
    logger.info(
        f"Wrote relation review: {sum(1 for e in all_entries if e.status == 'CONFIRMED')} confirmed, "
        f"{sum(1 for e in all_entries if e.status == 'REJECTED')} rejected, "
        f"{sum(1 for e in all_entries if e.status == 'DRAFT')} draft"
    )
    return filepath


def _write_yaml(path: Path, data: dict) -> None:
    """Write data to YAML with clean formatting."""
    with open(path, "w") as f:
        yaml.dump(
            data, f, default_flow_style=False, sort_keys=False, allow_unicode=True
        )


def _write_yaml_with_spaced_list(path: Path, data: dict, list_key: str) -> None:
    """Write YAML with blank lines between items in the specified list key."""
    text = yaml.dump(
        data, default_flow_style=False, sort_keys=False, allow_unicode=True
    )
    # Add blank line before each list entry (- source_id:) except the first
    text = re.sub(r"\n(- source_id:)", r"\n\n\1", text)
    with open(path, "w") as f:
        f.write(text)
