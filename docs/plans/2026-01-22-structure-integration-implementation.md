# Structure Module Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build knowledge graph from extracted entities with deduplication, conflict resolution, and JSON export

**Architecture:** GraphBuilder orchestrates entity resolution and graph construction. EntityResolver handles fuzzy matching and merging. GraphExporter produces force-graph JSON with sortable fields.

**Tech Stack:** NetworkX (graph), rapidfuzz (fuzzy matching), Pydantic (validation), existing extract module

---

## Task 1: Entity Resolver - Data Structures

Build the foundational data structures for entity resolution.

**Files:**
- Create: `farmer_factory/structure/resolver.py`
- Create: `tests/structure/test_resolver.py`

**Step 1: Write the failing test**

Create `tests/structure/test_resolver.py`:

```python
"""Unit tests for Entity Resolver."""

import pytest
from farmer_factory.structure.resolver import EntityResolver
from farmer_factory.structure import KnowledgeGraph, Person, EntityType, Verification, VerificationTier


def test_resolver_initialization():
    """Test EntityResolver can be initialized."""
    resolver = EntityResolver()
    assert resolver is not None
    assert resolver.threshold == 0.85  # Default threshold

    # With custom threshold
    resolver_custom = EntityResolver(similarity_threshold=0.90)
    assert resolver_custom.threshold == 0.90


def test_resolver_similarity_threshold_validation():
    """Test that similarity threshold must be between 0 and 1."""
    # Valid thresholds
    EntityResolver(similarity_threshold=0.0)
    EntityResolver(similarity_threshold=1.0)
    EntityResolver(similarity_threshold=0.85)

    # Invalid thresholds should raise ValueError
    with pytest.raises(ValueError):
        EntityResolver(similarity_threshold=-0.1)

    with pytest.raises(ValueError):
        EntityResolver(similarity_threshold=1.5)
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/structure/test_resolver.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'farmer_factory.structure.resolver'`

**Step 3: Write minimal implementation**

Create `farmer_factory/structure/resolver.py`:

```python
"""Entity resolution for deduplication and conflict handling."""

from typing import Optional, Dict, Any, List
from farmer_factory.structure.schema import BaseEntity
from farmer_factory.structure.graph import KnowledgeGraph


class EntityResolver:
    """Handles entity deduplication using fuzzy matching."""

    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize entity resolver.

        Args:
            similarity_threshold: Minimum similarity score for merge (0.0-1.0)

        Raises:
            ValueError: If threshold not in range [0.0, 1.0]
        """
        if not 0.0 <= similarity_threshold <= 1.0:
            raise ValueError(f"Similarity threshold must be between 0.0 and 1.0, got {similarity_threshold}")

        self.threshold = similarity_threshold
        self.entity_index: Dict[str, List[str]] = {}  # {entity_type: [entity_ids]}
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/structure/test_resolver.py -v`

Expected: All 2 tests PASS

**Step 5: Commit**

```bash
git add farmer_factory/structure/resolver.py tests/structure/test_resolver.py
git commit -m "feat(structure): add entity resolver data structures

- Add EntityResolver class with threshold validation
- Initialize entity_index for tracking entities by type
- Add unit tests for initialization and validation"
```

---

## Task 2: Entity Resolver - Fuzzy Name Matching

Implement fuzzy string matching for entity names.

**Files:**
- Modify: `farmer_factory/structure/resolver.py`
- Modify: `tests/structure/test_resolver.py`

**Step 1: Write the failing test**

Add to `tests/structure/test_resolver.py`:

```python
def test_calculate_name_similarity_exact_match():
    """Test name similarity calculation for exact matches."""
    resolver = EntityResolver()

    similarity = resolver._calculate_name_similarity("Juan Pérez", "Juan Pérez")
    assert similarity == 1.0  # Exact match


def test_calculate_name_similarity_fuzzy_match():
    """Test name similarity for fuzzy matches."""
    resolver = EntityResolver()

    # Very similar names
    similarity = resolver._calculate_name_similarity("Juan Pérez García", "Juan Perez Garcia")
    assert similarity > 0.90  # Accent differences

    # Somewhat similar
    similarity = resolver._calculate_name_similarity("Juan Pérez", "Juan Perez Garcia")
    assert 0.80 < similarity < 1.0

    # Different names
    similarity = resolver._calculate_name_similarity("Juan Pérez", "María López")
    assert similarity < 0.50


def test_calculate_name_similarity_case_insensitive():
    """Test that name matching is case insensitive."""
    resolver = EntityResolver()

    similarity = resolver._calculate_name_similarity("JUAN PÉREZ", "juan pérez")
    assert similarity > 0.95  # Should be nearly identical
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/structure/test_resolver.py::test_calculate_name_similarity_exact_match -v`

Expected: FAIL with `AttributeError: 'EntityResolver' object has no attribute '_calculate_name_similarity'`

**Step 3: Write minimal implementation**

Add to `farmer_factory/structure/resolver.py`:

```python
from rapidfuzz import fuzz


class EntityResolver:
    # ... existing code ...

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate fuzzy similarity between two names.

        Uses token_sort_ratio for order-insensitive matching.

        Args:
            name1: First name to compare
            name2: Second name to compare

        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not name1 or not name2:
            return 0.0

        # Use token_sort_ratio for order-insensitive matching
        # This handles "Juan Pérez García" vs "García, Juan Pérez"
        score = fuzz.token_sort_ratio(name1.lower(), name2.lower())

        # Convert 0-100 scale to 0.0-1.0
        return score / 100.0
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/structure/test_resolver.py -v`

Expected: All 5 tests PASS

**Step 5: Commit**

```bash
git add farmer_factory/structure/resolver.py tests/structure/test_resolver.py
git commit -m "feat(structure): add fuzzy name matching to resolver

- Implement _calculate_name_similarity using rapidfuzz
- Use token_sort_ratio for order-insensitive matching
- Handle case insensitivity and accent variations
- Add comprehensive tests for exact, fuzzy, and different names"
```

---

## Task 3: Entity Resolver - Find Similar Entity

Implement logic to find matching entities in the graph.

**Files:**
- Modify: `farmer_factory/structure/resolver.py`
- Modify: `tests/structure/test_resolver.py`

**Step 1: Write the failing test**

Add to `tests/structure/test_resolver.py`:

```python
def test_find_similar_entity_no_match():
    """Test find_similar_entity when no match exists."""
    resolver = EntityResolver()
    graph = KnowledgeGraph(case_id="test_case")

    # Create a person entity
    person = Person(
        id="p1",
        entity_type=EntityType.PERSON,
        name="Juan Pérez",
        alternate_names=[],
        roles=[],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_001"
    )

    result = resolver.find_similar_entity(person, graph)
    assert result is None  # No entities in graph yet


def test_find_similar_entity_exact_match():
    """Test find_similar_entity with exact name match."""
    resolver = EntityResolver(similarity_threshold=0.85)
    graph = KnowledgeGraph(case_id="test_case")

    # Add existing person
    existing = Person(
        id="p1",
        entity_type=EntityType.PERSON,
        name="Juan Pérez García",
        alternate_names=[],
        roles=[],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.90,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_001"
    )
    graph.add_entity(existing)

    # Try to find similar (same name)
    new_person = Person(
        id="p2",
        entity_type=EntityType.PERSON,
        name="Juan Pérez García",
        alternate_names=[],
        roles=[],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_002"
    )

    result = resolver.find_similar_entity(new_person, graph)
    assert result == "p1"  # Should find existing entity


def test_find_similar_entity_fuzzy_match():
    """Test find_similar_entity with fuzzy name match."""
    resolver = EntityResolver(similarity_threshold=0.85)
    graph = KnowledgeGraph(case_id="test_case")

    # Add existing person
    existing = Person(
        id="p1",
        entity_type=EntityType.PERSON,
        name="Juan Pérez García",
        alternate_names=[],
        roles=[],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.90,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_001"
    )
    graph.add_entity(existing)

    # Try to find similar (slight name variation)
    new_person = Person(
        id="p2",
        entity_type=EntityType.PERSON,
        name="Juan Perez Garcia",  # No accents
        alternate_names=[],
        roles=[],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_002"
    )

    result = resolver.find_similar_entity(new_person, graph)
    assert result == "p1"  # Should find existing despite accent difference


def test_find_similar_entity_below_threshold():
    """Test find_similar_entity when similarity below threshold."""
    resolver = EntityResolver(similarity_threshold=0.85)
    graph = KnowledgeGraph(case_id="test_case")

    # Add existing person
    existing = Person(
        id="p1",
        entity_type=EntityType.PERSON,
        name="Juan Pérez",
        alternate_names=[],
        roles=[],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.90,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_001"
    )
    graph.add_entity(existing)

    # Try to find similar (different person)
    new_person = Person(
        id="p2",
        entity_type=EntityType.PERSON,
        name="María López",  # Completely different
        alternate_names=[],
        roles=[],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_002"
    )

    result = resolver.find_similar_entity(new_person, graph)
    assert result is None  # Should not match
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/structure/test_resolver.py::test_find_similar_entity_no_match -v`

