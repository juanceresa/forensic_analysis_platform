#!/usr/bin/env python3
"""
Civic Table - Factory CLI
Command-line interface for document processing pipeline.
"""

import sys
from pathlib import Path

# Add the parent directory to sys.path to allow absolute imports of farmer_factory
current_dir = Path(__file__).resolve().parent
if current_dir.name == "farmer_factory":
    root_dir = current_dir.parent
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))

import click
import logging
from datetime import datetime

# Load .env file if it exists
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # python-dotenv not installed, env vars must be set manually
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_domain(domain_code: str) -> None:
    """Set up the active domain and refresh type enums.

    Args:
        domain_code: Domain identifier (e.g., "cuban_property")

    Raises:
        click.ClickException: If domain not found
    """
    from farmer_factory.domains import domain_registry
    from farmer_factory.structure.schema import refresh_type_enums

    # List available domains for validation
    available = domain_registry.list_available_domains()
    if domain_code not in available:
        raise click.ClickException(
            f"Unknown domain '{domain_code}'. Available: {', '.join(available)}"
        )

    # Set active domain
    domain_registry.set_active(domain_code)
    logger.info(f"Domain set to: {domain_code}")

    # Refresh enums to match domain config
    refresh_type_enums()
    logger.debug("Type enums refreshed from domain config")


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Civic Table Factory - Document Processing Pipeline"""
    pass


@cli.command()
@click.option("--id", "case_id", required=True, help="Case ID (e.g., CASE-001)")
@click.option("--name", required=True, help='Case name (e.g., "Ceresa Family Archive")')
@click.option("--family", required=True, help='Family name (e.g., "Ceresa")')
@click.option(
    "--domain",
    default="cuban_property",
    help="Domain configuration to use (default: cuban_property)",
)
def create_case(case_id: str, name: str, family: str, domain: str):
    """Create a new case directory structure."""
    # Validate domain exists
    from farmer_factory.domains import domain_registry

    available = domain_registry.list_available_domains()
    if domain not in available:
        raise click.ClickException(
            f"Unknown domain '{domain}'. Available: {', '.join(available)}"
        )

    logger.info(f"Creating case: {case_id}")

    # Create directory structure
    case_dir = Path("cases") / case_id

    if case_dir.exists():
        logger.error(f"Case {case_id} already exists")
        raise click.ClickException(f"Case {case_id} already exists")

    # Create subdirectories
    (case_dir / "intake").mkdir(parents=True)
    (case_dir / "preprocessed").mkdir(parents=True)
    (case_dir / "ocr").mkdir(parents=True)
    (case_dir / "output").mkdir(parents=True)

    # Create case metadata file with domain
    metadata = {
        "id": case_id,
        "name": name,
        "family": family,
        "domain": domain,
        "created_at": datetime.now().isoformat(),
        "status": "INTAKE",
    }

    import json

    with open(case_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"✓ Case created at: {case_dir}")
    logger.info("  Next steps:")
    logger.info(f"    1. Copy PDFs to: {case_dir / 'intake'}/")
    logger.info(f"    2. Run: python cli.py process {case_id} --domain {domain}")

    click.echo(f"\n✓ Case {case_id} created successfully (domain: {domain})")


@cli.command("detect-groups")
@click.argument("case_id")
@click.option("--force", is_flag=True, help="Overwrite existing document_groups.yaml")
def detect_groups(case_id: str, force: bool):
    """Detect multi-part documents and generate groupings for review.

    Scans intake/ folder for filename patterns that suggest multi-part documents
    (e.g., escritura_125_1.pdf, escritura_125_2.pdf) and generates a draft
    document_groups.yaml for analyst review.

    Example:
        python cli.py detect-groups TEST-CERESA

    After running:
        1. Review cases/TEST-CERESA/document_groups.yaml
        2. Edit group names and verify groupings are correct
        3. Change status from DRAFT to CONFIRMED
        4. Run: python cli.py process TEST-CERESA
    """
    from farmer_factory.intake.document_groups import (
        detect_groups as _detect_groups,
        generate_draft_yaml,
        load_document_groups,
    )

    case_dir = Path("cases") / case_id
    intake_dir = case_dir / "intake"

    if not case_dir.exists():
        raise click.ClickException(f"Case not found: {case_id}")

    if not intake_dir.exists():
        raise click.ClickException(f"Intake directory not found: {intake_dir}")

    # Check for existing file
    yaml_path = case_dir / "document_groups.yaml"
    if yaml_path.exists() and not force:
        existing = load_document_groups(case_dir)
        if existing and existing.is_confirmed():
            raise click.ClickException(
                f"document_groups.yaml already exists and is CONFIRMED.\n"
                f"Use --force to overwrite (this will reset to DRAFT)."
            )
        elif existing:
            click.echo(f"⚠️  Existing DRAFT file will be overwritten.")

    # Get PDF files
    pdf_files = sorted([f.name for f in intake_dir.glob("*.pdf")])

    if not pdf_files:
        raise click.ClickException(f"No PDF files found in {intake_dir}/")

    click.echo(f"\nScanning {len(pdf_files)} PDF files in {intake_dir}/...")

    # Detect groups
    groups, standalone = _detect_groups(pdf_files)

    # Generate YAML
    yaml_path = generate_draft_yaml(case_dir, groups, standalone)

    # Report results
    click.echo(f"\n{'=' * 60}")
    click.echo("Document Group Detection Results")
    click.echo(f"{'=' * 60}")

    if groups:
        click.echo(f"\n📁 Detected {len(groups)} document group(s):\n")
        for base_name, files in sorted(groups.items()):
            click.echo(f"  {base_name}:")
            for f in files:
                click.echo(f"    - {f}")
    else:
        click.echo("\n📄 No multi-part documents detected.")

    if standalone:
        click.echo(f"\n📄 {len(standalone)} standalone file(s)")

    click.echo(f"\n✓ Draft written to: {yaml_path}")
    click.echo("\n" + "=" * 60)
    click.echo("NEXT STEPS:")
    click.echo("=" * 60)
    click.echo(f"\n  1. Review: {yaml_path}")
    click.echo("  2. Edit group names to be descriptive")
    click.echo("  3. Verify groupings are correct")
    click.echo("  4. Change 'status: DRAFT' to 'status: CONFIRMED'")
    click.echo(f"  5. Run: python cli.py process {case_id}")


@cli.command()
@click.argument("case_id")
@click.option("--verbose", is_flag=True, help="Verbose output")
@click.option(
    "--file", "single_file", help="Process only this PDF file from intake/ directory"
)
@click.option(
    "--force-typed",
    is_flag=True,
    help="Force all documents to use OCR path (ignore triage)",
)
@click.option("--skip-validation", is_flag=True, help="Skip graph_data.json validation")
@click.option(
    "--domain",
    default="cuban_property",
    help="Domain configuration to use (default: cuban_property)",
)
def process(
    case_id: str,
    verbose: bool,
    single_file: str,
    force_typed: bool,
    skip_validation: bool,
    domain: str,
):
    """Process case documents through the pipeline."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Set up domain configuration
    setup_domain(domain)

    # Check for document groups configuration
    case_dir = Path("cases") / case_id
    from farmer_factory.intake.document_groups import load_document_groups

    doc_groups = load_document_groups(case_dir)
    if doc_groups and not doc_groups.is_confirmed():
        click.echo("\n❌ Document groups are in DRAFT status.")
        click.echo(f"\nPlease review and confirm: {case_dir / 'document_groups.yaml'}")
        click.echo("\nTo proceed:")
        click.echo("  1. Open the file and verify groupings are correct")
        click.echo("  2. Change 'status: DRAFT' to 'status: CONFIRMED'")
        click.echo(f"  3. Re-run: python cli.py process {case_id}")
        click.echo("\nOr delete document_groups.yaml to process without groupings.")
        raise click.ClickException("Document groups not confirmed")

    if doc_groups and doc_groups.is_confirmed():
        logger.info(
            f"Using document groups: {len(doc_groups.groups)} groups, "
            f"{len(doc_groups.standalone)} standalone"
        )

    if single_file:
        logger.info(f"Processing case: {case_id}, file: {single_file}")
    else:
        logger.info(f"Processing case: {case_id}")

    if force_typed:
        logger.info("Forcing TYPED path (skipping triage)")
    if skip_validation:
        logger.info("Skipping graph export validation")

    # Import here to avoid circular imports
    try:
        from farmer_factory.processing import process_case, ProcessingError
    except ModuleNotFoundError:
        from processing import process_case, ProcessingError

    try:
        # Run processing pipeline
        stats = process_case(
            case_id,
            single_file=single_file,
            force_typed=force_typed,
            skip_validation=skip_validation,
        )

        # Print summary
        click.echo("\n" + "=" * 60)
        click.echo("Processing Complete!")
        click.echo("=" * 60)
        click.echo(f"Documents processed: {stats['documents_processed']}")
        click.echo(f"Entities extracted:  {stats['entities_extracted']}")
        click.echo(f"Entities merged:     {stats['entities_merged']}")
        click.echo(f"Relations added:     {stats['relations_added']}")

        output_path = Path("cases") / case_id / "output" / "graph_data.json"
        click.echo(f"\nGraph saved to: {output_path}")

        # Generate case narrative (final pipeline step)
        try:
            from farmer_factory.narrative import CaseNarrativeGenerator
            from farmer_factory.structure.graph import KnowledgeGraph

            graph = KnowledgeGraph.load(output_path)
            generator = CaseNarrativeGenerator()
            output_dir = Path("cases") / case_id / "output"
            narrative_path = generator.generate_and_save(case_id, graph, output_dir)
            click.echo(f"Narrative saved to: {narrative_path}")
        except Exception as e:
            logger.warning(f"Narrative generation failed (non-fatal): {e}")
            click.echo(f"\n⚠️  Narrative generation skipped: {e}", err=True)

    except ProcessingError as e:
        logger.error(f"Processing failed: {e}")
        click.echo(f"\n❌ Processing failed: {e}", err=True)
        case_dir = Path("cases") / case_id
        if case_dir.exists():
            click.echo(f"Check detailed logs: {case_dir}/processing.log")
        raise click.ClickException(str(e))

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        click.echo(f"\n❌ Unexpected error: {e}", err=True)
        case_dir = Path("cases") / case_id
        if case_dir.exists():
            click.echo(f"Check detailed logs: {case_dir}/processing.log")
        raise click.ClickException(str(e))


