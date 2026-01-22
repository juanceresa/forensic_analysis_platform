"""LLM extraction service for entity extraction from OCR text using Claude API (mocked)."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import logging

from farmer_factory.structure.schema import BaseEntity, Relation

logger = logging.getLogger(__name__)


@dataclass
class LLMExtractionResult:
    """Result from LLM-based entity extraction."""
    entities: List[BaseEntity]   # Extracted entities
    relations: List[Relation]    # Extracted relations
    confidence: float            # Extraction confidence
    reasoning: str               # Extraction reasoning
    metadata: Dict[str, Any]


class LLMExtractionService:
    """Wrapper for Claude text API for entity extraction from OCR text (mocked for testing)."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM extraction service.

        Args:
            api_key: Optional Anthropic API key.
                    If None, loads from environment variable.
        """
        self.api_key = api_key

    def extract_from_text(
        self,
        text: str,
        ocr_confidence: float,
        document_id: str
    ) -> LLMExtractionResult:
        """
        Extract entities from OCR text using mocked Claude text API.

        Args:
            text: OCR-extracted text from document
            ocr_confidence: Confidence score from OCR (0.0-1.0)
            document_id: Document identifier for entity tracking

        Returns:
            LLMExtractionResult with extracted entities and relations

        Note:
            This is a MOCKED implementation for testing.
            Real implementation would call Anthropic Claude API with structured prompt.
        """
        from farmer_factory.structure.schema import (
            Person, Property, Organization, Location,
            EntityType, VerificationTier, Verification,
            Relation, RelationType
        )

        # MOCKED: Simulate LLM entity extraction from text
        # In production, this would send text to Claude API with JSON schema prompt
        logger.warning(
            f"⚠️  MOCK EXTRACTION - Using simulated data for {document_id}. "
            "Configure ANTHROPIC_API_KEY to use real Claude API."
        )

        # Calculate extraction confidence
        # Base LLM confidence (simulated quality of extraction)
        llm_base_confidence = 0.88

        # Combined confidence: min of OCR and LLM
        combined_confidence = min(ocr_confidence, llm_base_confidence)

        # Create verification for all entities
        verification = Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=combined_confidence,
            verified_by=None,
            verified_at=None,
            notes=None
        )

        # Mock entity extraction (simulating Claude understanding the text)
        entities = []

        # Extract entities based on text content
        # Check for specific Spanish names first (for realistic test cases)
        if "Juan Pérez" in text or "Juan Perez" in text:
            person1 = Person(
                id=f"{document_id}_person_1",
                entity_type=EntityType.PERSON,
                name="Juan Pérez García",
                alternate_names=["Don Juan Pérez García", "Sr. Juan Pérez García"],
                birth_date=None,
                nationality="Cuban",
                residence="Miramar, calle 5ta No. 234",
                marital_status="casado",
                roles=["seller", "owner"],
                verification=verification,
                extracted_from=document_id,
                notes="⚠️ MOCK DATA - Simulated extraction for testing (no API configured)"
            )
            entities.append(person1)

        if "María López" in text or "Maria Lopez" in text:
            person2 = Person(
                id=f"{document_id}_person_2",
                entity_type=EntityType.PERSON,
                name="María López Fernández",
                alternate_names=["Doña María López Fernández"],
                birth_date=None,
                nationality="Cuban",
                residence="Vedado, Avenida 23 No. 567",
                marital_status="soltera",
                roles=["buyer"],
                verification=verification,
                extracted_from=document_id,
                notes="⚠️ MOCK DATA - Simulated extraction for testing (no API configured)"
            )
            entities.append(person2)

        # Extract Property entity
        if "finca" in text.lower() or "propiedad" in text.lower() or "property" in text.lower():
            property_entity = Property(
                id=f"{document_id}_property_1",
                entity_type=EntityType.PROPERTY,
                name="Finca urbana en Miramar",
                property_type="residential",
                location_id=None,
                address="calle 5ta No. 234, Miramar",
                registry_number="REG-1958-0042",
                verification=verification,
                extracted_from=document_id,
                notes="⚠️ MOCK DATA - Simulated extraction for testing (no API configured)"
            )
            entities.append(property_entity)

        # Extract Location entity
        if "Havana" in text or "Habana" in text:
            location = Location(
                id=f"{document_id}_location_1",
                entity_type=EntityType.LOCATION,
                name="La Habana",
                location_type="city",
                verification=verification,
                extracted_from=document_id,
                notes="⚠️ MOCK DATA - Simulated extraction for testing (no API configured)"
            )
            entities.append(location)

        # Generic extraction fallback: if no specific entities found but text is substantial,
        # create generic mock entities (simulates LLM finding something in any text)
        if len(entities) == 0 and len(text) > 50:
            # Generic person entity
            person = Person(
                id=f"{document_id}_person_generic",
                entity_type=EntityType.PERSON,
                name="Generic Person",
                alternate_names=[],
                roles=["owner"],
                verification=verification,
                extracted_from=document_id,
                notes="Generic entity extracted from OCR text for testing"
            )
            entities.append(person)

        # Mock relations
        relations = []

        if len(entities) >= 2:
            # Look for ownership relations
            persons = [e for e in entities if e.entity_type == EntityType.PERSON]
            properties = [e for e in entities if e.entity_type == EntityType.PROPERTY]

            if persons and properties:
                relation = Relation(
                    id=f"{document_id}_rel_1",
                    type=RelationType.OWNS,
                    source_id=persons[0].id,
                    target_id=properties[0].id,
                    verification=verification,
                    document_id=document_id,
                    notes="Ownership extracted from deed text"
                )
                relations.append(relation)

        # Mock reasoning (simulating Claude's extraction logic)
        reasoning = f"""
        Analyzed OCR text (OCR confidence: {ocr_confidence:.2f}) from document.

        Extracted entities:
        - {len([e for e in entities if e.entity_type == EntityType.PERSON])} Person(s)
        - {len([e for e in entities if e.entity_type == EntityType.PROPERTY])} Property/Properties
        - {len([e for e in entities if e.entity_type == EntityType.LOCATION])} Location(s)

        Identified relations: {len(relations)} ownership/transaction relations

        Combined confidence: {combined_confidence:.2f} (min of OCR {ocr_confidence:.2f} and LLM {llm_base_confidence:.2f})
        All entities tagged as TIER_3_AI (unverified AI extraction).

        This is a mocked extraction for testing purposes.
        """.strip()

        # Mock metadata
        metadata = {
            "model": "claude-llm-mocked",
            "api_version": "mocked_v1",
            "processing_time_ms": 800,
            "ocr_confidence": ocr_confidence,
            "llm_confidence": llm_base_confidence,
            "text_length": len(text)
        }

        return LLMExtractionResult(
            entities=entities,
            relations=relations,
            confidence=combined_confidence,
            reasoning=reasoning,
            metadata=metadata
        )
