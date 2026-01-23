# Relation Extraction Design

> **Document Classification:** Internal Engineering Design
> **Version:** 1.0.0
> **Created:** 2026-01-22
> **Status:** Approved for Implementation

---

## Overview

This document specifies the design for relation extraction in the Civic Table platform. Relation extraction connects entities in the knowledge graph by identifying relationships like ownership, transfers, and legal actions from OCR text.

**Goal:** Extract all 11 relation types defined in PROMPTS.md to create a meaningful knowledge graph with complete ownership chains and social connections.

---

## Design Decisions

### 1. Two-Pass Approach

**Decision:** Extract entities first, then relations in a second Claude API call.

**Rationale:**
- Clean separation of concerns (easier debugging)
- Follows PROMPTS.md architecture (separate prompts already defined)
- Enables retry flexibility (can retry just relations if they fail)
- Each prompt has one clear job
- Cost is minimal (Haiku ~$0.25 per million tokens)

**Optimization:** Skip relation extraction if 0-1 entities found (no relations possible).

### 2. Extract All 11 Relation Types

**Decision:** Backend extracts all relation types; frontend filters into views.

**Relation types:**
- **Property relations:** OWNS, SOLD, BOUGHT, INHERITED, CONFISCATED
- **Legal/administrative:** WITNESSED, NOTARIZED, REGISTERED_IN
- **Spatial:** LOCATED_IN
- **Social/organizational:** EMPLOYED_BY, RELATED_TO

**Rationale:**
- Maximum data capture for forensic platform
- Frontend flexibility (users can filter by relation type)
- Supports multiple view modes (property graph vs family tree)
- Complete evidence picture

### 3. Smart Hybrid Entity Matching

**Decision:** Three-tier matching strategy for connecting relations to entity IDs.

**Matching algorithm:**
1. Exact match on `entity.name`
2. Exact match on `entity.alternate_names[]`
3. Fuzzy match with threshold ≥0.85 (log when used)
4. Return `None` if no match (skip relation, log warning)

**Rationale:**
- Handles title variations ("Mario Ceresa" vs "Don Mario Ceresa")
- Handles property name variations ("Central Santa Maria" vs "Ingenio Santa Maria")
- Handles OCR inconsistencies ("José" vs "Jose")
- Conservative threshold prevents false matches
- Transparent logging for analyst review

### 4. Tiered Confidence Approach

**Decision:** Store all relations regardless of confidence; flag low-confidence ones.

**Implementation:**
```python
if relation.confidence >= 0.70:
    relation.needs_review = False  # "Good" relation
else:
    relation.needs_review = True   # "Questionable" - flag for analyst
    relation.notes += f"Low confidence ({relation.confidence:.2f}) - requires analyst review"
```

**Rationale:**
- Missing data worse than noisy data in legal/forensic context
- Low-confidence relation (0.68) could be critical evidence
- Aligns with TIER_3_AI → TIER_2_ANALYST workflow
- Frontend can filter: "Show only confident" vs "Show all including flagged"
- Analysts see clear signal: "review these first"

### 5. Smart Temporal Handling

**Decision:** Apply context-dependent temporal logic based on relation type.

**Relation categorization:**

**Temporal relations** (dates important):
- SOLD, BOUGHT, INHERITED, CONFISCATED, WITNESSED, NOTARIZED
- These describe events at specific times

**State relations** (dates optional):
- OWNS, LOCATED_IN, EMPLOYED_BY, RELATED_TO, REGISTERED_IN
- These describe ongoing conditions

**Fallback strategy:**

For **temporal relations:**
1. Use Claude's extracted date if available
2. Fall back to document date with `date_precision: "year"`
3. Last resort: mark `date_precision: "unknown"` and flag for review

For **state relations:**
1. Use Claude's extracted date if available
2. Otherwise: `date_precision: "unknown"`, no review flag (dates not critical)

**Rationale:**
- Preserves all data (forensic principle)
- Intelligent fallbacks based on document metadata
- Respects semantic differences between relation types
- Flags genuinely problematic cases (event with no date)

### 6. Graceful Failure with Retry

