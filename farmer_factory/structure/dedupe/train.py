"""Train dedupe models using labeled examples."""

import dedupe
import itertools
import json
import logging
import random
from pathlib import Path
from typing import Dict, Any, List, Tuple
from .config import FIELD_CONFIG

logger = logging.getLogger(__name__)


def load_entities_from_case(
    case_id: str,
    entity_type: str,
    base_dir: Path = None
) -> Dict[str, Dict[str, Any]]:
    """
    Load all entities of a type from a case's extraction files.

    Args:
        case_id: Case identifier
        entity_type: Entity type to load (PERSON, LOCATION, etc.)
        base_dir: Base directory for cases

    Returns:
        Dictionary mapping entity_id -> entity_data
    """
    if base_dir is None:
        base_dir = Path('cases')

    extractions_dir = base_dir / case_id / 'extractions'
    entities = {}

    for extraction_file in extractions_dir.glob('*.json'):
        with open(extraction_file) as f:
            extraction = json.load(f)

        for entity in extraction.get('entities', []):
            if entity.get('entity_type') == entity_type:
                entity_id = entity['id']
                entities[entity_id] = entity

    logger.info(f"Loaded {len(entities)} {entity_type} entities from {case_id}")
    return entities


def train_dedupe_model(
    case_id: str,
    entity_type: str,
    num_examples: int = 30,
    base_dir: Path = None,
    model_dir: Path = None
) -> dedupe.Dedupe:
    """
    Train a dedupe model for an entity type.

    Interactive training session where user labels entity pairs.

    Args:
        case_id: Case to use for training data
        entity_type: Entity type to train
        num_examples: Number of labeled examples to collect
        base_dir: Base directory for cases
        model_dir: Directory to save trained model

    Returns:
        Trained dedupe.Dedupe object
    """
    if model_dir is None:
        model_dir = Path(__file__).parent / "models"
    model_dir.mkdir(exist_ok=True)

    # Load entities
    entities = load_entities_from_case(case_id, entity_type, base_dir)

    if len(entities) < 10:
        raise ValueError(f"Need at least 10 {entity_type} entities for training, found {len(entities)}")

    # Prepare data for dedupe
    data_dict = _prepare_training_data(entities, entity_type)

    # Get field configuration
    fields = FIELD_CONFIG[entity_type]

    # Create deduper
    deduper = dedupe.Dedupe(fields)

    # Sample for training
    deduper.prepare_training(data_dict)

    # Interactive labeling
    print(f"\n{'='*60}")
    print(f"Training {entity_type} Deduplication Model")
    print(f"{'='*60}\n")
    print("You'll be shown pairs of entities. Label them as:")
    print("  [y]es - Same entity")
    print("  [n]o  - Different entities")
    print("  [u]nsure - Skip this pair")
    print("  [f]inished - Done labeling\n")

    dedupe.console_label(deduper)

    # Train model
    print("\nTraining model...")
    deduper.train()

    # Save trained model
    settings_path = model_dir / f"{entity_type.lower()}_settings"

    with open(settings_path, 'wb') as f:
        deduper.write_settings(f)

    logger.info(f"Saved {entity_type} model to {settings_path}")

    return deduper


