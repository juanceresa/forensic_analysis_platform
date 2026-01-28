"""Response parsing and entity transformation for LLM extraction."""

import json
import logging
import uuid
from typing import List, Optional, Tuple

from farmer_factory.extract.models import (
    PersonExtraction,
    PropertyExtraction,
    OrganizationExtraction,
    LocationExtraction,
    StructuredEntityExtractionResult,
    TemporalInfo,
    ExtractedRelation,
    RelationExtractionResult,
)
from farmer_factory.structure.schema import (
    BaseEntity,
    Person,
    Property,
    Organization,
    Location,
    Relation,
    Verification,
    VerificationTier,
    RelationType,
)
from farmer_factory.extract.prompts.helpers import (
    get_temporal_relations,
    get_state_relations,
)

logger = logging.getLogger(__name__)


def parse_entity_response(response_text: str) -> StructuredEntityExtractionResult:
    """
    Parse Claude response into StructuredEntityExtractionResult.

    Handles markdown code blocks and validates JSON schema.

    Args:
        response_text: Raw response from Claude

    Returns:
        Validated StructuredEntityExtractionResult

    Raises:
        ValueError: If JSON parsing or validation fails
    """
    try:
        cleaned_text = _extract_json_from_response(response_text)
        data = json.loads(cleaned_text)
        return StructuredEntityExtractionResult(**data)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from Claude response: {str(e)}")
        logger.debug(f"Response text: {response_text[:500]}...")
        # Return empty result with warning instead of raising
        return StructuredEntityExtractionResult(
            entities=[],
            dates=[],
            monetary_values=[],
            registry_refs=[],
            document_date=None,
            document_date_confidence=None,
            extraction_notes=f"JSON parse failed: {str(e)}"
        )

    except Exception as e:
        logger.error(f"Failed to validate extraction result: {str(e)}")
        return StructuredEntityExtractionResult(
            entities=[],
            dates=[],
            monetary_values=[],
            registry_refs=[],
            document_date=None,
            document_date_confidence=None,
            extraction_notes=f"Schema validation failed: {str(e)}"
        )


def parse_relation_response(response_text: str) -> RelationExtractionResult:
    """
    Parse Claude response into RelationExtractionResult.

    Args:
        response_text: Raw response from Claude

    Returns:
        Validated RelationExtractionResult

    Raises:
        ValueError: If JSON parsing or validation fails
    """
    try:
        cleaned_text = _extract_json_from_response(response_text)
        data = json.loads(cleaned_text)
        return RelationExtractionResult(**data)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from Claude relation response: {str(e)}")
        logger.debug(f"Response text: {response_text[:500]}...")
        return RelationExtractionResult(
            relations=[],
            extraction_notes=f"JSON parse failed: {str(e)}"
        )

    except Exception as e:
        logger.error(f"Failed to validate relation extraction result: {str(e)}")
        return RelationExtractionResult(
            relations=[],
            extraction_notes=f"Schema validation failed: {str(e)}"
        )


def _extract_json_from_response(response_text: str) -> str:
    """Extract JSON from response, handling markdown code blocks."""
    cleaned_text = response_text.strip()

    if "```json" in cleaned_text:
        start = cleaned_text.find("```json") + 7
        end = cleaned_text.find("```", start)
        if end > start:
            cleaned_text = cleaned_text[start:end].strip()
    elif "```" in cleaned_text:
        start = cleaned_text.find("```") + 3
        end = cleaned_text.find("```", start)
        if end > start:
            cleaned_text = cleaned_text[start:end].strip()

    return cleaned_text


