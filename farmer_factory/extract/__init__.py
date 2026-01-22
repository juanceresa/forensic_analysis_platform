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

__all__ = [
    "OCRService",
    "OCRResult",
    "VisionExtractionService",
    "VisionExtractionResult",
    "LLMExtractionService",
    "LLMExtractionResult",
    "ExtractionPipeline",
    "ExtractionResult",
    "SchemaValidator",
]
