"""Read and validate entity merge authority YAML files.

Provides functions to load merge files and extract confirmed merge mappings
for use by the apply-merges engine.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

from .models import (
    CrossTypeRelationsFile,
    EntityGroupFile,
)
from .writer import ENTITY_TYPE_FILES

logger = logging.getLogger(__name__)


def read_entity_groups(case_dir: Path, entity_type: str) -> Optional[EntityGroupFile]:
    """Read and validate an entity group merge file.

    Args:
        case_dir: Path to case directory.
        entity_type: Entity type key (PERSON, PROPERTY, etc.)

    Returns:
        EntityGroupFile if file exists, None otherwise.
    """
    filename = ENTITY_TYPE_FILES.get(entity_type)
    if filename is None:
        raise ValueError(f"Unknown entity type: {entity_type}")

    filepath = case_dir / "entity_groups" / filename
    if not filepath.exists():
        return None

    with open(filepath) as f:
        data = yaml.safe_load(f)
    if data is None:
        return None

    return EntityGroupFile.model_validate(data)


def read_cross_type_relations(case_dir: Path) -> Optional[CrossTypeRelationsFile]:
    """Read and validate the cross-type relations file.

    Args:
        case_dir: Path to case directory.

    Returns:
        CrossTypeRelationsFile if file exists, None otherwise.
    """
    filepath = case_dir / "entity_groups" / "cross_type_relations.yaml"
    if not filepath.exists():
        return None

    with open(filepath) as f:
        data = yaml.safe_load(f)
    if data is None:
        return None

    return CrossTypeRelationsFile.model_validate(data)


def read_relation_review(case_dir: Path):
    """Read and validate the relation review file.

    Args:
        case_dir: Path to case directory.

    Returns:
        RelationReviewFile if file exists, None otherwise.
    """
    from .models import RelationReviewFile

    filepath = case_dir / "entity_groups" / "relation_review.yaml"
    if not filepath.exists():
        return None

    with open(filepath) as f:
        data = yaml.safe_load(f)
    if data is None:
        return None

    return RelationReviewFile.model_validate(data)


def get_confirmed_merges(
    case_dir: Path, include_drafts: bool = False
) -> Dict[str, str]:
    """Get all confirmed (or optionally draft) merge mappings.

    Returns a dict mapping each merged member ID to its canonical ID.
    The canonical entity itself is NOT in the mapping (it maps to itself implicitly).

    Args:
        case_dir: Path to case directory.
        include_drafts: If True, include DRAFT groups too (for preview).

    Returns:
        Dict mapping member_id → canonical_id.
    """
    merge_map: Dict[str, str] = {}

    for entity_type, filename in ENTITY_TYPE_FILES.items():
        entity_file = read_entity_groups(case_dir, entity_type)
        if entity_file is None:
            continue

        for group in entity_file.groups:
            if group.status == "CONFIRMED" or include_drafts:
                canonical = group.canonical_id
                for member in group.members:
                    if member.id != canonical:
                        merge_map[member.id] = canonical

    return merge_map


def get_all_entity_groups(
    case_dir: Path,
) -> List[Tuple[str, EntityGroupFile]]:
    """Load all entity group files that exist.

    Returns:
        List of (entity_type, EntityGroupFile) tuples.
    """
    results = []
    for entity_type in ENTITY_TYPE_FILES:
        entity_file = read_entity_groups(case_dir, entity_type)
        if entity_file is not None:
            results.append((entity_type, entity_file))
    return results