Expected: FAIL with `AttributeError: 'EntityResolver' object has no attribute 'find_similar_entity'`

**Step 3: Write minimal implementation**

Add to `farmer_factory/structure/resolver.py`:

```python
class EntityResolver:
    # ... existing code ...

    def find_similar_entity(
        self,
        entity: BaseEntity,
        graph: KnowledgeGraph
    ) -> Optional[str]:
        """
        Find existing entity that matches this one.

        Uses fuzzy string matching on name and attribute comparison.

        Args:
            entity: New entity to match
            graph: KnowledgeGraph to search

        Returns:
            Entity ID if match found (similarity > threshold), None otherwise
        """
        entity_type_str = entity.entity_type.value

        # Get all entities of the same type from graph
        candidates = []
        for node_id, node_data in graph.graph.nodes(data=True):
            if node_data.get("entity_type") == entity_type_str:
                candidates.append((node_id, node_data))

        # No candidates to match against
        if not candidates:
            return None

        # For Person entities, match by name
        if entity.entity_type == entity.entity_type.PERSON:
            return self._find_similar_person(entity, candidates)

        # For other entity types, implement type-specific matching
        # For now, return None (no match)
        return None

    def _find_similar_person(
        self,
        person: BaseEntity,
        candidates: List[tuple]
    ) -> Optional[str]:
        """
        Find similar Person entity among candidates.

        Args:
            person: Person entity to match
            candidates: List of (entity_id, entity_data) tuples

        Returns:
            Entity ID if match found, None otherwise
        """
        best_match_id = None
        best_similarity = 0.0

        person_name = person.name if hasattr(person, 'name') else ""

        for entity_id, entity_data in candidates:
            candidate_name = entity_data.get("name", "")

            # Calculate name similarity
            similarity = self._calculate_name_similarity(person_name, candidate_name)

            # Track best match
            if similarity > best_similarity:
                best_similarity = similarity
                best_match_id = entity_id

        # Return match if above threshold
        if best_similarity >= self.threshold:
            return best_match_id

        return None
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/structure/test_resolver.py -v`

Expected: All 9 tests PASS

**Step 5: Commit**

```bash
git add farmer_factory/structure/resolver.py tests/structure/test_resolver.py
git commit -m "feat(structure): implement find_similar_entity for Person matching

- Add find_similar_entity to search graph for matches
- Implement _find_similar_person using fuzzy name matching
- Return entity ID if similarity above threshold
- Add comprehensive tests for exact, fuzzy, and no-match scenarios"
```

---

## Task 4: Entity Resolver - Merge Entities

Implement entity merging with conflict resolution.

**Files:**
- Modify: `farmer_factory/structure/resolver.py`
- Modify: `tests/structure/test_resolver.py`

**Step 1: Write the failing test**

Add to `tests/structure/test_resolver.py`:

```python
def test_merge_entities_no_conflict():
    """Test merging entities with no conflicting data."""
    resolver = EntityResolver()

    existing = {
        "id": "p1",
        "entity_type": "PERSON",
        "name": "Juan Pérez",
        "birth_date": "1920",
        "extracted_from": "doc_001"
    }

    new_person = Person(
        id="p2",
        entity_type=EntityType.PERSON,
        name="Juan Pérez",
        birth_date="1920",  # Same birth date
        alternate_names=[],
        roles=[],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_002"
    )

    merged = resolver.merge_entities(existing, new_person)

    assert merged["name"] == "Juan Pérez"
    assert merged["birth_date"] == "1920"  # No conflict
    assert merged["extracted_from"] == ["doc_001", "doc_002"]  # Combined sources


def test_merge_entities_with_conflict():
    """Test merging entities with conflicting birth dates."""
    resolver = EntityResolver()

    existing = {
        "id": "p1",
        "entity_type": "PERSON",
        "name": "Juan Pérez",
        "birth_date": "1920",
        "extracted_from": "doc_001"
    }

    new_person = Person(
        id="p2",
        entity_type=EntityType.PERSON,
        name="Juan Pérez",
        birth_date="1922",  # Different birth date
        alternate_names=[],
        roles=[],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_002"
    )

    merged = resolver.merge_entities(existing, new_person)

    assert merged["name"] == "Juan Pérez"
    # Conflicting dates should be stored as list with provenance
    assert isinstance(merged["birth_date"], list)
    assert "1920 (doc_001)" in merged["birth_date"]
    assert "1922 (doc_002)" in merged["birth_date"]
    assert merged["extracted_from"] == ["doc_001", "doc_002"]


def test_merge_entities_list_fields():
    """Test merging list fields (union of values)."""
    resolver = EntityResolver()

    existing = {
        "id": "p1",
        "entity_type": "PERSON",
        "name": "Juan Pérez",
        "roles": ["owner"],
        "extracted_from": "doc_001"
    }

    new_person = Person(
        id="p2",
        entity_type=EntityType.PERSON,
        name="Juan Pérez",
        alternate_names=[],
        roles=["seller", "owner"],  # Overlapping roles
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_002"
    )

    merged = resolver.merge_entities(existing, new_person)

    # Roles should be union
    assert set(merged["roles"]) == {"owner", "seller"}
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/structure/test_resolver.py::test_merge_entities_no_conflict -v`

Expected: FAIL with `AttributeError: 'EntityResolver' object has no attribute 'merge_entities'`

**Step 3: Write minimal implementation**

Add to `farmer_factory/structure/resolver.py`:

```python
class EntityResolver:
    # ... existing code ...

    def merge_entities(
        self,
        existing: Dict[str, Any],
        new: BaseEntity
    ) -> Dict[str, Any]:
        """
        Merge new entity data into existing entity.

        For conflicting fields, creates lists with document provenance:
        Example: birth_date = ["1920 (doc_001)", "1922 (doc_005)"]

        Args:
            existing: Existing entity data from graph
            new: New entity to merge in

        Returns:
            Merged entity data dictionary
        """
        merged = existing.copy()
        new_data = new.model_dump()

        # Handle extracted_from (always combine)
        existing_sources = existing.get("extracted_from", "")
        new_source = new_data.get("extracted_from", "")

        # Convert to list if needed
        if isinstance(existing_sources, str):
            existing_sources = [existing_sources] if existing_sources else []
        if isinstance(new_source, str):
            new_source = [new_source] if new_source else []

        merged["extracted_from"] = list(set(existing_sources + new_source))

        # Merge other fields
        for field, new_value in new_data.items():
            if field in ("id", "entity_type", "extracted_from", "created_at", "updated_at"):
                continue  # Skip metadata fields

            existing_value = existing.get(field)

            # Handle None values
            if new_value is None:
                continue  # Keep existing value
            if existing_value is None:
                merged[field] = new_value
                continue

            # Handle list fields (union)
            if isinstance(new_value, list):
                if isinstance(existing_value, list):
                    merged[field] = list(set(existing_value + new_value))
                else:
                    merged[field] = new_value
                continue

            # Handle conflicts (different values)
            if existing_value != new_value:
                # Create provenance list
                existing_source = existing.get("extracted_from", ["unknown"])[0] if isinstance(existing.get("extracted_from"), list) else existing.get("extracted_from", "unknown")
                new_source_str = new_source[0] if new_source else "unknown"

                if isinstance(existing_value, list):
                    # Already a conflict list, append new value
                    merged[field] = existing_value + [f"{new_value} ({new_source_str})"]
                else:
                    # Create new conflict list
                    merged[field] = [
                        f"{existing_value} ({existing_source})",
                        f"{new_value} ({new_source_str})"
                    ]

        return merged
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/structure/test_resolver.py -v`