def transform_to_final_entities(
    extraction: StructuredEntityExtractionResult,
    document_id: str,
    ocr_confidence: float,
) -> List[BaseEntity]:
    """
    Transform structured entities to final schema entities.

    Args:
        extraction: Structured extraction result from Claude
        document_id: Document identifier
        ocr_confidence: OCR confidence score

    Returns:
        List of final entity objects
    """
    final_entities = []

    for entity in extraction.entities:
        combined_confidence = min(ocr_confidence, entity.confidence)

        verification = Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=combined_confidence,
            verified_by=None,
            verified_at=None,
            notes=entity.notes,
        )

        short_id = str(uuid.uuid4())[:8]
        entity_id = f"{document_id}_{entity.entity_type.lower()}_{short_id}"
        context_note = f"Extracted from context: {entity.context[:100] if entity.context else 'N/A'}..."

        if isinstance(entity, PersonExtraction):
            person = Person(
                id=entity_id,
                entity_type="PERSON",
                name=entity.name,
                alternate_names=entity.alternate_names,
                birth_date=entity.birth_date,
                death_date=entity.death_date,
                nationality=entity.nationality,
                residence=entity.residence,
                profession=entity.profession,
                marital_status=entity.marital_status,
                mother=entity.mother,
                father=entity.father,
                spouse=entity.spouse,
                children=entity.children,
                siblings=entity.siblings,
                roles=entity.roles,
                verification=verification,
                extracted_from=document_id,
                notes=context_note,
            )
            final_entities.append(person)

        elif isinstance(entity, PropertyExtraction):
            prop = Property(
                id=entity_id,
                entity_type="PROPERTY",
                name=entity.name,
                property_type=entity.property_type,
                address=entity.address,
                description=entity.description,
                area=entity.area,
                area_unit=entity.area_unit,
                registry_number=entity.registry_number,
                cadastral_info=entity.cadastral_info,
                folio_number=entity.folio_number,
                verification=verification,
                extracted_from=document_id,
                notes=context_note,
            )
            final_entities.append(prop)

        elif isinstance(entity, OrganizationExtraction):
            org = Organization(
                id=entity_id,
                entity_type="ORGANIZATION",
                name=entity.name,
                org_type=entity.org_type,
                address=entity.address,
                verification=verification,
                extracted_from=document_id,
                notes=context_note,
            )
            final_entities.append(org)

        elif isinstance(entity, LocationExtraction):
            location = Location(
                id=entity_id,
                entity_type="LOCATION",
                name=entity.name,
                location_type=entity.location_type,
                country=entity.country,
                verification=verification,
                extracted_from=document_id,
                notes=context_note,
            )
            final_entities.append(location)

    logger.info(
        f"Transformed {len(extraction.entities)} structured entities → "
        f"{len(final_entities)} final entities"
    )

    return final_entities


def transform_to_final_relations(
    extraction: RelationExtractionResult,
    entities: List[BaseEntity],
    document_id: str,
    document_date: Optional[str],
    match_entity_func,
) -> List[Relation]:
    """
    Transform intermediate relations to final schema.

    Args:
        extraction: Intermediate extraction result from Claude
        entities: Previously extracted entities
        document_id: Document identifier
        document_date: Document date for temporal fallback
        match_entity_func: Function to match entity names to IDs

    Returns:
        List of final Relation objects
    """
    final_relations = []
    temporal_relations = get_temporal_relations()

    for rel in extraction.relations:
        try:
            relation_type = RelationType(rel.relation_type)
        except ValueError:
            logger.warning(
                f"Skipping relation with invalid type '{rel.relation_type}' "
                f"from {document_id}"
            )
            continue

        source_id = match_entity_func(rel.source_entity, entities)
        target_id = match_entity_func(rel.target_entity, entities)

        if not source_id or not target_id:
            logger.warning(
                f"Skipping relation {rel.relation_type} - "
                f"unmatched entities: {rel.source_entity} -> {rel.target_entity}"
            )
            continue

        temporal_info = apply_temporal_logic(rel, document_date)

        verification = Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=rel.confidence,
            verified_by=None,
            verified_at=None,
            notes=rel.notes,
        )

        needs_review = rel.confidence < 0.70 or (
            relation_type.value in temporal_relations
            and temporal_info.date_precision == "unknown"
        )

        final_notes = rel.notes or ""
        if needs_review:
            if rel.confidence < 0.70:
                final_notes += f" Low confidence ({rel.confidence:.2f}) - requires analyst review."
            if (
                relation_type.value in temporal_relations
                and temporal_info.date_precision == "unknown"
            ):
                final_notes += " Missing temporal data for event relation."

        relation = Relation(
            id=f"{document_id}_rel_{uuid.uuid4().hex[:8]}",
            type=relation_type,
            source_id=source_id,
            target_id=target_id,
            verification=verification,
            document_id=document_id,
            evidence=rel.evidence,
            notes=final_notes.strip(),
            date=temporal_info.start_date,
        )

        final_relations.append(relation)

    logger.info(
        f"Transformed {len(extraction.relations)} intermediate relations → "
        f"{len(final_relations)} final relations"
    )

    return final_relations


def apply_temporal_logic(
    relation: ExtractedRelation, document_date: Optional[str]
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
    temporal_relations = get_temporal_relations()
    state_relations = get_state_relations()

    if relation.relation_type in temporal_relations:
        if temporal.start_date:
            return temporal
        elif document_date:
            logger.info(
                f"Using document date as fallback for {relation.relation_type} relation"
            )
            return TemporalInfo(
                start_date=document_date,
                date_precision="year",
                notes="Date inferred from document date",
            )
        else:
            logger.warning(
                f"No temporal data for {relation.relation_type} relation"
            )
            return TemporalInfo(
                date_precision="unknown",
                notes="Missing temporal data for event relation",
            )

    elif relation.relation_type in state_relations:
        if temporal.start_date:
            return temporal
        else:
            return TemporalInfo(date_precision="unknown", ongoing=True)

    return temporal
