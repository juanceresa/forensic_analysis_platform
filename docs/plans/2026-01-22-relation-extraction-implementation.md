# Relation Extraction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement two-pass relation extraction from OCR text using Claude API to build complete knowledge graph connections.

**Architecture:** Extend existing `LLMExtractionService` with relation extraction methods. Extract entities first, then make second Claude API call with entities + OCR text to extract 11 relation types. Smart entity matching connects relation strings to entity IDs. Store all relations with confidence-based review flags.

**Tech Stack:** Python 3.10+, Anthropic Claude API (Haiku), Pydantic validation, difflib for fuzzy matching

---

## Task 1: Add Intermediate Relation Models

**Files:**
- Modify: `farmer_factory/extract/llm.py:50-60`

**Step 1: Add TemporalInfo model after EntityExtractionResult**

Add after line 49 (after `EntityExtractionResult` class):

```python
class TemporalInfo(BaseModel):
    """Temporal information for a relation."""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    ongoing: bool = False
    date_precision: Literal["exact", "month", "year", "decade", "unknown"] = "unknown"
```

**Step 2: Import Literal from typing**

Modify line 4:

```python
from typing import List, Dict, Any, Optional, Literal
```

**Step 3: Add ExtractedRelation model**

Add after `TemporalInfo`:

```python
class ExtractedRelation(BaseModel):
    """Single relation extracted from document (intermediate format)."""
    relation_type: str  # Will be validated against RelationType enum
    source_entity: str  # Entity name as string (not ID yet)
    target_entity: str  # Entity name as string (not ID yet)
    confidence: float = Field(ge=0.0, le=1.0)
    temporal: Optional[TemporalInfo] = None
    evidence: str  # Quote from document
    notes: Optional[str] = None
```

**Step 4: Add RelationExtractionResult model**

Add after `ExtractedRelation`:

```python
class RelationExtractionResult(BaseModel):
    """Result from Claude relation extraction (intermediate format)."""
    relations: List[ExtractedRelation]
    extraction_notes: Optional[str] = None
```

**Step 5: Add relation type constants**

Add after the intermediate models (around line 85):

```python
# ============================================================================
# Relation Type Constants
# ============================================================================

# Temporal relations (events - need dates)
TEMPORAL_RELATIONS = {
    "SOLD",
    "BOUGHT",
    "INHERITED",
    "CONFISCATED",
    "WITNESSED",
    "NOTARIZED"
}

# State relations (conditions - dates optional)
STATE_RELATIONS = {
    "OWNS",
    "LOCATED_IN",
    "EMPLOYED_BY",
    "RELATED_TO",
    "REGISTERED_IN"
}
```

**Step 6: Verify imports work**

Run: `python3 -c "from farmer_factory.extract.llm import TemporalInfo, ExtractedRelation, RelationExtractionResult; print('Models imported successfully')"`

Expected: "Models imported successfully"

**Step 7: Commit**

```bash
git add farmer_factory/extract/llm.py
git commit -m "feat: add intermediate relation extraction models"
```

---

## Task 2: Implement Relation Prompt Builder

**Files:**
- Modify: `farmer_factory/extract/llm.py` (add method after `_build_entity_prompt`)

**Step 1: Add _build_relation_prompt method**

Add after the `_build_entity_prompt` method (around line 235):

```python
def _build_relation_prompt(
    self,
    text: str,
    entities: List[BaseEntity],
    document_id: str,
    document_type: str = "unknown"
) -> str:
    """
    Build relation extraction prompt using PROMPTS.md template.

    Args:
        text: OCR-extracted text
        entities: Previously extracted entities
        document_id: Document identifier
        document_type: Type of document

    Returns:
        Formatted prompt string
    """
    # Build entities JSON for prompt
    entities_list = []
    for entity in entities:
        entities_list.append({
            "id": entity.id,
            "type": entity.entity_type.value,
            "name": getattr(entity, 'name', str(entity.id))
        })

    entities_json = json.dumps(entities_list, indent=2, ensure_ascii=False)

    prompt = f"""You are a forensic document analyst extracting relationships from historical Cuban property documents. Extract factual relationships only — never make legal conclusions about claim validity.

Analyze the OCR text and the previously extracted entities to identify relationships between them.

For each relationship, provide:
1. relation_type: One of the defined types below
2. source_entity: The entity at the start of the relationship
3. target_entity: The entity at the end of the relationship
4. confidence: 0.0-1.0 based on textual evidence
5. temporal: Date or date range if applicable
6. evidence: Quote from document supporting this relationship
7. notes: Observations, caveats, or ambiguities

RELATION TYPES:
- OWNS: Person/Organization owns Property (current or historical)
- SOLD: Person sold Property to another Person (transaction)
- BOUGHT: Person bought Property from another Person
- INHERITED: Person inherited Property (from another Person)
- CONFISCATED: Government/Organization confiscated Property
- WITNESSED: Person witnessed a transaction or legal act
- NOTARIZED: Notary certified a document
- REGISTERED_IN: Property registered in a Registry
- LOCATED_IN: Property/Person located in a Location
- EMPLOYED_BY: Person employed by Organization
- RELATED_TO: Family relationship between Persons

TEMPORAL INFORMATION:
- Extract start_date and end_date where applicable
- For ongoing relationships, set ongoing: true
- Use date_precision: "exact", "month", "year", "decade", or "unknown"

CRITICAL: Only extract relationships explicitly stated or directly implied by the document. Do not infer relationships that require outside knowledge.

DOCUMENT METADATA:
Document ID: {document_id}
Document Type: {document_type}

EXTRACTED ENTITIES:
{entities_json}

OCR TEXT:
{text}

Respond with a JSON object:
{{
  "relations": [
    {{
      "relation_type": "OWNS",
      "source_entity": "Mario Ceresa",
      "target_entity": "Central Santa Maria",
      "confidence": 0.88,
      "temporal": {{
        "start_date": "1945-01-01",
        "end_date": null,
        "ongoing": true,
        "date_precision": "year"
      }},
      "evidence": "...Don Mario Ceresa, propietario del Central Santa Maria...",
      "notes": "Ownership stated but acquisition date not specified in this document"
    }}
  ],
  "extraction_notes": "Document is a notarial certification of ownership."
}}"""
    return prompt
```

