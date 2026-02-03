"""Main processing pipeline orchestration."""

import logging
import os
import cv2
from pathlib import Path
from typing import Dict, Any

try:
    from farmer_factory.prepare import PreprocessingPipeline
except (ModuleNotFoundError, ImportError):
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from farmer_factory.prepare import PreprocessingPipeline
from farmer_factory.extract import (
    ExtractionPipeline,
    OCRService,
    VisionExtractionService,
    LLMExtractionService,
    SchemaValidator,
    translate_text,
    needs_translation,
)
from farmer_factory.structure import (
    KnowledgeGraph,
    DedupeEntityResolver,
    GraphBuilder,
    GraphExporter
)
from farmer_factory.intake import ManifestManager
from farmer_factory.intake.document_groups import load_document_groups
from farmer_factory.config.settings import settings
from .helpers import load_pdf_pages, save_extraction_json, save_ocr_text, setup_logging
from .exceptions import ProcessingError

logger = logging.getLogger(__name__)


def process_case(
    case_id: str,
    base_dir: Path = None,
    single_file: str = None,
    force_typed: bool = False,
    skip_validation: bool = False
) -> Dict[str, Any]:
    """
    Process all PDFs in case through complete pipeline.

    Pipeline stages:
    1. PDF Loading - Convert PDFs to images using pdf2image
    2. Preprocessing - Deskew, denoise, triage (prepare module)
    3. Extraction - OCR + Vision + LLM entity/relation extraction
    4. Graph Building - Entity deduplication, graph construction
    5. Export - Save graph_data.json in force-graph format

    Args:
        case_id: Case identifier (e.g., "CASE-CERESA")
        base_dir: Base directory for cases (defaults to "cases")
        single_file: Optional filename to process only one PDF (for testing)
        force_typed: Force all documents to use TYPED path (skip triage, for testing OCR)
        skip_validation: Skip validating exported graph_data.json

    Returns:
        Dictionary with processing statistics

    Raises:
        ProcessingError: If any stage fails
    """
    if base_dir is None:
        base_dir = Path('cases')

    # 1. Setup paths and logging
    case_dir = base_dir / case_id
    if not case_dir.exists():
        raise ProcessingError(f"Case directory not found: {case_dir}")

    intake_dir = case_dir / 'intake'
    preprocessed_dir = case_dir / 'preprocessed'
    extractions_dir = case_dir / 'extractions'
    output_dir = case_dir / 'output'

    # Ensure output directories exist
    preprocessed_dir.mkdir(parents=True, exist_ok=True)
    extractions_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    setup_logging(case_dir / 'processing.log')
    logger.info(f"Starting processing for case: {case_id}")

    # Initialize manifest tracker
    manifest = ManifestManager(case_id)

    # 2. Initialize pipelines once (reuse across all documents)
    logger.info("Initializing pipelines...")
    try:
        # Check if real APIs should be used
        # Check for Google Cloud credentials
        # gcloud auth saves to default location, doesn't set env var
        default_creds = Path.home() / ".config" / "gcloud" / "application_default_credentials.json"
        use_google_ocr = (
            bool(os.getenv('GOOGLE_APPLICATION_CREDENTIALS')) or
            bool(os.getenv('GOOGLE_CLOUD_PROJECT')) or
            default_creds.exists()
        )

        use_anthropic = bool(settings.anthropic_api_key)

        if use_google_ocr:
            logger.info("✓ Google Cloud credentials detected - using real OCR")
        if use_anthropic:
            logger.info("✓ Anthropic API key detected - using real extraction")

        prep_pipeline = PreprocessingPipeline()
        extract_pipeline = ExtractionPipeline(
            ocr_service=OCRService(
                use_real_api=use_google_ocr,
                credentials_path=None  # Use Application Default Credentials (gcloud auth)
            ),
            vision_service=VisionExtractionService(api_key=settings.anthropic_api_key),
            llm_service=LLMExtractionService(api_key=settings.anthropic_api_key),
            validator=SchemaValidator()
        )
    except Exception as e:
        raise ProcessingError(f"Failed to initialize pipelines: {e}")

    # 3. Initialize graph builder
    logger.info("Initializing graph builder...")
    try:
        graph = KnowledgeGraph(case_id=case_id)

        # Use dedupe-based resolver with trained models
        resolver = DedupeEntityResolver(threshold=0.5)

        builder = GraphBuilder(knowledge_graph=graph, resolver=resolver)

        # Load and apply document groups if available
        doc_groups = load_document_groups(case_dir)
        if doc_groups and doc_groups.is_confirmed():
            builder.set_document_groups(doc_groups)
            logger.info(f"Loaded {len(doc_groups.groups)} confirmed document groups")
        elif doc_groups:
            logger.info("Document groups found but not CONFIRMED, skipping grouping")
    except Exception as e:
        raise ProcessingError(f"Failed to initialize graph builder: {e}")

    # 4. Process each PDF
    pdfs = sorted(intake_dir.glob('*.pdf'))

    # Filter to single file if requested
    if single_file:
        pdfs = [p for p in pdfs if p.name == single_file]
        if not pdfs:
            raise ProcessingError(f"File not found in intake/: {single_file}")
        logger.info(f"Processing single file: {single_file}")
    else:
        if not pdfs:
            raise ProcessingError(f"No PDFs found in intake/: {intake_dir}")
        logger.info(f"Found {len(pdfs)} PDFs to process")

    for pdf_idx, pdf_path in enumerate(pdfs, 1):
        logger.info(f"[{pdf_idx}/{len(pdfs)}] Processing {pdf_path.name}...")

        # Convert PDF to images
        try:
            page_images = load_pdf_pages(pdf_path, preprocessed_dir)
            logger.info(f"  Loaded {len(page_images)} pages")
        except Exception as e:
            raise ProcessingError(f"Failed to load PDF {pdf_path.name}: {e}")

        # Process each page
        for page_idx, page_path in enumerate(page_images, 1):
            logger.info(f"  Page {page_idx}/{len(page_images)}...")

            # Preprocess
            try:
                raw_image = cv2.imread(str(page_path), cv2.IMREAD_GRAYSCALE)
                if raw_image is None:
                    raise ValueError(f"Failed to load image: {page_path}")
                preprocessed = prep_pipeline.process_page(raw_image)
            except Exception as e:
                raise ProcessingError(f"Failed preprocessing {page_path.name}: {e}")

            # Save preprocessed image
            try:
                preprocessed_path = preprocessed_dir / f"{page_path.stem}_processed.png"
                cv2.imwrite(str(preprocessed_path), preprocessed.image)
            except Exception as e:
                logger.warning(f"Failed to save preprocessed image: {e}")

            # Extract entities
            try:
                document_id = page_path.stem

                # Force TYPED path if requested (for testing OCR)
                if force_typed:
                    from farmer_factory.prepare import DocumentPath
                    preprocessed.path = DocumentPath.TYPED
                    logger.debug(f"Forcing TYPED path for {document_id}")

                extraction = extract_pipeline.extract_page(preprocessed, document_id=document_id)
            except Exception as e:
                raise ProcessingError(f"Failed extraction {page_path.stem}: {e}")

            # Save extraction JSON
            try:
                extraction_path = extractions_dir / f"{document_id}.json"
                save_extraction_json(extraction, extraction_path)
            except Exception as e:
                logger.warning(f"Failed to save extraction JSON: {e}")

            # Save OCR text as standalone .txt file
            try:
                ocr_text_path = case_dir / 'ocr' / f"{document_id}.txt"
                save_ocr_text(extraction.ocr_result, ocr_text_path)
            except Exception as e:
                logger.warning(f"Failed to save OCR text: {e}")

            # Translate OCR text if enabled and non-English (local, offline)
            try:
                if settings.translation_enabled:
                    ocr_metadata = extraction.ocr_result.metadata if extraction.ocr_result else {}
                    detected_lang = ocr_metadata.get('language', 'unknown')

                    if needs_translation(detected_lang):
                        logger.info(f"    Translating from {detected_lang} via GCP...")
                        ocr_text = extraction.ocr_result.text if extraction.ocr_result else ""
                        translated = translate_text(
                            ocr_text,
                            source_language=detected_lang,
                            target_language=settings.translation_target_language,
                        )

                        if translated:
                            translated_dir = case_dir / 'ocr_translated'
                            translated_dir.mkdir(parents=True, exist_ok=True)
                            translated_path = translated_dir / f"{document_id}.txt"
                            translated_path.write_text(translated, encoding='utf-8')
                            logger.info(f"    Translation saved: {translated_path.name}")
                        else:
                            logger.warning("    Translation unavailable (missing GCP credentials?)")
            except Exception as e:
                logger.warning(f"Failed to translate OCR text: {e}")

            # Ensure document_id is in processing_metadata for grouping lookup
            if extraction.processing_metadata is not None:
                extraction.processing_metadata.setdefault("document_id", document_id)

            # Add to graph (with auto-deduplication)
            try:
                builder.add_extraction(extraction)
            except Exception as e:
                raise ProcessingError(f"Failed adding to graph {document_id}: {e}")

            logger.info(f"  Page {page_idx}/{len(page_images)} ✓")

        # Track document in manifest
        manifest.add_document(
            document_id=pdf_path.stem,
            filename=pdf_path.name,
            status="success",
            part_count=1,
            page_count=len(page_images),
        )

    # 5. Export graph
    logger.info("Exporting graph...")
    try:
        exporter = GraphExporter(knowledge_graph=graph)
        exporter.save(output_dir / 'graph_data.json', factory_version="1.0.0")
    except Exception as e:
        raise ProcessingError(f"Failed to export graph: {e}")

    # 5a. Generate/update entity merge files (DRAFT)
    try:
        from farmer_factory.structure.merge.writer import write_entity_groups, write_cross_type_relations
        from farmer_factory.structure.merge.engine import apply_merges

        # Collect dedupe clusters from the resolver's partition results
        # For now, generate merge files from the graph's merged entities
        # The builder tracks merges; we record them as DRAFT merge authority files
        _generate_merge_files(case_dir, graph, builder)

        # Apply any previously CONFIRMED merges (from prior analyst review)
        entity_groups_dir = case_dir / "entity_groups"
        if entity_groups_dir.exists() and any(entity_groups_dir.iterdir()):
            try:
                apply_merges(case_dir, include_drafts=False,
                            output_path=output_dir / 'graph_data.json')
                logger.info("Applied confirmed merges to graph")
            except FileNotFoundError:
                pass  # No graph yet, skip
            except Exception as e:
                logger.warning(f"Failed to apply confirmed merges: {e}")
    except Exception as e:
        logger.warning(f"Merge file generation failed (non-fatal): {e}")

    # 5b. Save manifest
    manifest.save_manifest(case_dir / 'manifest.json')
    logger.info(f"Manifest saved: {case_dir / 'manifest.json'}")

    # 5c. Validate export output
    if not skip_validation:
        try:
            import json
            from farmer_factory.structure.schema import GraphExport

            graph_file = output_dir / 'graph_data.json'
            with open(graph_file, 'r', encoding='utf-8') as f:
                export_data = json.load(f)

            GraphExport.model_validate(export_data)
        except Exception as e:
            raise ProcessingError(f"Export validation failed: {e}")

    # 6. Get summary statistics
    stats = builder.processing_stats
    logger.info("Processing complete!")
    logger.info(f"Documents processed: {stats['documents_processed']}")
    logger.info(f"Entities extracted:  {stats['entities_extracted']}")
    logger.info(f"Entities merged:     {stats['entities_merged']}")
    logger.info(f"Relations added:     {stats['relations_added']}")

    return stats