**Decision:** Store partial results when relation extraction fails; enable targeted retry.

**Failure handling:**
- If relation extraction fails: return empty `relations=[]`
- Flag document: `extraction_flags: ["RELATION_EXTRACTION_FAILED"]`
- Mark status: `"relation_extraction_status": "FAILED"`
- Preserve entities (already extracted successfully)

**Retry mechanism:**
```bash
# Initial processing
python cli.py process TEST-CERESA
# Output: "⚠️  4 documents incomplete (relation extraction failed)"

# Retry just failures
python cli.py retry-relations TEST-CERESA
```

**Rationale:**
- Batch resilience (one API hiccup doesn't kill entire run)
- No wasted work (entities preserved, don't re-run OCR)
- Easy recovery (target just the failures)
- Clear visibility (you know what needs attention)

### 7. Code Organization

**Decision:** Add relation extraction to existing `LLMExtractionService` class.

**Rationale:**
- Shares Claude API client (already initialized)
- Reuses retry logic (`_call_claude_api_with_retry`)
- Reuses JSON parsing infrastructure
- Shares settings (model, timeout, retries)
- File stays manageable (~700 lines total)
- Avoids code duplication

### 8. Validation Strategy

**Decision:** Manual spot-check + confidence monitoring for MVP1.

**Phase 1 - Manual validation:**
- Process 3-5 TEST-CERESA documents
- Review output JSON: do relations make sense?
- Check entity matching accuracy
- Verify temporal dates align with document content

**Phase 2 - Ongoing monitoring:**
```python
stats = {
    "avg_relations_per_doc": 3.2,
    "avg_relation_confidence": 0.78,
    "relation_type_breakdown": {"OWNS": 45, "SOLD": 12, ...},
    "low_confidence_relations": 8,
    "entity_matching_failures": 2
}
```

**Rationale:**
- Fast (no annotation work needed)
- Practical (uses real documents)
- Catches major issues via manual review
- Scalable (stats catch drift at scale)
- Forensic-appropriate (spot-checking is standard QA)

---

## Architecture

### High-Level Flow

```
1. extract_from_text() called [existing entry point]
2. Extract entities via _extract_entities() [existing]
3. Check: len(entities) >= 2?
   YES → Extract relations via _extract_relations() [new]
   NO  → Skip, return entities with relations=[]
4. Return LLMExtractionResult with entities + relations
```

### Class Structure

```python
class LLMExtractionService:
    # Existing methods
    extract_from_text()           # Modified to call relation extraction
    _build_entity_prompt()        # Existing
    _extract_entities()           # Existing (refactored from current code)
    _get_client()                 # Existing
    _call_claude_api_with_retry() # Existing (reused)
    _parse_extraction_response()  # Existing (entity parsing)
    _transform_to_final_entities() # Existing
    _mock_extract()               # Existing

    # New methods for relations
    _extract_relations()          # Main orchestrator
    _build_relation_prompt()      # Build from PROMPTS.md template
    _parse_relation_response()    # Parse Claude JSON
    _match_entity()               # Match string → entity ID
    _transform_to_final_relations() # Intermediate → final schema
    _apply_temporal_logic()       # Smart temporal fallbacks
```

---

## Data Models

### Intermediate Models

These match the PROMPTS.md JSON schema for Claude's response:

```python
class TemporalInfo(BaseModel):
    """Temporal information for a relation."""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    ongoing: bool = False
    date_precision: Literal["exact", "month", "year", "decade", "unknown"] = "unknown"

class ExtractedRelation(BaseModel):
    """Single relation extracted from document (intermediate format)."""
    relation_type: RelationType  # From schema.py
    source_entity: str  # Entity name as string (not ID yet)
    target_entity: str  # Entity name as string (not ID yet)
    confidence: float = Field(ge=0.0, le=1.0)
    temporal: Optional[TemporalInfo] = None
    evidence: str  # Quote from document
    notes: Optional[str] = None

class RelationExtractionResult(BaseModel):
    """Result from Claude relation extraction (intermediate format)."""
    relations: List[ExtractedRelation]
    extraction_notes: Optional[str] = None
```

### Constants

```python
TEMPORAL_RELATIONS = {
    RelationType.SOLD,
    RelationType.BOUGHT,
    RelationType.INHERITED,
    RelationType.CONFISCATED,
    RelationType.WITNESSED,
    RelationType.NOTARIZED
}

STATE_RELATIONS = {
    RelationType.OWNS,
    RelationType.LOCATED_IN,
    RelationType.EMPLOYED_BY,
    RelationType.RELATED_TO,
    RelationType.REGISTERED_IN
}
```

---

## Implementation Details

### Modified extract_from_text()

```python
def extract_from_text(
    self,
    text: str,
    ocr_confidence: float,
    document_id: str
) -> LLMExtractionResult:
    """Extract entities and relations from OCR text using Claude API."""

    if not self.api_key:
        return self._mock_extract(text, ocr_confidence, document_id)

    try:
        # STEP 1: Extract entities (existing)
        entities = self._extract_entities(text, ocr_confidence, document_id)

        # STEP 2: Extract relations (NEW)
        relations = []
        if len(entities) >= 2:
            logger.info(f"Extracting relations from {document_id} ({len(entities)} entities)...")
            relations = self._extract_relations(
                text=text,
                entities=entities,
                document_id=document_id,
                ocr_confidence=ocr_confidence
            )
        else:
            logger.info(f"Skipping relation extraction for {document_id} (only {len(entities)} entities)")

        # Calculate confidence, build reasoning, metadata
        # ...

        return LLMExtractionResult(
            entities=entities,
            relations=relations,  # Now populated!
            confidence=avg_confidence,
            reasoning=reasoning,
            metadata=metadata
        )

    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return self._mock_extract(text, ocr_confidence, document_id)
```

### Entity Matching Algorithm

```python
def _match_entity(
    self,
    entity_name: str,
    entities: List[BaseEntity]
) -> Optional[str]:
    """Match extracted entity name to entity ID."""

    # Step 1: Exact match on name
    for entity in entities:
        if entity.name == entity_name:
            return entity.id

    # Step 2: Exact match on alternate names
    for entity in entities:
        if entity_name in entity.alternate_names:
            return entity.id

    # Step 3: Fuzzy matching
    best_match = None
    best_similarity = 0.0

    for entity in entities:
        similarity = calculate_similarity(entity_name, entity.name)
        if similarity >= 0.85 and similarity > best_similarity:
            best_match = entity.id
            best_similarity = similarity

    if best_match:
        logger.info(f"Fuzzy matched '{entity_name}' (similarity: {best_similarity:.2f})")
        return best_match

    # Step 4: No match
    logger.warning(f"Could not match entity '{entity_name}' - relation skipped")
    return None
```

### Temporal Logic Application

```python
def _apply_temporal_logic(
    self,
    relation: ExtractedRelation,
    document_date: Optional[str],
    ocr_confidence: float
) -> TemporalInfo:
    """Apply smart temporal handling based on relation type."""

    temporal = relation.temporal or TemporalInfo()

    # TEMPORAL RELATIONS (events - need dates)
    if relation.relation_type in TEMPORAL_RELATIONS:
        if temporal.start_date:
            return temporal  # Claude found date
        elif document_date:
            # Fallback: infer from document
            return TemporalInfo(
                start_date=document_date,
                date_precision="year",
                notes="Date inferred from document date"
            )
        else:
            # Flag for review
            relation.needs_review = True
            relation.notes = (relation.notes or "") + " Missing temporal data."
            return TemporalInfo(date_precision="unknown")

    # STATE RELATIONS (conditions - dates optional)
    elif relation.relation_type in STATE_RELATIONS:
        if temporal.start_date:
            return temporal
        else:
            return TemporalInfo(
                date_precision="unknown",
                ongoing=True
            )

    return temporal
```

### Relation Transformation

```python
def _transform_to_final_relations(
    self,
    extraction: RelationExtractionResult,
    entities: List[BaseEntity],
    document_id: str,
    document_date: Optional[str],
    ocr_confidence: float
) -> List[Relation]:
    """Transform intermediate relations to final schema."""

    final_relations = []

    for rel in extraction.relations:
        # Match entities
        source_id = self._match_entity(rel.source_entity, entities)
        target_id = self._match_entity(rel.target_entity, entities)

        if not source_id or not target_id:
            logger.warning(f"Skipping relation - unmatched entities")
            continue

        # Apply temporal logic
        temporal = self._apply_temporal_logic(rel, document_date, ocr_confidence)

        # Create verification
        verification = Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=rel.confidence,
            verified_by=None,
            verified_at=None,
            notes=rel.notes
        )

        # Flag low confidence
        needs_review = rel.confidence < 0.70

        # Build final relation
        relation = Relation(
            id=f"{document_id}_rel_{uuid.uuid4().hex[:8]}",
            type=rel.relation_type,
            source_id=source_id,
            target_id=target_id,
            verification=verification,
            document_id=document_id,
            temporal=temporal,
            evidence=rel.evidence,
            notes=rel.notes,
            needs_review=needs_review
        )

        final_relations.append(relation)

    return final_relations
```

---

## Files to Modify

### 1. `farmer_factory/extract/llm.py` (Main Work)

**Add:**
- Intermediate models: `TemporalInfo`, `ExtractedRelation`, `RelationExtractionResult`
- Constants: `TEMPORAL_RELATIONS`, `STATE_RELATIONS`
- Methods:
  - `_extract_relations()`
  - `_build_relation_prompt()`
  - `_parse_relation_response()`
  - `_match_entity()`
  - `_transform_to_final_relations()`
  - `_apply_temporal_logic()`

**Modify:**
- `extract_from_text()` - Add relation extraction call after entities

**Estimated:** ~400-500 new lines

### 2. `farmer_factory/extract/pipeline.py` (Minor)

**Modify:**
- Add `extraction_flags: List[str]` to `ExtractionResult` dataclass
- Update logging to show relation statistics

**Estimated:** ~20 lines

### 3. `farmer_factory/cli.py` (New Command)

**Add:**
- `retry-relations` command to reprocess failed docs

**Estimated:** ~50 lines

### 4. `farmer_factory/structure/schema.py` (Verify)

**Check/Add:**
- Verify `Relation` model has `needs_review: bool` field
- May need to add if missing

**Estimated:** ~5 lines (if needed)

---

## Testing & Validation

### Manual Spot-Check

**Process:**
1. Run existing TEST-CERESA documents through pipeline
2. Review `graph_data.json` output:
   ```bash
   cat cases/TEST-CERESA/output/graph_data.json | jq '.edges'
   ```
3. Validate:
   - Relations make semantic sense
   - Entity matching is correct (valid source/target IDs)
   - Temporal dates align with document content
   - Confidence scores are reasonable

**Example checks:**
- "Mario Ceresa OWNS Central Santa Maria" - in document?
- "SOLD" relation has a date?
- Entity names matched correctly despite title variations?

### Confidence Monitoring

**Processing statistics to track:**

```python
{
    "relations_extracted": 127,
    "avg_relation_confidence": 0.78,
    "relation_type_breakdown": {
        "OWNS": 45,
        "SOLD": 12,
        "LOCATED_IN": 38,
        "INHERITED": 8,
        "CONFISCATED": 24
    },
    "low_confidence_relations": 8,  # <0.70
    "flagged_for_review": 8,
    "entity_matching_failures": 2,
    "incomplete_documents": 0
}
```

**Red flags:**
- Avg confidence <0.60 (prompt issue)
- Many entity matching failures (names too varied)
- High incomplete document rate (API reliability)

---

## Retry Mechanism

### CLI Command

```bash
python cli.py retry-relations <case_id>
```

### Implementation

```python
@cli.command()
@click.argument('case_id')
def retry_relations(case_id: str):
    """Retry relation extraction for documents that failed."""

    # 1. Load case graph data
    # 2. Find documents with "RELATION_EXTRACTION_FAILED" flag
    # 3. For each failed document:
    #    - Load existing entities from graph
    #    - Load OCR text from extractions/
    #    - Re-run _extract_relations() only
    #    - Update graph with new relations
    # 4. Save updated graph
    # 5. Report results

    click.echo(f"✓ Retried {failed_count} documents")
    click.echo(f"  {success_count} succeeded, {still_failed} still failed")
```

### Usage Flow

```bash
# Initial processing
./venv/bin/python3 farmer_factory/cli.py process TEST-CERESA

# Console output:
# "Processing complete: 20 documents"
# "  ✓ 16 fully processed"
# "  ⚠️  4 incomplete (relation extraction failed)"

# Retry failures
./venv/bin/python3 farmer_factory/cli.py retry-relations TEST-CERESA

# Console output:
# "Retrying 4 documents..."
# "✓ Retried 4 documents"
# "  3 succeeded, 1 still failed"
```

---

## Error Handling

### Relation Extraction Failure

**Scenario:** Claude API call fails after all retries during relation extraction.

**Handling:**
1. Log error with full context
2. Return empty `relations=[]`
3. Document flagged: `"RELATION_EXTRACTION_FAILED"`
4. Entities still saved (work not lost)
5. Processing continues to next document

**User visibility:**
- Console warning: `"⚠️  Document X INCOMPLETE - relation extraction failed"`
- Summary stats show incomplete count
- Retry command available

### Entity Matching Failure

**Scenario:** Claude returns relation with entity name we can't match to any extracted entity.

**Handling:**
1. Try exact match (name, alternate names)
2. Try fuzzy match ≥0.85
3. If no match: log warning, skip relation
4. Continue processing other relations

**Logging:**
```
WARNING: Could not match entity 'Don Mario C.' - relation skipped
  Available entities: ['Mario Ceresa', 'Central Santa Maria', ...]
```

### Low Confidence Relations

**Scenario:** Relation extracted with confidence <0.70.

**Handling:**
1. Store relation (don't discard)
2. Set `needs_review = True`
3. Add note: `"Low confidence (0.68) - requires analyst review"`
4. Include in stats: `low_confidence_relations: 8`

**Frontend impact:**
- Default view may filter these out
- Analyst view shows them with warning badge
- Promotes to TIER_2_ANALYST when analyst verifies

---

## Success Criteria

### Functional Requirements

- ✅ Extracts all 11 relation types from PROMPTS.md
- ✅ Matches entity names to IDs with ≥90% accuracy on test docs
- ✅ Applies temporal logic correctly (temporal vs state relations)
- ✅ Stores low-confidence relations with review flags
- ✅ Gracefully handles failures (returns partial results)
- ✅ Retry command successfully reprocesses failed docs

### Quality Requirements

- ✅ Manual validation shows relations make semantic sense
- ✅ Avg relation confidence ≥0.70 on test documents
- ✅ Entity matching failures <10% of relations
- ✅ No crashes on malformed API responses

### Performance Requirements

- ✅ Relation extraction adds <30s per document (Haiku is fast)
- ✅ Batch processing completes successfully (no hanging)
- ✅ API costs stay reasonable (~$0.01 per document)

---

## Future Enhancements (Post-MVP1)

### Golden Dataset Validation

Build annotated dataset (10-20 docs) with ground truth relations for precision/recall metrics.

### Relation Confidence Tuning

Analyze relation confidence distribution and adjust thresholds if needed.

### Advanced Entity Matching

- Context-aware matching (use relation evidence text)
- Disambiguation for common names ("José Fernández #1" vs "#2")
- Machine learning for entity resolution

### Relation Deduplication

Merge duplicate relations from multiple documents (e.g., same OWNS relation mentioned in 3 docs → single relation with 3 sources).

### Bidirectional Relations

Automatically create inverse relations (SOLD implies BOUGHT from other perspective).

---

## References

- **PROMPTS.md** - Prompt 2: Relation Extraction (lines 216-338)
- **SCHEMA.md** - Relation model specification
- **ROADMAP.md** - Phase 4: Entity & Relation Extraction
- **ARCHITECTURE.md** - Air Gap architecture, legal constraints

---

*This design enables complete knowledge graph construction by connecting entities through extracted relationships, providing the foundation for ownership chain analysis and forensic investigation.*
