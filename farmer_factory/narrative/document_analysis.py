"""Generate per-document analysis using Haiku for structured interpretive summaries."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from farmer_factory.config.settings import settings
from farmer_factory.extract.api_client import ClaudeAPIClient
from farmer_factory.narrative.models import (
    DocumentAnalysis,
    GenerationMetadata,
    OcrQuality,
)

if TYPE_CHECKING:
    from farmer_factory.intake.manifest import CaseFocus

logger = logging.getLogger(__name__)

PROMPT_VERSION = "1.0"

DOCUMENT_ANALYSIS_PROMPT = """You are a forensic research analyst examining a historical document related to property restitution. Produce a structured analysis of this document.

**CRITICAL CONSTRAINTS:**
1. State ONLY what the document shows — never infer ownership validity or legal conclusions
2. NEVER say "this proves" or "this establishes legal right" — say "this document states" or "this records"
3. Be specific: use names, dates, and references from the document
4. This is AI-generated research context, not a verified legal analysis

**DOCUMENT TEXT:**
{document_text}

**EXTRACTED ENTITIES:**
{entities_section}

**EXTRACTED RELATIONS:**
{relations_section}

**OCR CONFIDENCE:** {ocr_confidence}

Respond with ONLY valid JSON matching this exact schema (no markdown, no explanation):
{{
  "document_type": "<type of document, e.g. Escritura de Compraventa, Poder General, Certificación>",
  "executive_summary": "<2-4 sentence plain-English summary of what this document records>",
  "claim_relevance": {{
    "level": "<CRITICAL|HIGH|MEDIUM|LOW>",
    "reasoning": "<1-2 sentences explaining relevance to property restitution claims>"
  }},
  "key_facts": [
    "<specific factual statement from the document>"
  ],
  "cross_references": [
    "<reference to other documents, cases, or registry entries mentioned>"
  ],
  "quality_notes": {{
    "ocr_quality": "<EXCELLENT|GOOD|FAIR|POOR>",
    "missing_information": ["<gaps or illegible sections>"],
    "verification_needed": ["<claims that need independent verification>"]
  }}
}}"""


def _ocr_quality_from_confidence(confidence: float) -> str:
    """Map OCR confidence score to quality label."""
    if confidence > 0.90:
        return "EXCELLENT"
    elif confidence >= 0.75:
        return "GOOD"
    elif confidence >= 0.60:
        return "FAIR"
    return "POOR"


def _build_entities_section(extraction_data: dict[str, Any]) -> str:
    """Build entity summary from extraction JSON."""
    entities = extraction_data.get("entities", [])
    if not entities:
        return "No entities extracted"

    lines = []
    for e in entities[:20]:  # Cap at 20 to keep prompt reasonable
        name = e.get("name", "?")
        etype = e.get("entity_type", "?")
        roles = e.get("roleLabel", "")
        role_str = f" (role: {roles})" if roles else ""
        lines.append(f"- {name} [{etype}]{role_str}")
    if len(entities) > 20:
        lines.append(f"  ... and {len(entities) - 20} more")
    return "\n".join(lines)


def _build_relations_section(extraction_data: dict[str, Any]) -> str:
    """Build relation summary from extraction JSON."""
    relations = extraction_data.get("relations", [])
    if not relations:
        return "No relations extracted"

    lines = []
    for r in relations[:15]:  # Cap at 15
        rtype = r.get("relation_type", "?")
        source = r.get("source", "?")
        target = r.get("target", "?")
        evidence = r.get("evidence", "")
        ev_str = f' — "{evidence[:80]}"' if evidence else ""
        lines.append(f"- {source} → {rtype} → {target}{ev_str}")
    if len(relations) > 15:
        lines.append(f"  ... and {len(relations) - 15} more")
    return "\n".join(lines)


def _load_document_text(case_dir: Path, doc_stem: str) -> str:
    """Load cleaned OCR text, falling back to raw."""
    cleaned_path = case_dir / "ocr_cleaned" / f"{doc_stem}.txt"
    if cleaned_path.exists():
        return cleaned_path.read_text(encoding="utf-8")

    raw_path = case_dir / "ocr" / f"{doc_stem}.txt"
    if raw_path.exists():
        return raw_path.read_text(encoding="utf-8")

    return ""


def _load_extraction(extractions_dir: Path, doc_stem: str) -> dict[str, Any]:
    """Load extraction JSON for a document."""
    ext_path = extractions_dir / f"{doc_stem}.json"
    if ext_path.exists():
        return json.loads(ext_path.read_text(encoding="utf-8"))
    return {}


def _get_ocr_confidence(extraction: dict[str, Any]) -> float:
    """Extract OCR confidence from extraction data."""
    return extraction.get("confidence_scores", {}).get("ocr_confidence", 0.0)


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    """Write JSON atomically via temp file + os.replace()."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=str(path.parent), suffix=".tmp", prefix=".analysis_"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, str(path))
    except Exception:
        # Clean up temp file on failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def generate_document_analyses(
    case_id: str,
    max_cost: float = 1.00,
    case_focus: CaseFocus | None = None,
) -> Path:
    """Generate structured analysis for each document in a case.

    Reads extraction JSONs and OCR text, generates interpretive analysis via Haiku,
    and writes a separate document_analyses.json file.

    Args:
        case_id: Case identifier
        max_cost: Cost ceiling in USD (default $1.00)
        case_focus: Optional case-level focus configuration

    Returns:
        Path to document_analyses.json
    """
    case_dir = Path("cases") / case_id
    output_dir = case_dir / "output"
    extractions_dir = case_dir / "extractions"
    analyses_path = output_dir / "document_analyses.json"

    if not extractions_dir.exists():
        raise FileNotFoundError(f"Extractions not found: {extractions_dir}")

    # Load existing analyses to skip already-generated ones
    existing: dict[str, Any] = {}
    if analyses_path.exists():
        existing = json.loads(analyses_path.read_text(encoding="utf-8"))

    # Load document groups if available
    groups_config = _load_document_groups(case_dir)

    # Build target list: grouped documents + standalone
    targets = _build_target_list(case_dir, extractions_dir, groups_config, existing)

    if not targets:
        logger.info("All documents already have analyses, nothing to generate")
        return analyses_path

    logger.info(f"Generating analyses for {len(targets)} documents using Haiku")

    client = ClaudeAPIClient()
    total_cost = 0.0
    generated = 0

    for target in targets:
        if total_cost >= max_cost:
            logger.warning(f"Cost ceiling reached (${total_cost:.4f}/${max_cost:.2f}), stopping")
            break

        doc_key = target["key"]
        doc_text = target["text"]
        entities_section = target["entities_section"]
        relations_section = target["relations_section"]
        ocr_confidence = target["ocr_confidence"]
        source_docs = target["source_docs"]

        if not doc_text.strip():
            logger.warning(f"No OCR text for {doc_key}, skipping")
            continue

        focus_section = ""
        if case_focus is not None:
            focus_text = case_focus.to_prompt_section()
            if focus_text:
                focus_section = f"\n{focus_text}\n"

        prompt = f"{focus_section}{DOCUMENT_ANALYSIS_PROMPT}".format(
            document_text=doc_text[:12000],  # Cap text to keep prompt reasonable
            entities_section=entities_section,
            relations_section=relations_section,
            ocr_confidence=f"{ocr_confidence:.0%} ({_ocr_quality_from_confidence(ocr_confidence)})",
        )

        try:
            response = client.call_standard(
                prompt=prompt,
                model=settings.claude_model,  # Haiku
                max_retries=2,
                api_timeout=60,
            )

            # Parse and validate response
            analysis_data = _parse_analysis_response(response, source_docs)
            existing[doc_key] = analysis_data
            generated += 1

            cost = ClaudeAPIClient._compute_cost(
                settings.claude_model,
                int(len(prompt.split()) * 1.3),
                int(len(response.split()) * 1.3),
            )
            total_cost += cost

            logger.info(f"  [{generated}/{len(targets)}] {doc_key} — ${cost:.4f}")

        except Exception as e:
            logger.warning(f"Failed to generate analysis for {doc_key}: {e}")
            # Store error marker
            existing[doc_key] = {
                "_error": "generation_failed",
                "raw_response": str(e)[:500],
                "_metadata": {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "model": settings.claude_model,
                    "prompt_version": PROMPT_VERSION,
                },
            }
            continue

    # Atomic write
    _atomic_write_json(analyses_path, existing)

    logger.info(
        f"Done: {generated}/{len(targets)} analyses generated, "
        f"total cost ${total_cost:.4f}"
    )
    return analyses_path


