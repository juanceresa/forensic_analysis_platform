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