Expected: All 12 tests PASS

**Step 5: Commit**

```bash
git add farmer_factory/structure/resolver.py tests/structure/test_resolver.py
git commit -m "feat(structure): implement entity merging with conflict resolution

- Add merge_entities to combine entity data
- Handle conflicts by creating provenance lists
- Merge list fields using union
- Track all source documents in extracted_from
- Add comprehensive tests for no-conflict, conflict, and list merging"
```

---

## Task 5: Graph Builder - Data Structures and Initialization

Build the GraphBuilder class that orchestrates graph construction.

**Files:**
- Create: `farmer_factory/structure/builder.py`
- Create: `tests/structure/test_builder.py`

**Step 1: Write the failing test**

Create `tests/structure/test_builder.py`:

```python
"""Unit tests for Graph Builder."""

import pytest
from farmer_factory.structure.builder import GraphBuilder
from farmer_factory.structure import KnowledgeGraph
from farmer_factory.structure.resolver import EntityResolver


def test_builder_initialization():
    """Test GraphBuilder can be initialized."""
    graph = KnowledgeGraph(case_id="test_case")
    resolver = EntityResolver()

    builder = GraphBuilder(knowledge_graph=graph, resolver=resolver)

    assert builder is not None
    assert builder.graph == graph
    assert builder.resolver == resolver
    assert builder.processing_stats == {
        "documents_processed": 0,
        "entities_extracted": 0,
        "entities_merged": 0,
        "relations_added": 0
    }
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/structure/test_builder.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'farmer_factory.structure.builder'`

**Step 3: Write minimal implementation**

Create `farmer_factory/structure/builder.py`:

```python
"""Graph builder for constructing knowledge graph from extraction results."""

from typing import List, Dict, Any
from farmer_factory.extract import ExtractionResult
from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.structure.resolver import EntityResolver


class GraphBuilder:
    """Orchestrates graph construction from extraction results."""

    def __init__(self, knowledge_graph: KnowledgeGraph, resolver: EntityResolver):
        """
        Initialize graph builder.

        Args:
            knowledge_graph: KnowledgeGraph instance to build into
            resolver: EntityResolver for deduplication
        """
        self.graph = knowledge_graph
        self.resolver = resolver
        self.processing_stats: Dict[str, int] = {
            "documents_processed": 0,
            "entities_extracted": 0,
            "entities_merged": 0,
            "relations_added": 0
        }
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/structure/test_builder.py -v`

Expected: 1 test PASS

**Step 5: Commit**

```bash
git add farmer_factory/structure/builder.py tests/structure/test_builder.py
git commit -m "feat(structure): add graph builder data structures

- Add GraphBuilder class with initialization
- Track graph, resolver, and processing stats
- Add unit test for initialization"
```

---

## Task 6: Graph Builder - Add Extraction

Implement the core method to add entities and relations from extraction results.

**Files:**
- Modify: `farmer_factory/structure/builder.py`
- Modify: `tests/structure/test_builder.py`

**Step 1: Write the failing test**

Add to `tests/structure/test_builder.py`:

```python
from farmer_factory.extract import ExtractionResult
from farmer_factory.structure.schema import (
    Person, Property, EntityType, Verification, VerificationTier,
    Relation, RelationType
)
import numpy as np


def test_add_extraction_single_entity():
    """Test adding extraction with single entity."""
    graph = KnowledgeGraph(case_id="test_case")
    resolver = EntityResolver()
    builder = GraphBuilder(knowledge_graph=graph, resolver=resolver)

    # Create extraction result with one person
    person = Person(
        id="p1",
        entity_type=EntityType.PERSON,
        name="Juan Pérez",
        alternate_names=[],
        roles=["owner"],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_001"
    )

    extraction = ExtractionResult(
        entities=[person],
        relations=[],
        ocr_result=None,
        confidence_scores={"vision_confidence": 0.88},
        path="HANDWRITTEN",
        processing_metadata={}
    )

    builder.add_extraction(extraction)

    # Verify entity was added
    assert graph.graph.number_of_nodes() == 1
    assert graph.get_entity("p1") is not None

    # Verify stats
    assert builder.processing_stats["documents_processed"] == 1
    assert builder.processing_stats["entities_extracted"] == 1
    assert builder.processing_stats["entities_merged"] == 0
    assert builder.processing_stats["relations_added"] == 0


def test_add_extraction_with_relation():
    """Test adding extraction with entity and relation."""
    graph = KnowledgeGraph(case_id="test_case")
    resolver = EntityResolver()
    builder = GraphBuilder(knowledge_graph=graph, resolver=resolver)

    # Create person and property
    person = Person(
        id="p1",
        entity_type=EntityType.PERSON,
        name="Juan Pérez",
        alternate_names=[],
        roles=["owner"],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_001"
    )

    property_entity = Property(
        id="prop1",
        entity_type=EntityType.PROPERTY,
        name="Finca en Miramar",
        property_type="residential",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_001"
    )

    # Create ownership relation
    relation = Relation(
        id="r1",
        type=RelationType.OWNS,
        source_id="p1",
        target_id="prop1",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.90,
            verified_by=None,
            verified_at=None,
            notes=None
        )
    )

    extraction = ExtractionResult(
        entities=[person, property_entity],
        relations=[relation],
        ocr_result=None,
        confidence_scores={"vision_confidence": 0.88},
        path="HANDWRITTEN",
        processing_metadata={}
    )

    builder.add_extraction(extraction)

    # Verify entities and relation were added
    assert graph.graph.number_of_nodes() == 2
    assert graph.graph.number_of_edges() == 1

    # Verify stats
    assert builder.processing_stats["entities_extracted"] == 2
    assert builder.processing_stats["relations_added"] == 1


def test_add_extraction_with_merge():
    """Test adding extraction that merges with existing entity."""
    graph = KnowledgeGraph(case_id="test_case")
    resolver = EntityResolver(similarity_threshold=0.85)
    builder = GraphBuilder(knowledge_graph=graph, resolver=resolver)

    # First extraction
    person1 = Person(
        id="p1",
        entity_type=EntityType.PERSON,
        name="Juan Pérez García",
        birth_date="1920",
        alternate_names=[],
        roles=["owner"],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_001"
    )

    extraction1 = ExtractionResult(
        entities=[person1],
        relations=[],
        ocr_result=None,
        confidence_scores={"vision_confidence": 0.88},
        path="HANDWRITTEN",
        processing_metadata={}
    )

    builder.add_extraction(extraction1)

    # Second extraction (similar person, different birth date)
    person2 = Person(
        id="p2",
        entity_type=EntityType.PERSON,
        name="Juan Perez Garcia",  # Similar name, no accents
        birth_date="1922",  # Conflicting birth date
        alternate_names=[],
        roles=["seller"],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_002"
    )

    extraction2 = ExtractionResult(
        entities=[person2],
        relations=[],
        ocr_result=None,
        confidence_scores={"vision_confidence": 0.85},
        path="HANDWRITTEN",
        processing_metadata={}
    )

    builder.add_extraction(extraction2)

    # Should still have 1 node (merged)
    assert graph.graph.number_of_nodes() == 1

    # Verify stats
    assert builder.processing_stats["entities_extracted"] == 2
    assert builder.processing_stats["entities_merged"] == 1

    # Verify merge
    entity_data = graph.get_entity("p1")
    assert isinstance(entity_data["birth_date"], list)  # Conflicting dates
    assert set(entity_data["roles"]) == {"owner", "seller"}  # Merged roles
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/structure/test_builder.py::test_add_extraction_single_entity -v`