def rebuild_graph(
    case_id: str,
    base_dir: Path = None,
    skip_validation: bool = False,
) -> Dict[str, Any]:
    """Rebuild graph from existing extractions without OCR or LLM calls.

    Loads all extraction JSON files, runs them through the graph builder
    with current dedupe models, exports graph_data.json, generates merge
    files, and applies confirmed merges.

    Use after retraining dedupe models to see improved deduplication
    without re-running the expensive OCR/extraction pipeline.

    Args:
        case_id: Case identifier (e.g., "TEST-CERESA")
        base_dir: Base directory for cases (defaults to "cases")
        skip_validation: Skip validating exported graph_data.json

    Returns:
        Dictionary with processing statistics
    """
    import json
    from farmer_factory.structure.schema import BaseEntity, Relation

    if base_dir is None:
        base_dir = Path("cases")

    case_dir = base_dir / case_id
    if not case_dir.exists():
        raise ProcessingError(f"Case directory not found: {case_dir}")

    extractions_dir = case_dir / "extractions"
    output_dir = case_dir / "output"

    if not extractions_dir.exists():
        raise ProcessingError(f"No extractions directory: {extractions_dir}")

    extraction_files = sorted(extractions_dir.glob("*.json"))
    if not extraction_files:
        raise ProcessingError(f"No extraction JSON files in: {extractions_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Rebuilding graph for case: {case_id}")
    logger.info(f"Found {len(extraction_files)} extraction files")

    # Initialize graph builder with current dedupe models
    graph = KnowledgeGraph(case_id=case_id)
    resolver = DedupeEntityResolver(threshold=0.5)
    builder = GraphBuilder(knowledge_graph=graph, resolver=resolver)

    # Load and apply document groups if available
    doc_groups = load_document_groups(case_dir)
    if doc_groups and doc_groups.is_confirmed():
        builder.set_document_groups(doc_groups)
        logger.info(f"Loaded {len(doc_groups.groups)} confirmed document groups")

    # Load each extraction and feed into graph builder
    for ext_file in extraction_files:
        try:
            with open(ext_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Reconstruct entities from JSON
            entities = []
            for e_data in data.get("entities", []):
                entity_type = e_data.get("entity_type", "")
                entity_cls = _get_entity_class(entity_type)
                if entity_cls:
                    try:
                        entities.append(entity_cls.model_validate(e_data))
                    except Exception as e:
                        logger.warning(f"Failed to parse entity in {ext_file.name}: {e}")

            # Reconstruct relations from JSON
            relations = []
            for r_data in data.get("relations", []):
                try:
                    relations.append(Relation.model_validate(r_data))
                except Exception as e:
                    logger.warning(f"Failed to parse relation in {ext_file.name}: {e}")

            # Build a minimal ExtractionResult
            from farmer_factory.extract.pipeline import ExtractionResult
            from farmer_factory.prepare import DocumentPath

            # Inject document_id from filename so _create_document_entity
            # can identify the source file even when entities list is empty
            proc_meta = data.get("processing_metadata", {})
            proc_meta.setdefault("document_id", ext_file.stem)

            extraction = ExtractionResult(
                entities=entities,
                relations=relations,
                ocr_result=None,
                confidence_scores=data.get("confidence_scores", {}),
                path=DocumentPath.TYPED,
                processing_metadata=proc_meta,
            )
            builder.add_extraction(extraction)
            logger.info(f"  Loaded {ext_file.name}: {len(entities)} entities, {len(relations)} relations")

        except Exception as e:
            logger.warning(f"Failed to load {ext_file.name}: {e}")

    # Export graph
    logger.info("Exporting graph...")
    exporter = GraphExporter(knowledge_graph=graph)
    exporter.save(output_dir / "graph_data.json", factory_version="1.0.0")

    # Generate merge files (writer preserves CONFIRMED groups) and apply confirmed merges
    entity_groups_dir = case_dir / "entity_groups"
    try:
        _generate_merge_files(case_dir, graph, builder)
        if entity_groups_dir.exists() and any(entity_groups_dir.iterdir()):
            try:
                from farmer_factory.structure.merge.engine import apply_merges
                apply_merges(case_dir, include_drafts=False,
                            output_path=output_dir / "graph_data.json")
                logger.info("Applied confirmed merges to graph")
            except FileNotFoundError:
                pass
            except Exception as e:
                logger.warning(f"Failed to apply confirmed merges: {e}")
    except Exception as e:
        logger.warning(f"Merge file generation failed (non-fatal): {e}")

    # Validate
    if not skip_validation:
        try:
            from farmer_factory.structure.schema import GraphExport
            graph_file = output_dir / "graph_data.json"
            with open(graph_file, "r", encoding="utf-8") as f:
                export_data = json.load(f)
            GraphExport.model_validate(export_data)
        except Exception as e:
            raise ProcessingError(f"Export validation failed: {e}")

    stats = builder.processing_stats
    logger.info("Graph rebuild complete!")
    logger.info(f"Documents processed: {stats['documents_processed']}")
    logger.info(f"Entities extracted:  {stats['entities_extracted']}")
    logger.info(f"Entities merged:     {stats['entities_merged']}")
    logger.info(f"Relations added:     {stats['relations_added']}")

    return stats


def _get_entity_class(entity_type: str):
    """Get the Pydantic entity class for a given entity type string."""
    from farmer_factory.structure.schema import (
        Person, Property, Organization, Location, Document,
    )
    return {
        "PERSON": Person,
        "PROPERTY": Property,
        "ORGANIZATION": Organization,
        "LOCATION": Location,
        "DOCUMENT": Document,
    }.get(entity_type)


def _generate_merge_files(
    case_dir: Path,
    graph: "KnowledgeGraph",
    builder: "GraphBuilder",
) -> None:
    """Generate DRAFT entity merge files from the current graph state.

    Extracts clusters of merged entities from the graph builder's stats
    and writes them as DRAFT entity_groups/*.yaml files.
    """
    from collections import defaultdict
    from farmer_factory.structure.merge.writer import write_entity_groups, write_cross_type_relations

    # Build clusters from builder's merge_log
    # merge_log entries: (absorbed_id, absorbed_name, canonical_id, canonical_name, confidence)
    # Group by canonical_id
    clusters_by_canonical: Dict[str, list] = defaultdict(list)
    for absorbed_id, absorbed_name, canonical_id, canonical_name, confidence in builder.merge_log:
        clusters_by_canonical[canonical_id].append(
            (absorbed_id, absorbed_name, confidence)
        )

    # Determine entity type for each canonical from the graph
    clusters_by_type: Dict[str, list] = defaultdict(list)
    canonical_names: Dict[str, str] = {}
    for canonical_id, members in clusters_by_canonical.items():
        node_data = graph.graph.nodes.get(canonical_id)
        if not node_data:
            continue
        etype = node_data.get("entity_type", "")
        name = node_data.get("name", "")
        if isinstance(name, list):
            name = name[0] if name else ""
        canonical_names[canonical_id] = str(name)
        # Build cluster: canonical first (conf 1.0), then absorbed members
        cluster = [(canonical_id, str(name), 1.0)]
        for absorbed_id, absorbed_name, conf in members:
            cluster.append((absorbed_id, str(absorbed_name), conf))
        clusters_by_type[etype].append(cluster)

    # Identify all entity IDs that participated in a merge (canonical or absorbed)
    merged_ids: set = set()
    for canonical_id, members in clusters_by_canonical.items():
        merged_ids.add(canonical_id)
        for absorbed_id, _, _ in members:
            merged_ids.add(absorbed_id)

    # Group all graph entities by type; singletons are those not in any merge
    entities_by_type: Dict[str, list] = defaultdict(list)
    for node_id, node_data in graph.graph.nodes(data=True):
        etype = node_data.get("entity_type", "")
        if node_id not in merged_ids:
            name = node_data.get("name", "")
            if isinstance(name, list):
                name = name[0] if name else ""
            entities_by_type[etype].append((node_id, str(name)))

    # Write merge files per entity type
    for entity_type in ("PERSON", "PROPERTY", "ORGANIZATION", "LOCATION"):
        clusters = clusters_by_type.get(entity_type, [])
        singletons = entities_by_type.get(entity_type, [])
        try:
            write_entity_groups(
                case_dir=case_dir,
                entity_type=entity_type,
                clusters=clusters,
                singletons=singletons,
            )
            if clusters:
                logger.info(
                    f"Wrote {len(clusters)} merge group(s) for {entity_type}"
                )
        except Exception as e:
            logger.warning(f"Failed to write {entity_type} merge file: {e}")

    # Collect cross-type relations from graph
    cross_relations = []
    for source, target, _key, edge_data in graph.graph.edges(keys=True, data=True):
        source_type = graph.graph.nodes[source].get("entity_type", "")
        target_type = graph.graph.nodes[target].get("entity_type", "")
        if source_type != target_type:
            source_name = graph.graph.nodes[source].get("name", "")
            target_name = graph.graph.nodes[target].get("name", "")
            if isinstance(source_name, list):
                source_name = source_name[0] if source_name else ""
            if isinstance(target_name, list):
                target_name = target_name[0] if target_name else ""
            cross_relations.append({
                "source_id": source,
                "source_name": str(source_name),
                "target_id": target,
                "target_name": str(target_name),
                "relation_type": edge_data.get("relation_type", ""),
                "date": edge_data.get("date"),
                "source": "extraction",
            })

    if cross_relations:
        try:
            write_cross_type_relations(case_dir, cross_relations)
        except Exception as e:
            logger.warning(f"Failed to write cross-type relations: {e}")
