# OCR Text Storage Design

**Date:** 2026-01-22
**Status:** Approved
**Type:** Feature Design

---

## Problem Statement

The Factory pipeline successfully extracts OCR text from documents using Google Cloud Vision API, but this text is not being saved to the extraction JSON files. This creates critical gaps for:

1. **Audit trail** - Can't trace how AI conclusions were made
2. **Error detection** - Can't identify if extraction failures stem from OCR errors
3. **Analyst verification** - TIER_2_ANALYST workflow requires reviewing source text
4. **Debugging** - Can't troubleshoot "why wasn't X extracted?" without seeing OCR output

## Design Goals

- Save complete OCR output (text, blocks, confidence, metadata) to extraction JSON
- Maintain audit trail for forensic work
- Enable analyst verification workflow
- Support future UI features (text highlighting, confidence visualization)
- Document frontend requirements for later Vault implementation

## Current Architecture

**What exists:**
```python
class ExtractionResult:
    entities: List[BaseEntity]
    relations: List[Relation]
    ocr_result: Optional[OCRResult]  # ← Field exists but not serialized
    confidence_scores: Dict[str, float]
    path: DocumentPath
    processing_metadata: Dict[str, Any]
```

**What's saved:**
```json
{
  "entities": [...],
  "relations": [...],
  // ocr_result is dropped during serialization
  "confidence_scores": {...},
  "path": "TYPED",
  "processing_metadata": {...}
}
```

## Proposed Solution

### 1. Backend Implementation

**Update:** `farmer_factory/processing/helpers.py`

Add OCR serialization to `save_extraction_json()`:

```python
def save_extraction_json(extraction: ExtractionResult, output_path: Path):
    """Save extraction result to JSON file."""

    data = {
        "entities": [entity.model_dump() for entity in extraction.entities],
        "relations": [relation.model_dump() for relation in extraction.relations],
        "ocr_result": _serialize_ocr_result(extraction.ocr_result) if extraction.ocr_result else None,
        "confidence_scores": extraction.confidence_scores,
        "path": extraction.path.value,
        "processing_metadata": extraction.processing_metadata
    }

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

def _serialize_ocr_result(ocr: OCRResult) -> dict:
    """Convert OCRResult dataclass to JSON-serializable dict."""
    return {
        "text": ocr.text,
        "confidence": ocr.confidence,
        "page_confidence": ocr.page_confidence,
        "blocks": [_serialize_text_block(block) for block in ocr.blocks],
        "metadata": ocr.metadata
    }

def _serialize_text_block(block: TextBlock) -> dict:
    """Convert TextBlock dataclass to dict."""
    return {
        "text": block.text,
        "confidence": block.confidence,
        "bounding_box": list(block.bounding_box),  # tuple → list
        "block_type": block.block_type
    }
```

### 2. JSON Schema

**Updated extraction JSON structure:**

```json
{
  "entities": [...],
  "relations": [...],
  "ocr_result": {
    "text": "Full extracted text from document...",
    "confidence": 0.9267,
    "page_confidence": 0.9134,
    "blocks": [
      {
        "text": "Mario Ceresa",
        "confidence": 0.95,
        "bounding_box": [120, 450, 280, 35],
        "block_type": "paragraph"
      }
    ],
    "metadata": {
      "language": "es",
      "api_version": "google_cloud_vision_v1",
      "image_dimensions": {
        "height": 4200,
        "width": 2550
      }
    }
  },
  "confidence_scores": {...},
  "path": "TYPED",
  "processing_metadata": {...}
}
```

**Key points:**
- `ocr_result` is `null` for HANDWRITTEN path (uses Vision extraction)
- `ocr_result` populated for TYPED path with complete Google Cloud Vision response
- Bounding boxes: `[x, y, width, height]` for easy JSON serialization
- All existing fields unchanged (backwards compatible with pipeline)

### 3. Frontend Requirements

**Documented in:** `.claude/FRONTEND.md`

**Components needing OCR text:**

1. **SourceViewer** - Document viewer component
   - Display OCR text alongside document image
   - Show confidence: "OCR Confidence: 93%"
   - Show language: "Detected Language: Spanish (es)"
   - Color-code confidence: green >90%, yellow 70-90%, red <70%

2. **Analyst Review Panel** (TIER_2_ANALYST workflow)
   - Side-by-side: document image | OCR text | extracted entities
   - Per-block confidence for troubleshooting
   - "Why wasn't X extracted?" debugging

3. **Client/Family View** (transparency)
   - "Source Text" tab in document dossier
   - Read-only OCR text with confidence indicator
   - TIER_3_AI disclaimer required

**Access Control:**
- OCR text follows case-based permissions
- If user can see case, they can see OCR text
- No special permissions needed

**Future Enhancement (out of scope):**
- Click entity → highlight source text in document
- Requires mapping entities to OCR blocks via bounding boxes

## Implementation Steps

1. **Modify `helpers.py`** - Add OCR serialization functions
2. **Test with single file** - Verify OCR text appears in extraction JSON
3. **Verify actual text** - Confirm real Spanish text, not mock data
4. **Update FRONTEND.md** - Document OCR display requirements
5. **Commit design doc** - Save this document for reference

## Testing Plan

**Command:**
```bash
python farmer_factory/cli.py process TEST-CERESA \
  --file "1 4 1961 Mario Ceresa Money Transfer.pdf" \
  --force-typed --verbose
```

**Verify:**
- Extraction JSON contains `ocr_result` field
- `ocr_result.text` is actual Spanish text from document
- `ocr_result.confidence` is ~0.93 (from Google Cloud Vision)
- `ocr_result.metadata.language` is "es"
- `ocr_result.blocks` contains 27 text blocks with bounding boxes

## Success Criteria

- ✅ OCR text saved to extraction JSON
- ✅ Complete audit trail (text + confidence + blocks)
- ✅ Enables analyst verification workflow
- ✅ Frontend requirements documented
- ✅ No breaking changes to existing pipeline

## Future Considerations

**Not in scope for this implementation:**
- OCR text search/indexing
- Text highlighting in document viewer
- OCR correction/editing interface
- Multi-language OCR optimization

**Future enhancements:**
- Save OCR text to separate searchable index
- Map entity extractions back to OCR blocks
- Confidence-based filtering in Vault UI
- OCR quality metrics dashboard

---

*This design enables complete audit trails for forensic intelligence work while maintaining the Factory's air-gap architecture.*
