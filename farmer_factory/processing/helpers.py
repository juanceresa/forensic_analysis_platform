"""Helper functions for document processing pipeline."""

import json
import logging
from pathlib import Path
from typing import List
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)


def load_pdf_pages(pdf_path: Path, output_dir: Path) -> List[Path]:
    """
    Convert PDF to images, one per page.

    Args:
        pdf_path: Path to PDF file
        output_dir: Directory to save images

    Returns:
        List of paths to saved page images

    Raises:
        ValueError: If PDF cannot be converted
    """
    try:
        images = convert_from_path(
            pdf_path,
            dpi=300,              # High quality for OCR
            grayscale=True,       # Matches prepare module expectations
            fmt='png'
        )
    except Exception as e:
        raise ValueError(f"Failed to convert PDF {pdf_path.name}: {e}")

    page_paths = []
    for i, image in enumerate(images):
        page_path = output_dir / f"{pdf_path.stem}_page_{i}.png"
        image.save(page_path, 'PNG')
        page_paths.append(page_path)
        logger.debug(f"Saved page {i} to {page_path}")

    logger.info(f"Converted {pdf_path.name} to {len(page_paths)} images")
    return page_paths


def _serialize_text_block(block) -> dict:
    """
    Convert TextBlock dataclass to JSON-serializable dict.

    Args:
        block: TextBlock with text, confidence, bounding_box, block_type

    Returns:
        Dictionary with all TextBlock fields, bounding_box as list
    """
    return {
        "text": block.text,
        "confidence": block.confidence,
        "bounding_box": list(block.bounding_box),  # tuple → list for JSON
        "block_type": block.block_type
    }


def _serialize_ocr_result(ocr) -> dict:
    """
    Convert OCRResult dataclass to JSON-serializable dict.

    Args:
        ocr: OCRResult with text, confidence, blocks, metadata

    Returns:
        Dictionary with complete OCR data including serialized blocks
    """
    return {
        "text": ocr.text,
        "confidence": ocr.confidence,
        "page_confidence": ocr.page_confidence,
        "blocks": [_serialize_text_block(block) for block in ocr.blocks],
        "metadata": ocr.metadata
    }


def save_extraction_json(extraction, output_path: Path) -> None:
    """
    Save extraction result to JSON with proper serialization.

    Args:
        extraction: ExtractionResult object
        output_path: Path to save JSON file
    """
    from datetime import datetime

    class DateTimeEncoder(json.JSONEncoder):
        """Custom JSON encoder for datetime objects."""
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return super().default(obj)

    data = {
        'entities': [e.model_dump() for e in extraction.entities],
        'relations': [r.model_dump() for r in extraction.relations],
        'ocr_result': _serialize_ocr_result(extraction.ocr_result) if extraction.ocr_result else None,
        'confidence_scores': extraction.confidence_scores,
        'path': extraction.path.value,
        'processing_metadata': extraction.processing_metadata
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)

    logger.debug(f"Saved extraction to {output_path}")


def setup_logging(log_file: Path) -> None:
    """
    Configure dual logging: file (DEBUG) + console (INFO).

    Args:
        log_file: Path to log file
    """
    # Create log directory if needed
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # File handler: detailed logs
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    # Console handler: user-facing info
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logger.info(f"Logging configured: {log_file}")