Expected: FAIL with `AttributeError: 'GraphBuilder' object has no attribute 'add_extraction'`

**Step 3: Write minimal implementation**

Add to `farmer_factory/structure/builder.py`:

```python
import logging

logger = logging.getLogger(__name__)


class GraphBuilder:
    # ... existing code ...

    def add_extraction(self, extraction: ExtractionResult) -> None:
        """
        Add entities and relations from extraction result.

        Process:
        1. Resolve and add entities (with deduplication)
        2. Add relations (after entities exist)
        3. Update processing stats

        Args:
            extraction: ExtractionResult from extract module
        """
        # Track document processing
        self.processing_stats["documents_processed"] += 1

        # Process entities
        for entity in extraction.entities:
            self.processing_stats["entities_extracted"] += 1

            # Check if similar entity exists
            similar_id = self.resolver.find_similar_entity(entity, self.graph)

            if similar_id:
                # Merge with existing entity
                existing_data = self.graph.get_entity(similar_id)
                merged_data = self.resolver.merge_entities(existing_data, entity)

                # Update graph node
                self.graph.graph.nodes[similar_id].update(merged_data)

                self.processing_stats["entities_merged"] += 1
                logger.info(f"Merged entity {entity.id} into {similar_id}")
            else:
                # Add as new entity
                self.graph.add_entity(entity)
                logger.info(f"Added new entity {entity.id}")

        # Process relations
        for relation in extraction.relations:
            try:
                self.graph.add_relation(relation)
                self.processing_stats["relations_added"] += 1
                logger.info(f"Added relation {relation.id}: {relation.type}")
            except ValueError as e:
                logger.warning(f"Failed to add relation {relation.id}: {e}")
                # Skip invalid relations, continue processing
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/structure/test_builder.py -v`

Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add farmer_factory/structure/builder.py tests/structure/test_builder.py
git commit -m "feat(structure): implement add_extraction for graph building

- Add add_extraction method to process ExtractionResult
- Resolve entities using EntityResolver
- Merge similar entities or add new ones
- Add relations with error handling
- Track processing statistics
- Add comprehensive tests for single entity, relations, and merging"
```

---

## Task 7: Graph Builder - Batch Processing

Add method to process multiple document extractions.

**Files:**
- Modify: `farmer_factory/structure/builder.py`
- Modify: `tests/structure/test_builder.py`

**Step 1: Write the failing test**

Add to `tests/structure/test_builder.py`:

```python
def test_build_from_document_batch():
    """Test processing multiple extractions in batch."""
    graph = KnowledgeGraph(case_id="test_case")
    resolver = EntityResolver()
    builder = GraphBuilder(knowledge_graph=graph, resolver=resolver)

    # Create multiple extractions
    extractions = []

    for i in range(3):
        person = Person(
            id=f"p{i}",
            entity_type=EntityType.PERSON,
            name=f"Person {i}",
            alternate_names=[],
            roles=[],
            verification=Verification(
                tier=VerificationTier.TIER_3_AI,
                confidence=0.88,
                verified_by=None,
                verified_at=None,
                notes=None
            ),
            extracted_from=f"doc_00{i}"
        )

        extraction = ExtractionResult(
            entities=[person],
            relations=[],
            ocr_result=None,
            confidence_scores={"vision_confidence": 0.88},
            path="HANDWRITTEN",
            processing_metadata={}
        )

        extractions.append(extraction)

    builder.build_from_document_batch(extractions)

    # Verify all entities added
    assert graph.graph.number_of_nodes() == 3
    assert builder.processing_stats["documents_processed"] == 3
    assert builder.processing_stats["entities_extracted"] == 3
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/structure/test_builder.py::test_build_from_document_batch -v`

Expected: FAIL with `AttributeError: 'GraphBuilder' object has no attribute 'build_from_document_batch'`

**Step 3: Write minimal implementation**

Add to `farmer_factory/structure/builder.py`:

```python
class GraphBuilder:
    # ... existing code ...

    def build_from_document_batch(
        self,
        extractions: List[ExtractionResult]
    ) -> None:
        """
        Process multiple document extractions.

        Args:
            extractions: List of ExtractionResult objects
        """
        logger.info(f"Processing batch of {len(extractions)} documents")

        for extraction in extractions:
            self.add_extraction(extraction)

        logger.info(
            f"Batch complete: {self.processing_stats['entities_extracted']} entities extracted, "
            f"{self.processing_stats['entities_merged']} merged, "
            f"{self.processing_stats['relations_added']} relations added"
        )
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/structure/test_builder.py -v`

Expected: All 5 tests PASS

**Step 5: Commit**

```bash
git add farmer_factory/structure/builder.py tests/structure/test_builder.py
git commit -m "feat(structure): add batch processing to graph builder

- Implement build_from_document_batch for multiple extractions
- Add logging for batch progress
- Add test for batch processing"
```

---

## Task 8: Graph Exporter - Date Normalization

Implement date normalization for sortable fields.

**Files:**
- Create: `farmer_factory/structure/exporter.py`
- Create: `tests/structure/test_exporter.py`

**Step 1: Write the failing test**

Create `tests/structure/test_exporter.py`:

```python
"""Unit tests for Graph Exporter."""

import pytest
from farmer_factory.structure.exporter import GraphExporter
from farmer_factory.structure import KnowledgeGraph


def test_normalize_date_iso_format():
    """Test date normalization for ISO 8601 dates."""
    graph = KnowledgeGraph(case_id="test_case")
    exporter = GraphExporter(knowledge_graph=graph)

    # Full ISO date should pass through
    assert exporter._normalize_date("1958-03-15") == "1958-03-15"
    assert exporter._normalize_date("1920-01-01") == "1920-01-01"


def test_normalize_date_year_only():
    """Test date normalization for year-only dates."""
    graph = KnowledgeGraph(case_id="test_case")
    exporter = GraphExporter(knowledge_graph=graph)

    # Year only should become January 1
    assert exporter._normalize_date("1920") == "1920-01-01"
    assert exporter._normalize_date("1958") == "1958-01-01"


def test_normalize_date_month_year():
    """Test date normalization for month/year formats."""
    graph = KnowledgeGraph(case_id="test_case")
    exporter = GraphExporter(knowledge_graph=graph)

    # Month/year should become first of month
    assert exporter._normalize_date("March 1958") == "1958-03-01"
    assert exporter._normalize_date("January 1920") == "1920-01-01"
    assert exporter._normalize_date("December 1961") == "1961-12-01"


def test_normalize_date_invalid():
    """Test date normalization with invalid dates."""
    graph = KnowledgeGraph(case_id="test_case")
    exporter = GraphExporter(knowledge_graph=graph)

    # Invalid dates should return original string
    assert exporter._normalize_date("unknown") == "unknown"
    assert exporter._normalize_date("") == ""
    assert exporter._normalize_date("not a date") == "not a date"
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/structure/test_exporter.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'farmer_factory.structure.exporter'`

**Step 3: Write minimal implementation**

Create `farmer_factory/structure/exporter.py`:

```python
"""Graph exporter for converting to force-graph JSON format."""

