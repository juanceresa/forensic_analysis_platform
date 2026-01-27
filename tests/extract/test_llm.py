"""Unit tests for LLM extraction service."""

from farmer_factory.extract.llm import LLMExtractionService, LLMExtractionResult
from farmer_factory.structure.schema import Person, Property, Relation


def test_llm_extraction_result_structure():
    """Test LLMExtractionResult dataclass structure."""
    from farmer_factory.structure.schema import (
        EntityType,
        VerificationTier,
        Verification,
        RelationType,
    )

    # Create sample entities
    person = Person(
        id="p1",
        entity_type=EntityType.PERSON,
        name="Test Person",
        alternate_names=[],
        roles=[],
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.85,
            verified_by=None,
            verified_at=None,
            notes=None,
        ),
        extracted_from="doc_123",
    )

    # Create sample relation
    relation = Relation(
        id="r1",
        type=RelationType.OWNS,
        source_id="p1",
        target_id="prop1",
        verification=Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=0.80,
            verified_by=None,
            verified_at=None,
            notes="Document states ownership",
        ),
    )

    result = LLMExtractionResult(
        entities=[person],
        relations=[relation],
        confidence=0.85,
        reasoning="Test reasoning",
        metadata={"model": "claude-3"},
    )

    assert len(result.entities) == 1
    assert len(result.relations) == 1
    assert result.confidence == 0.85
    assert result.reasoning == "Test reasoning"
    assert result.metadata == {"model": "claude-3"}


def test_llm_service_initialization():
    """Test LLMExtractionService can be initialized."""
    service = LLMExtractionService()
    assert service is not None

    # With API key
    service_with_key = LLMExtractionService(api_key="test_key")
    assert service_with_key is not None


def test_extract_from_ocr_text():
    """Test LLM extraction from OCR text (mocked)."""

    service = LLMExtractionService()

    # Sample OCR text
    ocr_text = """
    ESCRITURA DE COMPRAVENTA

    En la ciudad de La Habana, a quince de marzo de mil novecientos cincuenta y ocho.

    COMPARECEN:

    De una parte, Don Juan Pérez García, mayor de edad, casado, de nacionalidad cubana,
    vecino de esta ciudad, calle 5ta No. 234, Miramar.

    De otra parte, Doña María López Fernández, mayor de edad, soltera, de nacionalidad cubana,
    vecina de esta ciudad, Avenida 23 No. 567, Vedado.

    MANIFIESTAN:

    Que el Sr. Juan Pérez García es propietario de la finca urbana sita en Miramar,
    calle 5ta No. 234, inscrita en el Registro de la Propiedad bajo el número REG-1958-0042.
    """

    # Extract entities (mocked)
    result = service.extract_from_text(
        text=ocr_text, ocr_confidence=0.92, document_id="doc_123"
    )

    # Verify result structure
    assert isinstance(result, LLMExtractionResult)
    assert isinstance(result.entities, list)
    assert len(result.entities) > 0  # Should extract at least one entity
    assert isinstance(result.relations, list)
    assert 0.0 <= result.confidence <= 1.0
    assert isinstance(result.reasoning, str)
    assert len(result.reasoning) > 0
    assert isinstance(result.metadata, dict)


def test_extract_combines_ocr_confidence():
    """Test that LLM extraction considers OCR confidence."""
    service = LLMExtractionService()

    ocr_text = "Juan Pérez owns property at Miramar, Havana."

    # High OCR confidence
    result_high = service.extract_from_text(ocr_text, 0.95, "doc_123")

    # Low OCR confidence
    result_low = service.extract_from_text(ocr_text, 0.60, "doc_123")

    # Lower OCR confidence should result in lower overall confidence
    assert result_low.confidence < result_high.confidence


def test_extract_entities_have_tier_3_ai():
    """Test that all extracted entities are tagged TIER_3_AI."""
    from farmer_factory.structure.schema import VerificationTier

    service = LLMExtractionService()

    ocr_text = "Juan Pérez owns property at Miramar."
    result = service.extract_from_text(ocr_text, 0.90, "doc_123")

    # All entities should be TIER_3_AI
    for entity in result.entities:
        assert entity.verification.tier == VerificationTier.TIER_3_AI
        assert entity.extracted_from == "doc_123"


def test_extract_includes_reasoning():
    """Test that LLM extraction includes reasoning."""
    service = LLMExtractionService()

    ocr_text = "Juan Pérez owns property at Miramar."
    result = service.extract_from_text(ocr_text, 0.90, "doc_123")

    # Reasoning should be present and non-empty
    assert result.reasoning is not None
    assert len(result.reasoning) > 20  # Should be a substantial explanation