@cli.command("generate-narrative")
@click.argument("case_id")
@click.option("--max-cost", default=2.0, help="Max generation cost in USD (default: 2.0)")
@click.option("--model", default="sonnet", type=click.Choice(["haiku", "sonnet"]), help="Primary model")
@click.option(
    "--domain",
    default="cuban_property",
    help="Domain configuration to use (default: cuban_property)",
)
def generate_narrative(case_id: str, max_cost: float, model: str, domain: str):
    """Generate or regenerate case narrative from existing graph data."""
    setup_domain(domain)

    graph_path = Path("cases") / case_id / "output" / "graph_data.json"
    if not graph_path.exists():
        raise click.ClickException(
            f"graph_data.json not found at {graph_path}. Run 'process' first."
        )

    from farmer_factory.narrative import CaseNarrativeGenerator
    from farmer_factory.structure.graph import KnowledgeGraph

    click.echo(f"Loading graph from {graph_path}...")
    graph = KnowledgeGraph.load(graph_path)

    click.echo(f"Generating narrative (model={model}, max_cost=${max_cost:.2f})...")
    generator = CaseNarrativeGenerator(max_cost=max_cost, primary_model=model)
    output_dir = Path("cases") / case_id / "output"
    narrative_path = generator.generate_and_save(case_id, graph, output_dir)

    click.echo(f"\n✅ Narrative saved to: {narrative_path}")
    click.echo(f"   Cost: ${generator.total_cost:.4f}")


