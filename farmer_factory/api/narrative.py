"""Narrative generation API endpoint."""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.narrative import NarrativeGenerator
from farmer_factory.narrative.exceptions import (
    SessionCostLimitExceeded,
    InsufficientGraphData
)
from farmer_factory.utils import validate_case_id

logger = logging.getLogger(__name__)


def generate_narrative_endpoint(
    case_id: str,
    request_data: Dict[str, Any],
    api_key: Optional[str] = None,
    max_cost_per_session: float = 1.0
) -> Dict[str, Any]:
    """
    API endpoint for narrative generation.

    POST /api/cases/{caseId}/narrative

    Request:
    {
        "clicked_node_id": "prop_villa_aurelia_001",
        "session_id": "user_session_123",
        "max_depth": 3  // Optional, not used in MVP1
    }

    Response:
    {
        "focal_entity_id": "prop_villa_aurelia_001",
        "focal_entity_name": "Villa Aurelia",
        "focal_entity_type": "PROPERTY",
        "main_narrative": "Villa Aurelia first appears...",
        "highlighted_events": [...],
        "model_used": "haiku",
        "generation_cost": 0.0007,
        "from_cache": false,
        "session_total_cost": 0.0142
    }

    Args:
        case_id: Case identifier
        request_data: Request payload
        api_key: Optional Anthropic API key
        max_cost_per_session: Session cost limit

    Returns:
        Narrative result as dict

    Raises:
        ValueError: If required parameters missing
        SessionCostLimitExceeded: If session exceeds cost limit
        InsufficientGraphData: If entity not found
    """
    # Generate narrative
    try:
        # Validate case_id to prevent path traversal
        if not validate_case_id(case_id):
            raise ValueError(f"Invalid case_id: {case_id}")

        # Validate request
        clicked_node_id = request_data.get("clicked_node_id")
        session_id = request_data.get("session_id")

        if not clicked_node_id:
            raise ValueError("Missing required parameter: clicked_node_id")
        if not session_id:
            raise ValueError("Missing required parameter: session_id")

        logger.info(f"Narrative request: case={case_id}, entity={clicked_node_id}, session={session_id}")

        # Load graph
        graph_path = Path(f"cases/{case_id}/output/graph_data.json")
        if not graph_path.exists():
            raise FileNotFoundError(f"Graph data not found: {graph_path}")

        # Note: Assuming KnowledgeGraph has a load method
        # If not, you'll need to implement it or load differently
        graph = KnowledgeGraph.load(graph_path)

        # Initialize generator
        generator = NarrativeGenerator(api_key=api_key, use_cache=True)

        result = generator.generate(
            clicked_node_id=clicked_node_id,
            graph=graph,
            session_id=session_id,
            max_cost_per_session=max_cost_per_session
        )

        # Add session total cost to response
        response = result.model_dump()
        response["session_total_cost"] = generator.session_costs.get(session_id, 0.0)

        logger.info(
            f"Narrative generated: entity={result.focal_entity_name}, "
            f"model={result.model_used}, cost=${result.generation_cost:.4f}"
        )

        return response

    except ValueError as e:
        logger.warning(f"Narrative request error: {e}")
        return {
            "error": str(e),
            "type": "bad_request",
            "status_code": 400
        }

    except FileNotFoundError as e:
        logger.warning(f"Graph data not found: {e}")
        return {
            "error": str(e),
            "type": "not_found",
            "status_code": 404
        }

    except SessionCostLimitExceeded as e:
        logger.warning(f"Session cost limit exceeded: {e}")
        return {
            "error": str(e),
            "type": "cost_limit",
            "status_code": 402
        }

    except InsufficientGraphData as e:
        logger.error(f"Insufficient graph data: {e}")
        return {
            "error": str(e),
            "type": "insufficient_graph_data",
            "status_code": 422
        }

    except Exception as e:
        logger.error(f"Narrative generation error: {e}", exc_info=True)
        return {
            "error": "Narrative generation failed",
            "type": "internal_error",
            "status_code": 500
        }
