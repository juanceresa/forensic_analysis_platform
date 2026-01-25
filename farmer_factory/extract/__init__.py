"""
Extraction module.
Handles OCR (Google Cloud Vision) and LLM-based entity/relation extraction (Anthropic Claude).
All extracted data starts at TIER_3_AI verification level.
"""

from .ocr import OCRService, OCRResult
from .vision import VisionExtractionService, VisionExtractionResult
from .llm import LLMExtractionService, LLMExtractionResult
from .pipeline import ExtractionPipeline, ExtractionResult
from .validator import SchemaValidator

# Export models for external use
from .models import (
    PersonExtraction,
    PropertyExtraction,
    OrganizationExtraction,
    LocationExtraction,
    StructuredEntityExtractionResult,
    ExtractedRelation,
    RelationExtractionResult
)

# Export API client for direct use if needed
from .api_client import ClaudeAPIClient

__all__ = [
    # Services
    "OCRService",
    "OCRResult",
    "VisionExtractionService",
    "VisionExtractionResult",
    "LLMExtractionService",
    "LLMExtractionResult",
    "ExtractionPipeline",
    "ExtractionResult",
    "SchemaValidator",

    # Models
    "PersonExtraction",
    "PropertyExtraction",
    "OrganizationExtraction",
    "LocationExtraction",
    "StructuredEntityExtractionResult",
    "ExtractedRelation",
    "RelationExtractionResult",

    # API Client
    "ClaudeAPIClient",
]
