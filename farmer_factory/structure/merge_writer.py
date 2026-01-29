"""Write entity merge authority YAML files from dedupe results.

Generates DRAFT merge files from dedupe clusters, preserving existing
CONFIRMED entries when updating.
"""

import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

from .merge_models import (
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
        filtered = [(eid, name, conf) for eid, name, conf in cluster
                     if eid not in confirmed_member_ids]
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
        draft_groups.append(MergeGroup(
            canonical_id=canonical_id,
            canonical_name=canonical_name,
            status="DRAFT",
            members=members,
        ))

    # Build unmerged list (singletons not in any confirmed group)
    unmerged = [
        UnmergedEntity(id=eid, name=name)
        for eid, name in working_singletons
        if eid not in confirmed_member_ids
    ]

    # Build relations list
    draft_relations: list[SameTypeRelation] = []
    if relations:
        confirmed_rel_keys = {
            (r.source_id, r.target_id, r.relation_type) for r in confirmed_relations
        }
        for rel_dict in relations:
            key = (rel_dict["source_id"], rel_dict["target_id"], rel_dict["relation_type"])
            if key not in confirmed_rel_keys:
                draft_relations.append(SameTypeRelation(
                    source_id=rel_dict["source_id"],
                    target_id=rel_dict["target_id"],
                    relation_type=rel_dict["relation_type"],
                    date=rel_dict.get("date"),
                    source="extraction",
                    status="DRAFT",
                ))

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
            confirmed_relations = [r for r in existing.relations if r.status == "CONFIRMED"]

    confirmed_keys = {
        (r.source_id, r.target_id, r.relation_type) for r in confirmed_relations
    }

    draft_relations = []
    for rel_dict in relations:
        key = (rel_dict["source_id"], rel_dict["target_id"], rel_dict["relation_type"])
        if key not in confirmed_keys:
            draft_relations.append(CrossTypeRelation(
                source_id=rel_dict["source_id"],
                target_id=rel_dict["target_id"],
                relation_type=rel_dict["relation_type"],
                date=rel_dict.get("date"),
                source=rel_dict.get("source", "extraction"),
                status="DRAFT",
            ))

    all_relations = confirmed_relations + draft_relations
    has_draft = any(r.status == "DRAFT" for r in all_relations)

    cross_file = CrossTypeRelationsFile(
        status="DRAFT" if has_draft else "CONFIRMED",
        extractions_hash=extractions_hash,
        relations=all_relations,
    )

    _write_yaml(filepath, cross_file.model_dump())
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

    # Check if canonical already has a group
    target_group: Optional[MergeGroup] = None
    for group in existing.groups:
        if group.canonical_id == canonical_id:
            target_group = group
            break

    new_member = MergeGroupMember(
        id=member_id, name=member_name, source="analyst", confidence=1.0
    )

    if target_group:
        # Add to existing group (skip if already a member)
        if not any(m.id == member_id for m in target_group.members):
            target_group.members.append(new_member)
        target_group.status = "CONFIRMED"
    else:
        # Create new group
        canonical_member = MergeGroupMember(
            id=canonical_id, name=canonical_name, source="analyst", confidence=1.0
        )
        new_group = MergeGroup(
            canonical_id=canonical_id,
            canonical_name=canonical_name,
            status="CONFIRMED",
            members=[canonical_member, new_member],
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


def _write_yaml(path: Path, data: dict) -> None:
    """Write data to YAML with clean formatting."""
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