**Step 2: Test prompt builder manually**

Create test script `test_relation_prompt.py`:

```python
from farmer_factory.extract.llm import LLMExtractionService
from farmer_factory.structure.schema import Person, EntityType, Verification, VerificationTier

# Create test entities
person = Person(
    id="test_person_1",
    entity_type=EntityType.PERSON,
    name="Mario Ceresa",
    verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.95),
    extracted_from="test_doc"
)

service = LLMExtractionService()
prompt = service._build_relation_prompt(
    text="Mario Ceresa es propietario del Central Santa Maria",
    entities=[person],
    document_id="test_doc"
)

print(prompt[:200])
assert "OWNS" in prompt
assert "Mario Ceresa" in prompt
print("✓ Prompt builder working")
```

Run: `python3 test_relation_prompt.py`

Expected: Prints prompt preview and "✓ Prompt builder working"

**Step 3: Remove test script**

Run: `rm test_relation_prompt.py`

**Step 4: Commit**

```bash
git add farmer_factory/extract/llm.py
git commit -m "feat: add relation extraction prompt builder"
```

---

## Task 3: Implement Entity Matching

**Files:**
- Modify: `farmer_factory/extract/llm.py` (add method after `_build_relation_prompt`)

**Step 1: Import difflib for fuzzy matching**

Add to imports at top of file (around line 10):

```python
from difflib import SequenceMatcher
```

**Step 2: Add _match_entity method**

Add after `_build_relation_prompt`:

```python
def _match_entity(
    self,
    entity_name: str,
    entities: List[BaseEntity]
) -> Optional[str]:
    """
    Match extracted entity name to entity ID using hybrid strategy.

    Strategy:
    1. Exact match on entity.name
    2. Exact match on entity.alternate_names[]
    3. Fuzzy match with threshold ≥0.85
    4. Return None if no match

    Args:
        entity_name: Entity name from Claude (e.g., "Don Mario Ceresa")
        entities: List of extracted entities to search

    Returns:
        Entity ID if match found, None otherwise
    """
    # Step 1: Exact match on name
    for entity in entities:
        if hasattr(entity, 'name') and entity.name == entity_name:
            return entity.id

    # Step 2: Exact match on alternate names
    for entity in entities:
        if hasattr(entity, 'alternate_names'):
            if entity_name in entity.alternate_names:
                return entity.id

    # Step 3: Fuzzy matching with SequenceMatcher
    best_match_id = None
    best_similarity = 0.0

    for entity in entities:
        if hasattr(entity, 'name'):
            # Calculate similarity
            similarity = SequenceMatcher(None, entity_name.lower(), entity.name.lower()).ratio()

            if similarity >= 0.85 and similarity > best_similarity:
                best_match_id = entity.id
                best_similarity = similarity

    if best_match_id:
        logger.info(f"Fuzzy matched '{entity_name}' to entity (similarity: {best_similarity:.2f})")
        return best_match_id

    # Step 4: No match found
    logger.warning(f"Could not match entity '{entity_name}' - relation will be skipped")
    return None
```

**Step 3: Test entity matching**

Create test script `test_entity_matching.py`:

```python
from farmer_factory.extract.llm import LLMExtractionService
from farmer_factory.structure.schema import Person, EntityType, Verification, VerificationTier

# Create test entities
person1 = Person(
    id="person_1",
    entity_type=EntityType.PERSON,
    name="Mario Ceresa",
    alternate_names=["Don Mario Ceresa"],
    verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.95),
    extracted_from="test"
)

person2 = Person(
    id="person_2",
    entity_type=EntityType.PERSON,
    name="María López",
    verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.95),
    extracted_from="test"
)

entities = [person1, person2]
service = LLMExtractionService()

# Test exact match
assert service._match_entity("Mario Ceresa", entities) == "person_1"
print("✓ Exact match works")

# Test alternate name match
assert service._match_entity("Don Mario Ceresa", entities) == "person_1"
print("✓ Alternate name match works")

# Test fuzzy match
assert service._match_entity("Mario C.", entities) == "person_1"
print("✓ Fuzzy match works")

# Test no match
assert service._match_entity("José Fernández", entities) is None
print("✓ No match returns None")

print("✓ All entity matching tests passed")
```

Run: `python3 test_entity_matching.py`

Expected: All checks pass

**Step 4: Remove test script**

Run: `rm test_entity_matching.py`

**Step 5: Commit**

```bash
git add farmer_factory/extract/llm.py
git commit -m "feat: add smart entity matching for relations"
```

---

## Task 4: Implement Temporal Logic

**Files:**
- Modify: `farmer_factory/extract/llm.py` (add method after `_match_entity`)

**Step 1: Add _apply_temporal_logic method**

Add after `_match_entity`:

```python
def _apply_temporal_logic(
    self,
    relation: ExtractedRelation,
    document_date: Optional[str]
) -> TemporalInfo:
    """
    Apply smart temporal handling based on relation type.

    Args:
        relation: Extracted relation with temporal info
        document_date: Document date from entity extraction (fallback)

    Returns:
        Enriched TemporalInfo with fallbacks applied
    """
    temporal = relation.temporal or TemporalInfo()

    # TEMPORAL RELATIONS (events - need dates)
    if relation.relation_type in TEMPORAL_RELATIONS:
        if temporal.start_date:
            # Claude found a date - use it
            return temporal

        elif document_date:
            # Fallback: infer from document date
            logger.info(f"Using document date as fallback for {relation.relation_type} relation")
            return TemporalInfo(
                start_date=document_date,
                date_precision="year",
                notes="Date inferred from document date"
            )

        else:
            # Last resort: mark unknown and will be flagged for review
            logger.warning(f"No temporal data for {relation.relation_type} relation")
            return TemporalInfo(
                date_precision="unknown",
                notes="Missing temporal data for event relation"
            )

    # STATE RELATIONS (conditions - dates optional)
    elif relation.relation_type in STATE_RELATIONS:
        if temporal.start_date:
            return temporal
        else:
            # Dates are nice-to-have, not required
            return TemporalInfo(
                date_precision="unknown",
                ongoing=True
            )

    # Unknown relation type - return as-is
    return temporal
```

**Step 2: Test temporal logic**

Create test script `test_temporal_logic.py`:

```python
from farmer_factory.extract.llm import LLMExtractionService, ExtractedRelation, TemporalInfo

service = LLMExtractionService()

# Test temporal relation with date
rel1 = ExtractedRelation(
    relation_type="SOLD",
    source_entity="Mario",
    target_entity="Property",
    confidence=0.9,
    temporal=TemporalInfo(start_date="1958-03-15", date_precision="exact"),
    evidence="test"
)
result1 = service._apply_temporal_logic(rel1, document_date=None)
assert result1.start_date == "1958-03-15"
print("✓ Temporal relation with date preserved")

# Test temporal relation without date (fallback to doc date)
rel2 = ExtractedRelation(
    relation_type="SOLD",
    source_entity="Mario",
    target_entity="Property",
    confidence=0.9,
    evidence="test"
)
result2 = service._apply_temporal_logic(rel2, document_date="1960-01-01")
assert result2.start_date == "1960-01-01"
assert result2.date_precision == "year"
print("✓ Temporal relation fallback to document date works")

# Test state relation without date
rel3 = ExtractedRelation(
    relation_type="OWNS",
    source_entity="Mario",
    target_entity="Property",
    confidence=0.9,
    evidence="test"
)
result3 = service._apply_temporal_logic(rel3, document_date=None)
assert result3.date_precision == "unknown"
assert result3.ongoing == True
print("✓ State relation without date works")

print("✓ All temporal logic tests passed")
```

Run: `python3 test_temporal_logic.py`

Expected: All tests pass

**Step 3: Remove test script**

Run: `rm test_temporal_logic.py`

**Step 4: Commit**

```bash
git add farmer_factory/extract/llm.py
git commit -m "feat: add smart temporal logic for relations"
```

---

## Task 5: Implement Relation Transformation

**Files:**
- Modify: `farmer_factory/extract/llm.py` (add method after `_apply_temporal_logic`)

**Step 1: Add _transform_to_final_relations method**

Add after `_apply_temporal_logic`:

```python
def _transform_to_final_relations(
    self,
    extraction: RelationExtractionResult,
    entities: List[BaseEntity],
    document_id: str,
    document_date: Optional[str]
) -> List[Relation]:
    """
    Transform intermediate relations to final schema.

    Args:
        extraction: Intermediate extraction result from Claude
        entities: Previously extracted entities
        document_id: Document identifier
        document_date: Document date for temporal fallback

    Returns:
        List of final Relation objects
    """
    from farmer_factory.structure.schema import Verification, VerificationTier

    final_relations = []

    for rel in extraction.relations:
        # Match source and target entities
        source_id = self._match_entity(rel.source_entity, entities)
        target_id = self._match_entity(rel.target_entity, entities)

        if not source_id or not target_id:
            logger.warning(
                f"Skipping relation {rel.relation_type} - "
                f"unmatched entities: {rel.source_entity} -> {rel.target_entity}"
            )
            continue

        # Apply temporal logic
        temporal_info = self._apply_temporal_logic(rel, document_date)

        # Create verification
        verification = Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=rel.confidence,
            verified_by=None,
            verified_at=None,
            notes=rel.notes
        )

        # Determine if needs review (low confidence or missing temporal data)
        needs_review = (
            rel.confidence < 0.70 or
            (rel.relation_type in TEMPORAL_RELATIONS and temporal_info.date_precision == "unknown")
        )

        # Build notes with review flag if needed
        final_notes = rel.notes or ""
        if needs_review:
            if rel.confidence < 0.70:
                final_notes += f" Low confidence ({rel.confidence:.2f}) - requires analyst review."
            if rel.relation_type in TEMPORAL_RELATIONS and temporal_info.date_precision == "unknown":
                final_notes += " Missing temporal data for event relation."

        # Create final relation
        relation = Relation(
            id=f"{document_id}_rel_{uuid.uuid4().hex[:8]}",
            type=rel.relation_type,
            source_id=source_id,
            target_id=target_id,
            verification=verification,
            document_id=document_id,
            evidence=rel.evidence,
            notes=final_notes.strip(),
            # Temporal fields (if supported by Relation model)
            date=temporal_info.start_date,
        )

        final_relations.append(relation)

    logger.info(
        f"Transformed {len(extraction.relations)} intermediate relations → "
        f"{len(final_relations)} final relations "
        f"({len(extraction.relations) - len(final_relations)} skipped due to entity matching failures)"
    )

    return final_relations
```

**Step 2: Check Relation model supports needed fields**

Run: `python3 -c "from farmer_factory.structure.schema import Relation; r = Relation(id='test', type='OWNS', source_id='a', target_id='b', verification=None, document_id='d', evidence='e'); print('✓ Relation model OK')"`

Expected: May show error if `evidence` or `document_id` not in model

**Step 3: Update Relation model if needed**

If previous step failed, modify `farmer_factory/structure/schema.py`:

Find the `Relation` class (around line 170) and ensure it has:

```python
class Relation(BaseModel):
    """Relation between entities in the knowledge graph."""
    id: str
    type: str  # Will store RelationType values as strings
    source_id: str
    target_id: str
    verification: Verification

    # Context fields
    document_id: str
    evidence: Optional[str] = None
    date: Optional[str] = None
    amount: Optional[float] = None
    notes: Optional[str] = None
```

**Step 4: Commit schema changes if modified**

```bash
git add farmer_factory/structure/schema.py
git commit -m "feat: add evidence and document_id fields to Relation model"
```

**Step 5: Test transformation**

Create test script `test_transform_relations.py`:

```python
from farmer_factory.extract.llm import (
    LLMExtractionService, RelationExtractionResult,
    ExtractedRelation, TemporalInfo
)
from farmer_factory.structure.schema import Person, EntityType, Verification, VerificationTier

# Create entities
person = Person(
    id="person_1",
    entity_type=EntityType.PERSON,
    name="Mario Ceresa",
    verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.95),
    extracted_from="test"
)

# Create intermediate relation
intermediate = RelationExtractionResult(
    relations=[
        ExtractedRelation(
            relation_type="OWNS",
            source_entity="Mario Ceresa",
            target_entity="Central Santa Maria",  # Won't match (no property entity)
            confidence=0.88,
            evidence="Test evidence",
            temporal=TemporalInfo(start_date="1945-01-01", date_precision="year")
        )
    ]
)

service = LLMExtractionService()
final_relations = service._transform_to_final_relations(
    extraction=intermediate,
    entities=[person],
    document_id="test_doc",
    document_date="1960-01-01"
)

# Should skip because target entity doesn't match
assert len(final_relations) == 0
print("✓ Transformation correctly skips unmatched entities")

print("✓ Relation transformation test passed")
```

Run: `python3 test_transform_relations.py`

Expected: Test passes

**Step 6: Remove test script**

Run: `rm test_transform_relations.py`

**Step 7: Commit**