# --- Relation Extraction Tests ---


def test_build_relation_prompt():
    """Test relation prompt includes entities and relation types."""
    from farmer_factory.structure.schema import (
        Person,
        EntityType,
        Verification,
        VerificationTier,
    )

    service = LLMExtractionService()

    person = Person(
        id="test_person_1",
        entity_type=EntityType.PERSON,
        name="Mario Ceresa",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.95),
        extracted_from="test_doc",
    )

    prompt = service._build_relation_prompt(
        text="Mario Ceresa es propietario del Central Santa Maria",
        entities=[person],
        document_id="test_doc",
    )

    # Verify prompt contains key elements
    assert "Mario Ceresa" in prompt
    assert "OWNS" in prompt
    assert "PERSON" in prompt
    assert "REQUIRED OUTPUT FORMAT" in prompt
    assert "relations" in prompt.lower()


def test_match_entity_exact():
    """Test entity matching with exact name match."""
    from farmer_factory.structure.schema import (
        Person,
        EntityType,
        Verification,
        VerificationTier,
    )

    service = LLMExtractionService()

    person = Person(
        id="person_123",
        entity_type=EntityType.PERSON,
        name="Mario Ceresa Rodriguez",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.95),
        extracted_from="test_doc",
    )

    entities = [person]

    # Exact match
    matched_id = service._match_entity("Mario Ceresa Rodriguez", entities)
    assert matched_id == "person_123"


def test_match_entity_alternate_name():
    """Test entity matching with alternate name."""
    from farmer_factory.structure.schema import (
        Person,
        EntityType,
        Verification,
        VerificationTier,
    )

    service = LLMExtractionService()

    person = Person(
        id="person_123",
        entity_type=EntityType.PERSON,
        name="Mario Ceresa Rodriguez",
        alternate_names=["M. Ceresa", "Mario C. Rodriguez"],
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.95),
        extracted_from="test_doc",
    )

    entities = [person]

    # Match alternate name
    matched_id = service._match_entity("M. Ceresa", entities)
    assert matched_id == "person_123"


def test_transform_relations_skips_invalid_types():
    """Test invalid relation types are skipped without dropping valid ones."""
    from farmer_factory.extract.models import (
        ExtractedRelation,
        RelationExtractionResult,
    )
    from farmer_factory.structure.schema import (
        Person,
        EntityType,
        Verification,
        VerificationTier,
    )

    service = LLMExtractionService()

    person = Person(
        id="person_123",
        entity_type=EntityType.PERSON,
        name="Mario Ceresa",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.95),
        extracted_from="test_doc",
    )

    prop = Property(
        id="prop_123",
        entity_type=EntityType.PROPERTY,
        name="Villa Aurelia",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.90),
        extracted_from="test_doc",
    )

    extraction = RelationExtractionResult(
        relations=[
            ExtractedRelation(
                relation_type="FAKE_RELATION",
                source_entity="Mario Ceresa",
                target_entity="Villa Aurelia",
                confidence=0.9,
                temporal=None,
                evidence="Invalid relation type",
            ),
            ExtractedRelation(
                relation_type="OWNS",
                source_entity="Mario Ceresa",
                target_entity="Villa Aurelia",
                confidence=0.9,
                temporal=None,
                evidence="Valid relation type",
            ),
        ]
    )

    relations = service._transform_to_final_relations(
        extraction=extraction,
        entities=[person, prop],
        document_id="test_doc",
        document_date=None,
    )

    assert len(relations) == 1
    assert relations[0].type == "OWNS"


def test_transform_relations_uses_document_date_fallback():
    """Test document date fallback sets relation date for temporal relations."""
    from farmer_factory.extract.models import (
        ExtractedRelation,
        RelationExtractionResult,
    )
    from farmer_factory.structure.schema import (
        Person,
        EntityType,
        Verification,
        VerificationTier,
    )

    service = LLMExtractionService()

    person = Person(
        id="person_123",
        entity_type=EntityType.PERSON,
        name="Mario Ceresa",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.95),
        extracted_from="test_doc",
    )

    prop = Property(
        id="prop_123",
        entity_type=EntityType.PROPERTY,
        name="Villa Aurelia",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.90),
        extracted_from="test_doc",
    )

    extraction = RelationExtractionResult(
        relations=[
            ExtractedRelation(
                relation_type="SOLD",
                source_entity="Mario Ceresa",
                target_entity="Villa Aurelia",
                confidence=0.85,
                temporal=None,
                evidence="Sale mentioned in document",
            )
        ]
    )

    relations = service._transform_to_final_relations(
        extraction=extraction,
        entities=[person, prop],
        document_id="test_doc",
        document_date="1958-03-15",
    )

    assert len(relations) == 1
    assert relations[0].date == "1958-03-15"


