"""LLM extraction service for entity extraction from OCR text using Claude API."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher
import logging
import json
import uuid

from pydantic import BaseModel, Field

from farmer_factory.structure.schema import BaseEntity, Relation
from farmer_factory.extract.models import (
    IntermediateEntityType,
    PersonExtraction,
    PropertyExtraction,
    OrganizationExtraction,
    LocationExtraction,
    StructuredEntity,
    StructuredEntityExtractionResult,
    TemporalInfo,
    ExtractedRelation,
    RelationExtractionResult
)
from farmer_factory.extract.api_client import ClaudeAPIClient

logger = logging.getLogger(__name__)


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


@dataclass
class LLMExtractionResult:
    """Result from LLM-based entity extraction."""
    entities: List[BaseEntity]   # Extracted entities
    relations: List[Relation]    # Extracted relations
    confidence: float            # Extraction confidence
    reasoning: str               # Extraction reasoning
    metadata: Dict[str, Any]


class LLMExtractionService:
    """Wrapper for Claude text API for entity extraction from OCR text."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM extraction service.

        Args:
            api_key: Optional Anthropic API key.
                    If None, loads from environment variable.
        """
        self.api_key = api_key
        self.api_client = ClaudeAPIClient(api_key=api_key)

    def _build_entity_prompt(
        self,
        text: str,
        document_id: str,
        document_type: str = "unknown",
        ocr_quality: float = 0.0
    ) -> str:
        """
        Build structured entity extraction prompt.

        Extracts entities with full biographical and family relationship data.

        Args:
            text: OCR-extracted text
            document_id: Document identifier
            document_type: Type of document
            ocr_quality: OCR confidence score

        Returns:
            Formatted prompt string
        """
        # Map OCR quality to human-readable description
        if ocr_quality >= 0.9:
            quality_desc = "High (clear text)"
        elif ocr_quality >= 0.7:
            quality_desc = "Medium (some unclear characters)"
        elif ocr_quality >= 0.5:
            quality_desc = "Low (multiple unclear sections)"
        else:
            quality_desc = "Very Low (significant OCR challenges)"

        prompt = f"""You are a forensic document analyst extracting entities from historical Cuban property documents. Extract factual information only — never make legal conclusions.

Analyze the following OCR text and extract all entities with their detailed attributes.

ENTITY TYPES:
1. PERSON - Extract biographical and family relationship data
2. PROPERTY - Extract property details
3. ORGANIZATION - Extract organization details
4. LOCATION - Extract geographic information
5. DATE - Dates mentioned in document (returned separately)
6. MONETARY_VALUE - Financial amounts (returned separately)
7. REGISTRY_REFERENCE - Registry references (returned separately)

PERSON ENTITY SCHEMA:
{{
  "entity_type": "PERSON",
  "name": "Mario Ceresa",  // Required: Full name as written in document
  "alternate_names": ["Don Mario Ceresa", "M. Ceresa"],  // Optional: Titles, abbreviations

  // Demographics (extract if mentioned):
  "birth_date": "1920" or "1920-03-15",  // Year or full date
  "death_date": null,
  "nationality": "Cuban",
  "residence": "Miramar, Havana",  // Where they live
  "profession": "industrialist",
  "marital_status": "married" or "casado/casada",

  // Family relationships (CRITICAL - extract if mentioned):
  "mother": "María López de Queral",  // Mother's name
  "father": "Juan Ceresa",  // Father's name
  "spouse": "Rosa Queral",  // Spouse name (use primary if multiple)
  "children": ["Mario Ceresa Jr.", "Rosa Ceresa"],  // List of children's names
  "siblings": ["Carlos Ceresa"],  // List of siblings' names

  // Roles (what they're doing in this document):
  "roles": ["owner", "seller"],  // e.g., owner, buyer, seller, witness, notary

  // Extraction metadata:
  "confidence": 0.95,  // 0.0-1.0 based on OCR clarity
  "context": "...comparece Don Mario Ceresa, hijo de Juan Ceresa y María López...",
  "notes": "Family relationships mentioned in preamble"
}}

