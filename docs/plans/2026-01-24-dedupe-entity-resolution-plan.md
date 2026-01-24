# Implementation Plan: Dedupe-Based Entity Resolution

> **Document Type:** Implementation Plan
> **Date:** 2026-01-24
> **Phase:** Phase 5 - Graph Construction
> **Status:** READY FOR IMPLEMENTATION
> **Estimated Effort:** 1-2 days

---

## Overview

Replace the current rapidfuzz-based entity deduplication with the `dedupe` library for machine learning-based record linkage. This provides multi-attribute matching across all entity types (Person, Location, Property, Organization) with active learning capabilities.

## Current State

**Existing Implementation:**
- `farmer_factory/structure/resolver.py` - Uses rapidfuzz for string similarity
- Only matches Person entities by name
- Fixed 85% similarity threshold
- Single-attribute comparison
- No learning from examples

**What Works:**
- Successfully merges obvious duplicates like "Mario Ceresa" and "Mario Cereza"
- Conflict resolution creates provenance lists
- Integration with GraphBuilder

**Limitations:**
- Only Person names matched (Location, Property, Organization not deduplicated)
- No context awareness (can't use birth_date, residence, etc.)
- Typos and Spanish characters require high string similarity
- No way to improve over time

## Target State

**New Implementation:**
- `farmer_factory/structure/resolver.py` - Uses `dedupe` library
- Matches all 4 entity types with type-specific field configurations
- Multi-attribute comparison (name + date + location + context)
- Probabilistic scoring with confidence thresholds
- Active learning from analyst feedback
- Trained models saved to `structure/models/`

**New Capabilities:**
- Match "María Rodríguez García" with "Maria Rodriguez" using multiple fields
- Distinguish between two "Jose Garcia" persons using birth_date or residence
- Deduplicate locations like "Holguin, Oriente" and "HOLGUIN, ORIENTE"
- Learn from corrections over time

---

## Dependencies

**Python Packages:**
```
dedupe>=2.0.0
```

**Prerequisite Work:**
- ✅ Phase 4 complete (entity/relation extraction working)
- ✅ TEST-CERESA case processed (18 documents with extracted entities)
- ✅ GraphBuilder integration points identified

**Blocks:**
- Phase 6 export quality (better deduplication = cleaner graphs)
- Analyst verification workflow (fewer false duplicates to fix)

---

## Implementation Tasks

### Task 1: Install dedupe Library

**File:** `farmer_factory/requirements.txt`

**Changes:**
```diff
+ dedupe>=2.0.0
+ unidecode>=1.3.0  # For Spanish character normalization
```

**Verification:**
```bash
pip install -r farmer_factory/requirements.txt
python -c "import dedupe; print(dedupe.__version__)"
```

---

### Task 2: Create Entity Field Configurations

**File:** `farmer_factory/structure/dedupe_config.py` (NEW)

**Purpose:** Define field configurations for each entity type.

**Implementation:**
```python
"""Dedupe field configurations for entity types."""

# Person fields - multi-attribute matching
PERSON_FIELDS = [
    {'field': 'name', 'type': 'String'},
    {'field': 'birth_date', 'type': 'String', 'has missing': True},
    {'field': 'death_date', 'type': 'String', 'has missing': True},
    {'field': 'residence', 'type': 'String', 'has missing': True},
    {'field': 'profession', 'type': 'String', 'has missing': True},
    {'field': 'nationality', 'type': 'String', 'has missing': True},
]

# Location fields
LOCATION_FIELDS = [
    {'field': 'name', 'type': 'String'},
    {'field': 'location_type', 'type': 'String', 'has missing': True},
    {'field': 'country', 'type': 'String', 'has missing': True},
    {'field': 'parent_location_id', 'type': 'String', 'has missing': True},
]

# Property fields
PROPERTY_FIELDS = [
    {'field': 'name', 'type': 'String'},
    {'field': 'property_type', 'type': 'String', 'has missing': True},
    {'field': 'location_id', 'type': 'String', 'has missing': True},
    {'field': 'size_hectares', 'type': 'Price', 'has missing': True},
]

# Organization fields
ORGANIZATION_FIELDS = [
    {'field': 'name', 'type': 'String'},
    {'field': 'org_type', 'type': 'String', 'has missing': True},
    {'field': 'location_id', 'type': 'String', 'has missing': True},
]

# Field configuration mapping
FIELD_CONFIG = {
    'PERSON': PERSON_FIELDS,
    'LOCATION': LOCATION_FIELDS,
    'PROPERTY': PROPERTY_FIELDS,
    'ORGANIZATION': ORGANIZATION_FIELDS,
}
```

**Verification:**
- Import in resolver.py works
- All 4 entity types have configurations
- Field names match schema.py

---

### Task 3: Rewrite EntityResolver with Dedupe

**File:** `farmer_factory/structure/resolver.py`

**Strategy:** Complete rewrite, keep old code in `resolver_legacy.py` as backup.

**Key Changes:**

**1. Class Structure:**
```python
import dedupe
from pathlib import Path
import pickle
from typing import Dict, Any, List, Optional, Tuple
from .dedupe_config import FIELD_CONFIG
from .schema import BaseEntity, EntityType

class DedupeEntityResolver:
    """Machine learning-based entity resolution using dedupe library."""

    def __init__(self, model_dir: Path = None, threshold: float = 0.5):
        """
        Initialize resolver with trained models.

        Args:
            model_dir: Directory containing trained dedupe models
            threshold: Match probability threshold (0.0-1.0), default 0.5
        """
        self.model_dir = model_dir or Path(__file__).parent / "models"
        self.model_dir.mkdir(exist_ok=True)
        self.threshold = threshold

        # Separate deduper for each entity type
        self.dedupers: Dict[str, dedupe.Dedupe] = {}
        self._load_models()
```

**2. Model Loading:**
```python
def _load_models(self):
    """Load pre-trained models from disk."""
    for entity_type in ["PERSON", "LOCATION", "PROPERTY", "ORGANIZATION"]:
        model_path = self.model_dir / f"{entity_type.lower()}_dedupe.pkl"
        settings_path = self.model_dir / f"{entity_type.lower()}_settings"

        if model_path.exists() and settings_path.exists():
            logger.info(f"Loading {entity_type} deduplication model...")
            with open(settings_path, 'rb') as f:
                deduper = dedupe.StaticDedupe(f)
            self.dedupers[entity_type] = deduper
        else:
            logger.warning(f"No trained model for {entity_type}, will skip deduplication")
```

**3. Entity Matching:**
```python
def find_similar_entity(
    self,
    entity: BaseEntity,
    graph: KnowledgeGraph
) -> Optional[str]:
    """
    Find matching entity using dedupe.

    Args:
        entity: New entity to match
        graph: KnowledgeGraph to search

    Returns:
        Entity ID if match found, None otherwise
    """
    entity_type_str = entity.entity_type.value

    # Check if we have a trained model for this type
    if entity_type_str not in self.dedupers:
        return None

    # Get all entities of same type from graph
    candidates = []
    for node_id, node_data in graph.graph.nodes(data=True):
        if node_data.get("entity_type") == entity_type_str:
            candidates.append((node_id, node_data))

    if not candidates:
        return None

    # Prepare data for dedupe
    data_dict = {}

    # Add new entity
    new_entity_data = self._prepare_entity_data(entity)
    data_dict[entity.id] = new_entity_data

    # Add candidates
    for candidate_id, candidate_data in candidates:
        candidate_entity_data = self._prepare_entity_data_from_dict(
            candidate_data,
            entity_type_str
        )
        data_dict[candidate_id] = candidate_entity_data

    # Get deduper for this entity type
    deduper = self.dedupers[entity_type_str]

    # Find clusters
    clustered_dupes = deduper.partition(data_dict, threshold=self.threshold)

    # Find cluster containing new entity
    for cluster_id, (record_ids, scores) in enumerate(clustered_dupes):
        if entity.id in record_ids:
            # Found a match - return first existing entity in cluster
            for record_id in record_ids:
                if record_id != entity.id:
                    return record_id

    return None
```

**4. Entity Data Preparation:**
```python
def _prepare_entity_data(self, entity: BaseEntity) -> Dict[str, Any]:
    """Extract fields for dedupe based on entity type."""
    entity_type = entity.entity_type.value

    if entity_type == "PERSON":
        return {
            'name': entity.name or '',
            'birth_date': entity.birth_date or '',
            'death_date': entity.death_date or '',
            'residence': entity.residence or '',
            'profession': entity.profession or '',
            'nationality': entity.nationality or '',
        }
    elif entity_type == "LOCATION":
        return {
            'name': entity.name or '',
            'location_type': entity.location_type or '',
            'country': entity.country or '',
            'parent_location_id': entity.parent_location_id or '',
        }
    elif entity_type == "PROPERTY":
        return {
            'name': entity.name or '',
            'property_type': entity.property_type or '',
            'location_id': entity.location_id or '',
            'size_hectares': str(entity.size_hectares or ''),
        }
    elif entity_type == "ORGANIZATION":
        return {
            'name': entity.name or '',
            'org_type': entity.org_type or '',
            'location_id': entity.location_id or '',
        }
    else:
        return {}

def _prepare_entity_data_from_dict(
    self,
    entity_data: Dict[str, Any],
    entity_type: str
) -> Dict[str, Any]:
    """Extract fields from graph node data."""
    # Similar to _prepare_entity_data but works with dict
    if entity_type == "PERSON":
        return {
            'name': entity_data.get('name', ''),
            'birth_date': entity_data.get('birth_date', ''),
            'death_date': entity_data.get('death_date', ''),
            'residence': entity_data.get('residence', ''),
            'profession': entity_data.get('profession', ''),
            'nationality': entity_data.get('nationality', ''),
        }
    # ... similar for other types
```

**5. Confidence-Weighted Merging:**
```python
def merge_entities(
    self,
    existing: Dict[str, Any],
    new: BaseEntity,
    match_confidence: float = 0.8
) -> Dict[str, Any]:
    """
    Merge entities using confidence-weighted approach.

    For high-confidence matches (≥0.8), prefer higher quality data.
    For lower confidence, create conflict lists with provenance.
    """
    merged = existing.copy()
    new_data = new.model_dump()

    # Always combine sources
    existing_sources = existing.get("extracted_from", "")
    new_source = new_data.get("extracted_from", "")

    if isinstance(existing_sources, str):
        existing_sources = [existing_sources] if existing_sources else []
    if isinstance(new_source, str):
        new_source = [new_source] if new_source else []

    merged["extracted_from"] = list(set(existing_sources + new_source))

    # Merge other fields
    for field, new_value in new_data.items():
        if field in ("id", "entity_type", "extracted_from", "created_at", "updated_at"):
            continue

        existing_value = existing.get(field)

        if new_value is None:
            continue
        if existing_value is None:
            merged[field] = new_value
            continue

        # Both have values - decide merge strategy
        if existing_value != new_value:
            if match_confidence >= 0.8:
                # High confidence - choose better value
                merged[field] = self._choose_better_value(
                    existing_value,
                    new_value,
                    existing.get('verification', {}).get('confidence', 0.5),
                    new.verification.confidence
                )
            else:
                # Lower confidence - create conflict list
                merged[field] = self._create_conflict_list(
                    existing_value,
                    new_value,
                    merged["extracted_from"]
                )

    return merged

def _choose_better_value(
    self,
    existing_value: Any,
    new_value: Any,
    existing_confidence: float,
    new_confidence: float
) -> Any:
    """Choose better value based on confidence and completeness."""
    # Confidence difference > 0.1 is significant
    if new_confidence - existing_confidence > 0.1:
        return new_value
    if existing_confidence - new_confidence > 0.1:
        return existing_value

    # Confidence similar - prefer more complete
    if isinstance(existing_value, str) and isinstance(new_value, str):
        if len(new_value) > len(existing_value) * 1.2:
            return new_value
        return existing_value

    return existing_value

def _create_conflict_list(
    self,
    existing_value: Any,
    new_value: Any,
    sources: List[str]
) -> List[str]:
    """Create conflict list with provenance."""
    if isinstance(existing_value, list):
        # Already a conflict list
        return existing_value + [f"{new_value} ({sources[-1]})"]
    else:
        return [
            f"{existing_value} ({sources[0] if sources else 'unknown'})",
            f"{new_value} ({sources[-1] if len(sources) > 1 else 'unknown'})"
        ]
```

**Verification:**
- Resolver imports without errors
- Can instantiate DedupeEntityResolver
- find_similar_entity returns None when no models exist (expected)

---

### Task 4: Create Training Module

**File:** `farmer_factory/structure/train_dedupe.py` (NEW)

**Purpose:** Interactive training workflow for building dedupe models.

**Implementation:**
```python
"""Train dedupe models using labeled examples."""

import dedupe
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
from .dedupe_config import FIELD_CONFIG
from .schema import EntityType

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
    model_path = model_dir / f"{entity_type.lower()}_dedupe.pkl"

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
            }
        elif entity_type == "LOCATION":
            data_dict[entity_id] = {
                'name': entity_data.get('name', ''),
                'location_type': entity_data.get('location_type', ''),
                'country': entity_data.get('country', ''),
                'parent_location_id': entity_data.get('parent_location_id', ''),
            }
        elif entity_type == "PROPERTY":
            data_dict[entity_id] = {
                'name': entity_data.get('name', ''),
                'property_type': entity_data.get('property_type', ''),
                'location_id': entity_data.get('location_id', ''),
                'size_hectares': str(entity_data.get('size_hectares', '')),
            }
        elif entity_type == "ORGANIZATION":
            data_dict[entity_id] = {
                'name': entity_data.get('name', ''),
                'org_type': entity_data.get('org_type', ''),
                'location_id': entity_data.get('location_id', ''),
            }

    return data_dict
```

**Verification:**
- Module imports successfully
- Can load entities from TEST-CERESA case
- train_dedupe_model function callable (won't test interactively yet)

---

### Task 5: Add CLI Command for Training

**File:** `farmer_factory/cli.py`

**Changes:**
```python
@cli.command()
@click.argument('case_id')
@click.option('--entity-type',
              type=click.Choice(['PERSON', 'LOCATION', 'PROPERTY', 'ORGANIZATION']),
              help='Train specific entity type (default: all)')
@click.option('--num-examples', default=30,
              help='Number of labeled examples to collect per type')
def train_deduplication(case_id: str, entity_type: str, num_examples: int):
    """
    Train entity deduplication models using labeled examples.

    Interactive session where you label entity pairs as matches or not.
    Models are saved to farmer_factory/structure/models/ for use in
    future processing runs.

    Example:
        python cli.py train-deduplication TEST-CERESA --entity-type PERSON
    """
    from farmer_factory.structure.train_dedupe import train_dedupe_model

    case_dir = Path('cases') / case_id
    extractions_dir = case_dir / 'extractions'

    if not extractions_dir.exists():
        raise click.ClickException(
            f"No extractions found for {case_id}. "
            f"Run 'python cli.py process {case_id}' first."
        )

    click.echo(f"\n{'='*60}")
    click.echo("Deduplication Model Training")
    click.echo(f"{'='*60}\n")
    click.echo(f"Case: {case_id}")
    click.echo(f"Examples per type: {num_examples}\n")

    entity_types = [entity_type] if entity_type else ['PERSON', 'LOCATION', 'PROPERTY', 'ORGANIZATION']

    for etype in entity_types:
        try:
            click.echo(f"\n--- Training {etype} ---\n")
            model = train_dedupe_model(
                case_id=case_id,
                entity_type=etype,
                num_examples=num_examples
            )
            click.echo(f"✓ {etype} model trained and saved\n")
        except ValueError as e:
            click.echo(f"⚠️  Skipping {etype}: {e}\n")
            continue
        except Exception as e:
            logger.exception(f"Failed to train {etype} model")
            click.echo(f"❌ Failed to train {etype}: {e}\n")
            continue

    click.echo(f"\n{'='*60}")
    click.echo("Training Complete!")
    click.echo(f"{'='*60}")
    click.echo("\nModels saved to: farmer_factory/structure/models/")
    click.echo("\nNext steps:")
    click.echo(f"  1. Test models: python cli.py process {case_id} --force-typed")
    click.echo(f"  2. Review deduplication in: cases/{case_id}/output/graph_data.json")
    click.echo(f"  3. If quality is good, process new cases with trained models")
```

**Verification:**
- CLI command shows in help: `python cli.py --help`
- Command accepts case_id argument
- Error handling works for missing case

---

### Task 6: Update GraphBuilder Integration

**File:** `farmer_factory/structure/builder.py`

**Changes:**
```python
# Update import
from farmer_factory.structure.resolver import DedupeEntityResolver  # Changed from EntityResolver

# Update __init__
def __init__(self, knowledge_graph: KnowledgeGraph, resolver: DedupeEntityResolver):
    """
    Initialize graph builder.

    Args:
        knowledge_graph: KnowledgeGraph instance to build into
        resolver: DedupeEntityResolver for ML-based deduplication
    """
    self.graph = knowledge_graph
    self.resolver = resolver
    # ... rest unchanged
```

**File:** `farmer_factory/processing/pipeline.py`

**Changes:**
```python
# Update import
from farmer_factory.structure import (
    KnowledgeGraph,
    DedupeEntityResolver,  # Changed from EntityResolver
    GraphBuilder,
    GraphExporter
)

# Update initialization
def process_case(case_id: str, base_dir: Path = None, single_file: str = None, force_typed: bool = False):
    # ... existing code ...

    # 3. Initialize graph builder
    logger.info("Initializing graph builder...")
    try:
        graph = KnowledgeGraph(case_id=case_id)

        # Use dedupe-based resolver with trained models
        resolver = DedupeEntityResolver(threshold=0.5)  # Changed

        builder = GraphBuilder(knowledge_graph=graph, resolver=resolver)
    except Exception as e:
        raise ProcessingError(f"Failed to initialize graph builder: {e}")

    # ... rest unchanged
```

**Verification:**
- Pipeline imports successfully
- Can instantiate DedupeEntityResolver
- Processing runs (will skip deduplication if no models trained yet)

---

### Task 7: Update Tests

**File:** `tests/structure/test_resolver.py` (NEW)

**Purpose:** Unit tests for DedupeEntityResolver.

**Implementation:**
```python
"""Tests for dedupe-based entity resolution."""

import pytest
from pathlib import Path
from farmer_factory.structure.resolver import DedupeEntityResolver
from farmer_factory.structure.schema import Person, Verification, EntityType


def test_resolver_initialization():
    """Test resolver initializes without trained models."""
    resolver = DedupeEntityResolver()
    assert resolver.threshold == 0.5
    assert resolver.dedupers == {}  # No models loaded yet


def test_resolver_with_missing_models():
    """Test resolver handles missing models gracefully."""
    resolver = DedupeEntityResolver()

    # Create test entity
    person = Person(
        id="test_1",
        entity_type=EntityType.PERSON,
        verification=Verification(tier="TIER_3_AI", confidence=0.8),
        extracted_from="doc_1",
        name="Test Person"
    )

    # Should return None when no model exists
    result = resolver.find_similar_entity(person, None)
    assert result is None


def test_entity_data_preparation():
    """Test entity data preparation for dedupe."""
    resolver = DedupeEntityResolver()

    person = Person(
        id="test_1",
        entity_type=EntityType.PERSON,
        verification=Verification(tier="TIER_3_AI", confidence=0.8),
        extracted_from="doc_1",
        name="Mario Ceresa",
        birth_date="1920",
        residence="Holguin"
    )

    data = resolver._prepare_entity_data(person)

    assert data['name'] == "Mario Ceresa"
    assert data['birth_date'] == "1920"
    assert data['residence'] == "Holguin"
    assert 'profession' in data  # Should have all fields even if None


def test_confidence_weighted_merging():
    """Test merge logic uses confidence scores."""
    resolver = DedupeEntityResolver()

    existing = {
        'name': 'Mario Ceresa',
        'birth_date': '1920',
        'extracted_from': ['doc_1'],
        'verification': {'confidence': 0.7}
    }

    new_person = Person(
        id="test_2",
        entity_type=EntityType.PERSON,
        verification=Verification(tier="TIER_3_AI", confidence=0.9),
        extracted_from="doc_2",
        name="Mario Cereza",  # Slight variation
        birth_date="1922"  # Conflict
    )

    # High confidence match (0.8)
    merged = resolver.merge_entities(existing, new_person, match_confidence=0.8)

    # Should pick better value based on confidence
    assert 'doc_1' in merged['extracted_from']
    assert 'doc_2' in merged['extracted_from']

    # Low confidence match (0.6)
    merged_low = resolver.merge_entities(existing, new_person, match_confidence=0.6)

    # Should create conflict list
    assert isinstance(merged_low['birth_date'], list)
```

**Verification:**
- All tests pass: `pytest tests/structure/test_resolver.py`
- Coverage for key methods

---

## Training Workflow

### Step 1: Initial Training on TEST-CERESA

**Run training command:**
```bash
python cli.py train-deduplication TEST-CERESA
```

**Expected interaction:**
```
============================================================
Training PERSON Deduplication Model
============================================================

You'll be shown pairs of entities. Label them as:
  [y]es - Same entity
  [n]o  - Different entities
  [u]nsure - Skip this pair
  [f]inished - Done labeling

Are these the same PERSON?
1. Mario Ceresa Rodriguez (birth: unknown, residence: unknown)
2. Mario Cereza Rodriguez (birth: unknown, residence: Holguin)

[y]es / [n]o / [u]nsure / [f]inished: y

Are these the same PERSON?
1. Rosalia Queral Cartaya (birth: unknown)
2. Rosalia Queral (birth: unknown)

[y]es / [n]o / [u]nsure / [f]inished: y

... (continue for ~30 pairs)
```

**Training time:** ~10-15 minutes for all 4 entity types

**Models saved to:**
```
farmer_factory/structure/models/
├── person_settings
├── person_dedupe.pkl
├── location_settings
├── location_dedupe.pkl
├── property_settings
├── property_dedupe.pkl
├── organization_settings
└── organization_dedupe.pkl
```

### Step 2: Test Trained Models

**Reprocess TEST-CERESA with trained models:**
```bash
python cli.py process TEST-CERESA --force-typed
```

**Check deduplication results:**
```bash
# Count entities before/after deduplication
python -c "
import json
with open('cases/TEST-CERESA/output/graph_data.json') as f:
    data = json.load(f)
print(f'Total entities: {len(data[\"nodes\"])}')
print(f'Entities merged: {data[\"metadata\"][\"processing_stats\"][\"entities_merged\"]}')
"
```

**Expected improvement:**
- Before: ~90 entities extracted, ~10 merged (11% dedup rate)
- After: ~90 entities extracted, ~25-30 merged (28-33% dedup rate)

### Step 3: Evaluate Quality

**Manual review:**
1. Open `graph_data.json` in editor
2. Search for entities with multiple `extracted_from` sources (merged entities)
3. Verify merges are correct (same real-world entity)
4. Check for missed duplicates (entities that should have merged but didn't)

**Quality metrics:**
- **Precision:** % of merges that are correct (aim for >90%)
- **Recall:** % of duplicates that were merged (aim for >70%)

**If quality is low:**
- Re-run training with more examples: `--num-examples 50`
- Adjust threshold: modify `DedupeEntityResolver(threshold=0.6)` in pipeline.py
- Add more fields to field configurations

---

## Rollback Plan

If dedupe implementation has issues:

**Step 1:** Backup current code
```bash
cp farmer_factory/structure/resolver.py farmer_factory/structure/resolver_dedupe.py
```

**Step 2:** Restore legacy rapidfuzz resolver
```bash
git checkout HEAD -- farmer_factory/structure/resolver.py
```

**Step 3:** Update imports in builder.py and pipeline.py
```python
from farmer_factory.structure.resolver import EntityResolver  # Back to old name
resolver = EntityResolver(similarity_threshold=0.85)
```

**Step 4:** Verify processing works with old resolver
```bash
python cli.py process TEST-CERESA --force-typed
```

---

## Success Criteria

**Implementation Complete When:**
- ✅ `dedupe` library installed
- ✅ DedupeEntityResolver implemented with all 4 entity types
- ✅ Training CLI command works
- ✅ Models can be saved and loaded
- ✅ Pipeline integration uses new resolver
- ✅ Tests pass

**Training Complete When:**
- ✅ Trained on TEST-CERESA case (~18 documents)
- ✅ All 4 entity types have models
- ✅ ~20-30 labeled examples per type
- ✅ Models saved to structure/models/

**Quality Acceptable When:**
- ✅ Deduplication rate improves (10% → 25%+)
- ✅ Manual review shows >90% precision on merges
- ✅ No obvious duplicates left unmerged
- ✅ Multi-attribute matching working (name + date + location)

---

## Next Steps After Implementation

1. **Process full TEST-CERESA case** with trained models
2. **Document training procedure** in ANALYST_GUIDE.md
3. **Add to Phase 6:** Export deduplication statistics in metadata
4. **Phase 7 consideration:** Web UI for active learning (analyst corrects merges, model improves)
5. **MVP2:** Expand training data as more cases are processed

---

## Notes

**Why dedupe over alternatives:**
- ✅ Designed specifically for record linkage
- ✅ Active learning reduces training data needs
- ✅ Handles missing fields gracefully (`has missing: True`)
- ✅ Probabilistic scoring better than hard thresholds
- ✅ Proven in data journalism and government applications

**Spanish name handling:**
- dedupe's String type handles accents/diacritics
- Multi-attribute matching helps distinguish common names
- Training on Cuban names improves accuracy

**Performance:**
- Training: ~10-15 min for 4 types (one-time cost)
- Processing: Adds ~5-10% to pipeline time
- Acceptable tradeoff for 2-3x better deduplication

---

**Status:** Ready for implementation. Begin with Task 1.