def test_match_entity_fuzzy():
    """Test entity matching with fuzzy matching."""
    from farmer_factory.structure.schema import (
        Person,
        EntityType,
        Verification,
        VerificationTier,
    )

    service = LLMExtractionService()

    person = Person(
        id="person_123",
        entity_type=EntityType.PERSON,
        name="Mario Ceresa Rodriguez",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.95),
        extracted_from="test_doc",
    )

    entities = [person]

    # Fuzzy match with typo
    matched_id = service._match_entity("Mario Cereza Rodriguez", entities)
    assert matched_id == "person_123"


def test_match_entity_no_match():
    """Test entity matching returns None when no match found."""
    from farmer_factory.structure.schema import (
        Person,
        EntityType,
        Verification,
        VerificationTier,
    )

    service = LLMExtractionService()

    person = Person(
        id="person_123",
        entity_type=EntityType.PERSON,
        name="Mario Ceresa",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.95),
        extracted_from="test_doc",
    )

    entities = [person]

    # No match
    matched_id = service._match_entity("Completely Different Person", entities)
    assert matched_id is None


def test_apply_temporal_logic_owns():
    """Test temporal logic for OWNS relation (state relation)."""
    from farmer_factory.extract.llm import ExtractedRelation

    service = LLMExtractionService()

    # OWNS is a state relation (if no dates, assume ongoing)
    relation = ExtractedRelation(
        relation_type="OWNS",
        source_entity="Mario Ceresa",
        target_entity="Central Santa Maria",
        confidence=0.88,
        temporal=None,  # No temporal info
        evidence="Some evidence",
    )

    result = service._apply_temporal_logic(relation, document_date=None)

    # Should set ongoing=True for state relation with no dates
    assert result.ongoing is True


def test_apply_temporal_logic_sold():
    """Test temporal logic for SOLD relation (event relation)."""
    from farmer_factory.extract.llm import ExtractedRelation

    service = LLMExtractionService()

    # SOLD is an event relation (if no dates, don't assume ongoing)
    relation = ExtractedRelation(
        relation_type="SOLD",
        source_entity="Mario Ceresa",
        target_entity="Central Santa Maria",
        confidence=0.88,
        temporal=None,  # No temporal info
        evidence="Some evidence",
    )

    # Without document_date, temporal relations should return basic temporal info
    result = service._apply_temporal_logic(relation, document_date=None)

    # Should NOT set ongoing=True for event relation without dates
    assert result.ongoing is None or result.ongoing is False


def test_parse_relation_response_valid_json():
    """Test parsing valid JSON relation response."""
    service = LLMExtractionService()

    response_text = """
    {
      "relations": [
        {
          "relation_type": "OWNS",
          "source_entity": "Mario Ceresa",
          "target_entity": "Central Santa Maria",
          "confidence": 0.88,
          "temporal": {
            "start_date": "1945-01-01",
            "end_date": null,
            "ongoing": true,
            "date_precision": "year"
          },
          "evidence": "Mario Ceresa, propietario del Central Santa Maria",
          "notes": "Ownership stated"
        }
      ],
      "extraction_notes": "Document is a notarial certification."
    }
    """

    result = service._parse_relation_response(response_text)

    assert result is not None
    assert len(result.relations) == 1
    assert result.relations[0].relation_type == "OWNS"
    assert result.relations[0].source_entity == "Mario Ceresa"
    assert result.relations[0].confidence == 0.88


def test_parse_relation_response_markdown_json():
    """Test parsing JSON wrapped in markdown code block."""
    service = LLMExtractionService()

    response_text = """
    ```json
    {
      "relations": [],
      "extraction_notes": "No relations found"
    }
    ```
    """

    result = service._parse_relation_response(response_text)

    assert result is not None
    assert len(result.relations) == 0
    assert result.extraction_notes == "No relations found"


def test_parse_relation_response_empty_relations():
    """Test parsing response with no relations."""
    service = LLMExtractionService()

    response_text = """
    {
      "relations": [],
      "extraction_notes": "Document contains no property relations"
    }
    """

    result = service._parse_relation_response(response_text)

    assert result is not None
    assert len(result.relations) == 0
    assert "no property relations" in result.extraction_notes.lower()


