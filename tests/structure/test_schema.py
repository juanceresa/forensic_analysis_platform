"""Tests for schema models."""

import pytest
from datetime import datetime
from farmer_factory.structure.schema import (
    VerificationTier,
    Verification,
    EntityType,
)


def test_verification_tier_enum():
    """Test VerificationTier enum values."""
    assert VerificationTier.TIER_3_AI == "TIER_3_AI"
    assert VerificationTier.TIER_2_ANALYST == "TIER_2_ANALYST"
    assert VerificationTier.TIER_2_INSTITUTIONAL == "TIER_2_INSTITUTIONAL"
    assert VerificationTier.TIER_1_CERTIFIED == "TIER_1_CERTIFIED"


def test_verification_model_minimal():
    """Test Verification with minimal required fields."""
    verification = Verification(
        tier=VerificationTier.TIER_3_AI,
        confidence=0.85
    )
    assert verification.tier == VerificationTier.TIER_3_AI
    assert verification.confidence == 0.85
    assert verification.verified_by is None
    assert verification.verified_at is None
    assert verification.notes is None


def test_verification_model_full():
    """Test Verification with all fields."""
    now = datetime.now()
    verification = Verification(
        tier=VerificationTier.TIER_2_ANALYST,
        confidence=0.95,
        verified_by="analyst_123",
        verified_at=now,
        notes="Verified against original document"
    )
    assert verification.tier == VerificationTier.TIER_2_ANALYST
    assert verification.confidence == 0.95
    assert verification.verified_by == "analyst_123"
    assert verification.verified_at == now
    assert verification.notes == "Verified against original document"


def test_verification_confidence_range():
    """Test confidence must be between 0.0 and 1.0."""
    # Valid
    Verification(tier=VerificationTier.TIER_3_AI, confidence=0.0)
    Verification(tier=VerificationTier.TIER_3_AI, confidence=1.0)

    # Invalid - too low
    with pytest.raises(ValueError):
        Verification(tier=VerificationTier.TIER_3_AI, confidence=-0.1)

    # Invalid - too high
    with pytest.raises(ValueError):
        Verification(tier=VerificationTier.TIER_3_AI, confidence=1.1)


def test_entity_type_enum():
    """Test EntityType enum values."""
    assert EntityType.PERSON == "PERSON"
    assert EntityType.PROPERTY == "PROPERTY"
    assert EntityType.ORGANIZATION == "ORGANIZATION"
    assert EntityType.LOCATION == "LOCATION"
    assert EntityType.DOCUMENT == "DOCUMENT"