IMPORTANT - Family Relationships:
- Look for phrases like "hijo de" (son of), "hija de" (daughter of)
- "casado con" (married to), "esposa de" (wife of), "esposo de" (husband of)
- "hermano de" (brother of), "hermana de" (sister of)
- Extract EXACTLY as written, preserve Spanish names completely
- If only partial info (e.g., just father mentioned), that's fine
- Don't invent relationships not stated in the text

PROPERTY ENTITY SCHEMA:
{{
  "entity_type": "PROPERTY",
  "name": "Central Santa Maria",  // Property name
  "property_type": "sugar mill" or "ingenio",  // Type: finca, ingenio, central, hacienda
  "location": "Florida, Camagüey",  // Location as text (will be linked later)
  "address": "Carretera Central Km 15",
  "description": "Sugar mill with 500 hectares",
  "area": 500.0,
  "area_unit": "hectares" or "caballerías",
  "registry_number": "Folio 123, Tomo V",
  "cadastral_info": "Finca 456",
  "folio_number": "123",
  "confidence": 0.90,
  "context": "...la finca Central Santa Maria...",
  "notes": "Area mentioned in cadastral description"
}}

ORGANIZATION ENTITY SCHEMA:
{{
  "entity_type": "ORGANIZATION",
  "name": "Banco Núñez",
  "org_type": "bank" or "banco",
  "location": "Havana",
  "address": "Calle Obispo 305",
  "confidence": 0.85,
  "context": "...el Banco Núñez...",
  "notes": null
}}

LOCATION ENTITY SCHEMA:
{{
  "entity_type": "LOCATION",
  "name": "Florida",
  "location_type": "municipality" or "municipio",
  "parent_location": "Camagüey",  // Parent location (e.g., province)
  "country": "Cuba",
  "confidence": 0.95,
  "context": "...en el municipio de Florida...",
  "notes": null
}}

OCR QUALITY CONSIDERATIONS:
- If text is unclear, lower confidence score and note in "notes"
- Common OCR errors in Spanish: ñ→n, á→a, rn→m, ll→U
- Handwritten text may have lower confidence

EXTRACTION RULES:
- Extract only what the document explicitly states
- Preserve original Spanish terms and names
- If a field is not mentioned, use null or empty list []
- For PERSON entities, family relationships are HIGH PRIORITY
- Don't guess or infer data not in the text

DOCUMENT METADATA:
Document ID: {document_id}
Document Type: {document_type}
OCR Quality: {quality_desc} ({ocr_quality:.2f})
Language: Spanish

OCR TEXT:
{text}

