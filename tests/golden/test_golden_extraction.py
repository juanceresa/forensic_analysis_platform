"""Golden standard evaluation tests for extraction quality.

These tests compare extraction results against human-annotated ground truth
to measure and track extraction quality over time.

Test Categories:
- Mock tests: Run without API key, validate structure and basic behavior
- Real extraction tests: Run with ANTHROPIC_API_KEY, validate actual extraction quality
"""

import json
import os
from pathlib import Path
from typing import Set, Dict, List, Tuple
from dataclasses import dataclass

import pytest

from farmer_factory.extract.llm import LLMExtractionService


GOLDEN_DIR = Path(__file__).parent

# Quality thresholds for real extraction tests
QUALITY_THRESHOLDS = {
    "person_recall": 0.5,      # Should find at least 50% of expected persons
    "property_recall": 0.6,    # Should find at least 60% of expected properties
    "location_recall": 0.4,    # Locations often vary in naming
    "overall_precision": 0.3,  # At least 30% of extracted entities should be valid
    "relation_recall": 0.3,    # Should find at least 30% of expected relations
}


@dataclass
class ExtractionMetrics:
    """Metrics for extraction quality evaluation."""
    precision: float
    recall: float
    f1: float
    true_positives: int
    false_positives: int
    false_negatives: int

    @classmethod
    def calculate(cls, expected: Set[str], extracted: Set[str]) -> "ExtractionMetrics":
        """Calculate precision, recall, and F1 from sets."""
        true_positives = expected & extracted
        false_positives = extracted - expected
        false_negatives = expected - extracted

        precision = len(true_positives) / len(extracted) if extracted else 0
        recall = len(true_positives) / len(expected) if expected else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        return cls(
            precision=precision,
            recall=recall,
            f1=f1,
            true_positives=len(true_positives),
            false_positives=len(false_positives),
            false_negatives=len(false_negatives),
        )


def load_golden_case(case_name: str) -> tuple[str, dict]:
    """Load a golden test case (text + expected results)."""
    text_path = GOLDEN_DIR / f"{case_name}.txt"
    expected_path = GOLDEN_DIR / f"{case_name}_expected.json"

    text = text_path.read_text(encoding="utf-8")
    expected = json.loads(expected_path.read_text(encoding="utf-8"))

    return text, expected


def normalize_name(name: str) -> str:
    """Normalize a name for comparison."""
    import unicodedata
    # Remove accents
    normalized = unicodedata.normalize('NFKD', name.lower())
    normalized = ''.join(c for c in normalized if not unicodedata.combining(c))
    # Remove common titles
    for title in ['don ', 'dona ', 'doña ', 'dr. ', 'doctor ', 'señor ', 'señora ', 'sr. ', 'sra. ']:
        normalized = normalized.replace(title, '')
    return normalized.strip()


def extract_entity_names(entities: list, entity_type: str) -> Set[str]:
    """Extract normalized names from entities of a specific type."""
    names = set()
    for entity in entities:
        etype = getattr(entity, 'entity_type', None)
        if etype:
            etype_val = etype.value if hasattr(etype, 'value') else etype
            if etype_val == entity_type:
                name = getattr(entity, 'name', None)
                if name:
                    names.add(normalize_name(name))
    return names


def get_expected_names(expected: dict, category: str) -> Set[str]:
    """Get normalized expected names from golden data."""
    entities = expected.get("expected_entities", {}).get(category, [])
    return {normalize_name(e["name"]) for e in entities if "name" in e}


