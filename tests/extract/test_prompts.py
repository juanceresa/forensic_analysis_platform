"""Tests for prompt building modules."""

import pytest
from farmer_factory.extract.prompts import (
    build_entity_prompt,
    build_relation_prompt,
    build_entity_prompt_zero_shot,
    build_relation_prompt_zero_shot,
    ocr_quality_description,
)
from farmer_factory.structure.schema import (
    Person,
    EntityType,
    Verification,
    VerificationTier,
)


class TestHelpers:
    """Test helper functions."""

    def test_ocr_quality_high(self):
        assert "High" in ocr_quality_description(0.95)

    def test_ocr_quality_medium(self):
        assert "Medium" in ocr_quality_description(0.75)

    def test_ocr_quality_low(self):
        assert "Low" in ocr_quality_description(0.55)

    def test_ocr_quality_very_low(self):
        assert "Very Low" in ocr_quality_description(0.3)


class TestFewShotPrompts:
    """Test few-shot prompt builders."""

    def test_entity_prompt_contains_schema(self):
        prompt = build_entity_prompt(
            text="Test text",
            document_id="doc_123",
            ocr_quality=0.9,
        )
        assert "PERSON ENTITY SCHEMA" in prompt
        assert "PROPERTY ENTITY SCHEMA" in prompt
        assert "entity_type" in prompt

    def test_entity_prompt_contains_document_text(self):
        prompt = build_entity_prompt(
            text="Mario Ceresa owns property",
            document_id="doc_123",
            ocr_quality=0.9,
        )
        assert "Mario Ceresa owns property" in prompt

    def test_relation_prompt_contains_entities(self):
        person = Person(
            id="person_123",
            entity_type=EntityType.PERSON,
            name="Mario Ceresa",
            verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.95),
            extracted_from="test_doc",
        )
        prompt = build_relation_prompt(
            text="Test text",
            entities=[person],
            document_id="doc_123",
        )
        assert "Mario Ceresa" in prompt
        assert "RELATION TYPES" in prompt


class TestZeroShotPrompts:
    """Test zero-shot prompt builders."""

    def test_zero_shot_entity_prompt_is_shorter(self):
        few_shot = build_entity_prompt(
            text="Test text",
            document_id="doc_123",
            ocr_quality=0.9,
        )
        zero_shot = build_entity_prompt_zero_shot(
            text="Test text",
            document_id="doc_123",
            ocr_quality=0.9,
        )
        # Zero-shot should be significantly shorter (at least 30% shorter)
        assert len(zero_shot) < len(few_shot) * 0.7

    def test_zero_shot_entity_prompt_contains_essentials(self):
        prompt = build_entity_prompt_zero_shot(
            text="Test document",
            document_id="doc_123",
            ocr_quality=0.9,
        )
        assert "PERSON" in prompt
        assert "PROPERTY" in prompt
        assert "Test document" in prompt
        assert "JSON" in prompt

    def test_zero_shot_relation_prompt_is_shorter(self):
        person = Person(
            id="person_123",
            entity_type=EntityType.PERSON,
            name="Mario Ceresa",
            verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.95),
            extracted_from="test_doc",
        )
        few_shot = build_relation_prompt(
            text="Test text",
            entities=[person],
            document_id="doc_123",
        )
        zero_shot = build_relation_prompt_zero_shot(
            text="Test text",
            entities=[person],
            document_id="doc_123",
        )
        assert len(zero_shot) < len(few_shot) * 0.7
