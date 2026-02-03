"""LLM extraction service for entity extraction from OCR text using Claude API."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher
import logging
import time

from farmer_factory.structure.schema import BaseEntity, Relation
from farmer_factory.extract.api_client import ClaudeAPIClient
from farmer_factory.extract.chunker import TextChunker
from farmer_factory.extract.prompts import (
    build_entity_prompt_zero_shot,
    build_relation_prompt_zero_shot,
)
from farmer_factory.extract.parsers import (
    parse_entity_response,
    parse_relation_response,
    transform_to_final_entities,
    transform_to_final_relations,
)

# Chunk threshold from Chilean KG paper (arXiv:2408.11975)
CHUNK_THRESHOLD = 5000  # Characters - process as chunks if longer

logger = logging.getLogger(__name__)


# Helper functions have been moved to farmer_factory.extract.prompts.helpers


@dataclass
class LLMExtractionResult:
    """Result from LLM-based entity extraction."""

    entities: List[BaseEntity]  # Extracted entities
    relations: List[Relation]  # Extracted relations
    confidence: float  # Extraction confidence
    reasoning: str  # Extraction reasoning
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

    # _build_entity_prompt has been moved to farmer_factory.extract.prompts.few_shot
    # _build_relation_prompt has been moved to farmer_factory.extract.prompts.few_shot

    def _match_entity(
        self, entity_name: str, entities: List[BaseEntity]
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
            if hasattr(entity, "name") and entity.name:
                if entity.name.lower().strip() == entity_name_normalized:
                    return entity.id

        # Step 2: Exact match on alternate names (case-insensitive)
        for entity in entities:
            if hasattr(entity, "alternate_names") and entity.alternate_names:
                for alt_name in entity.alternate_names:
                    if alt_name.lower().strip() == entity_name_normalized:
                        return entity.id

        # Step 3: Fuzzy matching with SequenceMatcher (lowered threshold to 0.75)
        best_match_id = None
        best_similarity = 0.0

        for entity in entities:
            if hasattr(entity, "name") and entity.name:
                # Calculate similarity
                similarity = SequenceMatcher(
                    None, entity_name_normalized, entity.name.lower().strip()
                ).ratio()

                if similarity >= 0.75 and similarity > best_similarity:
                    best_match_id = entity.id
                    best_similarity = similarity

        if best_match_id:
            logger.info(
                f"Fuzzy matched '{entity_name}' to entity (similarity: {best_similarity:.2f})"
            )
            return best_match_id

        # Step 4: Partial match - check if entity name is contained in or contains the extracted name
        for entity in entities:
            if hasattr(entity, "name") and entity.name:
                entity_name_lower = entity.name.lower().strip()
                # Check if one is substring of the other
                if (
                    entity_name_normalized in entity_name_lower
                    or entity_name_lower in entity_name_normalized
                ):
                    # Require at least 60% of the shorter string to match
                    min_len = min(len(entity_name_normalized), len(entity_name_lower))
                    if min_len >= 3:  # Only for names with 3+ chars
                        logger.info(
                            f"Partial matched '{entity_name}' to entity '{entity.name}'"
                        )
                        return entity.id

        # Step 5: No match found
        logger.warning(
            f"Could not match entity '{entity_name}' - relation will be skipped"
        )
        return None

    # _apply_temporal_logic has been moved to farmer_factory.extract.parsers
    # _transform_to_final_relations has been moved to farmer_factory.extract.parsers
    # _parse_relation_response has been moved to farmer_factory.extract.parsers

    def _extract_relations(
        self,
        text: str,
        entities: List[BaseEntity],
        document_id: str,
        ocr_confidence: float,
        document_date: Optional[str],
    ) -> List[Relation]:
        """
        Extract relations from OCR text using Claude API.

        Args:
            text: OCR-extracted text
            entities: Previously extracted entities
            document_id: Document identifier
            ocr_confidence: OCR confidence for logging
            document_date: Document date for temporal fallback

        Returns:
            List of Relation objects (empty if extraction fails)
        """
        from farmer_factory.config.settings import settings

        try:
            start_time = time.time()

            # Build zero-shot prompt (more effective and cost-efficient)
            prompt = build_relation_prompt_zero_shot(
                text=text, entities=entities, document_id=document_id
            )

            # Call Claude API with retry logic
            logger.info(
                f"Calling Claude API for relation extraction from {document_id}..."
            )
            response_text = self.api_client.call_standard(
                prompt=prompt,
                max_retries=settings.max_retries,
                retry_delay=settings.retry_delay,
                api_timeout=settings.api_timeout,
            )

            # Parse response using parsers module
            extraction = parse_relation_response(response_text)

            # Transform to final relations using parsers module
            relations = transform_to_final_relations(
                extraction=extraction,
                entities=entities,
                document_id=document_id,
                document_date=document_date,
                match_entity_func=self._match_entity,
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

    # _parse_extraction_response has been moved to farmer_factory.extract.parsers
    # _transform_to_final_entities has been moved to farmer_factory.extract.parsers

    def _extract_entities(
        self, text: str, ocr_confidence: float, document_id: str
    ) -> tuple[List[BaseEntity], Optional[str]]:
        """
        Extract entities from OCR text (first pass).

        Returns:
            Tuple of (entities list, document_date)
        """
        from farmer_factory.config.settings import settings

        start_time = time.time()

        # Build zero-shot prompt (more effective and cost-efficient)
        prompt = build_entity_prompt_zero_shot(
            text=text, document_id=document_id, ocr_quality=ocr_confidence
        )

        # Call Claude API
        logger.info(f"Calling Claude API for entity extraction from {document_id}...")
        response_text = self.api_client.call_standard(
            prompt=prompt,
            max_retries=settings.max_retries,
            retry_delay=settings.retry_delay,
            api_timeout=settings.api_timeout,
        )

        # Parse response using parsers module
        extraction = parse_entity_response(response_text)

        # Transform to final entities using parsers module
        entities = transform_to_final_entities(
            extraction=extraction,
            document_id=document_id,
            ocr_confidence=ocr_confidence,
        )

        return entities, extraction.document_date

    def extract_from_text(
        self, text: str, ocr_confidence: float, document_id: str
    ) -> LLMExtractionResult:
        """
        Extract entities and relations from OCR text using Claude API.

        For documents over 5000 characters, uses chunked extraction
        with 10% overlap and merges results.

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

        # Check if chunking is needed
        if len(text) > CHUNK_THRESHOLD:
            return self._extract_with_chunking(
                text=text,
                ocr_confidence=ocr_confidence,
                document_id=document_id,
            )

        # Try real Claude API extraction
        try:
            # STEP 1: Extract entities (first pass)
            entities, document_date = self._extract_entities(
                text, ocr_confidence, document_id
            )

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
                    ocr_confidence=ocr_confidence,
                    document_date=document_date,
                )
            else:
                logger.info(
                    f"Skipping relation extraction for {document_id} (only {len(entities)} entities)"
                )

            # Calculate overall confidence
            if entities:
                avg_entity_confidence = sum(
                    e.verification.confidence for e in entities
                ) / len(entities)
            else:
                avg_entity_confidence = ocr_confidence

            if relations:
                avg_relation_confidence = sum(
                    r.verification.confidence for r in relations
                ) / len(relations)
                avg_confidence = (avg_entity_confidence + avg_relation_confidence) / 2
            else:
                avg_confidence = avg_entity_confidence

            # Build reasoning
            reasoning = f"""
Entity and relation extraction completed using Claude API.

Extracted {len(entities)} entities and {len(relations)} relations from document.
- {len([e for e in entities if e.entity_type == "PERSON"])} Person(s)
- {len([e for e in entities if e.entity_type == "PROPERTY"])} Property/Properties
- {len([e for e in entities if e.entity_type == "ORGANIZATION"])} Organization(s)
- {len([e for e in entities if e.entity_type == "LOCATION"])} Location(s)

OCR confidence: {ocr_confidence:.2f}
Average entity confidence: {avg_entity_confidence:.2f}
Average relation confidence: {avg_relation_confidence if relations else "N/A"}

All entities and relations tagged as TIER_3_AI (unverified AI extraction).
            """.strip()

            # Build metadata
            metadata = {
                "model": settings.claude_model,
                "api_version": "anthropic_v1",
                "prompt_mode": "zero_shot",
                "ocr_confidence": ocr_confidence,
                "entity_count": len(entities),
                "relation_count": len(relations),
                "relation_extraction_status": (
                    "COMPLETE" if relations or len(entities) < 2 else "FAILED"
                ),
                "document_date": document_date,
                "text_length": len(text),
            }

            return LLMExtractionResult(
                entities=entities,
                relations=relations,
                confidence=avg_confidence,
                reasoning=reasoning,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Claude API extraction failed: {str(e)}")
            logger.warning(f"Falling back to mock extraction for {document_id}")
            return self._mock_extract(text, ocr_confidence, document_id)

    def _extract_with_chunking(
        self,
        text: str,
        ocr_confidence: float,
        document_id: str,
    ) -> LLMExtractionResult:
        """
        Extract from long document using chunked processing.

        Strategy from Chilean KG paper (arXiv:2408.11975):
        1. Split into 5000-char chunks with 10% overlap
        2. Extract entities from each chunk
        3. Merge entities across chunks (deduplicate by name)
        4. Extract relations using full text + merged entity list

        Args:
            text: Full document text (over CHUNK_THRESHOLD)
            ocr_confidence: OCR confidence score
            document_id: Document identifier

        Returns:
            LLMExtractionResult with merged entities and relations
        """
        from farmer_factory.config.settings import settings

        chunker = TextChunker(chunk_size=5000, overlap_ratio=0.1)
        chunks = chunker.chunk(text)

        logger.info(f"Processing {len(chunks)} chunks for document {document_id}")

        # Phase 1: Extract entities from all chunks
        all_entities: List[BaseEntity] = []
        chunk_confidences: List[tuple] = []
        document_date = None

        for chunk in chunks:
            chunk_doc_id = f"{document_id}_chunk{chunk.chunk_index}"
            try:
                entities, chunk_date = self._extract_entities(
                    text=chunk.text,
                    ocr_confidence=ocr_confidence,
                    document_id=chunk_doc_id,
                )
                all_entities.extend(entities)
                # Use first non-None document date found
                if document_date is None and chunk_date:
                    document_date = chunk_date
                # Track confidence weighted by chunk length
                if entities:
                    avg_conf = sum(e.verification.confidence for e in entities) / len(
                        entities
                    )
                    chunk_confidences.append((avg_conf, len(chunk.text)))
                else:
                    chunk_confidences.append((ocr_confidence, len(chunk.text)))
            except Exception as e:
                logger.warning(f"Chunk {chunk.chunk_index} extraction failed: {e}")
                chunk_confidences.append((0.0, len(chunk.text)))

        # Phase 2: Deduplicate entities across chunks
        merged_entities = self._merge_chunk_entities(all_entities, document_id)

        # Phase 3: Extract relations using full text + merged entities
        relations: List[Relation] = []
        if len(merged_entities) >= 2:
            relations = self._extract_relations(
                text=text,  # Use full text for relation context
                entities=merged_entities,
                document_id=document_id,
                ocr_confidence=ocr_confidence,
                document_date=document_date,
            )

        # Calculate weighted confidence by chunk length
        if chunk_confidences:
            total_len = sum(length for _, length in chunk_confidences)
            avg_confidence = (
                sum(conf * length for conf, length in chunk_confidences)
                / max(total_len, 1)
            )
        else:
            avg_confidence = ocr_confidence

        # Build reasoning
        reasoning = f"""
Chunked extraction completed using Claude API.

Processed {len(chunks)} chunks from document (text length: {len(text)} chars).
Extracted {len(all_entities)} entities (before merge), {len(merged_entities)} entities (after merge).
Extracted {len(relations)} relations.

Based on Chilean KG paper optimal chunking parameters (arXiv:2408.11975).
All entities tagged as TIER_3_AI (unverified AI extraction).
        """.strip()

        # Build metadata
        metadata = {
            "model": settings.claude_model,
            "api_version": "anthropic_v1",
            "prompt_mode": "zero_shot",
            "ocr_confidence": ocr_confidence,
            "entity_count": len(merged_entities),
            "relation_count": len(relations),
            "document_date": document_date,
            "text_length": len(text),
            "chunks_processed": len(chunks),
            "entities_before_merge": len(all_entities),
            "entities_after_merge": len(merged_entities),
            "chunk_confidences": [conf for conf, _ in chunk_confidences],
            "failed_chunks": sum(1 for conf, _ in chunk_confidences if conf == 0.0),
        }

        return LLMExtractionResult(
            entities=merged_entities,
            relations=relations,
            confidence=avg_confidence,
            reasoning=reasoning,
            metadata=metadata,
        )

    def _merge_chunk_entities(
        self,
        entities: List[BaseEntity],
        document_id: str,
    ) -> List[BaseEntity]:
        """
        Merge duplicate entities extracted from different chunks.

        Uses name-based matching (case-insensitive, ignoring titles).

        Args:
            entities: All entities from all chunks
            document_id: Main document identifier

        Returns:
            Deduplicated list of entities
        """
        merged: Dict[str, BaseEntity] = {}

        for entity in entities:
            name = getattr(entity, "name", None)
            if not name:
                continue

            # Normalize name for matching
            normalized = self._normalize_name_for_matching(name)
            entity_type = (
                entity.entity_type.value
                if hasattr(entity.entity_type, "value")
                else entity.entity_type
            )
            # Key includes entity type to avoid collapsing different entity types
            key = f"{entity_type}:{normalized}"

            if key in merged:
                existing = merged[key]
                # Merge roles if present
                if hasattr(existing, "roles") and hasattr(entity, "roles"):
                    existing.roles = list(
                        set(getattr(existing, "roles", []) + getattr(entity, "roles", []))
                    )
                # Merge alternate_names if present
                if hasattr(existing, "alternate_names") and hasattr(
                    entity, "alternate_names"
                ):
                    existing.alternate_names = list(
                        set(
                            getattr(existing, "alternate_names", [])
                            + getattr(entity, "alternate_names", [])
                        )
                    )
                # Merge list fields generically (children, siblings, etc.)
                for field_name, field_info in entity.model_fields.items():
                    if field_name in {"roles", "alternate_names", "verification"}:
                        continue
                    incoming_value = getattr(entity, field_name, None)
                    existing_value = getattr(existing, field_name, None)
                    if isinstance(incoming_value, list):
                        merged_list = list(
                            {
                                *[v for v in existing_value or [] if v is not None],
                                *[v for v in incoming_value if v is not None],
                            }
                        )
                        setattr(existing, field_name, merged_list)
                    else:
                        if (existing_value in (None, "", [])) and incoming_value not in (None, "", []):
                            setattr(existing, field_name, incoming_value)
                # Keep highest confidence verification
                if entity.verification.confidence > existing.verification.confidence:
                    existing.verification = entity.verification
            else:
                merged[key] = entity

        # Update extracted_from to use main document_id
        result = []
        for entity in merged.values():
            sources = set()
            existing_src = getattr(entity, "extracted_from", "")
            if existing_src:
                sources.update(str(existing_src).split(","))
            sources.add(document_id)
            entity.extracted_from = ",".join(sorted(s.strip() for s in sources if s))
            result.append(entity)

        logger.info(
            f"Merged {len(entities)} chunk entities into {len(result)} unique entities"
        )
        return result

    def _normalize_name_for_matching(self, name: str) -> str:
        """Normalize name for deduplication matching."""
        # Remove common Spanish titles
        name = name.lower()
        for title in ["don ", "dona ", "sr. ", "sra. ", "dr. ", "dra. "]:
            name = name.replace(title, "")
        return name.strip()

    def _mock_extract(
        self, text: str, ocr_confidence: float, document_id: str
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
            Person,
            Property,
            Location,
            VerificationTier,
            Verification,
            Relation,
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
            notes=None,
        )

        # Mock entity extraction (simulating Claude understanding the text)
        entities = []

        # Extract entities based on text content
        # Check for specific Spanish names first (for realistic test cases)
        if "Juan Pérez" in text or "Juan Perez" in text:
            person1 = Person(
                id=f"{document_id}_person_1",
                entity_type="PERSON",
                name="Juan Pérez García",
                alternate_names=["Don Juan Pérez García", "Sr. Juan Pérez García"],
                birth_date=None,
                nationality="Cuban",
                residence="Miramar, calle 5ta No. 234",
                marital_status="casado",
                roles=["seller", "owner"],
                verification=verification,
                extracted_from=document_id,
                notes="⚠️ MOCK DATA - Simulated extraction for testing (no API configured)",
            )
            entities.append(person1)

        if "María López" in text or "Maria Lopez" in text:
            person2 = Person(
                id=f"{document_id}_person_2",
                entity_type="PERSON",
                name="María López Fernández",
                alternate_names=["Doña María López Fernández"],
                birth_date=None,
                nationality="Cuban",
                residence="Vedado, Avenida 23 No. 567",
                marital_status="soltera",
                roles=["buyer"],
                verification=verification,
                extracted_from=document_id,
                notes="⚠️ MOCK DATA - Simulated extraction for testing (no API configured)",
            )
            entities.append(person2)

        # Extract Property entity
        if (
            "finca" in text.lower()
            or "propiedad" in text.lower()
            or "property" in text.lower()
        ):
            property_entity = Property(
                id=f"{document_id}_property_1",
                entity_type="PROPERTY",
                name="Finca urbana en Miramar",
                property_type="residential",
                location_id=None,
                address="calle 5ta No. 234, Miramar",
                registry_number="REG-1958-0042",
                verification=verification,
                extracted_from=document_id,
                notes="⚠️ MOCK DATA - Simulated extraction for testing (no API configured)",
            )
            entities.append(property_entity)

        # Extract Location entity
        if "Havana" in text or "Habana" in text:
            location = Location(
                id=f"{document_id}_location_1",
                entity_type="LOCATION",
                name="La Habana",
                location_type="city",
                verification=verification,
                extracted_from=document_id,
                notes="⚠️ MOCK DATA - Simulated extraction for testing (no API configured)",
            )
            entities.append(location)

        # Generic extraction fallback: if no specific entities found but text is substantial,
        # create generic mock entities (simulates LLM finding something in any text)
        if len(entities) == 0 and len(text) > 50:
            # Generic person entity
            person = Person(
                id=f"{document_id}_person_generic",
                entity_type="PERSON",
                name="Generic Person",
                alternate_names=[],
                roles=["owner"],
                verification=verification,
                extracted_from=document_id,
                notes="Generic entity extracted from OCR text for testing",
            )
            entities.append(person)

        # Mock relations
        relations = []

        if len(entities) >= 2:
            # Look for ownership relations
            persons = [e for e in entities if e.entity_type == "PERSON"]
            properties = [e for e in entities if e.entity_type == "PROPERTY"]

            if persons and properties:
                relation = Relation(
                    id=f"{document_id}_rel_1",
                    type="OWNS",
                    source_id=persons[0].id,
                    target_id=properties[0].id,
                    verification=verification,
                    document_id=document_id,
                    notes="Ownership extracted from deed text",
                )
                relations.append(relation)

        # Mock reasoning (simulating Claude's extraction logic)
        reasoning = f"""
        Analyzed OCR text (OCR confidence: {ocr_confidence:.2f}) from document.

        Extracted entities:
        - {len([e for e in entities if e.entity_type == "PERSON"])} Person(s)
        - {len([e for e in entities if e.entity_type == "PROPERTY"])} Property/Properties
        - {len([e for e in entities if e.entity_type == "LOCATION"])} Location(s)

        Identified relations: {len(relations)} ownership/transaction relations

        Combined confidence: {combined_confidence:.2f} (min of OCR {ocr_confidence:.2f} and LLM {llm_base_confidence:.2f})
        All entities tagged as TIER_3_AI (unverified AI extraction).

        This is a mocked extraction for testing purposes.
        """.strip()

        # Mock metadata
        metadata = {
            "model": "claude-llm-mocked",
            "api_version": "mocked_v1",
            "prompt_mode": "zero_shot",
            "processing_time_ms": 800,
            "ocr_confidence": ocr_confidence,
            "llm_confidence": llm_base_confidence,
            "text_length": len(text),
        }

        return LLMExtractionResult(
            entities=entities,
            relations=relations,
            confidence=combined_confidence,
            reasoning=reasoning,
            metadata=metadata,
        )