def train_dedupe_model_from_groups(
    case_id: str,
    entity_type: str,
    base_dir: Path = None,
    model_dir: Path = None,
) -> dedupe.Dedupe:
    """Train a dedupe model using CONFIRMED entity groups as labeled data.

    Reads CONFIRMED merge groups from entity_groups/ YAML files and uses them
    to generate match/distinct pairs for dedupe training — no interactive
    labeling required.

    Args:
        case_id: Case to use for training data.
        entity_type: Entity type to train (PERSON, LOCATION, etc.)
        base_dir: Base directory for cases.
        model_dir: Directory to save trained model.

    Returns:
        Trained dedupe.Dedupe object.
    """
    from farmer_factory.structure.merge.reader import read_entity_groups

    if base_dir is None:
        base_dir = Path("cases")
    if model_dir is None:
        model_dir = Path(__file__).parent / "models"
    model_dir.mkdir(exist_ok=True)

    case_dir = base_dir / case_id

    # Load CONFIRMED groups
    group_file = read_entity_groups(case_dir, entity_type)
    if group_file is None:
        raise ValueError(
            f"No entity group file found for {entity_type} in {case_dir / 'entity_groups'}"
        )

    confirmed_groups = [g for g in group_file.groups if g.status == "CONFIRMED"]
    if not confirmed_groups:
        raise ValueError(
            f"No CONFIRMED groups for {entity_type}. "
            "Confirm groups in entity_groups/ before training from them."
        )

    # Load entity data from extractions
    entities = load_entities_from_case(case_id, entity_type, base_dir)
    data_dict = _prepare_training_data(entities, entity_type)

    # Build match pairs from intra-group combinations
    match_pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    group_id_sets: List[set] = []

    for group in confirmed_groups:
        member_ids = [m.id for m in group.members if m.id in data_dict]
        if len(member_ids) < 2:
            continue
        group_id_sets.append(set(member_ids))
        for a, b in itertools.combinations(member_ids, 2):
            match_pairs.append((data_dict[a], data_dict[b]))

    if not match_pairs:
        raise ValueError(
            f"No valid match pairs could be built from CONFIRMED {entity_type} groups. "
            "Ensure group member IDs exist in extraction data."
        )

    # Build distinct pairs from cross-group + singleton sampling
    all_grouped_ids = set()
    for ids in group_id_sets:
        all_grouped_ids.update(ids)

    singleton_ids = [
        u.id for u in group_file.unmerged if u.id in data_dict
    ]

    # Collect representative IDs per group (canonical or first available)
    group_representatives = []
    for group in confirmed_groups:
        for m in group.members:
            if m.id in data_dict:
                group_representatives.append(m.id)
                break

    # Pool of IDs for distinct sampling: one per group + singletons
    distinct_pool = group_representatives + singleton_ids

    distinct_pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    if len(distinct_pool) >= 2:
        all_cross_pairs = list(itertools.combinations(distinct_pool, 2))
        # Filter out pairs from the same group
        same_group_pairs = set()
        for ids in group_id_sets:
            for a, b in itertools.combinations(ids, 2):
                same_group_pairs.add((a, b))
                same_group_pairs.add((b, a))

        all_cross_pairs = [
            (a, b) for a, b in all_cross_pairs if (a, b) not in same_group_pairs
        ]

        target_distinct = min(len(all_cross_pairs), 3 * len(match_pairs))
        sampled = random.sample(all_cross_pairs, target_distinct) if len(all_cross_pairs) > target_distinct else all_cross_pairs
        distinct_pairs = [(data_dict[a], data_dict[b]) for a, b in sampled]

    logger.info(
        f"Training {entity_type} from groups: "
        f"{len(match_pairs)} match pairs, {len(distinct_pairs)} distinct pairs"
    )

    # Train dedupe model
    fields = FIELD_CONFIG[entity_type]
    deduper = dedupe.Dedupe(fields)
    deduper.prepare_training(data_dict)
    deduper.mark_pairs({"match": match_pairs, "distinct": distinct_pairs})
    deduper.train()

    settings_path = model_dir / f"{entity_type.lower()}_settings"
    with open(settings_path, "wb") as f:
        deduper.write_settings(f)

    logger.info(f"Saved {entity_type} model to {settings_path}")
    return deduper


def _prepare_training_data(
    entities: Dict[str, Dict[str, Any]],
    entity_type: str
) -> Dict[str, Dict[str, Any]]:
    """Extract relevant fields for dedupe training."""
    data_dict = {}

    for entity_id, entity_data in entities.items():
        if entity_type == "PERSON":
            data_dict[entity_id] = {
                'name': entity_data.get('name', ''),
                'birth_date': entity_data.get('birth_date', ''),
                'death_date': entity_data.get('death_date', ''),
                'residence': entity_data.get('residence', ''),
                'profession': entity_data.get('profession', ''),
                'nationality': entity_data.get('nationality', ''),
                'marital_status': entity_data.get('marital_status', ''),
            }
        elif entity_type == "LOCATION":
            data_dict[entity_id] = {
                'name': entity_data.get('name', ''),
                'location_type': entity_data.get('location_type', ''),
                'country': entity_data.get('country', ''),
                'parent_location_id': entity_data.get('parent_location_id', ''),
            }
        elif entity_type == "PROPERTY":
            area_value = entity_data.get('area')
            data_dict[entity_id] = {
                'name': entity_data.get('name', ''),
                'property_type': entity_data.get('property_type', ''),
                'location_id': entity_data.get('location_id', ''),
                'area': float(area_value) if area_value is not None else None,
            }
        elif entity_type == "ORGANIZATION":
            data_dict[entity_id] = {
                'name': entity_data.get('name', ''),
                'org_type': entity_data.get('org_type', ''),
                'location_id': entity_data.get('location_id', ''),
            }

    return data_dict
