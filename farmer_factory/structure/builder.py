"""Graph builder for constructing knowledge graph from extraction results."""

from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, TYPE_CHECKING
import logging
from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.structure.resolver import DedupeEntityResolver
from farmer_factory.structure.schema import Document, Verification, VerificationTier
from farmer_factory.structure.postprocessor import GraphPostProcessor

if TYPE_CHECKING:
    from farmer_factory.extract import ExtractionResult
    from farmer_factory.intake.document_groups import DocumentGroupsConfig

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
        self.document_groups: Optional["DocumentGroupsConfig"] = None
        self._file_to_group_id: Dict[str, str] = {}  # Maps filename to group doc ID
        # Records (absorbed_id, absorbed_name, canonical_id, canonical_name, confidence)
        self.merge_log: List[tuple] = []
        self.processing_stats: Dict[str, int] = {
            "documents_processed": 0,
            "entities_extracted": 0,
            "entities_merged": 0,
            "relations_added": 0,
            "document_groups_used": 0,
        }

    def set_document_groups(self, config: "DocumentGroupsConfig") -> None:
        """
        Set document groupings configuration.

        Args:
            config: DocumentGroupsConfig with confirmed groupings
        """
        self.document_groups = config

        # Build file-to-group mapping for quick lookups
        self._file_to_group_id = {}
        for group in config.groups:
            group_doc_id = f"doc_{group.id}"
            for filename in group.files:
                self._file_to_group_id[filename] = group_doc_id
                # Also map without extension for flexibility
                stem = Path(filename).stem
                self._file_to_group_id[stem] = group_doc_id

        logger.info(
            f"Document groups configured: {len(config.groups)} groups, "
            f"{len(self._file_to_group_id)} file mappings"
        )

    def _get_document_id_for_file(self, file_ref: str) -> str:
        """
        Get the document ID for a file, using group ID if part of a group.

        Args:
            file_ref: Filename or document reference

        Returns:
            Document ID (group ID if grouped, original ID otherwise)
        """
        if not self.document_groups:
            return file_ref

        # Try exact match first
        if file_ref in self._file_to_group_id:
            return self._file_to_group_id[file_ref]

        # Try stem (without extension)
        stem = Path(file_ref).stem
        if stem in self._file_to_group_id:
            return self._file_to_group_id[stem]

        # Try common variations
        for suffix in ["_page_0", "_page_1", "_page_2"]:
            base = file_ref.replace(suffix, "")
            if base in self._file_to_group_id:
                return self._file_to_group_id[base]

        return file_ref

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

        # Remap extracted_from to group document ID if applicable
        group_doc_id = None
        if extraction.entities:
            original_ref = extraction.entities[0].extracted_from
            group_doc_id = self._get_document_id_for_file(original_ref)

        # Process entities
        for entity in extraction.entities:
            # Update extracted_from to reference group document if applicable
            if group_doc_id and group_doc_id != entity.extracted_from:
                # Create updated entity with remapped extracted_from
                entity_dict = entity.model_dump()
                entity_dict["extracted_from"] = group_doc_id
                entity = entity.__class__(**entity_dict)
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

                # Record merge decision for entity group files
                canonical_name = existing_data.get("name", "")
                if isinstance(canonical_name, list):
                    canonical_name = canonical_name[0] if canonical_name else ""
                absorbed_name = entity.name if hasattr(entity, "name") else ""
                self.merge_log.append((
                    entity.id, str(absorbed_name),
                    similar_id, str(canonical_name),
                    match_confidence,
                ))

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

        If the file is part of a document group, creates/updates a unified
        DOCUMENT entity for the group instead of individual file entities.

        Args:
            extraction: ExtractionResult containing document metadata
        """
        # Extract document info from processing metadata
        metadata = extraction.processing_metadata or {}
        ocr_metadata = metadata.get("ocr_metadata", {})

        # Get original file reference from the first entity's extracted_from field
        original_file_ref = None
        if extraction.entities:
            original_file_ref = extraction.entities[0].extracted_from

        if not original_file_ref:
            original_file_ref = metadata.get(
                "document_id", f"doc_{self.processing_stats['documents_processed']}"
            )

        # Determine the actual document ID (may be group ID)
        doc_id = self._get_document_id_for_file(original_file_ref)
        is_grouped = doc_id != original_file_ref

        # Check if document already exists (avoid duplicates for multi-page/grouped docs)
        existing_doc = self.graph.get_entity(doc_id)
        if existing_doc:
            # For grouped documents, update source_files list
            if is_grouped and "source_files" in existing_doc:
                if original_file_ref not in existing_doc["source_files"]:
                    existing_doc["source_files"].append(original_file_ref)
                    existing_doc["page_count"] = len(existing_doc["source_files"])
                    self.graph.graph.nodes[doc_id].update(existing_doc)
                    logger.debug(f"Updated grouped document {doc_id} with file {original_file_ref}")
            else:
                logger.debug(f"Document entity already exists: {doc_id}")
            return

        # Get group metadata if available
        group_name = None
        group_doc_type = None
        group_date = None
        source_files = [original_file_ref]

        if is_grouped and self.document_groups:
            for group in self.document_groups.groups:
                if f"doc_{group.id}" == doc_id:
                    group_name = group.name
                    group_doc_type = group.document_type
                    group_date = group.date
                    source_files = group.files.copy()
                    self.processing_stats["document_groups_used"] += 1
                    break

        # Determine document type from group config, ID pattern, or metadata
        doc_type = group_doc_type or self._infer_document_type(doc_id)

        # Extract date from group config, OCR metadata, or LLM metadata
        doc_date = group_date or metadata.get("llm_metadata", {}).get("document_date")

        # Calculate confidence from extraction
        confidence_scores = extraction.confidence_scores or {}
        confidence = confidence_scores.get("combined_confidence", 0.8)

        # Build title
        if group_name:
            title = group_name
        else:
            title = self._extract_title_from_id(doc_id)

        # Build notes
        notes = "Document entity auto-created from extraction"
        if is_grouped:
            notes = f"Unified document from {len(source_files)} files"

        # Create DOCUMENT entity
        doc_entity = Document(
            id=doc_id,
            verification=Verification(
                tier=VerificationTier.TIER_3_AI,
                confidence=confidence,
                notes=notes,
            ),
            extracted_from=doc_id,
            title=title,
            document_type=doc_type,
            date=doc_date,
            file_path=source_files[0] if source_files else doc_id,
            page_count=len(source_files),
            ocr_text=extraction.ocr_result.text if extraction.ocr_result else None,
        )

        self.graph.add_entity(doc_entity)

        # Store source_files as additional node attribute for grouped docs
        if is_grouped and len(source_files) > 1:
            self.graph.graph.nodes[doc_id]["source_files"] = source_files

        self.processing_stats["entities_extracted"] += 1
        logger.info(f"Created DOCUMENT entity: {doc_id}" + (" (grouped)" if is_grouped else ""))

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