```bash
git add farmer_factory/extract/llm.py
git commit -m "feat: add relation transformation to final schema"
```

---

## Task 6: Implement Relation Extraction Response Parser

**Files:**
- Modify: `farmer_factory/extract/llm.py` (add method after `_transform_to_final_relations`)

**Step 1: Add _parse_relation_response method**

Add after `_transform_to_final_relations`:

```python
def _parse_relation_response(self, response_text: str) -> RelationExtractionResult:
    """
    Parse Claude response into RelationExtractionResult.

    Handles markdown code blocks and validates JSON schema.

    Args:
        response_text: Raw response from Claude

    Returns:
        Validated RelationExtractionResult

    Raises:
        ValueError: If JSON parsing or validation fails
    """
    try:
        # Extract JSON from markdown code blocks if present
        cleaned_text = response_text.strip()

        # Check for markdown JSON code blocks
        if "```json" in cleaned_text:
            start = cleaned_text.find("```json") + 7
            end = cleaned_text.find("```", start)
            if end > start:
                cleaned_text = cleaned_text[start:end].strip()
        elif "```" in cleaned_text:
            # Generic code block
            start = cleaned_text.find("```") + 3
            end = cleaned_text.find("```", start)
            if end > start:
                cleaned_text = cleaned_text[start:end].strip()

        # Parse JSON
        data = json.loads(cleaned_text)

        # Validate with Pydantic model
        result = RelationExtractionResult(**data)
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from Claude relation response: {str(e)}")
        logger.debug(f"Response text: {response_text[:500]}...")
        raise ValueError(f"Invalid JSON in Claude response: {str(e)}")

    except Exception as e:
        logger.error(f"Failed to validate relation extraction result: {str(e)}")
        logger.debug(f"Parsed data: {data if 'data' in locals() else 'N/A'}")
        raise ValueError(f"Invalid relation extraction result schema: {str(e)}")
```

**Step 2: Test parser with sample JSON**

Create test script `test_relation_parser.py`:

```python
from farmer_factory.extract.llm import LLMExtractionService

service = LLMExtractionService()

# Test valid JSON
valid_json = '''
{
  "relations": [
    {
      "relation_type": "OWNS",
      "source_entity": "Mario Ceresa",
      "target_entity": "Central Santa Maria",
      "confidence": 0.88,
      "temporal": {
        "start_date": "1945-01-01",
        "date_precision": "year",
        "ongoing": true
      },
      "evidence": "Test evidence",
      "notes": "Test notes"
    }
  ],
  "extraction_notes": "Test extraction"
}
'''

result = service._parse_relation_response(valid_json)
assert len(result.relations) == 1
assert result.relations[0].relation_type == "OWNS"
print("✓ Parser handles valid JSON")

# Test JSON in markdown code block
markdown_json = '''```json
{
  "relations": [],
  "extraction_notes": "No relations found"
}
```'''

result2 = service._parse_relation_response(markdown_json)
assert len(result2.relations) == 0
print("✓ Parser handles markdown code blocks")

print("✓ Relation parser tests passed")
```

Run: `python3 test_relation_parser.py`

Expected: All tests pass

**Step 3: Remove test script**

Run: `rm test_relation_parser.py`

**Step 4: Commit**

```bash
git add farmer_factory/extract/llm.py
git commit -m "feat: add relation response parser with markdown handling"
```

---

## Task 7: Implement Main Relation Extraction Method

**Files:**
- Modify: `farmer_factory/extract/llm.py` (add method after `_parse_relation_response`)

**Step 1: Add _extract_relations method**

Add after `_parse_relation_response`:

```python
def _extract_relations(
    self,
    text: str,
    entities: List[BaseEntity],
    document_id: str,
    ocr_confidence: float
) -> List[Relation]:
    """
    Extract relations from OCR text using Claude API.

    Args:
        text: OCR-extracted text
        entities: Previously extracted entities
        document_id: Document identifier
        ocr_confidence: OCR confidence for logging

    Returns:
        List of Relation objects (empty if extraction fails)
    """
    from farmer_factory.config.settings import settings

    try:
        start_time = time.time()

        # Build prompt
        prompt = self._build_relation_prompt(
            text=text,
            entities=entities,
            document_id=document_id
        )

        # Call Claude API with retry logic
        logger.info(f"Calling Claude API for relation extraction from {document_id}...")
        response_text = self._call_claude_api_with_retry(
            prompt=prompt,
            max_retries=settings.max_retries,
            retry_delay=settings.retry_delay,
            api_timeout=settings.api_timeout
        )

        # Parse response
        extraction = self._parse_relation_response(response_text)

        # Get document date from metadata (if available)
        # This would come from entity extraction phase
        document_date = None  # TODO: pass this from entity extraction

        # Transform to final relations
        relations = self._transform_to_final_relations(
            extraction=extraction,
            entities=entities,
            document_id=document_id,
            document_date=document_date
        )

        processing_time = time.time() - start_time
        logger.info(
            f"Relation extraction completed in {processing_time:.2f}s - "
            f"extracted {len(relations)} relations"
        )

        return relations

    except Exception as e:
        logger.error(f"Relation extraction failed for {document_id}: {str(e)}")
        logger.debug(f"Error details: {type(e).__name__}: {str(e)}")
        # Return empty list - document will be flagged as incomplete
        return []