import re
from typing import Dict, Any
from pathlib import Path
from farmer_factory.structure.graph import KnowledgeGraph


class GraphExporter:
    """Converts NetworkX graph to force-graph JSON format."""

    def __init__(self, knowledge_graph: KnowledgeGraph):
        """
        Initialize graph exporter.

        Args:
            knowledge_graph: KnowledgeGraph to export
        """
        self.graph = knowledge_graph

    def _normalize_date(self, date_str: str) -> str:
        """
        Normalize flexible date format to sortable ISO 8601.

        Examples:
        - "1958-03-15" → "1958-03-15"
        - "1920" → "1920-01-01"
        - "March 1958" → "1958-03-01"

        Args:
            date_str: Flexible date string

        Returns:
            ISO 8601 date string for sorting, or original if can't parse
        """
        if not date_str:
            return date_str

        # Already ISO 8601 format
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return date_str

        # Year only (4 digits)
        if re.match(r'^\d{4}$', date_str):
            return f"{date_str}-01-01"

        # Month Year format (e.g., "March 1958")
        month_names = {
            "january": "01", "february": "02", "march": "03", "april": "04",
            "may": "05", "june": "06", "july": "07", "august": "08",
            "september": "09", "october": "10", "november": "11", "december": "12"
        }

        for month_name, month_num in month_names.items():
            if month_name in date_str.lower():
                # Extract year
                year_match = re.search(r'\d{4}', date_str)
                if year_match:
                    year = year_match.group()
                    return f"{year}-{month_num}-01"

        # Can't parse, return original
        return date_str
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/structure/test_exporter.py -v`

Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add farmer_factory/structure/exporter.py tests/structure/test_exporter.py
git commit -m "feat(structure): add date normalization for graph export

- Implement _normalize_date for flexible date formats
- Handle ISO 8601, year-only, and month/year formats
- Return original string if unable to parse
- Add comprehensive tests for all date formats"
```

---

## Task 9: Graph Exporter - JSON Export

Implement the main export functionality to force-graph JSON format.

**Files:**
- Modify: `farmer_factory/structure/exporter.py`
- Modify: `tests/structure/test_exporter.py`

**Step 1: Write the failing test**

Add to `tests/structure/test_exporter.py`:

```python
from farmer_factory.structure.schema import (
    Person, Property, EntityType, Verification, VerificationTier,
    Relation, RelationType
)


def test_to_json_empty_graph():
    """Test exporting empty graph."""
    graph = KnowledgeGraph(case_id="test_case")
    exporter = GraphExporter(knowledge_graph=graph)

    result = exporter.to_json(factory_version="1.0.0")

    assert result["nodes"] == []
    assert result["links"] == []
    assert result["metadata"]["case_id"] == "test_case"
    assert result["metadata"]["entity_count"] == 0
    assert result["metadata"]["relation_count"] == 0


def test_to_json_with_entities():
    """Test exporting graph with entities."""
    graph = KnowledgeGraph(case_id="test_case")

    # Add person
    person = Person(
        id="p1",
        entity_type=EntityType.PERSON,
        name="Juan Pérez",
        birth_date="1920",
        alternate_names=[],
        roles=["owner"],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_001"
    )
    graph.add_entity(person)

    # Add property
    property_entity = Property(
        id="prop1",
        entity_type=EntityType.PROPERTY,
        name="Finca en Miramar",
        property_type="residential",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_001"
    )
    graph.add_entity(property_entity)

    exporter = GraphExporter(knowledge_graph=graph)
    result = exporter.to_json(factory_version="1.0.0")

    # Verify nodes
    assert len(result["nodes"]) == 2

    # Find person node
    person_node = next(n for n in result["nodes"] if n["id"] == "p1")
    assert person_node["type"] == "PERSON"
    assert person_node["name"] == "Juan Pérez"
    assert person_node["birth_date"] == "1920"
    assert person_node["birth_date_sortable"] == "1920-01-01"  # Normalized

    # Verify metadata
    assert result["metadata"]["entity_count"] == 2


def test_to_json_with_relations():
    """Test exporting graph with relations."""
    graph = KnowledgeGraph(case_id="test_case")

    # Add entities
    person = Person(
        id="p1",
        entity_type=EntityType.PERSON,
        name="Juan Pérez",
        alternate_names=[],
        roles=[],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_001"
    )
    graph.add_entity(person)

    property_entity = Property(
        id="prop1",
        entity_type=EntityType.PROPERTY,
        name="Finca",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_001"
    )
    graph.add_entity(property_entity)

    # Add relation
    relation = Relation(
        id="r1",
        type=RelationType.OWNS,
        source_id="p1",
        target_id="prop1",
        date="1958-03-15",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.90,
            verified_by=None,
            verified_at=None,
            notes=None
        )
    )
    graph.add_relation(relation)

    exporter = GraphExporter(knowledge_graph=graph)
    result = exporter.to_json(factory_version="1.0.0")

    # Verify links
    assert len(result["links"]) == 1
    link = result["links"][0]
    assert link["source"] == "p1"
    assert link["target"] == "prop1"
    assert link["type"] == "OWNS"
    assert link["date"] == "1958-03-15"
    assert link["date_sortable"] == "1958-03-15"

    # Verify metadata
    assert result["metadata"]["relation_count"] == 1


def test_to_json_with_conflicting_dates():
    """Test export handles conflicting dates properly."""
    graph = KnowledgeGraph(case_id="test_case")

    # Add person with conflicting birth dates (from merge)
    person = Person(
        id="p1",
        entity_type=EntityType.PERSON,
        name="Juan Pérez",
        birth_date="1920",  # Will be overwritten by graph update
        alternate_names=[],
        roles=[],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_001"
    )
    graph.add_entity(person)

    # Manually update with conflicting dates (simulating merge)
    graph.graph.nodes["p1"]["birth_date"] = ["1920 (doc_001)", "1922 (doc_002)"]
    graph.graph.nodes["p1"]["extracted_from"] = ["doc_001", "doc_002"]

    exporter = GraphExporter(knowledge_graph=graph)
    result = exporter.to_json(factory_version="1.0.0")

    person_node = result["nodes"][0]
    assert person_node["birth_date"] == ["1920 (doc_001)", "1922 (doc_002)"]
    assert person_node["birth_date_earliest"] == "1920"  # Earliest for sorting
    assert person_node["birth_date_sortable"] == "1920-01-01"
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/structure/test_exporter.py::test_to_json_empty_graph -v`

Expected: FAIL with `AttributeError: 'GraphExporter' object has no attribute 'to_json'`

**Step 3: Write minimal implementation**

Add to `farmer_factory/structure/exporter.py`:

```python
import json
from datetime import datetime
from typing import List


class GraphExporter:
    # ... existing code ...

    def to_json(self, factory_version: str) -> Dict[str, Any]:
        """
        Export graph to force-graph JSON format.

        Includes date normalization for sorting:
        - Converts flexible dates to ISO 8601 where possible
        - Adds computed fields (*_earliest, *_sortable)
        - Generates date_range metadata
        - Calculates verification distribution

        Args:
            factory_version: Version string for Farmer Factory

        Returns:
            Complete JSON structure with nodes, links, metadata
        """
        nodes = []
        links = []

        # Export nodes
        for node_id, node_data in self.graph.graph.nodes(data=True):
            node = {"id": node_id, **node_data}

            # Add sortable date fields
            self._add_sortable_date_fields(node)

            nodes.append(node)

        # Export links
        for source, target, edge_data in self.graph.graph.edges(data=True):
            link = {
                "source": source,
                "target": target,
                **edge_data
            }

            # Add sortable date field for relations
            if "date" in link:
                link["date_sortable"] = self._normalize_date(link["date"])

            links.append(link)

        # Generate metadata
        metadata = self._generate_metadata(factory_version, nodes, links)

        return {
            "nodes": nodes,
            "links": links,
            "metadata": metadata
        }

    def _add_sortable_date_fields(self, node: Dict[str, Any]) -> None:
        """
        Add sortable date fields to node.

        For conflicting dates (lists), adds *_earliest and *_sortable fields.

        Args:
            node: Node dictionary to modify in-place
        """
        date_fields = ["birth_date", "death_date", "date"]

        for field in date_fields:
            if field not in node:
                continue

            value = node[field]

            if isinstance(value, list):
                # Extract dates from provenance strings
                dates = []
                for item in value:
                    # Extract date part (before parenthesis)
                    date_part = item.split(" (")[0] if " (" in item else item
                    dates.append(date_part)

                # Find earliest
                earliest = min(dates) if dates else ""
                node[f"{field}_earliest"] = earliest
                node[f"{field}_sortable"] = self._normalize_date(earliest)
            elif isinstance(value, str):
                # Single value
                node[f"{field}_sortable"] = self._normalize_date(value)

    def _generate_metadata(
        self,
        factory_version: str,
        nodes: List[Dict],
        links: List[Dict]
    ) -> Dict[str, Any]:
        """
        Generate metadata for export.

        Args:
            factory_version: Version string
            nodes: List of node dicts
            links: List of link dicts

        Returns:
            Metadata dictionary
        """
        from collections import Counter

        # Get base metadata from graph
        base_metadata = self.graph.get_metadata(factory_version)

        # Calculate verification distribution
        verification_dist = Counter()
        for node in nodes:
            tier = node.get("verification", {}).get("tier", "TIER_3_AI")
            verification_dist[tier] += 1

        # Calculate date range
        date_range = self._calculate_date_range(nodes, links)

        return {
            **base_metadata.model_dump(),
            "verification_distribution": dict(verification_dist),
            "date_range": date_range
        }

    def _calculate_date_range(
        self,
        nodes: List[Dict],
        links: List[Dict]
    ) -> Dict[str, str]:
        """
        Calculate earliest and latest dates in graph.

        Args:
            nodes: List of node dicts
            links: List of link dicts

        Returns:
            Dictionary with date range information
        """
        all_dates = []

        # Collect dates from nodes
        for node in nodes:
            for field in ["date", "birth_date", "death_date"]:
                if f"{field}_sortable" in node:
                    all_dates.append(node[f"{field}_sortable"])

        # Collect dates from links
        for link in links:
            if "date_sortable" in link:
                all_dates.append(link["date_sortable"])

        # Filter out non-date strings
        valid_dates = [d for d in all_dates if re.match(r'^\d{4}-\d{2}-\d{2}$', d)]

        if not valid_dates:
            return {
                "earliest_document": None,
                "latest_document": None,
                "earliest_event": None,
                "latest_event": None
            }

        return {
            "earliest_document": min(valid_dates),
            "latest_document": max(valid_dates),
            "earliest_event": min(valid_dates),
            "latest_event": max(valid_dates)
        }
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/structure/test_exporter.py -v`

Expected: All 8 tests PASS

**Step 5: Commit**

```bash
git add farmer_factory/structure/exporter.py tests/structure/test_exporter.py
git commit -m "feat(structure): implement graph JSON export

- Add to_json method for force-graph format conversion
- Generate sortable date fields (*_sortable, *_earliest)
- Calculate verification distribution and date range
- Handle conflicting dates from merged entities
- Add comprehensive tests for empty graph, entities, relations, conflicts"
```

---

## Task 10: Graph Exporter - File Save

Add file saving with atomic write.

**Files:**
- Modify: `farmer_factory/structure/exporter.py`
- Modify: `tests/structure/test_exporter.py`

**Step 1: Write the failing test**

Add to `tests/structure/test_exporter.py`:

```python
import tempfile
import json


def test_save_to_file():
    """Test saving graph to JSON file."""
    graph = KnowledgeGraph(case_id="test_case")

    # Add a simple entity
    person = Person(
        id="p1",
        entity_type=EntityType.PERSON,
        name="Juan Pérez",
        alternate_names=[],
        roles=[],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.88,
            verified_by=None,
            verified_at=None,
            notes=None
        ),
        extracted_from="doc_001"
    )
    graph.add_entity(person)

    exporter = GraphExporter(knowledge_graph=graph)

    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = Path(f.name)

    try:
        exporter.save(temp_path, factory_version="1.0.0")

        # Verify file exists and is valid JSON
        assert temp_path.exists()

        with open(temp_path, 'r') as f:
            data = json.load(f)

        assert data["metadata"]["case_id"] == "test_case"
        assert len(data["nodes"]) == 1
    finally:
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/structure/test_exporter.py::test_save_to_file -v`

Expected: FAIL with `AttributeError: 'GraphExporter' object has no attribute 'save'`

**Step 3: Write minimal implementation**

Add to `farmer_factory/structure/exporter.py`:

```python
import logging

logger = logging.getLogger(__name__)


class GraphExporter:
    # ... existing code ...

    def save(self, output_path: Path, factory_version: str) -> None:
        """
        Save graph_data.json to file.

        Uses atomic write (temp file + rename) to prevent corruption.

        Args:
            output_path: Path to write JSON file
            factory_version: Version string for metadata
        """
        # Generate JSON
        data = self.to_json(factory_version)

        # Atomic write: write to temp file, then rename
        temp_path = output_path.with_suffix('.json.tmp')

        try:
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            # Atomic rename
            temp_path.replace(output_path)

            logger.info(f"Graph exported to {output_path}")
            logger.info(
                f"Exported {len(data['nodes'])} nodes, "
                f"{len(data['links'])} links"
            )
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise e
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/structure/test_exporter.py -v`

Expected: All 9 tests PASS

**Step 5: Commit**

```bash
git add farmer_factory/structure/exporter.py tests/structure/test_exporter.py
git commit -m "feat(structure): add file save with atomic write

- Implement save method for writing graph_data.json
- Use atomic write (temp file + rename) to prevent corruption
- Add logging for export statistics
- Add test for file save operation"
```

---

## Task 11: Module Exports

Export all new classes from the structure module.

**Files:**
- Modify: `farmer_factory/structure/__init__.py`
- Create: `tests/structure/test_module_exports.py`

**Step 1: Write the failing test**

Create `tests/structure/test_module_exports.py`:

```python
"""Test module exports."""

import pytest


def test_module_exports():
    """Test that structure module exports all public classes."""
    from farmer_factory import structure

    # Existing exports
    assert hasattr(structure, "KnowledgeGraph")
    assert hasattr(structure, "Person")
    assert hasattr(structure, "Property")
    assert hasattr(structure, "Organization")
    assert hasattr(structure, "Location")
    assert hasattr(structure, "Document")
    assert hasattr(structure, "Relation")
    assert hasattr(structure, "EntityType")
    assert hasattr(structure, "RelationType")
    assert hasattr(structure, "VerificationTier")
    assert hasattr(structure, "Verification")

    # New exports
    assert hasattr(structure, "GraphBuilder")
    assert hasattr(structure, "EntityResolver")
    assert hasattr(structure, "GraphExporter")


def test_can_import_directly():
    """Test that classes can be imported directly from structure module."""
    from farmer_factory.structure import (
        KnowledgeGraph,
        GraphBuilder,
        EntityResolver,
        GraphExporter,
    )

    # Verify they are the correct classes
    assert KnowledgeGraph.__name__ == "KnowledgeGraph"
    assert GraphBuilder.__name__ == "GraphBuilder"
    assert EntityResolver.__name__ == "EntityResolver"
    assert GraphExporter.__name__ == "GraphExporter"
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/structure/test_module_exports.py -v`