@cli.command()
@click.argument("case_id")
@click.option("--force", is_flag=True, help="Force re-upload even if already exists")
def upload(case_id: str, force: bool):
    """Upload graph_data.json to Supabase Storage."""
    logger.info(f"Uploading case: {case_id}")

    case_dir = Path("cases") / case_id
    graph_file = case_dir / "output" / "graph_data.json"

    if not graph_file.exists():
        raise click.ClickException(f"Graph data not found: {graph_file}")

    # TODO: Implement Supabase upload
    click.echo(f"Uploading {graph_file}...")
    click.echo("\n⚠️  Supabase upload not yet implemented")
    click.echo("Coming in Phase 6 of ROADMAP.md")


@cli.command()
@click.argument("case_id")
@click.option(
    "--domain",
    default="cuban_property",
    help="Domain configuration to use (default: cuban_property)",
)
def validate(case_id: str, domain: str):
    """Validate graph_data.json against schema."""
    # Set up domain for validation
    setup_domain(domain)

    logger.info(f"Validating case: {case_id}")

    case_dir = Path("cases") / case_id
    graph_file = case_dir / "output" / "graph_data.json"

    if not graph_file.exists():
        raise click.ClickException(f"Graph data not found: {graph_file}")

    click.echo(f"Validating {graph_file}...")

    try:
        import json
        from farmer_factory.structure.schema import GraphExport

        with open(graph_file, "r", encoding="utf-8") as f:
            export_data = json.load(f)

        GraphExport.model_validate(export_data)
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise click.ClickException(f"Validation failed: {e}")

    click.echo("✓ Graph data is valid")


