#!/usr/bin/env python3
"""
CLI script for narrative generation (called by Next.js API).

Usage:
    python generate_narrative.py --case-id TEST-CERESA --node-id prop_001 --session-id sess_123 --json
"""

import sys
import json
import argparse
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.narrative import NarrativeGenerator
from farmer_factory.narrative.exceptions import (
    SessionCostLimitExceeded,
    InsufficientGraphData
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Generate narrative for entity')
    parser.add_argument('--case-id', required=True, help='Case ID')
    parser.add_argument('--node-id', required=True, help='Clicked node ID')
    parser.add_argument('--session-id', required=True, help='Session ID')
    parser.add_argument('--json', action='store_true', help='Output JSON')
    parser.add_argument('--max-cost', type=float, default=1.0, help='Max session cost')
    parser.add_argument('--api-key', help='Anthropic API key (or use ANTHROPIC_API_KEY env var)')

    args = parser.parse_args()

    try:
        # Load graph
        graph_path = Path(f"cases/{args.case_id}/output/graph_data.json")
        if not graph_path.exists():
            raise FileNotFoundError(f"Graph not found: {graph_path}")

        graph = KnowledgeGraph(case_id=args.case_id)
        # Note: If KnowledgeGraph doesn't have a load method, implement it
        # For now, assuming graph loads its data in __init__

        # Generate narrative
        generator = NarrativeGenerator(api_key=args.api_key, use_cache=True)

        result = generator.generate(
            clicked_node_id=args.node_id,
            graph=graph,
            session_id=args.session_id,
            max_cost_per_session=args.max_cost
        )

        # Add session total
        output = result.model_dump()
        output["session_total_cost"] = generator.session_costs.get(args.session_id, 0.0)

        if args.json:
            print(json.dumps(output, default=str))
        else:
            print(f"Narrative for {result.focal_entity_name}:")
            print(result.main_narrative)
            print(f"\nCost: ${result.generation_cost:.4f}")
            print(f"Session total: ${output['session_total_cost']:.4f}")

    except SessionCostLimitExceeded as e:
        logger.error(f"Cost limit exceeded: {e}")
        if args.json:
            print(json.dumps({"error": str(e), "type": "cost_limit"}), file=sys.stderr)
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    except InsufficientGraphData as e:
        logger.error(f"Insufficient data: {e}")
        if args.json:
            print(json.dumps({"error": str(e), "type": "insufficient_data"}), file=sys.stderr)
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        if args.json:
            print(json.dumps({"error": str(e), "type": "unknown"}), file=sys.stderr)
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