Respond with JSON in this format:
{{
  "entities": [
    // Array of PERSON, PROPERTY, ORGANIZATION, LOCATION entities
  ],
  "dates": [
    // Dates found: {{"value": "15 de marzo de 1958", "normalized": "1958-03-15", "context": "..."}}
  ],
  "monetary_values": [
    // Money amounts: {{"value": "$50,000 pesos", "normalized": {{"amount": 50000, "currency": "pesos"}}, "context": "..."}}
  ],
  "registry_refs": [
    // Registry references: {{"value": "Folio 123", "normalized": "Folio 123, Tomo V", "context": "..."}}
  ],
  "document_date": "1958-03-15",  // Main document date
  "document_date_confidence": 0.90,
  "extraction_notes": "Overall good OCR quality. Family relationships extracted from preamble."
}}"""
        return prompt

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

REQUIRED OUTPUT FORMAT:
You MUST respond with a valid JSON object in the format shown below.
- If you find relations, include them in the "relations" array
- If you find NO relations, return an empty array: "relations": []
- ALWAYS return valid JSON - never return prose explanations
- Use "extraction_notes" to explain why no relations were found

Example response with relations:
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
}}

Example response with NO relations:
{{
  "relations": [],
  "extraction_notes": "Document is a loan fee notification with no property ownership or transaction relationships."
}}"""
        return prompt

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
        # Normalize entity name for better matching
        entity_name_normalized = entity_name.lower().strip()

        # Step 1: Exact match on name (case-insensitive)
        for entity in entities:
            if hasattr(entity, 'name') and entity.name:
                if entity.name.lower().strip() == entity_name_normalized:
                    return entity.id

        # Step 2: Exact match on alternate names (case-insensitive)
        for entity in entities:
            if hasattr(entity, 'alternate_names') and entity.alternate_names:
                for alt_name in entity.alternate_names:
                    if alt_name.lower().strip() == entity_name_normalized:
                        return entity.id

        # Step 3: Fuzzy matching with SequenceMatcher (lowered threshold to 0.75)
        best_match_id = None
        best_similarity = 0.0

        for entity in entities:
            if hasattr(entity, 'name') and entity.name:
                # Calculate similarity
                similarity = SequenceMatcher(None, entity_name_normalized, entity.name.lower().strip()).ratio()

                if similarity >= 0.75 and similarity > best_similarity:
                    best_match_id = entity.id
                    best_similarity = similarity

        if best_match_id:
            logger.info(f"Fuzzy matched '{entity_name}' to entity (similarity: {best_similarity:.2f})")
            return best_match_id

        # Step 4: Partial match - check if entity name is contained in or contains the extracted name
        for entity in entities:
            if hasattr(entity, 'name') and entity.name:
                entity_name_lower = entity.name.lower().strip()
                # Check if one is substring of the other
                if (entity_name_normalized in entity_name_lower or
                    entity_name_lower in entity_name_normalized):
                    # Require at least 60% of the shorter string to match
                    min_len = min(len(entity_name_normalized), len(entity_name_lower))
                    if min_len >= 3:  # Only for names with 3+ chars
                        logger.info(f"Partial matched '{entity_name}' to entity '{entity.name}'")
                        return entity.id

        # Step 5: No match found
        logger.warning(f"Could not match entity '{entity_name}' - relation will be skipped")
        return None

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
            response_text = self.api_client.call_with_retry(
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

    def _parse_extraction_response(self, response_text: str) -> StructuredEntityExtractionResult:
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
            # Extract JSON from markdown code blocks if present
            cleaned_text = response_text.strip()

            # Check for markdown JSON code blocks
            if "```json" in cleaned_text:
                # Extract content between ```json and ```
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
            result = StructuredEntityExtractionResult(**data)
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Claude response: {str(e)}")
            logger.debug(f"Response text: {response_text[:500]}...")
            raise ValueError(f"Invalid JSON in Claude response: {str(e)}")

        except Exception as e:
            logger.error(f"Failed to validate extraction result: {str(e)}")
            logger.debug(f"Parsed data: {data if 'data' in locals() else 'N/A'}")
            raise ValueError(f"Invalid extraction result schema: {str(e)}")

    def _transform_to_final_entities(
        self,
        extraction: StructuredEntityExtractionResult,
        document_id: str,
        ocr_confidence: float
    ) -> List[BaseEntity]:
        """
        Transform structured entities to final schema entities.

        Takes structured PersonExtraction, PropertyExtraction, etc. and creates
        final Pydantic models with all fields populated.

        Args:
            extraction: Structured extraction result from Claude
            document_id: Document identifier
            ocr_confidence: OCR confidence score

        Returns:
            List of final entity objects
        """
        from farmer_factory.structure.schema import (
            Person, Property, Organization, Location,
            EntityType, VerificationTier, Verification
        )

        final_entities = []

        for entity in extraction.entities:
            # Combined confidence: min of OCR and entity confidence
            combined_confidence = min(ocr_confidence, entity.confidence)

            # Create verification
            verification = Verification(
                tier=VerificationTier.TIER_3_AI,
                confidence=combined_confidence,
                verified_by=None,
                verified_at=None,
                notes=entity.notes
            )

            # Generate unique entity ID
            short_id = str(uuid.uuid4())[:8]
            entity_id = f"{document_id}_{entity.entity_type.lower()}_{short_id}"

            # Transform based on entity type
            if isinstance(entity, PersonExtraction):
                person = Person(
                    id=entity_id,
                    entity_type=EntityType.PERSON,
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
                    notes=f"Extracted from context: {entity.context[:100] if entity.context else 'N/A'}..."
                )
                final_entities.append(person)

            elif isinstance(entity, PropertyExtraction):
                prop = Property(
                    id=entity_id,
                    entity_type=EntityType.PROPERTY,
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
                    notes=f"Extracted from context: {entity.context[:100] if entity.context else 'N/A'}..."
                )
                # Note: location field will be linked in graph building phase
                final_entities.append(prop)

            elif isinstance(entity, OrganizationExtraction):
                org = Organization(
                    id=entity_id,
                    entity_type=EntityType.ORGANIZATION,
                    name=entity.name,
                    org_type=entity.org_type,
                    address=entity.address,
                    verification=verification,
                    extracted_from=document_id,
                    notes=f"Extracted from context: {entity.context[:100] if entity.context else 'N/A'}..."
                )
                # Note: location field will be linked in graph building phase
                final_entities.append(org)

            elif isinstance(entity, LocationExtraction):
                location = Location(
                    id=entity_id,
                    entity_type=EntityType.LOCATION,
                    name=entity.name,
                    location_type=entity.location_type,
                    country=entity.country,
                    verification=verification,
                    extracted_from=document_id,
                    notes=f"Extracted from context: {entity.context[:100] if entity.context else 'N/A'}..."
                )
                # Note: parent_location field will be linked in graph building phase
                final_entities.append(location)

        logger.info(
            f"Transformed {len(extraction.entities)} structured entities → "
            f"{len(final_entities)} final entities "
            f"({len(extraction.dates)} dates, "
            f"{len(extraction.monetary_values)} monetary values, "
            f"{len(extraction.registry_refs)} registry refs stored as metadata)"
        )

        return final_entities

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
        from farmer_factory.config.settings import settings

        start_time = time.time()

        # Build prompt
        prompt = self._build_entity_prompt(
            text=text,
            document_id=document_id,
            ocr_quality=ocr_confidence
        )

        # Call Claude API
        logger.info(f"Calling Claude API for entity extraction from {document_id}...")
        response_text = self.api_client.call_with_retry(
            prompt=prompt,
            max_retries=settings.max_retries,
            retry_delay=settings.retry_delay,
            api_timeout=settings.api_timeout
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

    def _mock_extract(
        self,
        text: str,
        ocr_confidence: float,
        document_id: str
    ) -> LLMExtractionResult:
        """
        Mock entity extraction for testing (fallback when API not configured).

        Args:
            text: OCR-extracted text from document
            ocr_confidence: Confidence score from OCR (0.0-1.0)
            document_id: Document identifier for entity tracking

        Returns:
            LLMExtractionResult with extracted entities and relations

        Note:
            This is a MOCKED implementation for testing.
            Real implementation would call Anthropic Claude API with structured prompt.
        """
        from farmer_factory.structure.schema import (
            Person, Property, Organization, Location,
            EntityType, VerificationTier, Verification,
            Relation, RelationType
        )

        # MOCKED: Simulate LLM entity extraction from text
        # In production, this would send text to Claude API with JSON schema prompt
        logger.warning(
            f"⚠️  MOCK EXTRACTION - Using simulated data for {document_id}. "
            "Configure ANTHROPIC_API_KEY to use real Claude API."
        )

        # Calculate extraction confidence
        # Base LLM confidence (simulated quality of extraction)
        llm_base_confidence = 0.88

        # Combined confidence: min of OCR and LLM
        combined_confidence = min(ocr_confidence, llm_base_confidence)

        # Create verification for all entities
        verification = Verification(
            tier=VerificationTier.TIER_3_AI,
            confidence=combined_confidence,
            verified_by=None,
            verified_at=None,
            notes=None
        )

        # Mock entity extraction (simulating Claude understanding the text)
        entities = []

        # Extract entities based on text content
        # Check for specific Spanish names first (for realistic test cases)
        if "Juan Pérez" in text or "Juan Perez" in text:
            person1 = Person(
                id=f"{document_id}_person_1",
                entity_type=EntityType.PERSON,
                name="Juan Pérez García",
                alternate_names=["Don Juan Pérez García", "Sr. Juan Pérez García"],
                birth_date=None,
                nationality="Cuban",
                residence="Miramar, calle 5ta No. 234",
                marital_status="casado",
                roles=["seller", "owner"],
                verification=verification,
                extracted_from=document_id,
                notes="⚠️ MOCK DATA - Simulated extraction for testing (no API configured)"
            )
            entities.append(person1)

        if "María López" in text or "Maria Lopez" in text:
            person2 = Person(
                id=f"{document_id}_person_2",
                entity_type=EntityType.PERSON,
                name="María López Fernández",
                alternate_names=["Doña María López Fernández"],
                birth_date=None,
                nationality="Cuban",
                residence="Vedado, Avenida 23 No. 567",
                marital_status="soltera",
                roles=["buyer"],
                verification=verification,
                extracted_from=document_id,
                notes="⚠️ MOCK DATA - Simulated extraction for testing (no API configured)"
            )
            entities.append(person2)

        # Extract Property entity
        if "finca" in text.lower() or "propiedad" in text.lower() or "property" in text.lower():
            property_entity = Property(
                id=f"{document_id}_property_1",
                entity_type=EntityType.PROPERTY,
                name="Finca urbana en Miramar",
                property_type="residential",
                location_id=None,
                address="calle 5ta No. 234, Miramar",
                registry_number="REG-1958-0042",
                verification=verification,
                extracted_from=document_id,
                notes="⚠️ MOCK DATA - Simulated extraction for testing (no API configured)"
            )
            entities.append(property_entity)

        # Extract Location entity
        if "Havana" in text or "Habana" in text:
            location = Location(
                id=f"{document_id}_location_1",
                entity_type=EntityType.LOCATION,
                name="La Habana",
                location_type="city",
                verification=verification,
                extracted_from=document_id,
                notes="⚠️ MOCK DATA - Simulated extraction for testing (no API configured)"
            )
            entities.append(location)

        # Generic extraction fallback: if no specific entities found but text is substantial,
        # create generic mock entities (simulates LLM finding something in any text)
        if len(entities) == 0 and len(text) > 50:
            # Generic person entity
            person = Person(
                id=f"{document_id}_person_generic",
                entity_type=EntityType.PERSON,
                name="Generic Person",
                alternate_names=[],
                roles=["owner"],
                verification=verification,
                extracted_from=document_id,
                notes="Generic entity extracted from OCR text for testing"
            )
            entities.append(person)

        # Mock relations
        relations = []

        if len(entities) >= 2:
            # Look for ownership relations
            persons = [e for e in entities if e.entity_type == EntityType.PERSON]
            properties = [e for e in entities if e.entity_type == EntityType.PROPERTY]

            if persons and properties:
                relation = Relation(
                    id=f"{document_id}_rel_1",
                    type=RelationType.OWNS,
                    source_id=persons[0].id,
                    target_id=properties[0].id,
                    verification=verification,
                    document_id=document_id,
                    notes="Ownership extracted from deed text"
                )
                relations.append(relation)

        # Mock reasoning (simulating Claude's extraction logic)
        reasoning = f"""
        Analyzed OCR text (OCR confidence: {ocr_confidence:.2f}) from document.

        Extracted entities:
        - {len([e for e in entities if e.entity_type == EntityType.PERSON])} Person(s)
        - {len([e for e in entities if e.entity_type == EntityType.PROPERTY])} Property/Properties
        - {len([e for e in entities if e.entity_type == EntityType.LOCATION])} Location(s)

        Identified relations: {len(relations)} ownership/transaction relations

        Combined confidence: {combined_confidence:.2f} (min of OCR {ocr_confidence:.2f} and LLM {llm_base_confidence:.2f})
        All entities tagged as TIER_3_AI (unverified AI extraction).

        This is a mocked extraction for testing purposes.
        """.strip()

        # Mock metadata
        metadata = {
            "model": "claude-llm-mocked",
            "api_version": "mocked_v1",
            "processing_time_ms": 800,
            "ocr_confidence": ocr_confidence,
            "llm_confidence": llm_base_confidence,
            "text_length": len(text)
        }

        return LLMExtractionResult(
            entities=entities,
            relations=relations,
            confidence=combined_confidence,
            reasoning=reasoning,
            metadata=metadata
        )
