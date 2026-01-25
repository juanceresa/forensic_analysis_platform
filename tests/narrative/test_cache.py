"""Tests for narrative session cache."""

import pytest
from unittest.mock import Mock
from farmer_factory.narrative.cache import InMemoryCache, NarrativeCache


def test_in_memory_cache_initialization():
    """Test InMemoryCache initialization."""
    cache = InMemoryCache()
    assert cache is not None


def test_cache_key_generation():
    """Test cache key generation."""
    cache = InMemoryCache()

    key = cache.generate_cache_key(
        session_id="sess_123",
        focal_entity_id="prop_001",
        graph_hash="abc123"
    )

    assert "sess_123" in key
    assert "prop_001" in key
    assert "abc123" in key


def test_cache_miss_returns_none():
    """Test cache miss returns None."""
    cache = InMemoryCache()

    result = cache.get(
        session_id="sess_123",
        focal_entity_id="prop_001",
        graph_hash="abc123"
    )

    assert result is None


def test_cache_hit_returns_data():
    """Test cache hit returns stored data."""
    cache = InMemoryCache()

    data = {"narrative": "Test narrative", "model": "haiku"}
    cache.set(
        session_id="sess_123",
        focal_entity_id="prop_001",
        graph_hash="abc123",
        data=data,
        ttl=3600
    )

    result = cache.get(
        session_id="sess_123",
        focal_entity_id="prop_001",
        graph_hash="abc123"
    )

    assert result == data


def test_cache_ttl_expiration():
    """Test cache TTL expiration."""
    cache = InMemoryCache()

    data = {"narrative": "Test"}
    cache.set(
        session_id="sess_123",
        focal_entity_id="prop_001",
        graph_hash="abc123",
        data=data,
        ttl=0  # Immediate expiration
    )

    import time
    time.sleep(0.1)

    result = cache.get(
        session_id="sess_123",
        focal_entity_id="prop_001",
        graph_hash="abc123"
    )

    # Should be expired
    assert result is None


def test_graph_hash_calculation():
    """Test graph hash calculation."""
    from farmer_factory.structure.graph import KnowledgeGraph
    from farmer_factory.structure.schema import (
        Property,
        EntityType,
        VerificationTier,
        Verification
    )

    cache = InMemoryCache()

    kg = KnowledgeGraph(case_id="test_001")
    prop = Property(
        id="prop_001",
        name="Villa Aurelia",
        entity_type=EntityType.PROPERTY,
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.75),
        extracted_from="doc_001"
    )
    kg.add_entity(prop)

    constellation = {"prop_001"}
    hash1 = cache.calculate_graph_hash(constellation, kg)

    # Update verification tier
    prop.verification.tier = VerificationTier.TIER_2_ANALYST
    kg.add_entity(prop)

    hash2 = cache.calculate_graph_hash(constellation, kg)

    # Hash should change (cache invalidation)
    assert hash1 != hash2