def _parse_analysis_response(response: str, source_docs: list[str]) -> dict[str, Any]:
    """Parse LLM response into validated DocumentAnalysis dict.

    Falls back to error-marker on validation failure.
    """
    metadata = GenerationMetadata(
        generated_at=datetime.now(timezone.utc).isoformat(),
        model=settings.claude_model,
        prompt_version=PROMPT_VERSION,
    )

    # Strip markdown fences if present
    text = response.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    try:
        raw = json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON from LLM: {e}")
        return {
            "_error": "validation_failed",
            "raw_response": response[:500],
            "_metadata": metadata.model_dump(),
        }

    # Add source_docs before validation
    raw["source_docs"] = source_docs

    try:
        analysis = DocumentAnalysis.model_validate(raw)
        result = analysis.model_dump()
        result["_metadata"] = metadata.model_dump()
        return result
    except Exception as e:
        logger.warning(f"Pydantic validation failed: {e}")
        return {
            "_error": "validation_failed",
            "raw_response": response[:500],
            "_metadata": metadata.model_dump(),
        }


def _load_document_groups(case_dir: Path):
    """Load document groups config if available and confirmed."""
    try:
        from farmer_factory.intake.document_groups import load_document_groups
        groups_config = load_document_groups(case_dir)
        if groups_config and groups_config.is_confirmed():
            return groups_config
    except Exception:
        pass
    return None