```

**Step 2: Verify method is callable**

Run: `python3 -c "from farmer_factory.extract.llm import LLMExtractionService; service = LLMExtractionService(); print('✓ _extract_relations method exists')"`

Expected: "✓ _extract_relations method exists"

**Step 3: Commit**

```bash
git add farmer_factory/extract/llm.py
git commit -m "feat: add main relation extraction orchestrator method"
```

---

## Task 8: Integrate Relation Extraction into extract_from_text

**Files:**
- Modify: `farmer_factory/extract/llm.py:455-560` (modify `extract_from_text` method)

**Step 1: Refactor entity extraction into separate method**

Find the `extract_from_text` method and create new `_extract_entities` method just before it:

```python
def _extract_entities(
    self,
    text: str,
    ocr_confidence: float,
    document_id: str
) -> tuple[List[BaseEntity], Optional[str]]:
    """
    Extract entities from OCR text (first pass).

    Returns:
        Tuple of (entities list, document_date)
    """
    start_time = time.time()

    # Build prompt
    prompt = self._build_entity_prompt(
        text=text,
        document_id=document_id,
        ocr_quality=ocr_confidence
    )

    # Call Claude API
    logger.info(f"Calling Claude API for entity extraction from {document_id}...")
    response_text = self._call_claude_api_with_retry(
        prompt=prompt,
        max_retries=self.settings.max_retries,
        retry_delay=self.settings.retry_delay,
        api_timeout=self.settings.api_timeout
    )

    # Parse response
    extraction = self._parse_extraction_response(response_text)

    # Transform to final entities
    entities = self._transform_to_final_entities(
        extraction=extraction,
        document_id=document_id,
        ocr_confidence=ocr_confidence
    )

    return entities, extraction.document_date
```

**Step 2: Modify extract_from_text to call both extraction methods**

Replace the entity extraction logic in `extract_from_text` (keep the API key check and try/except structure):

```python
def extract_from_text(
    self,
    text: str,
    ocr_confidence: float,
    document_id: str
) -> LLMExtractionResult:
    """
    Extract entities and relations from OCR text using Claude API.

    Falls back to mock extraction if:
    - API key not configured
    - API call fails after all retries

    Args:
        text: OCR-extracted text from document
        ocr_confidence: Confidence score from OCR (0.0-1.0)
        document_id: Document identifier for entity tracking

    Returns:
        LLMExtractionResult with extracted entities and relations
    """
    from farmer_factory.config.settings import settings

    # Check if API key is configured
    if not self.api_key:
        logger.warning(
            f"⚠️  No Anthropic API key configured. "
            f"Using mock extraction for {document_id}. "
            "Set ANTHROPIC_API_KEY environment variable to use real Claude API."
        )
        return self._mock_extract(text, ocr_confidence, document_id)

    # Try real Claude API extraction
    try:
        # STEP 1: Extract entities (first pass)
        entities, document_date = self._extract_entities(text, ocr_confidence, document_id)

        # STEP 2: Extract relations (second pass - only if we have 2+ entities)
        relations = []
        if len(entities) >= 2:
            logger.info(
                f"Extracting relations from {document_id} ({len(entities)} entities found)..."
            )
            relations = self._extract_relations(
                text=text,
                entities=entities,
                document_id=document_id,
                ocr_confidence=ocr_confidence
            )
        else:
            logger.info(
                f"Skipping relation extraction for {document_id} (only {len(entities)} entities)"
            )

        # Calculate overall confidence
        if entities:
            avg_entity_confidence = sum(e.verification.confidence for e in entities) / len(entities)
        else:
            avg_entity_confidence = ocr_confidence

        if relations:
            avg_relation_confidence = sum(r.verification.confidence for r in relations) / len(relations)
            avg_confidence = (avg_entity_confidence + avg_relation_confidence) / 2
        else:
            avg_confidence = avg_entity_confidence

        # Build reasoning
        reasoning = f"""
Entity and relation extraction completed using Claude API.

Extracted {len(entities)} entities and {len(relations)} relations from document.
- {len([e for e in entities if e.entity_type.value == 'PERSON'])} Person(s)
- {len([e for e in entities if e.entity_type.value == 'PROPERTY'])} Property/Properties
- {len([e for e in entities if e.entity_type.value == 'ORGANIZATION'])} Organization(s)
- {len([e for e in entities if e.entity_type.value == 'LOCATION'])} Location(s)

OCR confidence: {ocr_confidence:.2f}
Average entity confidence: {avg_entity_confidence:.2f}
Average relation confidence: {avg_relation_confidence if relations else 'N/A'}

All entities and relations tagged as TIER_3_AI (unverified AI extraction).
        """.strip()

        # Build metadata
        metadata = {
            "model": settings.claude_model,
            "api_version": "anthropic_v1",
            "ocr_confidence": ocr_confidence,
            "entity_count": len(entities),
            "relation_count": len(relations),
            "relation_extraction_status": (
                "COMPLETE" if relations or len(entities) < 2 else "FAILED"
            ),
            "document_date": document_date,
            "text_length": len(text)
        }

        return LLMExtractionResult(
            entities=entities,
            relations=relations,
            confidence=avg_confidence,
            reasoning=reasoning,
            metadata=metadata
        )

    except Exception as e:
        logger.error(f"Claude API extraction failed: {str(e)}")
        logger.warning(f"Falling back to mock extraction for {document_id}")
        return self._mock_extract(text, ocr_confidence, document_id)
