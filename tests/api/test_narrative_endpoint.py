"""Tests for narrative API endpoint."""

import pytest
from unittest.mock import Mock, patch
from farmer_factory.api.narrative import generate_narrative_endpoint
from farmer_factory.narrative.models import NarrativeResult


@pytest.fixture
def mock_graph():
    """Mock knowledge graph."""
    with patch('farmer_factory.api.narrative.KnowledgeGraph') as mock:
        mock.load.return_value = Mock()
        yield mock


@pytest.fixture
def mock_generator():
    """Mock narrative generator."""
    with patch('farmer_factory.api.narrative.NarrativeGenerator') as mock:
        generator_instance = Mock()
        mock.return_value = generator_instance

        # Mock generation result
        generator_instance.generate.return_value = NarrativeResult(
            focal_entity_id="prop_001",
            focal_entity_name="Villa Aurelia",
            focal_entity_type="PROPERTY",
            constellation_size=4,
            model_used="haiku",
            main_narrative="Test narrative [①].",
            facts=[],
            total_documents=1,
            total_citations=1,
            generation_cost=0.001,
            from_cache=False
        )

        yield generator_instance


def test_generate_narrative_endpoint_success(mock_graph, mock_generator):
    """Test successful narrative generation."""
    request_data = {
        "clicked_node_id": "person_001",
        "session_id": "sess_123"
    }

    with patch('pathlib.Path.exists', return_value=True):
        result = generate_narrative_endpoint(
            case_id="TEST-CERESA",
            request_data=request_data
        )

    assert result["focal_entity_name"] == "Villa Aurelia"
    assert result["model_used"] == "haiku"
    assert "main_narrative" in result
    assert result["generation_cost"] > 0


def test_endpoint_handles_missing_params():
    """Test endpoint validates required parameters."""
    request_data = {}  # Missing clicked_node_id

    result = generate_narrative_endpoint(
        case_id="TEST-CERESA",
        request_data=request_data
    )

    assert result["status_code"] == 400
    assert result["type"] == "bad_request"


def test_endpoint_rejects_invalid_case_id():
    """Test endpoint rejects path traversal attempts in case_id."""
    request_data = {
        "clicked_node_id": "person_001",
        "session_id": "sess_123"
    }

    # Test path traversal attempt
    result = generate_narrative_endpoint(
        case_id="../etc/passwd",
        request_data=request_data
    )

    assert result["status_code"] == 400
    assert result["type"] == "bad_request"
    assert "Invalid case_id" in result["error"]


def test_endpoint_rejects_case_id_with_slashes():
    """Test endpoint rejects case IDs with directory separators."""
    request_data = {
        "clicked_node_id": "person_001",
        "session_id": "sess_123"
    }

    result = generate_narrative_endpoint(
        case_id="case/admin",
        request_data=request_data
    )

    assert result["status_code"] == 400
    assert result["type"] == "bad_request"


def test_endpoint_handles_cost_limit_exceeded(mock_graph, mock_generator):
    """Test endpoint handles cost limit errors."""
    from farmer_factory.narrative.exceptions import SessionCostLimitExceeded

    mock_generator.generate.side_effect = SessionCostLimitExceeded(
        session_id="sess_123",
        current_cost=1.50,
        limit=1.0
    )

    request_data = {
        "clicked_node_id": "person_001",
        "session_id": "sess_123"
    }

    with patch('pathlib.Path.exists', return_value=True):
        result = generate_narrative_endpoint(
            case_id="TEST-CERESA",
            request_data=request_data
        )

    assert result["status_code"] == 402
    assert result["type"] == "cost_limit"