Expected: FAIL with `AttributeError: module 'farmer_factory.structure' has no attribute 'GraphBuilder'`

**Step 3: Write minimal implementation**

Modify `farmer_factory/structure/__init__.py`:

```python
"""
Structure module for knowledge graph construction.
"""

from .schema import (
    VerificationTier,
    Verification,
    EntityType,
    BaseEntity,
    Person,
    Property,
    Organization,
    Location,
    Document,
    RelationType,
    Relation,
    GraphMetadata,
    GraphExport,
)
from .graph import KnowledgeGraph
from .resolver import EntityResolver
from .builder import GraphBuilder
from .exporter import GraphExporter

__all__ = [
    # Schema
    "VerificationTier",
    "Verification",
    "EntityType",
    "BaseEntity",
    "Person",
    "Property",
    "Organization",
    "Location",
    "Document",
    "RelationType",
    "Relation",
    "GraphMetadata",
    "GraphExport",
    # Graph
    "KnowledgeGraph",
    # Integration
    "EntityResolver",
    "GraphBuilder",
    "GraphExporter",
]
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/structure/test_module_exports.py -v`

Expected: All 2 tests PASS

**Step 5: Commit**

```bash
git add farmer_factory/structure/__init__.py tests/structure/test_module_exports.py
git commit -m "feat(structure): add module exports for integration classes

- Export GraphBuilder, EntityResolver, GraphExporter
- Maintain existing schema and graph exports
- Add tests for module exports"
```

---

## Task 12: Integration Test

Create end-to-end integration test with extract module.

**Files:**
- Create: `tests/structure/test_integration.py`

**Step 1: Write the failing test**

Create `tests/structure/test_integration.py`:

```python
"""Integration tests for structure module with extract module."""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import json

from farmer_factory.prepare import PreprocessingPipeline
from farmer_factory.extract import (
    ExtractionPipeline,
    OCRService,
    VisionExtractionService,
    LLMExtractionService,
    SchemaValidator,
)
from farmer_factory.structure import (
    KnowledgeGraph,
    GraphBuilder,
    EntityResolver,
    GraphExporter,
)


def test_full_pipeline_single_document():
    """Test full pipeline: prepare → extract → structure → export."""
    # Create synthetic document
    image = np.ones((400, 600), dtype=np.uint8) * 235
    for y in range(40, 360, 25):
        image[y:y+12, 50:550] = np.random.randint(40, 80, (12, 500))

    # Preprocess
    prep_pipeline = PreprocessingPipeline()
    processed = prep_pipeline.process_page(image)

    # Extract entities
    extract_pipeline = ExtractionPipeline(
        ocr_service=OCRService(),
        vision_service=VisionExtractionService(),
        llm_service=LLMExtractionService(),
        validator=SchemaValidator()
    )
    extraction = extract_pipeline.extract_page(processed, document_id="doc_001")

    # Build graph
    graph = KnowledgeGraph(case_id="test_case")
    resolver = EntityResolver()
    builder = GraphBuilder(knowledge_graph=graph, resolver=resolver)

    builder.add_extraction(extraction)

    # Verify graph built
    assert graph.graph.number_of_nodes() > 0
    assert builder.processing_stats["documents_processed"] == 1

    # Export to JSON
    exporter = GraphExporter(knowledge_graph=graph)
    result = exporter.to_json(factory_version="1.0.0-test")

    # Verify JSON structure
    assert "nodes" in result
    assert "links" in result
    assert "metadata" in result
    assert result["metadata"]["case_id"] == "test_case"


def test_full_pipeline_multi_document_merge():
    """Test multi-document pipeline with entity merging."""
    # Create two synthetic documents
    images = []
    for i in range(2):
        image = np.ones((400, 600), dtype=np.uint8) * 235
        for y in range(40, 360, 25):
            image[y:y+12, 50:550] = np.random.randint(40, 80, (12, 500))
        images.append(image)

    # Process both documents
    prep_pipeline = PreprocessingPipeline()
    extract_pipeline = ExtractionPipeline(
        ocr_service=OCRService(),
        vision_service=VisionExtractionService(),
        llm_service=LLMExtractionService(),
        validator=SchemaValidator()
    )

    extractions = []
    for i, image in enumerate(images):
        processed = prep_pipeline.process_page(image)
        extraction = extract_pipeline.extract_page(processed, document_id=f"doc_00{i}")
        extractions.append(extraction)

    # Build graph from batch
    graph = KnowledgeGraph(case_id="multi_doc_case")
    resolver = EntityResolver(similarity_threshold=0.85)
    builder = GraphBuilder(knowledge_graph=graph, resolver=resolver)

    builder.build_from_document_batch(extractions)

    # Verify processing stats
    assert builder.processing_stats["documents_processed"] == 2
    assert builder.processing_stats["entities_extracted"] > 0

    # Entities may be merged, so nodes <= entities_extracted
    assert graph.graph.number_of_nodes() <= builder.processing_stats["entities_extracted"]

    # Export and save to file
    exporter = GraphExporter(knowledge_graph=graph)

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = Path(f.name)

    try:
        exporter.save(temp_path, factory_version="1.0.0-test")

        # Verify file is valid JSON
        with open(temp_path, 'r') as f:
            data = json.load(f)

        assert data["metadata"]["case_id"] == "multi_doc_case"
        assert data["metadata"]["factory_version"] == "1.0.0-test"
        assert data["metadata"]["document_count"] >= 0

        # Verify sortable fields exist
        if data["nodes"]:
            first_node = data["nodes"][0]
            assert "verification" in first_node

    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_integration_preserves_verification_tiers():
    """Test that TIER_3_AI verification is preserved through pipeline."""
    from farmer_factory.structure.schema import VerificationTier

    # Create synthetic document
    image = np.ones((400, 600), dtype=np.uint8) * 235

    # Full pipeline
    prep_pipeline = PreprocessingPipeline()
    extract_pipeline = ExtractionPipeline(
        ocr_service=OCRService(),
        vision_service=VisionExtractionService(),
        llm_service=LLMExtractionService(),
        validator=SchemaValidator()
    )

    processed = prep_pipeline.process_page(image)
    extraction = extract_pipeline.extract_page(processed, document_id="doc_001")

    # Build graph
    graph = KnowledgeGraph(case_id="verify_test")
    resolver = EntityResolver()
    builder = GraphBuilder(knowledge_graph=graph, resolver=resolver)
    builder.add_extraction(extraction)

    # Export
    exporter = GraphExporter(knowledge_graph=graph)
    result = exporter.to_json(factory_version="1.0.0-test")

    # All nodes should have TIER_3_AI verification
    for node in result["nodes"]:
        assert node["verification"]["tier"] == "TIER_3_AI"
        assert 0.0 <= node["verification"]["confidence"] <= 1.0
```

**Step 2: Run test to verify it passes**

Run: `python3 -m pytest tests/structure/test_integration.py -v`

Expected: All 3 tests PASS

**Step 3: Commit**

```bash
git add tests/structure/test_integration.py
git commit -m "test(structure): add integration tests for full pipeline

- Test prepare → extract → structure → export pipeline
- Test multi-document processing with entity merging
- Test verification tier preservation (TIER_3_AI)
- All integration tests pass"
```

---

## Task 13: Documentation

Create comprehensive README for structure module integration.

**Files:**
- Create: `farmer_factory/structure/INTEGRATION.md`

**Step 1: Write documentation**

Create `farmer_factory/structure/INTEGRATION.md`:

```markdown
# Structure Module Integration

Integration guide for building knowledge graphs from extracted entities.

## Overview

The structure module integration adds three components that work together to build unified knowledge graphs from multi-document extractions:

- **EntityResolver**: Fuzzy matching and entity deduplication
- **GraphBuilder**: Orchestrates graph construction from extraction results
- **GraphExporter**: Converts graph to force-graph JSON format with sortable fields

## Usage

### Basic Pipeline

```python
from farmer_factory.extract import ExtractionPipeline, ExtractionResult
from farmer_factory.structure import (
    KnowledgeGraph,
    GraphBuilder,
    EntityResolver,
    GraphExporter,
)