class TestGoldenExtraction:
    """Tests that validate extraction against golden standards (mock service)."""

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

        assert len(entity_types) > 0, "Should extract at least one entity type"
        assert "PROPERTY" in entity_types or "LOCATION" in entity_types, (
            "Should extract PROPERTY or LOCATION entities"
        )

    def test_sample_escritura_confidence_reasonable(self, service):
        """Test that confidence scores are reasonable."""
        text, expected = load_golden_case("sample_escritura")

        result = service.extract_from_text(
            text=text, ocr_confidence=0.95, document_id="sample_escritura"
        )

        assert result.confidence >= 0.5, "Confidence should be >= 0.5 for clear text"
        assert result.confidence <= 1.0, "Confidence should not exceed 1.0"

    def test_sample_escritura_metadata_complete(self, service):
        """Test that extraction metadata is complete."""
        text, expected = load_golden_case("sample_escritura")

        result = service.extract_from_text(
            text=text, ocr_confidence=0.95, document_id="sample_escritura"
        )

        assert "model" in result.metadata
        assert "text_length" in result.metadata
        assert result.metadata["text_length"] == len(text)
        assert "ocr_confidence" in result.metadata

    def test_sample_testamento_extracts_entities(self, service):
        """Test that sample testamento extracts expected entity types."""
        text, expected = load_golden_case("sample_testamento")

        result = service.extract_from_text(
            text=text, ocr_confidence=0.95, document_id="sample_testamento"
        )

        assert len(result.entities) > 0, "Should extract at least one entity"

    def test_golden_file_structure_escritura(self):
        """Test that escritura golden files have required structure."""
        text, expected = load_golden_case("sample_escritura")

        assert "document_id" in expected
        assert "expected_entities" in expected
        assert "expected_relations" in expected

        entities = expected["expected_entities"]
        assert "persons" in entities
        assert "properties" in entities
        assert "locations" in entities

        for person in entities["persons"]:
            assert "name" in person
            assert "roles" in person

        for prop in entities["properties"]:
            assert "name" in prop
            assert "property_type" in prop

    def test_golden_file_structure_testamento(self):
        """Test that testamento golden files have required structure."""
        text, expected = load_golden_case("sample_testamento")

        assert "document_id" in expected
        assert "expected_entities" in expected
        assert "expected_relations" in expected

        entities = expected["expected_entities"]
        assert "persons" in entities
        assert "properties" in entities
        assert "locations" in entities

        # Testamento should have heir/testator roles
        roles = set()
        for person in entities["persons"]:
            roles.update(person.get("roles", []))
        assert "testator" in roles or "heir" in roles, "Testament should have testator/heir"