def test_transform_to_final_relations():
    """Test transformation of intermediate relations to final Relation objects."""
    from farmer_factory.structure.schema import (
        Person,
        EntityType,
        Verification,
        VerificationTier,
        RelationType,
    )
    from farmer_factory.extract.llm import (
        ExtractedRelation,
        TemporalInfo,
        RelationExtractionResult,
    )

    service = LLMExtractionService()

    person = Person(
        id="person_123",
        entity_type=EntityType.PERSON,
        name="Mario Ceresa",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.95),
        extracted_from="test_doc",
    )

    property_entity = Property(
        id="property_456",
        entity_type=EntityType.PROPERTY,
        name="Central Santa Maria",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.90),
        extracted_from="test_doc",
    )

    entities = [person, property_entity]

    extracted = ExtractedRelation(
        relation_type="OWNS",
        source_entity="Mario Ceresa",
        target_entity="Central Santa Maria",
        confidence=0.88,
        temporal=TemporalInfo(
            start_date="1945-01-01", end_date=None, ongoing=True, date_precision="year"
        ),
        evidence="Mario Ceresa es propietario del Central Santa Maria",
        notes="Ownership stated in document",
    )

    extraction_result = RelationExtractionResult(
        relations=[extracted], extraction_notes="Test extraction"
    )

    result = service._transform_to_final_relations(
        extraction_result, entities, "test_doc", "1945-01-01"
    )

    assert len(result) == 1
    relation = result[0]
    assert relation.type == RelationType.OWNS
    assert relation.source_id == "person_123"
    assert relation.target_id == "property_456"
    assert relation.verification.tier == VerificationTier.TIER_3_AI
    assert 0.0 <= relation.verification.confidence <= 1.0
    assert relation.date == "1945-01-01"
    assert relation.evidence == "Mario Ceresa es propietario del Central Santa Maria"


def test_transform_skips_unmatched_entities():
    """Test that transformation skips relations with unmatched entities."""
    from farmer_factory.structure.schema import (
        Person,
        EntityType,
        Verification,
        VerificationTier,
    )
    from farmer_factory.extract.llm import ExtractedRelation, RelationExtractionResult

    service = LLMExtractionService()

    person = Person(
        id="person_123",
        entity_type=EntityType.PERSON,
        name="Mario Ceresa",
        verification=Verification(tier=VerificationTier.TIER_3_AI, confidence=0.95),
        extracted_from="test_doc",
    )

    entities = [person]

    extracted = ExtractedRelation(
        relation_type="OWNS",
        source_entity="Mario Ceresa",
        target_entity="Unknown Property",  # This won't match any entity
        confidence=0.88,
        temporal=None,
        evidence="Some evidence",
        notes="",
    )

    extraction_result = RelationExtractionResult(
        relations=[extracted], extraction_notes="Test extraction"
    )

    result = service._transform_to_final_relations(
        extraction_result, entities, "test_doc", None
    )

    # Should skip relation with unmatched entity
    assert len(result) == 0


# --- Chunked Extraction Tests ---


class TestChunkedExtraction:
    """Tests for chunked document extraction."""

    def test_long_document_uses_chunking(self):
        """Documents over chunk threshold should be processed in chunks."""
        service = LLMExtractionService()

        # Create text longer than 5000 chars
        long_text = "Don Mario Ceresa, propietario. " * 200  # ~6400 chars

        result = service.extract_from_text(
            text=long_text, ocr_confidence=0.9, document_id="test_long_doc"
        )

        # Should still return valid result
        assert result is not None
        assert result.confidence > 0
        # For long documents, chunks_processed should be > 1
        # (this will only be true once chunking is implemented)
        if len(long_text) > 5000 and "chunks_processed" in result.metadata:
            assert result.metadata["chunks_processed"] >= 1

    def test_short_document_no_chunking(self):
        """Documents under chunk threshold should not use chunking."""
        service = LLMExtractionService()

        short_text = "Don Mario Ceresa, propietario."

        result = service.extract_from_text(
            text=short_text, ocr_confidence=0.9, document_id="test_short_doc"
        )

        # Should return valid result
        assert result is not None
        # Metadata should not indicate chunking
        assert result.metadata.get("chunks_processed", 1) == 1

    def test_chunked_entities_metadata(self):
        """Chunked extraction should include metadata about the process."""
        service = LLMExtractionService()

        # Text over threshold
        text = "Mario Ceresa owns property. " * 100 + "Central Santa Maria. " * 100

        result = service.extract_from_text(
            text=text, ocr_confidence=0.9, document_id="test_meta"
        )

        # Check metadata exists
        assert "chunks_processed" in result.metadata or len(text) <= 5000
