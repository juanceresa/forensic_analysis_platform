#!/usr/bin/env python3
"""
Civic Table - Factory CLI
Command-line interface for document processing pipeline.
"""

import click
from pathlib import Path
import logging
from datetime import datetime

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
@click.option('--stage', type=click.Choice(['preprocessing', 'ocr', 'extraction', 'graph', 'all']),
              default='all', help='Processing stage to run')
@click.option('--document', help='Process single document ID')
@click.option('--verbose', is_flag=True, help='Verbose output')
def process(case_id: str, stage: str, document: str, verbose: bool):
    """Process case documents through the pipeline."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info(f"Processing case: {case_id} (stage: {stage})")

    case_dir = Path('cases') / case_id
    if not case_dir.exists():
        raise click.ClickException(f"Case {case_id} not found")

    # TODO: Implement processing pipeline
    click.echo(f"Processing {case_id}...")
    click.echo(f"Stage: {stage}")
    if document:
        click.echo(f"Document: {document}")

    click.echo("\n⚠️  Processing pipeline not yet implemented")
    click.echo("Coming in Phase 2-6 of ROADMAP.md")


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

    # TODO: Implement validation
    click.echo(f"Validating {graph_file}...")
    click.echo("\n⚠️  Validation not yet implemented")
    click.echo("Coming in Phase 6 of ROADMAP.md")


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


if __name__ == '__main__':
    cli()