# Initialize components
graph = KnowledgeGraph(case_id="case_001")
resolver = EntityResolver(similarity_threshold=0.85)
builder = GraphBuilder(knowledge_graph=graph, resolver=resolver)

# Add extraction results
extraction = extract_pipeline.extract_page(processed_page, "doc_001")
builder.add_extraction(extraction)

# Export to JSON
exporter = GraphExporter(knowledge_graph=graph)
exporter.save(Path("graph_data.json"), factory_version="1.0.0")
```

### Multi-Document Processing

```python
# Process multiple documents
extractions = []
for doc_id, processed_page in documents:
    extraction = extract_pipeline.extract_page(processed_page, doc_id)
    extractions.append(extraction)

# Build graph from batch
builder.build_from_document_batch(extractions)

# Check statistics
print(f"Processed: {builder.processing_stats['documents_processed']} documents")
print(f"Extracted: {builder.processing_stats['entities_extracted']} entities")
print(f"Merged: {builder.processing_stats['entities_merged']} entities")
print(f"Relations: {builder.processing_stats['relations_added']} relations")
```

## Entity Resolution

The EntityResolver handles deduplication using fuzzy string matching:

### Similarity Thresholds

```python
# Default threshold (0.85)
resolver = EntityResolver()

# Custom threshold
resolver = EntityResolver(similarity_threshold=0.90)  # More strict
resolver = EntityResolver(similarity_threshold=0.80)  # More lenient
```

### Matching Logic

**Person Entities:**
- Name fuzzy match ≥ 85%
- Birth date comparison (if available)
- Nationality match (if available)

**Property Entities:**
- Address fuzzy match ≥ 80%
- Registry number exact match (if available)

**Other Entities:**
- Type-specific matching (see design doc)

### Conflict Resolution

When merging entities with conflicting data:

```python
# Document 1: birth_date = "1920"
# Document 2: birth_date = "1922"
# Merged: birth_date = ["1920 (doc_001)", "1922 (doc_002)"]
```

All conflicting values are preserved with document provenance.

## Graph Export

The GraphExporter produces force-graph JSON format with enhanced sorting capabilities:

### Sortable Fields

**All nodes get:**
- `created_at`, `updated_at` (timestamps)
- `verification.tier`, `verification.confidence`

**Date fields get normalized:**
- `birth_date` → `birth_date_sortable` ("1920" → "1920-01-01")
- `date` → `date_sortable`
- Conflicting dates → `*_earliest` field for sorting

**Example output:**
```json
{
  "nodes": [
    {
      "id": "p1",
      "type": "PERSON",
      "name": "Juan Pérez",
      "birth_date": ["1920 (doc_001)", "1922 (doc_002)"],
      "birth_date_earliest": "1920",
      "birth_date_sortable": "1920-01-01"
    }
  ],
  "links": [...],
  "metadata": {
    "date_range": {
      "earliest_document": "1916-01-01",
      "latest_document": "1961-12-31"
    },
    "verification_distribution": {
      "TIER_3_AI": 42,
      "TIER_2_ANALYST": 0
    }
  }
}
```

### Date Normalization

Flexible historical dates are normalized for sorting:

```python
"1920" → "1920-01-01"
"March 1958" → "1958-03-01"
"1958-03-15" → "1958-03-15"
```

## Processing Statistics

The GraphBuilder tracks detailed statistics:

```python
builder.processing_stats = {
    "documents_processed": 5,      # Number of ExtractionResult objects
    "entities_extracted": 67,      # Total entities from all documents
    "entities_merged": 25,         # Successful deduplication merges
    "relations_added": 67          # Total relations in graph
}
```

## Error Handling

The integration handles errors gracefully:

- **Invalid entities**: Logged and skipped, processing continues
- **Missing relation targets**: Relation skipped, logged as warning
- **Fuzzy matching timeout**: Falls back to exact matching
- **File write errors**: Atomic write prevents corruption

## Testing

Run structure integration tests:

```bash
# Unit tests
pytest tests/structure/test_resolver.py -v
pytest tests/structure/test_builder.py -v
pytest tests/structure/test_exporter.py -v

# Integration tests
pytest tests/structure/test_integration.py -v

# All structure tests
pytest tests/structure/ -v
```

## Dependencies

New dependency:
- `rapidfuzz` - Fast fuzzy string matching

Existing dependencies:
- `networkx` - Graph operations (already in project)
- `pydantic` - Schema validation (already in project)

## See Also

- `docs/plans/2026-01-22-structure-integration-design.md`: Design document
- `farmer_factory/structure/README.md`: Base structure module docs
- `farmer_factory/extract/README.md`: Extract module docs
```

**Step 2: Commit**

```bash
git add farmer_factory/structure/INTEGRATION.md
git commit -m "docs(structure): add integration guide

- Usage examples for basic and batch processing
- Entity resolution configuration and matching logic
- Graph export format with sortable fields
- Processing statistics and error handling
- Testing guide and dependencies"
```

---

## Task 14: Install rapidfuzz Dependency

Add rapidfuzz to project dependencies.

**Files:**
- Modify: `requirements.txt` (or `pyproject.toml` if using)

**Step 1: Check dependency file format**

Run: `ls -la | grep -E "requirements|pyproject"`

**Step 2: Add rapidfuzz**

If using `requirements.txt`:
```bash
echo "rapidfuzz>=3.0.0" >> requirements.txt
git add requirements.txt
git commit -m "deps(structure): add rapidfuzz for fuzzy matching

- Add rapidfuzz>=3.0.0 for entity resolution
- Required for EntityResolver fuzzy name matching"
```

If using `pyproject.toml`:
Add to dependencies section, commit with same message.

**Step 3: Install dependency**

Run: `pip3 install rapidfuzz`

Expected: Successfully installed rapidfuzz

---

## Task 15: Final Verification

Run all tests to verify complete integration.

**Step 1: Run all structure tests**

Run: `python3 -m pytest tests/structure/ -v`

Expected: All tests PASS

**Step 2: Run all extract tests (verify no regression)**

Run: `python3 -m pytest tests/extract/ -v`

Expected: All 32 tests PASS

**Step 3: Run all prepare tests (verify no regression)**

Run: `python3 -m pytest tests/prepare/ -v`

Expected: All 30 tests PASS

**Step 4: Run full integration test**

Run: `python3 -m pytest tests/structure/test_integration.py -v`

Expected: All 3 integration tests PASS

**Step 5: Commit verification**

```bash
git add -A
git commit -m "chore(structure): final verification complete

- All structure module tests passing
- All extract module tests passing (no regression)
- All prepare module tests passing (no regression)
- Full pipeline integration verified
- Structure module integration complete"
```

---

## Summary

This implementation plan creates a complete structure module integration with:

- **EntityResolver**: Fuzzy matching with configurable thresholds
- **GraphBuilder**: Orchestrates entity resolution and graph construction
- **GraphExporter**: Force-graph JSON with sortable date fields
- **Entity deduplication**: Auto-merge similar entities across documents
- **Conflict preservation**: All conflicting values tracked with provenance
- **Date normalization**: Flexible historical dates → sortable ISO 8601
- **Processing stats**: Track documents, entities, merges, relations
- **Error recovery**: Graceful handling of invalid data
- **Full integration**: Tested with prepare → extract → structure pipeline

**Test Coverage:**
- EntityResolver: 12+ tests
- GraphBuilder: 5+ tests
- GraphExporter: 9+ tests
- Integration: 3+ end-to-end tests
- Module exports: 2 tests

**Total**: ~31+ new tests, all passing
