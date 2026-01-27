"""Comprehensive tests for CLI commands."""

import pytest
import json
import shutil
from pathlib import Path
from datetime import datetime
from click.testing import CliRunner
from farmer_factory.cli import cli


class TestCreateCase:
    """Tests for the create-case CLI command."""

    def test_create_case_success(self, tmp_path):
        """Test successful case creation."""
        import os
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)

            runner = CliRunner()
            result = runner.invoke(cli, [
                'create-case',
                '--id', 'TEST-001',
                '--name', 'Test Case',
                '--family', 'TestFamily'
            ])

            assert result.exit_code == 0
            assert "created successfully" in result.output

            # Verify directory structure
            case_dir = tmp_path / 'cases' / 'TEST-001'
            assert case_dir.exists()
            assert (case_dir / 'intake').exists()
            assert (case_dir / 'preprocessed').exists()
            assert (case_dir / 'ocr').exists()
            assert (case_dir / 'output').exists()

            # Verify metadata
            metadata_file = case_dir / 'metadata.json'
            assert metadata_file.exists()
            with open(metadata_file, encoding='utf-8') as f:
                metadata = json.load(f)
            assert metadata['id'] == 'TEST-001'
            assert metadata['name'] == 'Test Case'
            assert metadata['family'] == 'TestFamily'
            assert metadata['status'] == 'INTAKE'

        finally:
            os.chdir(original_dir)

    def test_create_case_already_exists(self, tmp_path):
        """Test error when case already exists."""
        import os
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Create case directory first
            (tmp_path / 'cases' / 'TEST-DUP').mkdir(parents=True)

            runner = CliRunner()
            result = runner.invoke(cli, [
                'create-case',
                '--id', 'TEST-DUP',
                '--name', 'Duplicate Case',
                '--family', 'TestFamily'
            ])

            assert result.exit_code != 0
            assert "already exists" in result.output

        finally:
            os.chdir(original_dir)

    def test_create_case_invalid_domain(self, tmp_path):
        """Test error with invalid domain."""
        import os
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)

            runner = CliRunner()
            result = runner.invoke(cli, [
                'create-case',
                '--id', 'TEST-002',
                '--name', 'Test Case',
                '--family', 'TestFamily',
                '--domain', 'invalid_domain'
            ])

            assert result.exit_code != 0
            assert "Unknown domain" in result.output

        finally:
            os.chdir(original_dir)


class TestClean:
    """Tests for the clean CLI command."""

    def test_clean_success(self, tmp_path):
        """Test successful cleaning of case outputs."""
        import os
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Set up case directory with content
            case_dir = tmp_path / 'cases' / 'TEST-CLEAN'
            (case_dir / 'intake').mkdir(parents=True)
            (case_dir / 'extractions').mkdir()
            (case_dir / 'ocr').mkdir()
            (case_dir / 'preprocessed').mkdir()
            (case_dir / 'output').mkdir()

            # Add a sample PDF to intake (required for clean to work)
            sample_pdf = case_dir / 'intake' / 'test.pdf'
            sample_pdf.write_bytes(b'%PDF-1.4 sample')

            # Add files to directories that should be cleaned
            (case_dir / 'extractions' / 'test.json').write_text('{}')
            (case_dir / 'ocr' / 'test.txt').write_text('OCR text')
            (case_dir / 'preprocessed' / 'test.png').write_bytes(b'PNG')
            (case_dir / 'output' / 'graph_data.json').write_text('{}')

            runner = CliRunner()
            result = runner.invoke(cli, ['clean', 'TEST-CLEAN', '--confirm'])

            assert result.exit_code == 0
            assert "cleaned successfully" in result.output

            # Verify directories are empty but exist
            assert (case_dir / 'extractions').exists()
            assert not list((case_dir / 'extractions').iterdir())
            assert (case_dir / 'output').exists()
            assert not list((case_dir / 'output').iterdir())

            # Verify intake PDFs preserved
            assert sample_pdf.exists()

        finally:
            os.chdir(original_dir)

    def test_clean_nonexistent_case(self, tmp_path):
        """Test error when cleaning nonexistent case."""
        import os
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)

            runner = CliRunner()
            result = runner.invoke(cli, ['clean', 'NONEXISTENT', '--confirm'])

            assert result.exit_code != 0
            assert "not found" in result.output

        finally:
            os.chdir(original_dir)

    def test_clean_no_pdfs(self, tmp_path):
        """Test error when case has no PDFs."""
        import os
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Create case without PDFs
            case_dir = tmp_path / 'cases' / 'TEST-EMPTY'
            (case_dir / 'intake').mkdir(parents=True)

            runner = CliRunner()
            result = runner.invoke(cli, ['clean', 'TEST-EMPTY', '--confirm'])

            assert result.exit_code != 0
            assert "No PDFs found" in result.output

        finally:
            os.chdir(original_dir)