@cli.command()
@click.argument("case_id")
def retry(case_id: str):
    """Retry failed processing jobs."""
    logger.info(f"Retrying failed jobs for: {case_id}")

    # TODO: Implement retry logic
    click.echo(f"Retrying failed jobs for {case_id}...")
    click.echo("\n⚠️  Retry logic not yet implemented")
    click.echo("Coming in Phase 8 of ROADMAP.md")


@cli.command()
@click.argument("case_id")
@click.option("--verbose", is_flag=True, help="Verbose output")
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
    click.echo("\nFor now, re-run the full process command:")
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


@cli.command()
@click.argument("case_id")
@click.option(
    "--entity-type",
    help="Train specific entity type (default: all deduplicatable types from domain)",
)
@click.option(
    "--num-examples", default=30, help="Number of labeled examples to collect per type"
)
@click.option(
    "--domain",
    default="cuban_property",
    help="Domain configuration to use (default: cuban_property)",
)
def train_deduplication(case_id: str, entity_type: str, num_examples: int, domain: str):
    """
    Train entity deduplication models using labeled examples.

    Interactive session where you label entity pairs as matches or not.
    Models are saved to farmer_factory/structure/models/ for use in
    future processing runs.

    Example:
        python cli.py train-deduplication TEST-CERESA --entity-type PERSON --domain cuban_property
    """
    # Set up domain configuration
    setup_domain(domain)

    from farmer_factory.domains import domain_registry

    try:
        from farmer_factory.structure.train_dedupe import train_dedupe_model
    except ModuleNotFoundError:
        from structure.train_dedupe import train_dedupe_model

    case_dir = Path("cases") / case_id
    extractions_dir = case_dir / "extractions"

    if not extractions_dir.exists():
        raise click.ClickException(
            f"No extractions found for {case_id}. "
            f"Run 'python cli.py process {case_id}' first."
        )

    click.echo(f"\n{'=' * 60}")
    click.echo("Deduplication Model Training")
    click.echo(f"{'=' * 60}\n")
    click.echo(f"Case: {case_id}")
    click.echo(f"Domain: {domain}")
    click.echo(f"Examples per type: {num_examples}\n")

    # Get entity types from domain config (filter to deduplicatable types)
    if entity_type:
        entity_types = [entity_type]
    else:
        # Default to common deduplicatable types available in domain
        all_types = domain_registry.get_entity_types()
        # Filter to types that typically need deduplication
        dedup_types = ["PERSON", "LOCATION", "PROPERTY", "ORGANIZATION"]
        entity_types = [t for t in dedup_types if t in all_types]

    for etype in entity_types:
        try:
            click.echo(f"\n--- Training {etype} ---\n")
            model = train_dedupe_model(
                case_id=case_id, entity_type=etype, num_examples=num_examples
            )
            click.echo(f"✓ {etype} model trained and saved\n")
        except ValueError as e:
            click.echo(f"⚠️  Skipping {etype}: {e}\n")
            continue
        except Exception as e:
            logger.exception(f"Failed to train {etype} model")
            click.echo(f"❌ Failed to train {etype}: {e}\n")
            continue

    click.echo(f"\n{'=' * 60}")
    click.echo("Training Complete!")
    click.echo(f"{'=' * 60}")
    click.echo("\nModels saved to: farmer_factory/structure/models/")
    click.echo("\nNext steps:")
    click.echo(f"  1. Test models: python cli.py process {case_id} --force-typed")
    click.echo(f"  2. Review deduplication in: cases/{case_id}/output/graph_data.json")
    click.echo("  3. If quality is good, process new cases with trained models")


