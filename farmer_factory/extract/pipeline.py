"""Extraction pipeline orchestrating OCR, Vision, and LLM services."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from farmer_factory.prepare import DocumentPath, ProcessedPage
from farmer_factory.structure.schema import BaseEntity, Relation
from farmer_factory.extract.ocr import OCRService, OCRResult
from farmer_factory.extract.vision import VisionExtractionService
from farmer_factory.extract.llm import LLMExtractionService
from farmer_factory.extract.validator import SchemaValidator


@dataclass
class ExtractionResult:
    """Complete extraction result for a document page."""
    entities: List[BaseEntity]              # All extracted entities
    relations: List[Relation]               # All extracted relations
    ocr_result: Optional[OCRResult]         # OCR output (TYPED path only)
    confidence_scores: Dict[str, float]     # Multi-level confidence tracking
    path: DocumentPath                      # Which path was used
    processing_metadata: Dict[str, Any]     # Processing metadata


class ExtractionPipeline:
    """Orchestrates the two-path extraction process."""

    def __init__(
        self,
        ocr_service: OCRService,
        vision_service: VisionExtractionService,
        llm_service: LLMExtractionService,
        validator: SchemaValidator
    ):
        """
        Initialize extraction pipeline with services.

        Args:
            ocr_service: OCR service for typed documents
            vision_service: Vision service for handwritten documents
            llm_service: LLM service for entity extraction from text
            validator: Schema validator for Pydantic models
        """
        self.ocr_service = ocr_service
        self.vision_service = vision_service
        self.llm_service = llm_service
        self.validator = validator