```

**Step 3: Fix settings reference**

The method needs access to settings. Add at the top of `_extract_entities`:

```python
from farmer_factory.config.settings import settings
```

**Step 4: Test the integration compiles**

Run: `python3 -c "from farmer_factory.extract.llm import LLMExtractionService; service = LLMExtractionService(); print('✓ extract_from_text modified successfully')"`

Expected: No errors

**Step 5: Commit**

```bash
git add farmer_factory/extract/llm.py
git commit -m "feat: integrate relation extraction into extract_from_text

Two-pass extraction: entities first, then relations if 2+ entities found.
Includes fallback handling and comprehensive metadata tracking."
```

---

## Task 9: Add Extraction Flags to Pipeline

**Files:**
- Modify: `farmer_factory/extract/pipeline.py:14-23`

**Step 1: Add extraction_flags to ExtractionResult dataclass**

Modify the `ExtractionResult` dataclass (around line 14):

```python
from dataclasses import dataclass, field

@dataclass
class ExtractionResult:
    """Complete extraction result for a document page."""
    entities: List[BaseEntity]
    relations: List[Relation]
    ocr_result: Optional[OCRResult]
    confidence_scores: Dict[str, float]
    path: DocumentPath
    processing_metadata: Dict[str, Any]
    extraction_flags: List[str] = field(default_factory=list)  # NEW
```

**Step 2: Update typed path to check for relation extraction failures**

In `_extract_typed_path` method (around line 73), after creating the `ExtractionResult`, add:

```python
# Check for relation extraction failure
relation_status = llm_result.metadata.get("relation_extraction_status", "UNKNOWN")
if relation_status == "FAILED":
    extraction_flags = ["RELATION_EXTRACTION_FAILED"]
    logger.warning(
        f"⚠️  {document_id} INCOMPLETE - has entities but relation extraction failed"
    )
else:
    extraction_flags = []

return ExtractionResult(
    entities=validated_entities,
    relations=validated_relations,
    ocr_result=ocr_result,
    confidence_scores=confidence_scores,
    path=DocumentPath.TYPED,
    processing_metadata=processing_metadata,
    extraction_flags=extraction_flags  # NEW
)
```

**Step 3: Add relation stats to logging**

In the same method, update the processing metadata to include relation info:

```python
processing_metadata = {
    "path": "TYPED",
    "ocr_metadata": ocr_result.metadata,
    "llm_metadata": llm_result.metadata,
    "preprocessing_metadata": processed_page.metadata,
    "relation_count": len(validated_relations),  # NEW
    "relation_extraction_status": llm_result.metadata.get("relation_extraction_status")  # NEW
}
```

**Step 4: Test pipeline still works**

Run: `python3 -c "from farmer_factory.extract.pipeline import ExtractionPipeline; print('✓ Pipeline updated successfully')"`

Expected: No errors

**Step 5: Commit**

```bash
git add farmer_factory/extract/pipeline.py
git commit -m "feat: add relation extraction status tracking to pipeline"
```

---

## Task 10: Test End-to-End with Real Document

**Files:**
- Test with existing CLI

**Step 1: Process test document**

Run:
```bash
./venv/bin/python3 farmer_factory/cli.py process TEST-CERESA \
  --file "1 4 1961 Mario Ceresa Money Transfer.pdf" \
  --force-typed --verbose
```

Expected output should show:
- "Extracting relations from..." message
- Relation count in output
- No crashes

**Step 2: Inspect output JSON**

Run:
```bash
cat cases/TEST-CERESA/output/graph_data.json | jq '.edges | length'
```

Expected: Should show number > 0 if relations were extracted (depends on document content and if API key is valid)

**Step 3: Check for relation details**

Run:
```bash
cat cases/TEST-CERESA/output/graph_data.json | jq '.edges[0]' 2>/dev/null || echo "No relations extracted (expected if no API key)"
```

Expected: Shows relation structure or message about no relations

**Step 4: Verify metadata includes relation info**

Run:
```bash
cat cases/TEST-CERESA/output/graph_data.json | jq '.metadata'
```

Expected: Should include relation_count and other stats

**Step 5: Document test results**

Create `docs/testing/relation-extraction-test-results.md`:

```markdown
# Relation Extraction Test Results

