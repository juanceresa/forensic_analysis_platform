"""Narrative generation orchestrator with session cost tracking."""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.narrative.constellation import ConstellationAnalyzer
from farmer_factory.narrative.prompts import NarrativePrompts
from farmer_factory.narrative.cache import InMemoryCache, NarrativeCache
from farmer_factory.narrative.models import (
    NarrativeResult,
    FactualClaim,
    EvidenceCitation,
    EventHighlight
)
from farmer_factory.narrative.exceptions import SessionCostLimitExceeded, InsufficientGraphData
from farmer_factory.extract.api_client import ClaudeAPIClient
from farmer_factory.structure.schema import VerificationTier, RelationType

logger = logging.getLogger(__name__)


# Anthropic pricing (2026 estimates)
MODEL_PRICING = {
    "haiku": {"input": 0.25 / 1_000_000, "output": 1.25 / 1_000_000},  # per token
    "sonnet": {"input": 3.00 / 1_000_000, "output": 15.00 / 1_000_000}
}


class NarrativeGenerator:
    """Orchestrates single-stage narrative generation with caching and cost tracking."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        use_cache: bool = True,
        cache: Optional[NarrativeCache] = None
    ):
        """
        Initialize narrative generator.

        Args:
            api_key: Anthropic API key
            use_cache: Enable session caching
            cache: Optional custom cache implementation
        """
        self.api_client = ClaudeAPIClient(api_key=api_key)
        self.analyzer = ConstellationAnalyzer()
        self.prompts = NarrativePrompts()
        self.cache = cache or (InMemoryCache() if use_cache else None)
        self.session_costs: Dict[str, float] = {}

    def generate(
        self,
        clicked_node_id: str,
        graph: KnowledgeGraph,
        session_id: str,
        max_cost_per_session: float = 1.0
    ) -> NarrativeResult:
        """
        Generate contextual narrative for clicked entity.

        Pipeline:
        1. Extract constellation around clicked node
        2. Identify optimal narrative hub
        3. Check session cost limit
        4. Check cache (session + graph hash)
        5. Select model based on complexity
        6. Generate narrative with single LLM call
        7. Extract highlighted events
        8. Cache result

        Args:
            clicked_node_id: ID of clicked entity
            graph: Knowledge graph
            session_id: User session ID
            max_cost_per_session: Max API cost per session (blocks at limit)

        Returns:
            NarrativeResult with narrative and metadata

        Raises:
            SessionCostLimitExceeded: If session cost exceeds limit
            InsufficientGraphData: If entity not found
        """
        logger.info(f"Generating narrative for {clicked_node_id} (session: {session_id})")

        # Step 1-2: Analyze constellation and identify hub
        constellation, hub_id = self.analyzer.analyze(clicked_node_id, graph)

        if not hub_id:
            raise InsufficientGraphData(f"Entity {clicked_node_id} not found in graph")

        # Step 3: Check session cost limit (before generating anything)
        current_cost = self.session_costs.get(session_id, 0.0)
        if current_cost >= max_cost_per_session:
            raise SessionCostLimitExceeded(session_id, current_cost, max_cost_per_session)

        # Handle insufficient data (< 3 entities)
        if len(constellation) < 3:
            return self._create_simple_narrative(hub_id, graph, session_id)

        # Step 4: Check cache
        if self.cache:
            graph_hash = self.cache.calculate_graph_hash(constellation, graph)
            cached = self.cache.get(session_id, hub_id, graph_hash)
            if cached:
                logger.info("Returning cached narrative")
                cached["from_cache"] = True
                return NarrativeResult(**cached)

        # Step 5: Select model
        model = self.analyzer.select_model(constellation, graph)

        # Step 6: Generate narrative
        hub_entity = graph.get_entity(hub_id)
        try:
            narrative_text, cost = self._generate_narrative(
                focal_entity_id=hub_id,
                focal_entity_name=hub_entity.get("name", "Unknown"),
                focal_entity_type=hub_entity.get("entity_type", "UNKNOWN"),
                constellation=constellation,
                graph=graph,
                model=model
            )
        except Exception as e:
            error_message = str(e).lower()
            if model == "sonnet" and "not_found" in error_message:
                logger.warning(
                    "Sonnet model unavailable, retrying narrative generation with Haiku."
                )
                model = "haiku"
                narrative_text, cost = self._generate_narrative(
                    focal_entity_id=hub_id,
                    focal_entity_name=hub_entity.get("name", "Unknown"),
                    focal_entity_type=hub_entity.get("entity_type", "UNKNOWN"),
                    constellation=constellation,
                    graph=graph,
                    model=model
                )
            else:
                raise

        # Update session cost
        self.session_costs[session_id] = self.session_costs.get(session_id, 0.0) + cost

        # Step 7: Extract highlighted events
        highlighted_events = self._extract_highlighted_events(constellation, graph)

        # Build result
        result = self._build_result(
            focal_entity_id=hub_id,
            focal_entity_name=hub_entity.get("name", "Unknown"),
            focal_entity_type=hub_entity.get("entity_type", "UNKNOWN"),
            constellation_size=len(constellation),
            model=model,
            narrative_text=narrative_text,
            highlighted_events=highlighted_events,
            graph=graph,
            constellation=constellation,
            generation_cost=cost
        )

        # Step 8: Cache result
        if self.cache:
            self.cache.set(
                session_id=session_id,
                focal_entity_id=hub_id,
                graph_hash=graph_hash,
                data=result.model_dump(),
                ttl=3600
            )

        return result

    def _generate_narrative(
        self,
        focal_entity_id: str,
        focal_entity_name: str,
        focal_entity_type: str,
        constellation: set,
        graph: KnowledgeGraph,
        model: str
    ) -> tuple[str, float]:
        """
        Single-stage narrative generation.

        Returns:
            (narrative_text, estimated_cost)
        """
        # Build graph context for prompt
        graph_context = self._build_graph_context(
            focal_entity_id=focal_entity_id,
            focal_entity_name=focal_entity_name,
            focal_entity_type=focal_entity_type,
            constellation=constellation,
            graph=graph
        )

        # Build prompt
        prompt = self.prompts.build_narrative_prompt(graph_context)

        # Call LLM
        model_name = "claude-3-haiku-latest" if model == "haiku" else "claude-3-5-sonnet-latest"

        narrative = self.api_client.call_with_retry(
            prompt=prompt,
            model=model_name
        )

        # Estimate cost (rough)
        input_tokens = len(prompt.split()) * 1.3  # Rough token estimate
        output_tokens = len(narrative.split()) * 1.3
        pricing = MODEL_PRICING[model]
        cost = (input_tokens * pricing["input"]) + (output_tokens * pricing["output"])

        logger.info(f"Generated narrative with {model}: ~{output_tokens:.0f} tokens, ${cost:.4f}")

        return narrative, cost

    def _build_graph_context(
        self,
        focal_entity_id: str,
        focal_entity_name: str,
        focal_entity_type: str,
        constellation: set,
        graph: KnowledgeGraph
    ) -> Dict[str, Any]:
        """Build graph context dict for prompt."""
        entities = []
        relations = []
        documents = set()
        seen_relations = set()

        for entity_id in constellation:
            entity = graph.get_entity(entity_id)
            if entity:
                entity_name = entity.get("name", entity_id)
                entity_type = entity.get("entity_type", "UNKNOWN")
                entities.append(f"{entity_name} ({entity_type})")

                extracted_from = entity.get("extracted_from", "")
                if extracted_from:
                    documents.update(doc.strip() for doc in extracted_from.split(",") if doc.strip())

            # Get relations
            rels = graph.get_relations(entity_id, direction="both")
            for rel in rels:
                source = rel.get("source")
                target = rel.get("target")
                if source in constellation and target in constellation:
                    relation_id = rel.get("relation_id")
                    if not relation_id:
                        relation_id = f"{source}->{target}:{rel.get('relation_type')}"
                    if relation_id in seen_relations:
                        continue
                    seen_relations.add(relation_id)
                    source_entity = graph.get_entity(source)
                    target_entity = graph.get_entity(target)
                    rel_type = rel.get("relation_type", "UNKNOWN")
                    date = rel.get("date", "")

                    relations.append({
                        "type": rel_type,
                        "source": source_entity.get("name", source) if source_entity else source,
                        "target": target_entity.get("name", target) if target_entity else target,
                        "date": date,
                        "document_id": rel.get("document_id") or rel.get("extracted_from"),
                        "evidence": rel.get("evidence")
                    })

        return {
            "focal_entity": {
                "name": focal_entity_name,
                "type": focal_entity_type
            },
            "entities": entities,
            "relations": relations,
            "documents": list(documents)
        }

    def _extract_highlighted_events(
        self,
        constellation: set,
        graph: KnowledgeGraph
    ) -> List[EventHighlight]:
        """Extract special events (CONFISCATED, SOLD, INHERITED) for highlighting."""
        highlighted = []
        citation_counter = 1
        seen_relations = set()  # Track processed relations to avoid duplicates

        for entity_id in constellation:
            relations = graph.get_relations(entity_id, direction="both")

            for rel in relations:
                rel_id = rel.get("relation_id")
                if rel_id in seen_relations:
                    continue  # Skip duplicate
                seen_relations.add(rel_id)

                rel_type_str = rel.get("relation_type", "")
                try:
                    rel_type = RelationType(rel_type_str)

                    if rel_type in [RelationType.CONFISCATED, RelationType.SOLD, RelationType.INHERITED]:
                        source_entity = graph.get_entity(rel.get("source"))
                        target_entity = graph.get_entity(rel.get("target"))

                        if not source_entity or not target_entity:
                            continue

                        event = EventHighlight(
                            event_type=rel_type.value,
                            summary=f"{source_entity.get('name', '?')} {rel_type.value.lower()} {target_entity.get('name', '?')}",
                            date=rel.get("date"),
                            citation_number=citation_counter,
                            evidence=[
                                EvidenceCitation(
                                    doc_id=rel.get("extracted_from", "unknown"),
                                    quote=rel.get("evidence", ""),
                                    confidence=rel.get("verification", {}).get("confidence", 0.8),
                                    verification_tier=rel.get("verification", {}).get("tier", VerificationTier.TIER_3_AI)
                                )
                            ],
                            parties_involved=[
                                source_entity.get("name", "Unknown"),
                                target_entity.get("name", "Unknown")
                            ]
                        )
                        highlighted.append(event)
                        citation_counter += 1

                except ValueError:
                    continue

        return highlighted

    def _build_result(
        self,
        focal_entity_id: str,
        focal_entity_name: str,
        focal_entity_type: str,
        constellation_size: int,
        model: str,
        narrative_text: str,
        highlighted_events: List[EventHighlight],
        graph: KnowledgeGraph,
        constellation: set,
        generation_cost: float
    ) -> NarrativeResult:
        """Build NarrativeResult from generation outputs."""
        # Count unique documents
        unique_docs = set()
        for entity_id in constellation:
            entity = graph.get_entity(entity_id)
            if entity:
                extracted_from = entity.get("extracted_from", "")
                if extracted_from:
                    unique_docs.update(doc.strip() for doc in extracted_from.split(",") if doc.strip())

        # Placeholder facts (narrative text contains inline citations)
        # In real implementation, would parse [①] markers and extract evidence
        facts = []

        return NarrativeResult(
            focal_entity_id=focal_entity_id,
            focal_entity_name=focal_entity_name,
            focal_entity_type=focal_entity_type,
            constellation_size=constellation_size,
            model_used=model,
            main_narrative=narrative_text,
            facts=facts,
            highlighted_events=highlighted_events,
            total_documents=len(unique_docs),
            total_citations=len(highlighted_events),  # Approximate
            generation_cost=generation_cost,
            from_cache=False
        )

    def _create_simple_narrative(
        self,
        entity_id: str,
        graph: KnowledgeGraph,
        session_id: str
    ) -> NarrativeResult:
        """Create simple narrative for insufficient data (< 3 entities)."""
        entity = graph.get_entity(entity_id)
        if not entity:
            raise InsufficientGraphData(f"Entity {entity_id} not found")

        name = entity.get("name", "Unknown")
        entity_type = entity.get("entity_type", "UNKNOWN")
        extracted_from = entity.get("extracted_from", "")
        if extracted_from:
            doc_count = len([doc for doc in extracted_from.split(",") if doc.strip()])
        else:
            doc_count = 0

        # Build context for simple prompt
        context = {
            "name": name,
            "type": entity_type,
            "document": extracted_from.split(",")[0].strip() if extracted_from else "unknown",
            "role": entity.get("profession") or entity.get("roles", [None])[0],
            "connections": []
        }

        # Get connected entities
        relations = graph.get_relations(entity_id, direction="both")
        for rel in relations[:3]:  # Max 3 connections
            other_id = rel.get("target") if rel.get("source") == entity_id else rel.get("source")
            other = graph.get_entity(other_id)
            if other:
                context["connections"].append(other.get("name", other_id))

        # Generate simple narrative
        prompt = self.prompts.build_simple_narrative_prompt(context)
        model_name = "claude-3-haiku-20240307"

        narrative = self.api_client.call_with_retry(
            prompt=prompt,
            model=model_name
        )

        # Minimal cost
        cost = 0.001

        # Update session cost
        self.session_costs[session_id] = self.session_costs.get(session_id, 0.0) + cost

        return NarrativeResult(
            focal_entity_id=entity_id,
            focal_entity_name=name,
            focal_entity_type=entity_type,
            constellation_size=1,
            model_used="haiku",
            main_narrative=narrative,
            facts=[],
            total_documents=doc_count,
            total_citations=0,
            generation_cost=cost,
            is_simple_entity=True
        )
