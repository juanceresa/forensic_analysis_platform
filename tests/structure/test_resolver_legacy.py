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
    assert similarity > 0.85  # Accent differences, still very similar

    # Somewhat similar (one name is subset of another)
    similarity = resolver._calculate_name_similarity("Juan Pérez", "Juan Perez Garcia")
    assert 0.60 < similarity < 1.0

    # Different names
    similarity = resolver._calculate_name_similarity("Juan Pérez", "María López")
    assert similarity < 0.50


def test_calculate_name_similarity_case_insensitive():
    """Test that name matching is case insensitive."""
    resolver = EntityResolver()

    similarity = resolver._calculate_name_similarity("JUAN PÉREZ", "juan pérez")
    assert similarity > 0.95  # Should be nearly identical


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
    assert set(merged["extracted_from"]) == {"doc_001", "doc_002"}  # Combined sources


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
    assert set(merged["extracted_from"]) == {"doc_001", "doc_002"}


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
