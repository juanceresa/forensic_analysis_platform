"""Batch case narrative generator — produces case_narrative.json during processing."""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from farmer_factory.config.settings import settings
from farmer_factory.extract.api_client import ClaudeAPIClient
from farmer_factory.narrative.models import (
    CaseNarrative,
    EventHighlight,
    NarrativeMetadata,
    NarrativePeriod,
)
from farmer_factory.narrative.prompts import build_period_prompt, build_summary_prompt
from farmer_factory.structure.graph import KnowledgeGraph

logger = logging.getLogger(__name__)

# Anthropic pricing (2026 estimates, per token)
MODEL_PRICING = {
    "haiku": {"input": 0.25 / 1_000_000, "output": 1.25 / 1_000_000},
    "sonnet": {"input": 3.00 / 1_000_000, "output": 15.00 / 1_000_000},
}

# Period labels for Cuban history context
PERIOD_LABELS = {
    (1910, 1929): "Early Property Records",
    (1930, 1944): "Pre-War Period",
    (1945, 1958): "Post-War Era",
    (1959, 1961): "Expropriation Period",
}


def _get_period_label(start_year: int, end_year: int) -> str:
    """Get contextual label for a time period."""
    for (lo, hi), label in PERIOD_LABELS.items():
        if start_year >= lo and end_year <= hi:
            return label
    return f"{start_year}-{end_year}"


def _estimate_cost(prompt: str, response: str, model: str) -> float:
    """Estimate API cost from prompt and response text."""
    input_tokens = len(prompt.split()) * 1.3
    output_tokens = len(response.split()) * 1.3
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["haiku"])
    return (input_tokens * pricing["input"]) + (output_tokens * pricing["output"])


def _prompt_hash(*prompts: str) -> str:
    """Hash prompt templates for reproducibility tracking."""
    combined = "".join(prompts)
    return hashlib.sha256(combined.encode()).hexdigest()[:12]