@cli.command()
@click.argument("case_id")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
def clean(case_id: str, confirm: bool):
    """Clean case outputs for fresh processing.

    Removes all processed outputs while keeping source PDFs intact:
    - extractions/ (AI-extracted entities)
    - ocr/ (OCR text files)
    - preprocessed/ (processed images)
    - output/ (graph_data.json)

    Your intake/ PDFs are never deleted.
    """
    case_dir = Path("cases") / case_id

    if not case_dir.exists():
        raise click.ClickException(f"Case not found: {case_id}")

    intake_dir = case_dir / "intake"
    if not intake_dir.exists() or not any(intake_dir.glob("*.pdf")):
        raise click.ClickException(f"No PDFs found in {intake_dir}/")

    # Show what will be deleted
    click.echo(f"\nCleaning case: {case_id}")
    click.echo("\nWill remove:")
    click.echo("  - extractions/")
    click.echo("  - ocr/")
    click.echo("  - preprocessed/")
    click.echo("  - output/")
    click.echo("\nWill keep:")
    click.echo(f"  - intake/ ({len(list(intake_dir.glob('*.pdf')))} PDFs)")

    if not confirm:
        click.echo("\nThis cannot be undone.")
        if not click.confirm("Continue?"):
            click.echo("Aborted.")
            return

    # Clean directories
    dirs_to_clean = ["extractions", "ocr", "preprocessed", "output"]
    for dir_name in dirs_to_clean:
        dir_path = case_dir / dir_name
        if dir_path.exists():
            import shutil

            shutil.rmtree(dir_path)
        dir_path.mkdir(parents=True, exist_ok=True)

    click.echo(f"\n✓ Case {case_id} cleaned successfully")
    click.echo("\nReady for fresh processing:")
    click.echo(f"  python cli.py process {case_id}")


@cli.command()
def list_cases():
    """List all cases."""
    cases_dir = Path("cases")

    if not cases_dir.exists():
        click.echo("No cases directory found")
        return

    cases = sorted([d for d in cases_dir.iterdir() if d.is_dir()])

    if not cases:
        click.echo("No cases found")
        return

    click.echo("\nCases:")
    for case_dir in cases:
        metadata_file = case_dir / "metadata.json"
        if metadata_file.exists():
            import json

            with open(metadata_file, encoding='utf-8') as f:
                metadata = json.load(f)
            click.echo(
                f"  {metadata['id']}: {metadata['name']} ({metadata.get('status', 'UNKNOWN')})"
            )
        else:
            click.echo(f"  {case_dir.name}: (no metadata)")


@cli.command("generate-dossier")
@click.argument("case_id")
@click.option("--property-id", required=True, help="Entity ID of the focal property")
@click.option("--family-member-id", required=True, help="Entity ID of primary claimant")
@click.option(
    "--output",
    "output_dir",
    type=click.Path(),
    help="Output directory (default: cases/{case_id}/output)",
)
@click.option(
    "--engine",
    default="xelatex",
    type=click.Choice(["xelatex", "pdflatex"]),
    help="LaTeX engine",
)
@click.option(
    "--dry-run", is_flag=True, help="Generate .tex only, skip PDF compilation"
)
@click.option(
    "--domain",
    default="cuban_property",
    help="Domain configuration to use (default: cuban_property)",
)
def generate_dossier(
    case_id: str,
    property_id: str,
    family_member_id: str,
    output_dir: str,
    engine: str,
    dry_run: bool,
    domain: str,
):
    """Generate PDF dossier for a case.

    Requires a processed case with graph_data.json.
    Use --dry-run to generate LaTeX without compiling (useful if LaTeX not installed).

    Example:
        python cli.py generate-dossier TEST-CERESA \\
            --property-id "property_abc123" \\
            --family-member-id "person_xyz789" \\
            --domain cuban_property
    """
    # Set up domain configuration
    setup_domain(domain)

    from farmer_factory.dossier import generate_dossier as gen_dossier
    from farmer_factory.dossier.compiler import check_latex_available

    logger.info(f"Generating dossier for case: {case_id}")
    logger.info(f"  Property: {property_id}")
    logger.info(f"  Claimant: {family_member_id}")

    # Check LaTeX availability
    if not dry_run:
        available, msg = check_latex_available(engine)
        if not available:
            click.echo(f"\n⚠ {msg}")
            click.echo("\nUse --dry-run to generate .tex file without PDF compilation.")
            if not click.confirm("Continue with --dry-run?"):
                raise click.Abort()
            dry_run = True

    try:
        output_path = Path(output_dir) if output_dir else None
        result_path = gen_dossier(
            case_id=case_id,
            focal_property_id=property_id,
            focal_family_member_id=family_member_id,
            output_dir=output_path,
            engine=engine,
            dry_run=dry_run,
        )

        if dry_run:
            click.echo(f"\n✓ LaTeX generated: {result_path}")
            click.echo("\nTo compile manually:")
            click.echo(f"  cd {result_path.parent}")
            click.echo(f"  {engine} {result_path.name}")
        else:
            click.echo(f"\n✓ Dossier generated: {result_path}")

    except Exception as e:
        logger.error(f"Dossier generation failed: {e}")
        raise click.ClickException(str(e))


