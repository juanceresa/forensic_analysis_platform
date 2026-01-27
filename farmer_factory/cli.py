#!/usr/bin/env python3
"""
Civic Table - Factory CLI
Command-line interface for document processing pipeline.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to allow absolute imports of farmer_factory
current_dir = Path(__file__).resolve().parent
if current_dir.name == 'farmer_factory':
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
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Civic Table Factory - Document Processing Pipeline"""
    pass


@cli.command()
@click.option('--id', 'case_id', required=True, help='Case ID (e.g., CASE-001)')
@click.option('--name', required=True, help='Case name (e.g., "Ceresa Family Archive")')
@click.option('--family', required=True, help='Family name (e.g., "Ceresa")')
def create_case(case_id: str, name: str, family: str):
    """Create a new case directory structure."""
    logger.info(f"Creating case: {case_id}")

    # Create directory structure
    case_dir = Path('cases') / case_id

    if case_dir.exists():
        logger.error(f"Case {case_id} already exists")
        raise click.ClickException(f"Case {case_id} already exists")

    # Create subdirectories
    (case_dir / 'intake').mkdir(parents=True)
    (case_dir / 'preprocessed').mkdir(parents=True)
    (case_dir / 'ocr').mkdir(parents=True)
    (case_dir / 'output').mkdir(parents=True)

    # Create case metadata file
    metadata = {
        'id': case_id,
        'name': name,
        'family': family,
        'created_at': datetime.now().isoformat(),
        'status': 'INTAKE'
    }

    import json
    with open(case_dir / 'metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"✓ Case created at: {case_dir}")
    logger.info(f"  Next steps:")
    logger.info(f"    1. Copy PDFs to: {case_dir / 'intake'}/")
    logger.info(f"    2. Run: python cli.py process {case_id}")

    click.echo(f"\n✓ Case {case_id} created successfully")


@cli.command()
@click.argument('case_id')
@click.option('--verbose', is_flag=True, help='Verbose output')
@click.option('--file', 'single_file', help='Process only this PDF file from intake/ directory')
@click.option('--force-typed', is_flag=True, help='Force all documents to use OCR path (ignore triage)')
@click.option('--skip-validation', is_flag=True, help='Skip graph_data.json validation')
def process(case_id: str, verbose: bool, single_file: str, force_typed: bool, skip_validation: bool):
    """Process case documents through the pipeline."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

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
            skip_validation=skip_validation
        )

        # Print summary
        click.echo("\n" + "="*60)
        click.echo("Processing Complete!")
        click.echo("="*60)
        click.echo(f"Documents processed: {stats['documents_processed']}")
        click.echo(f"Entities extracted:  {stats['entities_extracted']}")
        click.echo(f"Entities merged:     {stats['entities_merged']}")
        click.echo(f"Relations added:     {stats['relations_added']}")

        output_path = Path('cases') / case_id / 'output' / 'graph_data.json'
        click.echo(f"\nGraph saved to: {output_path}")

    except ProcessingError as e:
        logger.error(f"Processing failed: {e}")
        click.echo(f"\n❌ Processing failed: {e}", err=True)
        case_dir = Path('cases') / case_id
        if case_dir.exists():
            click.echo(f"Check detailed logs: {case_dir}/processing.log")
        raise click.ClickException(str(e))

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        click.echo(f"\n❌ Unexpected error: {e}", err=True)
        case_dir = Path('cases') / case_id
        if case_dir.exists():
            click.echo(f"Check detailed logs: {case_dir}/processing.log")
        raise click.ClickException(str(e))


@cli.command()
@click.argument('case_id')
@click.option('--force', is_flag=True, help='Force re-upload even if already exists')
def upload(case_id: str, force: bool):
    """Upload graph_data.json to Supabase Storage."""
    logger.info(f"Uploading case: {case_id}")

    case_dir = Path('cases') / case_id
    graph_file = case_dir / 'output' / 'graph_data.json'

    if not graph_file.exists():
        raise click.ClickException(f"Graph data not found: {graph_file}")

    # TODO: Implement Supabase upload
    click.echo(f"Uploading {graph_file}...")
    click.echo("\n⚠️  Supabase upload not yet implemented")
    click.echo("Coming in Phase 6 of ROADMAP.md")


@cli.command()
@click.argument('case_id')
def validate(case_id: str):
    """Validate graph_data.json against schema."""
    logger.info(f"Validating case: {case_id}")

    case_dir = Path('cases') / case_id
    graph_file = case_dir / 'output' / 'graph_data.json'

    if not graph_file.exists():
        raise click.ClickException(f"Graph data not found: {graph_file}")

    click.echo(f"Validating {graph_file}...")

    try:
        import json
        from farmer_factory.structure.schema import GraphExport

        with open(graph_file, 'r', encoding='utf-8') as f:
            export_data = json.load(f)

        GraphExport.model_validate(export_data)
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise click.ClickException(f"Validation failed: {e}")

    click.echo("✓ Graph data is valid")


@cli.command()
@click.argument('case_id')
def retry(case_id: str):
    """Retry failed processing jobs."""
    logger.info(f"Retrying failed jobs for: {case_id}")

    # TODO: Implement retry logic
    click.echo(f"Retrying failed jobs for {case_id}...")
    click.echo("\n⚠️  Retry logic not yet implemented")
    click.echo("Coming in Phase 8 of ROADMAP.md")


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


@cli.command()
@click.argument('case_id')
@click.option('--entity-type',
              type=click.Choice(['PERSON', 'LOCATION', 'PROPERTY', 'ORGANIZATION']),
              help='Train specific entity type (default: all)')
@click.option('--num-examples', default=30,
              help='Number of labeled examples to collect per type')
def train_deduplication(case_id: str, entity_type: str, num_examples: int):
    """
    Train entity deduplication models using labeled examples.

    Interactive session where you label entity pairs as matches or not.
    Models are saved to farmer_factory/structure/models/ for use in
    future processing runs.

    Example:
        python cli.py train-deduplication TEST-CERESA --entity-type PERSON
    """
    try:
        from farmer_factory.structure.train_dedupe import train_dedupe_model
    except ModuleNotFoundError:
        from structure.train_dedupe import train_dedupe_model

    case_dir = Path('cases') / case_id
    extractions_dir = case_dir / 'extractions'

    if not extractions_dir.exists():
        raise click.ClickException(
            f"No extractions found for {case_id}. "
            f"Run 'python cli.py process {case_id}' first."
        )

    click.echo(f"\n{'='*60}")
    click.echo("Deduplication Model Training")
    click.echo(f"{'='*60}\n")
    click.echo(f"Case: {case_id}")
    click.echo(f"Examples per type: {num_examples}\n")

    entity_types = [entity_type] if entity_type else ['PERSON', 'LOCATION', 'PROPERTY', 'ORGANIZATION']

    for etype in entity_types:
        try:
            click.echo(f"\n--- Training {etype} ---\n")
            model = train_dedupe_model(
                case_id=case_id,
                entity_type=etype,
                num_examples=num_examples
            )
            click.echo(f"✓ {etype} model trained and saved\n")
        except ValueError as e:
            click.echo(f"⚠️  Skipping {etype}: {e}\n")
            continue
        except Exception as e:
            logger.exception(f"Failed to train {etype} model")
            click.echo(f"❌ Failed to train {etype}: {e}\n")
            continue

    click.echo(f"\n{'='*60}")
    click.echo("Training Complete!")
    click.echo(f"{'='*60}")
    click.echo("\nModels saved to: farmer_factory/structure/models/")
    click.echo("\nNext steps:")
    click.echo(f"  1. Test models: python cli.py process {case_id} --force-typed")
    click.echo(f"  2. Review deduplication in: cases/{case_id}/output/graph_data.json")
    click.echo(f"  3. If quality is good, process new cases with trained models")


@cli.command()
@click.argument('case_id')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
def clean(case_id: str, confirm: bool):
    """Clean case outputs for fresh processing.

    Removes all processed outputs while keeping source PDFs intact:
    - extractions/ (AI-extracted entities)
    - ocr/ (OCR text files)
    - preprocessed/ (processed images)
    - output/ (graph_data.json)

    Your intake/ PDFs are never deleted.
    """
    case_dir = Path('cases') / case_id

    if not case_dir.exists():
        raise click.ClickException(f"Case not found: {case_id}")

    intake_dir = case_dir / 'intake'
    if not intake_dir.exists() or not list(intake_dir.glob('*.pdf')):
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
    dirs_to_clean = ['extractions', 'ocr', 'preprocessed', 'output']
    for dir_name in dirs_to_clean:
        dir_path = case_dir / dir_name
        if dir_path.exists():
            import shutil
            shutil.rmtree(dir_path)
        dir_path.mkdir(parents=True, exist_ok=True)

    click.echo(f"\n✓ Case {case_id} cleaned successfully")
    click.echo(f"\nReady for fresh processing:")
    click.echo(f"  python cli.py process {case_id}")


@cli.command()
def list_cases():
    """List all cases."""
    cases_dir = Path('cases')

    if not cases_dir.exists():
        click.echo("No cases directory found")
        return

    cases = sorted([d for d in cases_dir.iterdir() if d.is_dir()])

    if not cases:
        click.echo("No cases found")
        return

    click.echo("\nCases:")
    for case_dir in cases:
        metadata_file = case_dir / 'metadata.json'
        if metadata_file.exists():
            import json
            with open(metadata_file) as f:
                metadata = json.load(f)
            click.echo(f"  {metadata['id']}: {metadata['name']} ({metadata.get('status', 'UNKNOWN')})")
        else:
            click.echo(f"  {case_dir.name}: (no metadata)")


@cli.command('generate-dossier')
@click.argument('case_id')
@click.option('--property-id', required=True, help='Entity ID of the focal property')
@click.option('--family-member-id', required=True, help='Entity ID of primary claimant')
@click.option('--output', 'output_dir', type=click.Path(), help='Output directory (default: cases/{case_id}/output)')
@click.option('--engine', default='xelatex', type=click.Choice(['xelatex', 'pdflatex']), help='LaTeX engine')
@click.option('--dry-run', is_flag=True, help='Generate .tex only, skip PDF compilation')
def generate_dossier(case_id: str, property_id: str, family_member_id: str, output_dir: str, engine: str, dry_run: bool):
    """Generate PDF dossier for a case.

    Requires a processed case with graph_data.json.
    Use --dry-run to generate LaTeX without compiling (useful if LaTeX not installed).

    Example:
        python cli.py generate-dossier TEST-CERESA \\
            --property-id "property_abc123" \\
            --family-member-id "person_xyz789"
    """
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
            click.echo(f"\nTo compile manually:")
            click.echo(f"  cd {result_path.parent}")
            click.echo(f"  {engine} {result_path.name}")
        else:
            click.echo(f"\n✓ Dossier generated: {result_path}")

    except Exception as e:
        logger.error(f"Dossier generation failed: {e}")
        raise click.ClickException(str(e))


@cli.command('list-entities')
@click.argument('case_id')
@click.option('--type', 'entity_type', type=click.Choice(['PERSON', 'PROPERTY', 'DOCUMENT', 'ORGANIZATION', 'LOCATION']), help='Filter by entity type')
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


if __name__ == '__main__':
    cli()
