"""CLI integration tests."""

import pytest
import json
import shutil
from pathlib import Path
from datetime import datetime
from click.testing import CliRunner
from farmer_factory.cli import cli


def test_cli_process_command(tmp_path):
    """Test CLI process command end-to-end."""
    # Setup test case
    case_id = "TEST-CLI-001"
    case_dir = tmp_path / "cases" / case_id
    intake_dir = case_dir / "intake"
    intake_dir.mkdir(parents=True)

    # Copy sample PDF
    sample_pdf = Path("farmer_factory/sample_docs/1960 5 13 Mario Ceresa Co Heir Doc.pdf")
    if not sample_pdf.exists():
        pytest.skip("Sample PDF not found")

    shutil.copy(sample_pdf, intake_dir)

    # Create metadata
    metadata = {
        'id': case_id,
        'name': 'Test Case',
        'family': 'Test',
        'created_at': datetime.now().isoformat(),
        'status': 'INTAKE'
    }
    with open(case_dir / 'metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

    # Create required directories
    (case_dir / 'preprocessed').mkdir()
    (case_dir / 'extractions').mkdir()
    (case_dir / 'output').mkdir()

    # Run CLI command (change to tmp_path first)
    import os
    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(cli, ['process', case_id])

        # Verify success
        assert result.exit_code == 0, f"CLI failed: {result.output}"

        # Verify output message
        assert "Processing Complete!" in result.output
        assert "Graph saved to:" in result.output

    finally:
        os.chdir(original_dir)

    # Verify outputs exist
    assert (case_dir / 'output' / 'graph_data.json').exists()
    assert (case_dir / 'processing.log').exists()


def test_cli_process_nonexistent_case(tmp_path):
    """Test CLI error handling for nonexistent case."""
    import os
    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(cli, ['process', 'NONEXISTENT'])

        # Should fail with error
        assert result.exit_code != 0
        assert "Processing failed" in result.output or "not found" in result.output

    finally:
        os.chdir(original_dir)
