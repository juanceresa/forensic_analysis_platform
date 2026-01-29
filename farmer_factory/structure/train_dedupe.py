"""Train dedupe models using labeled examples."""

import dedupe
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from .dedupe_config import FIELD_CONFIG

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
