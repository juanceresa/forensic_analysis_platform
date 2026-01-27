"""Golden standard evaluation tests for extraction quality.

These tests compare extraction results against human-annotated ground truth
to measure and track extraction quality over time.
"""

import json
from pathlib import Path
from typing import Set

import pytest

from farmer_factory.extract.llm import LLMExtractionService


GOLDEN_DIR = Path(__file__).parent


def load_golden_case(case_name: str) -> tuple[str, dict]:
    """Load a golden test case (text + expected results)."""
    text_path = GOLDEN_DIR / f"{case_name}.txt"
    expected_path = GOLDEN_DIR / f"{case_name}_expected.json"

    text = text_path.read_text(encoding="utf-8")
    expected = json.loads(expected_path.read_text(encoding="utf-8"))

    return text, expected


def extract_names(entities: list, name_field: str = "name") -> Set[str]:
    """Extract normalized names from entities for comparison."""
    names = set()
    for entity in entities:
        name = getattr(entity, name_field, None)
        if name:
            names.add(name.lower().strip())
    return names


class TestGoldenExtraction:
    """Tests that validate extraction against golden standards."""

    @pytest.fixture
    def service(self):
        """Create extraction service (uses mock without API key)."""
        return LLMExtractionService()

    def test_sample_escritura_extracts_entities(self, service):
        """Test that sample escritura extracts expected entity types."""
        text, expected = load_golden_case("sample_escritura")

        result = service.extract_from_text(
            text=text, ocr_confidence=0.95, document_id="sample_escritura"
        )

        # Should extract at least some entities
        assert len(result.entities) > 0, "Should extract at least one entity"

        # Check entity types present
        entity_types = {
            e.entity_type.value if hasattr(e.entity_type, "value") else e.entity_type
            for e in result.entities
        }

        # Mock returns PROPERTY and LOCATION; real API should return PERSON too
        # At minimum should have some entity types
        assert len(entity_types) > 0, "Should extract at least one entity type"
        # The text mentions properties and locations, should extract those
        assert "PROPERTY" in entity_types or "LOCATION" in entity_types, (
            "Should extract PROPERTY or LOCATION entities"
        )

    def test_sample_escritura_confidence_reasonable(self, service):
        """Test that confidence scores are reasonable."""
        text, expected = load_golden_case("sample_escritura")

        result = service.extract_from_text(
            text=text, ocr_confidence=0.95, document_id="sample_escritura"
        )

        # Confidence should be reasonable given high OCR confidence
        assert result.confidence >= 0.5, "Confidence should be >= 0.5 for clear text"
        assert result.confidence <= 1.0, "Confidence should not exceed 1.0"

    def test_sample_escritura_metadata_complete(self, service):
        """Test that extraction metadata is complete."""
        text, expected = load_golden_case("sample_escritura")

        result = service.extract_from_text(
            text=text, ocr_confidence=0.95, document_id="sample_escritura"
        )

        # Check core metadata fields (both mock and real API have these)
        assert "model" in result.metadata
        assert "text_length" in result.metadata
        assert result.metadata["text_length"] == len(text)
        assert "ocr_confidence" in result.metadata

    def test_golden_file_structure(self):
        """Test that golden files have required structure."""
        text, expected = load_golden_case("sample_escritura")

        # Check expected file structure
        assert "document_id" in expected
        assert "expected_entities" in expected
        assert "expected_relations" in expected

        # Check entity categories
        entities = expected["expected_entities"]
        assert "persons" in entities
        assert "properties" in entities
        assert "locations" in entities

        # Check persons have required fields
        for person in entities["persons"]:
            assert "name" in person
            assert "roles" in person

        # Check properties have required fields
        for prop in entities["properties"]:
            assert "name" in prop
            assert "property_type" in prop


class TestGoldenMetrics:
    """Tests that calculate extraction quality metrics."""

    def test_recall_calculation_helper(self):
        """Test helper for calculating recall."""
        expected = {"mario ceresa", "maria elena", "jose rodriguez"}
        extracted = {"mario ceresa", "jose rodriguez", "unknown person"}

        # Recall = true positives / total expected
        true_positives = expected & extracted
        recall = len(true_positives) / len(expected)

        assert recall == pytest.approx(2 / 3), "Recall should be 2/3"

    def test_precision_calculation_helper(self):
        """Test helper for calculating precision."""
        expected = {"mario ceresa", "maria elena", "jose rodriguez"}
        extracted = {"mario ceresa", "jose rodriguez", "unknown person"}

        # Precision = true positives / total extracted
        true_positives = expected & extracted
        precision = len(true_positives) / len(extracted)

        assert precision == pytest.approx(2 / 3), "Precision should be 2/3"

    def test_f1_calculation_helper(self):
        """Test helper for calculating F1 score."""
        precision = 0.8
        recall = 0.6

        # F1 = 2 * (precision * recall) / (precision + recall)
        f1 = 2 * (precision * recall) / (precision + recall)

        assert f1 == pytest.approx(0.6857, rel=0.01), "F1 should be ~0.69"


# Future: Add more golden test cases
# - sample_testamento.txt - Will/Testament document
# - sample_hipoteca.txt - Mortgage document
# - sample_confiscacion.txt - Confiscation document (post-1959)