@cli.command("list-entities")
@click.argument("case_id")
@click.option(
    "--type",
    "entity_type",
    type=click.Choice(["PERSON", "PROPERTY", "DOCUMENT", "ORGANIZATION", "LOCATION"]),
    help="Filter by entity type",
)
def list_entities(case_id: str, entity_type: str):
    """List entities in a case graph for dossier generation.

    Use this to find entity IDs for --property-id and --family-member-id options.
    """
    from farmer_factory.structure.graph import KnowledgeGraph

    graph_path = Path(f"cases/{case_id}/output/graph_data.json")
    if not graph_path.exists():
        raise click.ClickException(f"Graph not found: {graph_path}")

    graph = KnowledgeGraph.load(graph_path)

    click.echo(f"\nEntities in {case_id}:")
    click.echo("-" * 60)

    for node_id in sorted(graph.graph.nodes()):
        entity = graph.get_entity(node_id)
        if not entity:
            continue

        etype = entity.get("entity_type", "UNKNOWN")
        if entity_type and etype != entity_type:
            continue

        name = entity.get("name", entity.get("title", "Unnamed"))
        click.echo(f"  [{etype}] {name}")
        click.echo(f"    ID: {node_id}")


@cli.command("list-domains")
def list_domains():
    """List available domain configurations."""
    from farmer_factory.domains import domain_registry

    available = domain_registry.list_available_domains()

    click.echo("\nAvailable Domains:")
    click.echo("-" * 40)
    for domain_code in sorted(available):
        try:
            config = domain_registry._loader.load(domain_code)
            click.echo(f"  {domain_code}: {config.name}")
        except Exception:
            click.echo(f"  {domain_code}: (failed to load)")


@cli.command("generate-manifest")
@click.argument("case_id")
def generate_manifest(case_id: str):
    """Generate manifest.json from existing processed files.

    Use this for cases that were processed before manifest generation was added.
    Scans the ocr/ directory to discover processed documents.

    Example:
        python cli.py generate-manifest TEST-CERESA
    """
    from farmer_factory.intake import ManifestManager

    case_dir = Path("cases") / case_id

    if not case_dir.exists():
        raise click.ClickException(f"Case not found: {case_id}")

    ocr_dir = case_dir / "ocr"
    if not ocr_dir.exists():
        raise click.ClickException(f"No OCR directory found. Run 'process' first.")

    # Discover documents from OCR files
    ocr_files = sorted(ocr_dir.glob("*.txt"))
    if not ocr_files:
        raise click.ClickException(f"No OCR text files found in {ocr_dir}")

    click.echo(f"\nGenerating manifest for: {case_id}")
    click.echo(f"Found {len(ocr_files)} processed documents")

    manifest = ManifestManager(case_id)

    for ocr_file in ocr_files:
        document_id = ocr_file.stem
        # Derive original filename (best guess - add .pdf extension)
        filename = document_id.replace("_page_0", "") + ".pdf"

        manifest.add_document(
            document_id=document_id,
            filename=filename,
            status="success",
            part_count=1,
            page_count=1,  # Each OCR file is one page
        )

    manifest_path = case_dir / "manifest.json"
    manifest.save_manifest(manifest_path)

    summary = manifest.get_summary()
    click.echo(f"\n✓ Manifest saved: {manifest_path}")
    click.echo(f"  Documents: {summary['total_documents']}")
    click.echo(f"  Successful: {summary['successful']}")


if __name__ == "__main__":
    cli()