class CaseNarrativeGenerator:
    """Generates a complete case narrative organized by time periods.

    Pipeline:
    1. Load graph_data.json
    2. Group documents by decade, merge sparse adjacent periods (<3 docs)
    3. For each period: single LLM call with period context
    4. Final LLM call for case_summary
    5. Return CaseNarrative model
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_cost: float = 2.0,
        primary_model: str = "sonnet",
    ):
        self.api_client = ClaudeAPIClient(api_key=api_key)
        self.max_cost = max_cost
        self.primary_model = primary_model
        self.fallback_model = "haiku"
        self.total_cost = 0.0

    def generate(self, case_id: str, graph: KnowledgeGraph) -> CaseNarrative:
        """Generate the full case narrative.

        Args:
            case_id: Case identifier
            graph: Loaded knowledge graph

        Returns:
            CaseNarrative with metadata, case_summary, and periods
        """
        logger.info(f"Generating case narrative for {case_id}")

        # Step 1: Extract documents with dates from graph
        documents = self._extract_documents(graph)
        all_entities = self._extract_non_document_entities(graph)
        all_relations = self._extract_relations(graph)

        if not documents:
            logger.warning(f"No dated documents found for {case_id}")
            return self._empty_narrative(case_id)

        # Step 2: Group by decade, merge sparse periods
        period_groups = self._group_by_decade(documents)
        period_groups = self._merge_sparse_periods(period_groups)

        logger.info(f"Narrative will cover {len(period_groups)} periods")

        # Step 3: Generate per-period narratives
        narrative_periods: List[NarrativePeriod] = []
        for period_key, period_docs in sorted(period_groups.items()):
            period_entities = self._entities_for_documents(period_docs, all_entities, graph)
            period_relations = self._relations_for_period(period_entities, all_relations)

            start_year, end_year = self._parse_period_key(period_key)
            label = _get_period_label(start_year, end_year)

            narrative_period = self._generate_period(
                case_id=case_id,
                period_key=period_key,
                label=label,
                documents=period_docs,
                entities=period_entities,
                relations=period_relations,
            )
            narrative_periods.append(narrative_period)

        # Step 4: Generate case summary
        case_summary = self._generate_summary(
            case_id=case_id,
            documents=documents,
            all_entities=all_entities,
            periods=narrative_periods,
        )

        # Build metadata
        from farmer_factory.narrative.prompts import (
            CASE_SUMMARY_TEMPLATE,
            PERIOD_NARRATIVE_TEMPLATE,
        )

        metadata = NarrativeMetadata(
            case_id=case_id,
            generated_at=datetime.utcnow(),
            model_used=self.primary_model,
            model_version=self._model_id(self.primary_model),
            prompt_hash=_prompt_hash(PERIOD_NARRATIVE_TEMPLATE, CASE_SUMMARY_TEMPLATE),
            generation_cost=self.total_cost,
            factory_version="1.6.0",
        )

        logger.info(
            f"Case narrative complete: {len(narrative_periods)} periods, "
            f"${self.total_cost:.4f} total cost"
        )

        return CaseNarrative(
            metadata=metadata,
            case_summary=case_summary,
            periods=narrative_periods,
        )

    def generate_and_save(
        self, case_id: str, graph: KnowledgeGraph, output_dir: Path
    ) -> Path:
        """Generate narrative and write to case_narrative.json.

        Args:
            case_id: Case identifier
            graph: Loaded knowledge graph
            output_dir: Directory to write case_narrative.json

        Returns:
            Path to the written file
        """
        narrative = self.generate(case_id, graph)
        output_path = output_dir / "case_narrative.json"
        output_path.write_text(
            narrative.model_dump_json(indent=2),
            encoding="utf-8",
        )
        logger.info(f"Wrote case narrative to {output_path}")
        return output_path

    # ── Period grouping ──────────────────────────────────────────────

    def _extract_documents(self, graph: KnowledgeGraph) -> List[Dict[str, Any]]:
        """Extract DOCUMENT entities with dates from the graph."""
        documents = []
        for node_id in graph.graph.nodes:
            node = graph.get_entity(node_id)
            if not node or node.get("entity_type") != "DOCUMENT":
                continue
            documents.append(
                {
                    "id": node_id,
                    "name": node.get("name", node_id),
                    "date": node.get("date"),
                    "document_type": node.get("document_type"),
                }
            )
        return documents

    def _extract_non_document_entities(
        self, graph: KnowledgeGraph
    ) -> List[Dict[str, Any]]:
        """Extract all non-DOCUMENT entities."""
        entities = []
        for node_id in graph.graph.nodes:
            node = graph.get_entity(node_id)
            if not node or node.get("entity_type") == "DOCUMENT":
                continue
            entities.append(
                {
                    "id": node_id,
                    "name": node.get("name", node_id),
                    "entity_type": node.get("entity_type", "UNKNOWN"),
                    "extracted_from": node.get("extracted_from", ""),
                }
            )
        return entities

    def _extract_relations(self, graph: KnowledgeGraph) -> List[Dict[str, Any]]:
        """Extract all relations from the graph."""
        relations = []
        seen = set()
        for node_id in graph.graph.nodes:
            for rel in graph.get_relations(node_id, direction="out"):
                rel_key = (
                    rel.get("source"),
                    rel.get("target"),
                    rel.get("relation_type"),
                )
                if rel_key in seen:
                    continue
                seen.add(rel_key)
                source_entity = graph.get_entity(rel.get("source"))
                target_entity = graph.get_entity(rel.get("target"))
                relations.append(
                    {
                        "source": rel.get("source"),
                        "target": rel.get("target"),
                        "source_name": source_entity.get("name", rel.get("source", "?"))
                        if source_entity
                        else rel.get("source", "?"),
                        "target_name": target_entity.get("name", rel.get("target", "?"))
                        if target_entity
                        else rel.get("target", "?"),
                        "relation_type": rel.get("relation_type", "UNKNOWN"),
                        "date": rel.get("date"),
                    }
                )
        return relations

    def _group_by_decade(
        self, documents: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group documents into decade-based periods."""
        periods: Dict[str, List[Dict[str, Any]]] = {}
        for doc in documents:
            date_str = doc.get("date")
            if not date_str:
                continue
            try:
                year = int(str(date_str)[:4])
            except (ValueError, TypeError):
                continue
            start = (year // 10) * 10
            end = start + 9
            key = f"{start}-{end}"
            periods.setdefault(key, []).append(doc)
        return periods

    def _merge_sparse_periods(
        self, periods: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Merge adjacent periods that each have <3 documents."""
        if len(periods) <= 1:
            return periods

        sorted_keys = sorted(periods.keys())
        merged: Dict[str, List[Dict[str, Any]]] = {}
        i = 0

        while i < len(sorted_keys):
            key = sorted_keys[i]
            docs = periods[key]

            # Check if this and next period are both sparse
            if (
                i + 1 < len(sorted_keys)
                and len(docs) < 3
                and len(periods[sorted_keys[i + 1]]) < 3
            ):
                next_key = sorted_keys[i + 1]
                next_docs = periods[next_key]
                # Merge into combined key
                start = key.split("-")[0]
                end = next_key.split("-")[1]
                combined_key = f"{start}-{end}"
                merged[combined_key] = docs + next_docs
                i += 2
            else:
                merged[key] = docs
                i += 1

        return merged

    def _parse_period_key(self, key: str) -> Tuple[int, int]:
        """Parse '1950-1959' into (1950, 1959)."""
        parts = key.split("-")
        return int(parts[0]), int(parts[1])

    def _entities_for_documents(
        self,
        documents: List[Dict[str, Any]],
        all_entities: List[Dict[str, Any]],
        graph: KnowledgeGraph,
    ) -> List[Dict[str, Any]]:
        """Find entities referenced by the given documents."""
        doc_ids = {doc["id"] for doc in documents}
        matched = []
        for ent in all_entities:
            extracted_from = ent.get("extracted_from", "")
            if not extracted_from:
                continue
            ent_doc_ids = {d.strip() for d in extracted_from.split(",") if d.strip()}
            if ent_doc_ids & doc_ids:
                matched.append(ent)
        return matched

    def _relations_for_period(
        self,
        period_entities: List[Dict[str, Any]],
        all_relations: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Filter relations to those between entities in this period."""
        entity_ids = {e["id"] for e in period_entities}
        return [
            r
            for r in all_relations
            if r.get("source") in entity_ids or r.get("target") in entity_ids
        ]

    # ── LLM generation ───────────────────────────────────────────────

    def _generate_period(
        self,
        case_id: str,
        period_key: str,
        label: str,
        documents: List[Dict[str, Any]],
        entities: List[Dict[str, Any]],
        relations: List[Dict[str, Any]],
    ) -> NarrativePeriod:
        """Generate narrative for a single period."""
        start_year, end_year = self._parse_period_key(period_key)

        prompt = build_period_prompt(
            period_label=label,
            period_range=period_key,
            documents=documents,
            entities=entities,
            relations=relations,
        )

        narrative_text, cost = self._call_llm(prompt)

        # Extract highlighted events from relations
        highlighted = self._extract_highlighted_events(entities, relations)

        # Evidence: document and relation summaries
        evidence = [f"doc:{d['id']}" for d in documents]
        for r in relations:
            evidence.append(
                f"rel:{r.get('relation_type')}:{r.get('source_name')}->{r.get('target_name')}"
            )

        return NarrativePeriod(
            period_id=period_key,
            label=label,
            narrative=narrative_text,
            document_ids=[d["id"] for d in documents],
            entity_ids=[e["id"] for e in entities],
            highlighted_events=highlighted,
            evidence=evidence,
        )

    def _generate_summary(
        self,
        case_id: str,
        documents: List[Dict[str, Any]],
        all_entities: List[Dict[str, Any]],
        periods: List[NarrativePeriod],
    ) -> str:
        """Generate overall case summary from period narratives."""
        # Determine date range
        dated_docs = [d for d in documents if d.get("date")]
        if dated_docs:
            years = []
            for d in dated_docs:
                try:
                    years.append(int(str(d["date"])[:4]))
                except (ValueError, TypeError):
                    pass
            date_range = f"{min(years)}-{max(years)}" if years else "Unknown"
        else:
            date_range = "Unknown"

        period_summaries = [
            {
                "label": p.label,
                "range": p.period_id,
                "narrative": p.narrative,
            }
            for p in periods
        ]

        prompt = build_summary_prompt(
            case_id=case_id,
            date_range=date_range,
            total_documents=len(documents),
            total_entities=len(all_entities),
            period_summaries=period_summaries,
        )

        summary_text, cost = self._call_llm(prompt)
        return summary_text

    def _call_llm(self, prompt: str) -> Tuple[str, float]:
        """Call the LLM with cost tracking and model downgrade on failure.

        Returns:
            (response_text, cost)

        Raises:
            RuntimeError: If cost limit exceeded before call
        """
        if self.total_cost >= self.max_cost:
            raise RuntimeError(
                f"Case narrative cost limit exceeded: "
                f"${self.total_cost:.4f} >= ${self.max_cost:.2f}"
            )

        model = self.primary_model
        model_id = self._model_id(model)

        try:
            response = self.api_client.call_with_retry(
                prompt=prompt,
                model=model_id,
            )
        except Exception as e:
            if model != self.fallback_model:
                logger.warning(
                    f"{model} failed ({e}), downgrading to {self.fallback_model}"
                )
                model = self.fallback_model
                model_id = self._model_id(model)
                response = self.api_client.call_with_retry(
                    prompt=prompt,
                    model=model_id,
                )
            else:
                raise

        cost = _estimate_cost(prompt, response, model)
        self.total_cost += cost
        logger.debug(f"LLM call ({model}): ${cost:.4f} (total: ${self.total_cost:.4f})")
        return response, cost

    def _extract_highlighted_events(
        self,
        entities: List[Dict[str, Any]],
        relations: List[Dict[str, Any]],
    ) -> List[EventHighlight]:
        """Extract CONFISCATED, SOLD, INHERITED events from relations."""
        highlighted = []
        for rel in relations:
            rel_type = rel.get("relation_type", "")
            if rel_type in ("CONFISCATED", "SOLD", "INHERITED"):
                highlighted.append(
                    EventHighlight(
                        event_type=rel_type,
                        summary=f"{rel.get('source_name', '?')} {rel_type.lower()} {rel.get('target_name', '?')}",
                        date=rel.get("date"),
                        parties_involved=[
                            rel.get("source_name", "Unknown"),
                            rel.get("target_name", "Unknown"),
                        ],
                    )
                )
        return highlighted

    def _empty_narrative(self, case_id: str) -> CaseNarrative:
        """Return empty narrative when no dated documents exist."""
        return CaseNarrative(
            metadata=NarrativeMetadata(
                case_id=case_id,
                model_used="none",
                generation_cost=0.0,
            ),
            case_summary="No dated documents available for narrative generation.",
            periods=[],
        )

    @staticmethod
    def _model_id(model: str) -> str:
        """Map short model name to full Anthropic model ID."""
        return {
            "haiku": settings.claude_model,
            "sonnet": settings.claude_model_retry,
        }.get(model, settings.claude_model)
