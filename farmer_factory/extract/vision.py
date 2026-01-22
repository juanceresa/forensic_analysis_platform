"""Vision extraction service for handwritten documents using Claude Vision API (mocked)."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np
import logging

from farmer_factory.structure.schema import BaseEntity, Relation

logger = logging.getLogger(__name__)


@dataclass
class VisionExtractionResult:
    """Result from vision-based entity extraction."""
    entities: List[BaseEntity]   # Extracted entities (Pydantic models)
    relations: List[Relation]    # Extracted relations
    confidence: float            # Overall extraction confidence
    reasoning: str               # Claude's reasoning for extractions
    metadata: Dict[str, Any]     # Vision model metadata


class VisionExtractionService:
    """Wrapper for Claude Vision API for handwritten document extraction (mocked for testing)."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Vision extraction service.

        Args:
            api_key: Optional Anthropic API key.
                    If None, loads from environment variable.
        """
        self.api_key = api_key

    def extract_from_image(
        self,
        image: np.ndarray,
        document_id: str
    ) -> VisionExtractionResult:
        """
        Extract entities directly from handwritten image using mocked Claude Vision API.

        Args:
            image: Grayscale image as numpy array (uint8, 0-255)
            document_id: Document identifier for entity tracking

        Returns:
            VisionExtractionResult with extracted entities and relations

        Note:
            This is a MOCKED implementation for testing.
            Real implementation would call Anthropic Claude Vision API.
        """
        from farmer_factory.structure.schema import (
            Person, Property, EntityType, VerificationTier, Verification
        )

        # MOCKED: Simulate vision-based entity extraction
        # In production, this would send image to Claude Vision API with structured prompt
        logger.warning(
            f"⚠️  MOCK EXTRACTION - Using simulated data for {document_id}. "
            "Configure ANTHROPIC_API_KEY to use real Claude Vision API."
        )

        # Calculate base confidence based on image quality
        # Simple heuristic: check contrast and text-like patterns
        mean_intensity = np.mean(image)
        std_intensity = np.std(image)

        # Good contrast indicates clearer handwriting
        contrast_score = min(1.0, std_intensity / 50.0)
        base_confidence = 0.65 + (contrast_score * 0.20)  # Range: 0.65-0.85

        # Mock extracted entities (simulating Claude Vision understanding)
        verification = Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=base_confidence,
            verified_by=None,
            verified_at=None,
            notes=None
        )

        # Mock Person entity
        person = Person(
            id=f"{document_id}_person_1",
            entity_type=EntityType.PERSON,
            name="Juan Pérez García",
            alternate_names=["J. Pérez"],
            birth_date="1920-03-15",
            nationality="Cuban",
            residence="Havana",
            roles=["owner"],
            verification=verification,
            extracted_from=document_id,
            notes="⚠️ MOCK DATA - Simulated extraction for testing (no API configured)"
        )

        # Mock Property entity
        property_entity = Property(
            id=f"{document_id}_property_1",
            entity_type=EntityType.PROPERTY,
            name="Casa en Miramar",
            property_type="residential",
            location_id=None,
            area_sq_meters=250.0,
            registry_number="REG-1958-0042",
            verification=verification,
            extracted_from=document_id,
            notes="⚠️ MOCK DATA - Simulated extraction for testing (no API configured)"
        )

        entities = [person, property_entity]

        # Mock relations
        from farmer_factory.structure.schema import Relation, RelationType

        relation = Relation(
            id=f"{document_id}_rel_1",
            type=RelationType.OWNS,
            source_id=person.id,
            target_id=property_entity.id,
            verification=verification,
            document_id=document_id,
            notes="⚠️ MOCK DATA - Simulated relation for testing (no API configured)"
        )

        relations = [relation]

        # Mock reasoning (simulating Claude's thought process)
        reasoning = f"""
        Analyzed handwritten document image ({image.shape[0]}x{image.shape[1]} pixels).

        Detected entities:
        - Person: Juan Pérez García, identified as owner based on document structure
        - Property: Casa en Miramar, residential property with registry number

        Confidence: {base_confidence:.2f} based on handwriting clarity and document condition.
        This is a mocked extraction for testing purposes.
        """.strip()

        # Mock metadata
        metadata = {
            "model": "claude-vision-mocked",
            "api_version": "mocked_v1",
            "processing_time_ms": 1500,
            "image_dimensions": {
                "height": image.shape[0],
                "width": image.shape[1]
            },
            "image_quality_score": contrast_score
        }

        return VisionExtractionResult(
            entities=entities,
            relations=relations,
            confidence=base_confidence,
            reasoning=reasoning,
            metadata=metadata
        )