class TestGoldenMetrics:
    """Tests that calculate and validate extraction quality metrics."""

    def test_metrics_calculation(self):
        """Test ExtractionMetrics calculation."""
        expected = {"mario ceresa", "maria elena", "jose rodriguez"}
        extracted = {"mario ceresa", "jose rodriguez", "unknown person"}

        metrics = ExtractionMetrics.calculate(expected, extracted)

        assert metrics.recall == pytest.approx(2 / 3), "Recall should be 2/3"
        assert metrics.precision == pytest.approx(2 / 3), "Precision should be 2/3"
        assert metrics.true_positives == 2
        assert metrics.false_positives == 1
        assert metrics.false_negatives == 1

    def test_f1_calculation(self):
        """Test F1 score calculation."""
        expected = {"a", "b", "c", "d", "e"}  # 5 expected
        extracted = {"a", "b", "c", "f"}       # 4 extracted, 3 correct

        metrics = ExtractionMetrics.calculate(expected, extracted)

        # Recall = 3/5 = 0.6, Precision = 3/4 = 0.75
        # F1 = 2 * 0.6 * 0.75 / (0.6 + 0.75) = 0.667
        assert metrics.f1 == pytest.approx(0.667, rel=0.01)

    def test_normalize_name(self):
        """Test name normalization for comparison."""
        assert normalize_name("Mario Ceresa") == normalize_name("mario ceresa")
        assert normalize_name("Don Mario Ceresa") == normalize_name("Mario Ceresa")
        assert normalize_name("María Elena") == normalize_name("Maria Elena")
        assert normalize_name("Dr. José Rodriguez") == normalize_name("jose rodriguez")


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="Requires ANTHROPIC_API_KEY for real extraction tests"
)
class TestRealExtraction:
    """Tests that validate real LLM extraction quality against golden standards.

    These tests only run when ANTHROPIC_API_KEY is set.
    They measure precision, recall, and F1 scores against expected output.
    """

    @pytest.fixture
    def service(self):
        """Create extraction service with real API."""
        return LLMExtractionService(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def test_escritura_person_recall(self, service):
        """Test that extraction finds expected persons in escritura."""
        text, expected = load_golden_case("sample_escritura")
        result = service.extract_from_text(
            text=text, ocr_confidence=0.95, document_id="sample_escritura"
        )

        expected_names = get_expected_names(expected, "persons")
        extracted_names = extract_entity_names(result.entities, "PERSON")

        metrics = ExtractionMetrics.calculate(expected_names, extracted_names)

        assert metrics.recall >= QUALITY_THRESHOLDS["person_recall"], (
            f"Person recall {metrics.recall:.2f} below threshold {QUALITY_THRESHOLDS['person_recall']}. "
            f"Found {metrics.true_positives}/{len(expected_names)}. "
            f"Missing: {expected_names - extracted_names}"
        )

    def test_escritura_property_recall(self, service):
        """Test that extraction finds expected properties in escritura."""
        text, expected = load_golden_case("sample_escritura")
        result = service.extract_from_text(
            text=text, ocr_confidence=0.95, document_id="sample_escritura"
        )

        expected_names = get_expected_names(expected, "properties")
        extracted_names = extract_entity_names(result.entities, "PROPERTY")

        metrics = ExtractionMetrics.calculate(expected_names, extracted_names)

        assert metrics.recall >= QUALITY_THRESHOLDS["property_recall"], (
            f"Property recall {metrics.recall:.2f} below threshold. "
            f"Missing: {expected_names - extracted_names}"
        )

    def test_testamento_person_recall(self, service):
        """Test that extraction finds expected persons in testamento."""
        text, expected = load_golden_case("sample_testamento")
        result = service.extract_from_text(
            text=text, ocr_confidence=0.95, document_id="sample_testamento"
        )

        expected_names = get_expected_names(expected, "persons")
        extracted_names = extract_entity_names(result.entities, "PERSON")

        metrics = ExtractionMetrics.calculate(expected_names, extracted_names)

        assert metrics.recall >= QUALITY_THRESHOLDS["person_recall"], (
            f"Person recall {metrics.recall:.2f} below threshold. "
            f"Found {metrics.true_positives}/{len(expected_names)}. "
            f"Missing: {expected_names - extracted_names}"
        )

    def test_testamento_heir_property_extraction(self, service):
        """Test that key heir and property are extracted from testament."""
        text, expected = load_golden_case("sample_testamento")
        result = service.extract_from_text(
            text=text, ocr_confidence=0.95, document_id="sample_testamento"
        )

        # These are the critical entities for a will
        extracted_person_names = extract_entity_names(result.entities, "PERSON")
        extracted_property_names = extract_entity_names(result.entities, "PROPERTY")

        # Mario Ceresa y Queral (heir) and Hacienda Aguaras (property) are essential
        assert any("ceresa" in name for name in extracted_person_names), (
            "Should extract Mario Ceresa y Queral (heir)"
        )
        # Property extraction is critical for land claims
        expected_properties = get_expected_names(expected, "properties")
        assert len(extracted_property_names) > 0 or len(expected_properties) == 0, (
            f"Should extract properties. Expected: {expected_properties}"
        )

    def test_extraction_quality_report(self, service):
        """Generate a summary quality report for all golden cases."""
        cases = ["sample_escritura", "sample_testamento"]
        reports = []

        for case_name in cases:
            text, expected = load_golden_case(case_name)
            result = service.extract_from_text(
                text=text, ocr_confidence=0.95, document_id=case_name
            )

            # Calculate metrics for each entity type
            case_report = {"case": case_name, "metrics": {}}

            for category, entity_type in [
                ("persons", "PERSON"),
                ("properties", "PROPERTY"),
                ("locations", "LOCATION"),
            ]:
                expected_names = get_expected_names(expected, category)
                if not expected_names:
                    continue
                extracted_names = extract_entity_names(result.entities, entity_type)
                metrics = ExtractionMetrics.calculate(expected_names, extracted_names)
                case_report["metrics"][category] = {
                    "recall": metrics.recall,
                    "precision": metrics.precision,
                    "f1": metrics.f1,
                    "expected": len(expected_names),
                    "found": metrics.true_positives,
                }

            reports.append(case_report)

        # Print report (visible in pytest -v output)
        print("\n\n=== EXTRACTION QUALITY REPORT ===")
        for report in reports:
            print(f"\n{report['case']}:")
            for category, m in report["metrics"].items():
                print(f"  {category}: R={m['recall']:.2f} P={m['precision']:.2f} F1={m['f1']:.2f} ({m['found']}/{m['expected']} found)")

        # Basic assertion to ensure tests ran
        assert len(reports) == len(cases), "All cases should be processed"


# Future: Add more golden test cases
# - sample_hipoteca.txt - Mortgage document
# - sample_confiscacion.txt - Confiscation document (post-1959)

# Helper functions for A/B comparison tests
def get_expected_names(expected: dict, entity_category: str) -> Set[str]:
    """Extract normalized names from expected entities."""
    names = set()
    for entity in expected["expected_entities"].get(entity_category, []):
        name = entity.get("name", "")
        if name:
            names.add(name.lower().strip())
    return names


def extract_entity_names(entities: list, entity_type: str) -> Set[str]:
    """Extract normalized names from extracted entities of a specific type."""
    names = set()
    for entity in entities:
        type_val = entity.entity_type.value if hasattr(entity.entity_type, "value") else entity.entity_type
        if type_val == entity_type:
            name = getattr(entity, "name", None)
            if name:
                names.add(name.lower().strip())
    return names


class ExtractionMetrics:
    """Metrics for evaluating extraction quality."""

    def __init__(self, precision: float, recall: float, f1: float, true_positives: int):
        self.precision = precision
        self.recall = recall
        self.f1 = f1
        self.true_positives = true_positives

    @classmethod
    def calculate(cls, expected: Set[str], extracted: Set[str]) -> "ExtractionMetrics":
        """Calculate precision, recall, and F1 score."""
        if not extracted:
            return cls(0.0, 0.0, 0.0, 0)

        true_positives = len(expected & extracted)
        precision = true_positives / len(extracted) if extracted else 0.0
        recall = true_positives / len(expected) if expected else 0.0
        f1 = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        return cls(precision, recall, f1, true_positives)


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
)
class TestZeroShotExtraction:
    """Test zero-shot extraction quality against golden standards."""

    @pytest.fixture
    def service(self):
        return LLMExtractionService(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )

    def test_escritura_person_recall_zero_shot(self, service):
        """Test zero-shot person recall on escritura."""
        text, expected = load_golden_case("sample_escritura")
        result = service.extract_from_text(
            text=text, ocr_confidence=0.95, document_id="sample_escritura_zero_shot"
        )

        expected_names = get_expected_names(expected, "persons")
        extracted_names = extract_entity_names(result.entities, "PERSON")
        metrics = ExtractionMetrics.calculate(expected_names, extracted_names)

        # Zero-shot threshold may be lower - we're testing cost/quality tradeoff
        assert metrics.recall >= 0.4, (
            f"Zero-shot person recall {metrics.recall:.2f} below threshold. "
            f"Found {metrics.true_positives}/{len(expected_names)}."
        )

    def test_extraction_metadata_has_prompt_mode(self):
        """Verify extraction metadata includes prompt_mode."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        text, _ = load_golden_case("sample_escritura")

        service = LLMExtractionService(api_key=api_key)
        result = service.extract_from_text(
            text=text, ocr_confidence=0.95, document_id="test_metadata"
        )

        # Verify metadata
        assert result.metadata.get("prompt_mode") == "zero_shot"
        assert len(result.entities) > 0