def _build_target_list(
    case_dir: Path,
    extractions_dir: Path,
    groups_config: Any,
    existing: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build list of documents to analyze, handling groups and standalone docs."""
    targets = []
    processed_stems: set[str] = set()

    # Handle grouped documents first
    if groups_config:
        for group in groups_config.groups:
            group_key = f"doc_{group.id}"
            if group_key in existing:
                # Mark all group file stems as processed
                for f in group.files:
                    stem = Path(f).stem
                    processed_stems.add(stem)
                    processed_stems.add(f"{stem}_page_0")
                continue

            # Concatenate all page texts and merge extractions
            all_text_parts = []
            all_entities: list[Any] = []
            all_relations: list[Any] = []
            max_confidence = 0.0
            source_doc_stems = []

            for filename in group.files:
                stem = Path(filename).stem
                # Try with _page_0 suffix (standard extraction naming)
                page_stem = f"{stem}_page_0"
                processed_stems.add(stem)
                processed_stems.add(page_stem)

                text = _load_document_text(case_dir, page_stem)
                if not text:
                    text = _load_document_text(case_dir, stem)
                all_text_parts.append(text)

                ext = _load_extraction(extractions_dir, page_stem)
                if not ext:
                    ext = _load_extraction(extractions_dir, stem)
                all_entities.extend(ext.get("entities", []))
                all_relations.extend(ext.get("relations", []))
                conf = _get_ocr_confidence(ext)
                if conf > max_confidence:
                    max_confidence = conf

                source_doc_stems.append(page_stem)

            merged_extraction = {
                "entities": all_entities,
                "relations": all_relations,
            }

            targets.append({
                "key": group_key,
                "text": "\n\n---\n\n".join(all_text_parts),
                "entities_section": _build_entities_section(merged_extraction),
                "relations_section": _build_relations_section(merged_extraction),
                "ocr_confidence": max_confidence,
                "source_docs": source_doc_stems,
            })

    # Handle standalone documents
    extraction_files = sorted(extractions_dir.glob("*.json"))
    for ext_file in extraction_files:
        stem = ext_file.stem
        if stem in processed_stems:
            continue
        if stem in existing:
            continue

        text = _load_document_text(case_dir, stem)
        extraction = _load_extraction(extractions_dir, stem)

        targets.append({
            "key": stem,
            "text": text,
            "entities_section": _build_entities_section(extraction),
            "relations_section": _build_relations_section(extraction),
            "ocr_confidence": _get_ocr_confidence(extraction),
            "source_docs": [stem],
        })

    return targets