**Date:** 2026-01-22
**Document:** TEST-CERESA / 1 4 1961 Mario Ceresa Money Transfer.pdf

## Results

- Entities extracted: [count]
- Relations extracted: [count]
- Relation extraction status: [COMPLETE/FAILED/SKIPPED]
- Processing time: [time]

## Sample Relations

[Paste sample relation JSON here]

## Issues Found

[List any issues or N/A]

## Next Steps

[What needs attention or N/A]
```

**Step 6: Commit test documentation**

```bash
git add docs/testing/relation-extraction-test-results.md
git commit -m "docs: add relation extraction test results"
```

---

## Task 11: Add CLI Retry Command (Future Enhancement)

**Files:**
- Modify: `farmer_factory/cli.py` (add new command)

**Note:** This task creates the CLI command structure but doesn't implement the full retry logic (that can be done later).

**Step 1: Add retry-relations command skeleton**

Add after the `process` command in `cli.py`:

```python
@cli.command()
@click.argument('case_id')
@click.option('--verbose', is_flag=True, help='Verbose output')
def retry_relations(case_id: str, verbose: bool):
    """Retry relation extraction for documents that failed.

    Finds documents with RELATION_EXTRACTION_FAILED flag and
    re-runs only relation extraction (preserves entities).
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info(f"Retrying relation extraction for case: {case_id}")

    click.echo("⚠️  retry-relations command not yet implemented")
    click.echo("    This will be implemented in a future update")
    click.echo(f"\nFor now, re-run the full process command:")
    click.echo(f"  python cli.py process {case_id}")

    # TODO: Implement retry logic
    # 1. Load graph data
    # 2. Find documents with RELATION_EXTRACTION_FAILED flag
    # 3. For each failed doc:
    #    - Load entities from graph
    #    - Load OCR text from extractions/
    #    - Re-run relation extraction
    #    - Update graph with new relations
    # 4. Save updated graph
    # 5. Report results
```

**Step 2: Test command exists**

Run: `./venv/bin/python3 farmer_factory/cli.py retry-relations --help`

Expected: Shows help message for retry-relations command

**Step 3: Test command runs**

Run: `./venv/bin/python3 farmer_factory/cli.py retry-relations TEST-CERESA`

Expected: Shows "not yet implemented" message

**Step 4: Commit**

```bash
git add farmer_factory/cli.py
git commit -m "feat: add retry-relations CLI command skeleton

Command structure in place but full implementation deferred.
Users can re-run process command as workaround for now."
```

---

## Verification Checklist

After completing all tasks, verify:

- ✅ All intermediate models defined (`TemporalInfo`, `ExtractedRelation`, `RelationExtractionResult`)
- ✅ Relation constants defined (`TEMPORAL_RELATIONS`, `STATE_RELATIONS`)
- ✅ Prompt builder creates valid prompts with entities JSON
- ✅ Entity matching handles exact, alternate, and fuzzy matching
- ✅ Temporal logic applies context-dependent fallbacks
- ✅ Relation transformation creates valid `Relation` objects
- ✅ Response parser handles JSON and markdown code blocks
- ✅ Main extraction method orchestrates all steps
- ✅ `extract_from_text` calls both entity and relation extraction
- ✅ Pipeline tracks extraction flags and metadata
- ✅ End-to-end test runs without crashes
- ✅ retry-relations command structure exists

---

## Success Criteria

**Functional:**
- ✅ Extracts relations when 2+ entities found
- ✅ Skips relation extraction when <2 entities
- ✅ Matches entity names to IDs successfully
- ✅ Applies temporal logic correctly
- ✅ Stores all relations with review flags
- ✅ Returns empty relations on failure (doesn't crash)

**Quality:**
- ✅ Code follows existing patterns in `llm.py`
- ✅ All methods have docstrings
- ✅ Error handling logs useful information
- ✅ Commits are atomic and well-messaged

**Output:**
- ✅ `graph_data.json` includes edges array
- ✅ Metadata shows relation count and status
- ✅ Relations have proper source/target IDs
- ✅ Low-confidence relations flagged

---

## Next Steps After Implementation

1. **Test with multiple documents** - Process 10-20 docs to see relation quality
2. **Analyze confidence distribution** - Are most relations ≥0.70?
3. **Check entity matching accuracy** - How many relations skipped due to matching failures?
4. **Implement retry-relations fully** - Complete the TODO in CLI command
5. **Frontend integration** - Display relations in knowledge graph UI

---

*This plan implements the complete relation extraction design in bite-sized, testable steps.*