class TestListCases:
    """Tests for the list-cases CLI command."""

    def test_list_cases_empty(self, tmp_path):
        """Test listing with no cases."""
        import os
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)

            runner = CliRunner()
            result = runner.invoke(cli, ['list-cases'])

            assert result.exit_code == 0
            assert "No cases" in result.output or "not found" in result.output

        finally:
            os.chdir(original_dir)

    def test_list_cases_with_cases(self, tmp_path):
        """Test listing existing cases."""
        import os
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Create cases directory with a case
            cases_dir = tmp_path / 'cases'
            case_dir = cases_dir / 'TEST-LIST'
            case_dir.mkdir(parents=True)

            metadata = {
                'id': 'TEST-LIST',
                'name': 'Test List Case',
                'family': 'TestFamily',
                'status': 'PROCESSED'
            }
            with open(case_dir / 'metadata.json', 'w', encoding='utf-8') as f:
                json.dump(metadata, f)

            runner = CliRunner()
            result = runner.invoke(cli, ['list-cases'])

            assert result.exit_code == 0
            assert 'TEST-LIST' in result.output
            assert 'Test List Case' in result.output

        finally:
            os.chdir(original_dir)


class TestListDomains:
    """Tests for the list-domains CLI command."""

    def test_list_domains(self):
        """Test listing available domains."""
        runner = CliRunner()
        result = runner.invoke(cli, ['list-domains'])

        assert result.exit_code == 0
        assert 'cuban_property' in result.output
        assert 'Available Domains' in result.output


class TestValidate:
    """Tests for the validate CLI command."""

    def test_validate_valid_graph(self, tmp_path):
        """Test validating a valid graph."""
        import os
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Create minimal valid graph
            case_dir = tmp_path / 'cases' / 'TEST-VALID'
            output_dir = case_dir / 'output'
            output_dir.mkdir(parents=True)

            graph_data = {
                "metadata": {
                    "case_id": "TEST-VALID",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "factory_version": "1.0.0",
                    "entity_count": 0,
                    "relation_count": 0,
                    "document_count": 0,
                    "processing_stats": {}
                },
                "nodes": [],
                "links": []
            }

            with open(output_dir / 'graph_data.json', 'w', encoding='utf-8') as f:
                json.dump(graph_data, f)

            runner = CliRunner()
            result = runner.invoke(cli, ['validate', 'TEST-VALID'])

            assert result.exit_code == 0
            assert "valid" in result.output.lower()

        finally:
            os.chdir(original_dir)

    def test_validate_missing_graph(self, tmp_path):
        """Test error when graph file missing."""
        import os
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Create case without graph file
            case_dir = tmp_path / 'cases' / 'TEST-NO-GRAPH'
            case_dir.mkdir(parents=True)

            runner = CliRunner()
            result = runner.invoke(cli, ['validate', 'TEST-NO-GRAPH'])

            assert result.exit_code != 0
            assert "not found" in result.output

        finally:
            os.chdir(original_dir)
