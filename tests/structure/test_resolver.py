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
