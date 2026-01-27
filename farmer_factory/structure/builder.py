"""Graph builder for constructing knowledge graph from extraction results."""

from datetime import datetime
from typing import List, Dict, Any, TYPE_CHECKING
import logging
from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.structure.resolver import DedupeEntityResolver
from farmer_factory.structure.schema import Document, Verification, VerificationTier
from farmer_factory.structure.postprocessor import GraphPostProcessor

if TYPE_CHECKING:
    from farmer_factory.extract import ExtractionResult

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Orchestrates graph construction from extraction results."""

    def __init__(self, knowledge_graph: KnowledgeGraph, resolver: DedupeEntityResolver):
        """
        Initialize graph builder.

        Args:
            knowledge_graph: KnowledgeGraph instance to build into
            resolver: DedupeEntityResolver for ML-based deduplication
        """
        self.graph = knowledge_graph
        self.resolver = resolver
        self.processing_stats: Dict[str, int] = {
            "documents_processed": 0,
            "entities_extracted": 0,
            "entities_merged": 0,
            "relations_added": 0
        }

    def add_extraction(self, extraction: "ExtractionResult") -> None:
        """
        Add entities and relations from extraction result.

        Process:
        1. Create DOCUMENT entity for the source document
        2. Resolve and add entities (with deduplication)
        3. Add relations (after entities exist)
        4. Update processing stats

        Args:
            extraction: ExtractionResult from extract module
        """
        # Track document processing
        self.processing_stats["documents_processed"] += 1

        # Create DOCUMENT entity for this source document
        self._create_document_entity(extraction)

        # Track ID remappings when entities are merged
        id_remapping: Dict[str, str] = {}

        # Process entities
        for entity in extraction.entities:
            self.processing_stats["entities_extracted"] += 1

            # Check if similar entity exists
            match = self.resolver.find_similar_entity(entity, self.graph)

            if match:
                similar_id, match_confidence = match
                # Merge with existing entity
                existing_data = self.graph.get_entity(similar_id)
                merged_data = self.resolver.merge_entities(
                    existing_data,
                    entity,
                    match_confidence=match_confidence
                )

                # Update graph node
                self.graph.graph.nodes[similar_id].update(merged_data)

                # Track that this entity's ID was remapped
                id_remapping[entity.id] = similar_id

                self.processing_stats["entities_merged"] += 1
                logger.info(f"Merged entity {entity.id} into {similar_id}")
            else:
                # Add as new entity
                self.graph.add_entity(entity)
                logger.info(f"Added new entity {entity.id}")

        # Process relations, remapping IDs if needed
        for relation in extraction.relations:
            # Remap source and target IDs if they were merged
            remapped_source = id_remapping.get(relation.source_id, relation.source_id)
            remapped_target = id_remapping.get(relation.target_id, relation.target_id)

            # Create a new relation dict with remapped IDs if needed
            if remapped_source != relation.source_id or remapped_target != relation.target_id:
                from pydantic import ValidationError
                try:
                    # Create new relation with remapped IDs
                    relation_dict = relation.model_dump()
                    relation_dict["source_id"] = remapped_source
                    relation_dict["target_id"] = remapped_target
                    # Recreate relation object with remapped IDs
                    relation = relation.__class__(**relation_dict)
                    logger.debug(f"Remapped relation {relation.id}: {relation.source_id} -> {relation.target_id}")
                except (ValidationError, Exception) as e:
                    logger.warning(f"Failed to remap relation {relation.id}: {e}")
                    continue

            try:
                self.graph.add_relation(relation)
                self.processing_stats["relations_added"] += 1
                logger.info(f"Added relation {relation.id}: {relation.type}")
            except ValueError as e:
                logger.warning(f"Failed to add relation {relation.id}: {e}")
                # Skip invalid relations, continue processing

    def _create_document_entity(self, extraction: "ExtractionResult") -> None:
        """
        Create a DOCUMENT entity for the source document.

        Args:
            extraction: ExtractionResult containing document metadata
        """
        # Extract document info from processing metadata
        metadata = extraction.processing_metadata or {}
        ocr_metadata = metadata.get("ocr_metadata", {})

        # Get document ID from the first entity's extracted_from field, or construct from metadata
        doc_id = None
        if extraction.entities:
            doc_id = extraction.entities[0].extracted_from

        if not doc_id:
            # Fallback: try to construct from metadata
            doc_id = metadata.get("document_id", f"doc_{self.processing_stats['documents_processed']}")

        # Check if document already exists (avoid duplicates for multi-page docs)
        if self.graph.get_entity(doc_id):
            logger.debug(f"Document entity already exists: {doc_id}")
            return

        # Determine document type from ID pattern or metadata
        doc_type = self._infer_document_type(doc_id)

        # Extract date from OCR metadata if available
        doc_date = metadata.get("llm_metadata", {}).get("document_date")

        # Calculate confidence from extraction
        confidence_scores = extraction.confidence_scores or {}
        confidence = confidence_scores.get("combined_confidence", 0.8)

        # Create DOCUMENT entity
        doc_entity = Document(
            id=doc_id,
            verification=Verification(
                tier=VerificationTier.TIER_3_AI,
                confidence=confidence,
                notes="Document entity auto-created from extraction"
            ),
            extracted_from=doc_id,
            title=self._extract_title_from_id(doc_id),
            document_type=doc_type,
            date=doc_date,
            file_path=doc_id,  # Use doc_id as file reference
            page_count=1,
            ocr_text=extraction.ocr_result.text if extraction.ocr_result else None,
        )

        self.graph.add_entity(doc_entity)
        self.processing_stats["entities_extracted"] += 1
        logger.info(f"Created DOCUMENT entity: {doc_id}")

    def _infer_document_type(self, doc_id: str) -> str:
        """Infer document type from document ID patterns."""
        doc_id_lower = doc_id.lower()

        if "will" in doc_id_lower or "testament" in doc_id_lower:
            return "Will/Testament"
        elif "deed" in doc_id_lower or "escritura" in doc_id_lower:
            return "Deed"
        elif "credit" in doc_id_lower or "loan" in doc_id_lower:
            return "Financial Document"
        elif "transfer" in doc_id_lower or "trans" in doc_id_lower:
            return "Property Transfer"
        elif "hacienda" in doc_id_lower or "finca" in doc_id_lower:
            return "Property Document"
        elif "millage" in doc_id_lower or "survey" in doc_id_lower:
            return "Survey Document"
        else:
            return "Historical Document"

    def _extract_title_from_id(self, doc_id: str) -> str:
        """Extract a readable title from document ID."""
        # Remove page suffix if present
        title = doc_id.replace("_page_0", "").replace("_page_1", "")
        # Replace underscores with spaces
        title = title.replace("_", " ")
        # Remove file extensions
        for ext in [".pdf", ".jpg", ".png", ".1pdf", ".2pdf", ".3pdf"]:
            title = title.replace(ext, "")
        return title.strip()

    def build_from_document_batch(
        self,
        extractions: List["ExtractionResult"]
    ) -> None:
        """
        Process multiple document extractions.

        Args:
            extractions: List of ExtractionResult objects
        """
        logger.info(f"Processing batch of {len(extractions)} documents")

        for extraction in extractions:
            self.add_extraction(extraction)

        # Post-process graph to remove redundancies
        postprocessor = GraphPostProcessor()
        cleanup_stats = postprocessor.remove_redundant_edges(self.graph)
        self.processing_stats.update(cleanup_stats)

        logger.info(
            f"Batch complete: {self.processing_stats['entities_extracted']} entities extracted, "
            f"{self.processing_stats['entities_merged']} merged, "
            f"{self.processing_stats['relations_added']} relations added, "
            f"{cleanup_stats['edges_removed']} redundant edges removed"
        )
