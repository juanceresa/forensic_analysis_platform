"""Data preparer for dossier generation.

Assembles DossierData from KnowledgeGraph and extraction files.
"""

import json
import logging
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from farmer_factory.structure.graph import KnowledgeGraph
from farmer_factory.structure.schema import VerificationTier

from .models import (
    DossierData,
    DocumentSummary,
    EvidenceCitation,
    FamilyMember,
    FamilyTreeData,
    OwnershipPeriod,
    PropertyData,
    TimelineEvent,
    VerificationStats,
    STANDARD_DISCLAIMER,
)

logger = logging.getLogger(__name__)


class PrepareError(Exception):
    """Raised when data preparation fails."""

    pass


class DossierPreparer:
    """Assembles DossierData from case artifacts.

    Reads from:
    - graph_data.json (deduplicated entities and relations)
    - extractions/*.json (for richer evidence quotes, optional)
    """

    # Event types that should appear in timeline
    TIMELINE_EVENT_TYPES = {
        "OWNS": "ACQUISITION",
        "OWNED": "OWNERSHIP",
        "INHERITED": "INHERITANCE",
        "SOLD": "SALE",
        "SOLD_TO": "SALE",
        "BOUGHT": "PURCHASE",
        "CONFISCATED": "CONFISCATION",
    }

    # Relation types indicating ownership
    OWNERSHIP_RELATIONS = {"OWNS", "OWNED", "INHERITED", "SOLD", "SOLD_TO", "BOUGHT", "CONFISCATED"}
    UNDATED_SENTINEL = "9999-99-99"

    def __init__(self, case_id: str, case_path: Path | None = None):
        """Initialize the preparer.

        Args:
            case_id: Case identifier
            case_path: Path to case directory (defaults to cases/{case_id})
        """
        self.case_id = case_id
        self.case_path = case_path or Path(f"cases/{case_id}")
        self._extractions_cache: dict[str, dict] = {}

    def prepare(
        self,
        focal_property_id: str,
        focal_family_member_id: str,
    ) -> DossierData:
        """Build complete DossierData for PDF generation.

        Args:
            focal_property_id: The property being claimed
            focal_family_member_id: Primary claimant or family representative

        Returns:
            Complete DossierData ready for rendering

        Raises:
            PrepareError: If required data is missing or invalid
        """
        # 1. Load graph
        graph_path = self.case_path / "output" / "graph_data.json"
        if not graph_path.exists():
            raise PrepareError(f"Graph data not found: {graph_path}")

        graph = KnowledgeGraph.load(graph_path)

        # 2. Resolve and validate focal entities (supports name-based lookup)
        resolved_property_id = self._assert_entity_exists(
            graph, focal_property_id, expected_type="PROPERTY"
        )
        resolved_family_member_id = self._assert_entity_exists(
            graph, focal_family_member_id, expected_type="PERSON"
        )

        # 3. Load extractions (optional, for richer evidence)
        self._load_extractions()

        # 4. Build sections
        timeline = self._build_timeline(graph)
        family = self._build_family_tree(graph, resolved_family_member_id)
        property_data = self._build_property(graph, resolved_property_id)
        ownership_history = self._build_ownership_chain(graph, resolved_property_id)
        documents = self._build_document_inventory(graph)

        # 5. Calculate verification stats
        verification_stats = self._calculate_verification_stats(
            graph, timeline, ownership_history, documents
        )

        # 6. Generate executive summary
        executive_summary = self._generate_executive_summary(
            family, property_data, ownership_history
        )

        # 7. Derive case title
        case_title = self._derive_case_title(family, property_data)

        return DossierData(
            case_id=self.case_id,
            case_title=case_title,
            generated_at=datetime.now(),
            executive_summary=executive_summary,
            timeline=timeline,
            family=family,
            property=property_data,
            ownership_history=ownership_history,
            documents=documents,
            verification_stats=verification_stats,
            disclaimer_text=STANDARD_DISCLAIMER,
        )

    def _resolve_entity_id(
        self, graph: KnowledgeGraph, identifier: str, expected_type: str | None = None
    ) -> str:
        """Resolve an entity identifier to its actual ID.

        Supports:
        - Exact ID match
        - Name-based lookup (case-insensitive, partial match)

        Args:
            graph: KnowledgeGraph instance
            identifier: Entity ID or name to find
            expected_type: Expected entity type (optional, used to narrow search)

        Returns:
            The resolved entity ID

        Raises:
            PrepareError: If entity not found or ambiguous
        """
        # Try exact ID match first
        entity = graph.get_entity(identifier)
        if entity is not None:
            if expected_type:
                actual_type = entity.get("entity_type")
                if actual_type != expected_type:
                    raise PrepareError(
                        f"Entity {identifier} is type {actual_type}, expected {expected_type}"
                    )
            return identifier

        # Fall back to name-based search
        identifier_lower = identifier.lower().strip()
        matches: list[tuple[str, dict]] = []

        for node_id in graph.graph.nodes():
            node_data = graph.get_entity(node_id)
            if not node_data:
                continue

            # Filter by type if specified
            if expected_type and node_data.get("entity_type") != expected_type:
                continue

            # Check name match
            name = node_data.get("name", "")
            if name and identifier_lower in name.lower():
                matches.append((node_id, node_data))

        if not matches:
            raise PrepareError(
                f"Entity not found: '{identifier}'. "
                f"Use 'list-entities' command to see available entities."
            )

        if len(matches) == 1:
            logger.info(f"Resolved '{identifier}' to entity ID: {matches[0][0]}")
            return matches[0][0]

        # Multiple matches - check for exact name match
        exact_matches = [
            (nid, data) for nid, data in matches
            if data.get("name", "").lower() == identifier_lower
        ]
        if len(exact_matches) == 1:
            logger.info(f"Resolved '{identifier}' to entity ID: {exact_matches[0][0]}")
            return exact_matches[0][0]

        # Ambiguous - list options
        options = "\n".join(
            f"  - {data.get('name', 'Unnamed')} (ID: {nid})"
            for nid, data in matches[:5]
        )
        raise PrepareError(
            f"Ambiguous entity name '{identifier}'. Multiple matches found:\n{options}\n"
            f"Please use the exact ID or a more specific name."
        )

    def _assert_entity_exists(
        self, graph: KnowledgeGraph, entity_id: str, expected_type: str | None = None
    ) -> str:
        """Verify an entity exists and return its resolved ID.

        Args:
            graph: KnowledgeGraph instance
            entity_id: Entity ID or name to check
            expected_type: Expected entity type (optional)

        Returns:
            The resolved entity ID

        Raises:
            PrepareError: If entity not found or wrong type
        """
        return self._resolve_entity_id(graph, entity_id, expected_type)

    def _load_extractions(self) -> None:
        """Load extraction JSON files for richer evidence quotes."""
        extractions_dir = self.case_path / "extractions"
        if not extractions_dir.exists():
            logger.warning(f"Extractions directory not found: {extractions_dir}")
            return

        for json_file in extractions_dir.glob("*.json"):
            try:
                data = json.loads(json_file.read_text())
                doc_id = json_file.stem
                self._extractions_cache[doc_id] = data
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load extraction {json_file}: {e}")

        logger.info(f"Loaded {len(self._extractions_cache)} extraction files")

    def _build_timeline(self, graph: KnowledgeGraph) -> list[TimelineEvent]:
        """Build chronological timeline from graph data.

        Args:
            graph: KnowledgeGraph instance

        Returns:
            List of TimelineEvents sorted by date
        """
        events: list[TimelineEvent] = []

        # Extract events from relations
        for node_id in graph.graph.nodes():
            for relation in graph.get_relations(node_id, direction="out"):
                relation_type = relation.get("relation_type", "")

                # Skip non-event relations
                if relation_type not in self.TIMELINE_EVENT_TYPES:
                    continue

                event_type = self.TIMELINE_EVENT_TYPES[relation_type]
                date = relation.get("date")
                date_sortable = relation.get("date_sortable") or self._normalize_date(date)
                if not date_sortable:
                    date_sortable = self.UNDATED_SENTINEL

                # Get entity names
                source_entity = graph.get_entity(relation["source"])
                target_entity = graph.get_entity(relation["target"])
                entities_involved = []
                if source_entity:
                    entities_involved.append(source_entity.get("name", relation["source"]))
                if target_entity:
                    entities_involved.append(target_entity.get("name", relation["target"]))

                # Build summary
                summary = self._build_event_summary(
                    event_type, source_entity, target_entity, relation
                )

                # Get verification
                verification = relation.get("verification", {})
                tier_str = verification.get("tier", "TIER_3_AI")
                tier = self._parse_verification_tier(tier_str)

                events.append(
                    TimelineEvent(
                        date=date,
                        date_sortable=None if date_sortable == self.UNDATED_SENTINEL else date_sortable,
                        event_type=event_type,
                        summary=summary,
                        entities_involved=entities_involved,
                        source_doc_id=relation.get("document_id"),
                        verification_tier=tier,
                    )
                )

        # Add birth/death events for persons
        for node_id in graph.graph.nodes():
            entity = graph.get_entity(node_id)
            if not entity or entity.get("entity_type") != "PERSON":
                continue

            name = entity.get("name", "Unknown")
            verification = entity.get("verification", {})
            tier = self._parse_verification_tier(verification.get("tier", "TIER_3_AI"))

            if entity.get("birth_date"):
                events.append(
                    TimelineEvent(
                        date=entity["birth_date"],
                        date_sortable=self._normalize_date(entity["birth_date"]),
                        event_type="BIRTH",
                        summary=f"{name} born",
                        entities_involved=[name],
                        verification_tier=tier,
                    )
                )

            if entity.get("death_date"):
                events.append(
                    TimelineEvent(
                        date=entity["death_date"],
                        date_sortable=self._normalize_date(entity["death_date"]),
                        event_type="DEATH",
                        summary=f"{name} died",
                        entities_involved=[name],
                        verification_tier=tier,
                    )
                )

        # Sort by date (None values at end)
        events.sort(key=lambda e: (e.date_sortable or self.UNDATED_SENTINEL, e.event_type))

        return events

    def _build_family_tree(
        self, graph: KnowledgeGraph, focal_person_id: str
    ) -> FamilyTreeData:
        """Build family tree from person entities.

        Args:
            graph: KnowledgeGraph instance
            focal_person_id: ID of primary claimant

        Returns:
            FamilyTreeData with members and lineage
        """
        # Get focal person
        focal_entity = graph.get_entity(focal_person_id)
        if not focal_entity:
            raise PrepareError(f"Focal person not found: {focal_person_id}")

        primary_claimant = self._entity_to_family_member(focal_entity, focal_person_id)

        # Find all related persons
        members: list[FamilyMember] = []
        family_relations = {"CHILD_OF", "SPOUSE_OF", "HEIR_OF", "RELATED_TO"}

        # Get all person entities and their relations to focal
        for node_id in graph.graph.nodes():
            if node_id == focal_person_id:
                continue

            entity = graph.get_entity(node_id)
            if not entity or entity.get("entity_type") != "PERSON":
                continue

            # Check if related to focal person
            relation_to_focal = self._find_relation_to_focal(
                graph, node_id, focal_person_id, family_relations
            )

            if relation_to_focal:
                member = self._entity_to_family_member(
                    entity, node_id, relation_to_claimant=relation_to_focal
                )
                members.append(member)

        # Generate lineage summary
        lineage_summary = self._generate_lineage_summary(primary_claimant, members)

        return FamilyTreeData(
            primary_claimant=primary_claimant,
            members=members,
            lineage_summary=lineage_summary,
        )

    def _build_property(self, graph: KnowledgeGraph, property_id: str) -> PropertyData:
        """Build property section from property entity.

        Args:
            graph: KnowledgeGraph instance
            property_id: ID of focal property

        Returns:
            PropertyData
        """
        entity = graph.get_entity(property_id)
        if not entity:
            raise PrepareError(f"Property not found: {property_id}")

        verification = entity.get("verification", {})
        tier = self._parse_verification_tier(verification.get("tier", "TIER_3_AI"))

        # Build location description
        location_parts = []
        if entity.get("address"):
            location_parts.append(entity["address"])
        # Try to get location name from related location entity
        for relation in graph.get_relations(property_id, direction="out"):
            if relation.get("relation_type") == "LOCATED_IN":
                loc_entity = graph.get_entity(relation["target"])
                if loc_entity:
                    location_parts.append(loc_entity.get("name", ""))

        return PropertyData(
            entity_id=property_id,
            name=entity.get("name"),
            property_type=entity.get("property_type"),
            address=entity.get("address"),
            location_description=", ".join(filter(None, location_parts)) or "Cuba",
            area=entity.get("area"),
            area_unit=entity.get("area_unit"),
            registry_info=self._build_registry_info(entity),
            description=entity.get("description"),
            map_image_path=None,  # Geolocation module not yet implemented
            verification_tier=tier,
        )

    def _build_ownership_chain(
        self, graph: KnowledgeGraph, property_id: str
    ) -> list[OwnershipPeriod]:
        """Build ownership history from relations.

        Args:
            graph: KnowledgeGraph instance
            property_id: ID of focal property

        Returns:
            List of OwnershipPeriods in chronological order
        """
        periods: list[OwnershipPeriod] = []

        # Get all relations involving this property
        relations = graph.get_relations(property_id, direction="both")

        # Filter to ownership-related relations
        ownership_events = []
        for rel in relations:
            rel_type = rel.get("relation_type", "")
            if rel_type in self.OWNERSHIP_RELATIONS:
                ownership_events.append(rel)

        # Normalize dates and sort; undated last
        def sort_key(rel: dict) -> tuple[str, str]:
            ds = rel.get("date_sortable") or self._normalize_date(rel.get("date"))
            if not ds:
                ds = self.UNDATED_SENTINEL
            return (ds, rel.get("relation_type", ""))

        ownership_events.sort(key=sort_key)

        # Group adjacent events by owner and period_type when dates are the same
        grouped: list[dict[str, Any]] = []
        for rel in ownership_events:
            rel_type = rel.get("relation_type", "OWNS")
            period_type = self._map_period_type(rel_type, periods)
            date_norm = self._normalize_date(rel.get("date"))
            source_entity = graph.get_entity(rel["source"])
            owner_name = source_entity.get("name", "Unknown") if source_entity else "Unknown"
            doc_id = rel.get("document_id")
            evidence = []
            if doc_id:
                verification = rel.get("verification", {})
                tier = self._parse_verification_tier(verification.get("tier", "TIER_3_AI"))
                quote = rel.get("evidence")
                # Try to augment from extractions
                extraction = self._extractions_cache.get(doc_id, {})
                extracted_quote = extraction.get("quote") or extraction.get("text")
                if extracted_quote and not quote:
                    quote = extracted_quote
                evidence.append(
                    EvidenceCitation(
                        doc_id=doc_id,
                        doc_title=None,
                        page=extraction.get("page"),
                        quote=quote,
                        verification_tier=tier,
                    )
                )
            narrative = self._build_ownership_narrative(rel_type, rel, graph)

            if grouped:
                last = grouped[-1]
                same_owner = owner_name in last["owner_names"]
                same_period = last["period_type"] == period_type
                same_date = (last["start_date"] == date_norm) or (last["start_date"] is None and date_norm is None)
                if same_owner and same_period and same_date:
                    last["evidence"].extend(evidence)
                    continue

            grouped.append(
                {
                    "period_type": period_type,
                    "start_date": date_norm,
                    "owner_names": [owner_name],
                    "narrative": narrative,
                    "evidence": evidence,
                }
            )

        # Fill in end dates (only when next period has a real date)
        periods_out: list[OwnershipPeriod] = []
        for i, g in enumerate(grouped):
            end_date = None
            if i < len(grouped) - 1:
                next_start = grouped[i + 1]["start_date"]
                if next_start and next_start != self.UNDATED_SENTINEL:
                    end_date = next_start
            periods_out.append(
                OwnershipPeriod(
                    period_type=g["period_type"],
                    start_date=g["start_date"],
                    end_date=end_date,
                    owner_names=g["owner_names"],
                    narrative=g["narrative"],
                    evidence=g["evidence"],
                )
            )

        return periods_out

    def _map_period_type(self, rel_type: str, existing: list[OwnershipPeriod]) -> str:
        """Map relation type to period type with sensible defaults."""
        if rel_type in {"OWNS", "OWNED", "BOUGHT"}:
            return "ACQUISITION" if not existing else "OWNERSHIP"
        if rel_type == "INHERITED":
            return "INHERITANCE"
        if rel_type in {"SOLD", "SOLD_TO"}:
            return "SALE"
        if rel_type == "CONFISCATED":
            return "CONFISCATION"
        return "OWNERSHIP"

    def _build_document_inventory(self, graph: KnowledgeGraph) -> list[DocumentSummary]:
        """Build document inventory from document entities.

        Args:
            graph: KnowledgeGraph instance

        Returns:
            List of DocumentSummary objects
        """
        documents: list[DocumentSummary] = []

        for node_id in graph.graph.nodes():
            entity = graph.get_entity(node_id)
            if not entity or entity.get("entity_type") != "DOCUMENT":
                continue

            verification = entity.get("verification", {})
            tier = self._parse_verification_tier(verification.get("tier", "TIER_3_AI"))

            # Find entities mentioned in this document
            key_entities = self._find_entities_in_document(graph, node_id)

            # Determine what document proves
            what_it_proves = self._determine_what_document_proves(graph, node_id, entity)

            # Normalize date for sorting
            date_norm = self._normalize_date(entity.get("date")) or self.UNDATED_SENTINEL

            documents.append(
                DocumentSummary(
                    doc_id=node_id,
                    title=entity.get("title"),
                    document_type=entity.get("document_type", "Unknown"),
                    date=entity.get("date"),
                    page_count=entity.get("page_count", 1),
                    what_it_proves=what_it_proves,
                    key_entities=key_entities,
                    verification_tier=tier,
                    verification_confidence=verification.get("confidence"),
                    extracted_from=entity.get("extracted_from", "").split(", ") if entity.get("extracted_from") else None,
                    # store sortable date internally if needed
                    # date_sortable=date_norm,
                )
            )

        # Sort by normalized date; undated last
        documents.sort(key=lambda d: self._normalize_date(d.date) or self.UNDATED_SENTINEL)

        return documents

    def _calculate_verification_stats(
        self,
        graph: KnowledgeGraph,
        timeline: list[TimelineEvent],
        ownership_history: list[OwnershipPeriod],
        documents: list[DocumentSummary],
    ) -> VerificationStats:
        """Calculate aggregate verification statistics.

        Args:
            graph: KnowledgeGraph instance
            timeline: Timeline events
            ownership_history: Ownership periods
            documents: Document inventory

        Returns:
            VerificationStats
        """
        tier_counts: Counter[str] = Counter()
        section_breakdown: dict[str, dict[str, int]] = {}

        # Count timeline tiers
        timeline_tiers: Counter[str] = Counter()
        for event in timeline:
            tier_str = event.verification_tier.value
            tier_counts[tier_str] += 1
            timeline_tiers[tier_str] += 1
        section_breakdown["timeline"] = dict(timeline_tiers)

        # Count ownership tiers
        ownership_tiers: Counter[str] = Counter()
        for period in ownership_history:
            for evidence in period.evidence:
                tier_str = evidence.verification_tier.value
                tier_counts[tier_str] += 1
                ownership_tiers[tier_str] += 1
        section_breakdown["ownership"] = dict(ownership_tiers)

        # Count document tiers
        document_tiers: Counter[str] = Counter()
        for doc in documents:
            tier_str = doc.verification_tier.value
            tier_counts[tier_str] += 1
            document_tiers[tier_str] += 1
        section_breakdown["documents"] = dict(document_tiers)

        # Calculate overall confidence (weighted by tier)
        tier_weights = {
            "TIER_3_AI": 0.5,
            "TIER_2_ANALYST": 0.75,
            "TIER_2_INSTITUTIONAL": 0.85,
            "TIER_1_CERTIFIED": 1.0,
        }
        total_weight = 0.0
        total_count = 0
        for tier, count in tier_counts.items():
            weight = tier_weights.get(tier, 0.5)
            total_weight += weight * count
            total_count += count

        overall_confidence = total_weight / total_count if total_count > 0 else 0.0

        return VerificationStats(
            total_data_points=sum(tier_counts.values()),
            tier_distribution=dict(tier_counts),
            overall_confidence=overall_confidence,
            section_breakdown=section_breakdown,
        )

    def _generate_executive_summary(
        self,
        family: FamilyTreeData,
        property_data: PropertyData,
        ownership_history: list[OwnershipPeriod],
    ) -> str:
        """Generate executive summary using LLM.

        Uses hybrid approach: template extracts facts, LLM polishes prose.

        Args:
            family: Family tree data
            property_data: Property data
            ownership_history: Ownership history

        Returns:
            2-paragraph executive summary
        """
        # Extract key facts
        family_name = family.primary_claimant.name
        property_name = property_data.name or property_data.address or "the property"
        location = property_data.location_description

        # Determine acquisition and loss dates
        acquired = "Unknown"
        lost = "Unknown"
        loss_type = "Unknown"

        if ownership_history:
            first_period = ownership_history[0]
            acquired = first_period.start_date or "Unknown"

            last_period = ownership_history[-1]
            if last_period.period_type in {"CONFISCATION", "SALE"}:
                lost = last_period.start_date or "Unknown"
                loss_type = last_period.period_type.lower()

        # Try to use LLM for polished summary
        try:
            return self._generate_summary_with_llm(
                family_name, property_name, location, acquired, lost, loss_type
            )
        except Exception as e:
            logger.warning(f"LLM summary generation failed, using template: {e}")
            return self._generate_summary_template(
                family_name, property_name, location, acquired, lost, loss_type
            )

    def _generate_summary_with_llm(
        self,
        family_name: str,
        property_name: str,
        location: str,
        acquired: str,
        lost: str,
        loss_type: str,
    ) -> str:
        """Generate polished summary using Claude API.

        Args:
            Various facts extracted from case data

        Returns:
            Polished 2-paragraph summary
        """
        from anthropic import Anthropic

        client = Anthropic(timeout=10)  # guard hangs

        facts = f"""
Family: {family_name}
Property: {property_name}
Location: {location}
Acquired: {acquired}
Lost: {lost}
Loss type: {loss_type}
"""

        prompt = f"""Write a 2-paragraph executive summary for a property restitution dossier.
Use ONLY the facts provided. Do not add information or make legal conclusions.
Do not use phrases like "strong case" or "proves ownership."

Facts:
{facts}

Paragraph 1: Who the family is and what they owned.
Paragraph 2: What happened to the property and current documentation status."""

        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=350,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
            timeout=10,
        )

        return response.content[0].text if response.content else ""

    def _generate_summary_template(
        self,
        family_name: str,
        property_name: str,
        location: str,
        acquired: str,
        lost: str,
        loss_type: str,
    ) -> str:
        """Generate summary using template (fallback).

        Args:
            Various facts extracted from case data

        Returns:
            Template-based 2-paragraph summary
        """
        para1 = f"The {family_name} family owned {property_name} in {location}. "
        if acquired != "Unknown":
            para1 += f"The property was acquired in {acquired}."
        else:
            para1 += "The date of acquisition is documented in the attached records."

        para2 = ""
        if loss_type == "confiscation":
            para2 = f"The property was confiscated"
            if lost != "Unknown":
                para2 += f" in {lost}"
            para2 += " during the Cuban Revolution. "
        elif loss_type == "sale":
            para2 = f"The property was sold"
            if lost != "Unknown":
                para2 += f" in {lost}"
            para2 += ". "
        else:
            para2 = "The ownership history is documented in the attached records. "

        para2 += "This dossier presents the forensic evidence supporting the family's connection to the property."

        return f"{para1}\n\n{para2}"

    def _derive_case_title(self, family: FamilyTreeData, property_data: PropertyData) -> str:
        """Derive a case title from family and property data.

        Args:
            family: Family tree data
            property_data: Property data

        Returns:
            Case title string
        """
        # Extract family surname
        full_name = family.primary_claimant.name
        name_parts = full_name.split() if full_name else []
        surname = name_parts[-1] if name_parts else "Unknown"

        return f"{surname} Family Property Claim"

    # =========================================================================
    # Helper methods
    # =========================================================================

    def _parse_verification_tier(self, tier_str: str) -> VerificationTier:
        """Parse verification tier string to enum."""
        try:
            return VerificationTier(tier_str)
        except ValueError:
            return VerificationTier.TIER_3_AI

    def _normalize_date(self, date_str: str | None) -> str | None:
        """Normalize date string to sortable format.

        Handles various formats: ISO, year-only, "circa 1950s"
        """
        if not date_str:
            return None

        # Already ISO format
        if len(date_str) == 10 and date_str[4] == "-":
            return date_str

        # Year only
        if date_str.isdigit() and len(date_str) == 4:
            return f"{date_str}-01-01"

        # "circa 1950s" or similar
        import re

        match = re.search(r"(\d{4})", date_str)
        if match:
            return f"{match.group(1)}-01-01"

        return None

    def _build_event_summary(
        self,
        event_type: str,
        source_entity: dict | None,
        target_entity: dict | None,
        relation: dict,
    ) -> str:
        """Build a human-readable summary for a timeline event."""
        source_name = source_entity.get("name", "Unknown") if source_entity else "Unknown"
        target_name = target_entity.get("name", "Unknown") if target_entity else "Unknown"

        summaries = {
            "ACQUISITION": f"{source_name} acquired {target_name}",
            "OWNERSHIP": f"{source_name} owned {target_name}",
            "INHERITANCE": f"{target_name} inherited from {source_name}",
            "SALE": f"{source_name} sold {target_name}",
            "PURCHASE": f"{source_name} purchased {target_name}",
            "CONFISCATION": f"{target_name} was confiscated",
        }

        return summaries.get(event_type, f"{event_type}: {source_name} → {target_name}")

    def _entity_to_family_member(
        self,
        entity: dict,
        entity_id: str,
        relation_to_claimant: str | None = None,
    ) -> FamilyMember:
        """Convert entity dict to FamilyMember model."""
        verification = entity.get("verification", {})
        tier = self._parse_verification_tier(verification.get("tier", "TIER_3_AI"))

        return FamilyMember(
            entity_id=entity_id,
            name=entity.get("name", "Unknown"),
            relation_to_claimant=relation_to_claimant,
            birth_date=entity.get("birth_date"),
            death_date=entity.get("death_date"),
            roles=entity.get("roles", []),
            verification_tier=tier,
        )

    def _find_relation_to_focal(
        self,
        graph: KnowledgeGraph,
        person_id: str,
        focal_id: str,
        family_relations: set[str],
    ) -> str | None:
        """Find the relation type between a person and the focal person."""
        # Check direct relations
        for rel in graph.get_relations(person_id, direction="both"):
            if rel.get("relation_type") in family_relations:
                if rel["source"] == focal_id or rel["target"] == focal_id:
                    return rel.get("relation_type", "").replace("_", " ").lower()

        return None

    def _generate_lineage_summary(
        self, primary: FamilyMember, members: list[FamilyMember]
    ) -> str:
        """Generate a brief lineage summary."""
        if not members:
            return f"{primary.name} is the primary claimant in this case."

        relations = [m.relation_to_claimant for m in members if m.relation_to_claimant]
        if relations:
            return (
                f"{primary.name} is the primary claimant. "
                f"Related family members include: {', '.join(set(relations))}."
            )

        return f"{primary.name} is the primary claimant with {len(members)} related family members identified."

    def _build_registry_info(self, entity: dict) -> str | None:
        """Build registry info string from entity fields."""
        parts = []
        if entity.get("registry_number"):
            parts.append(f"Registry #{entity['registry_number']}")
        if entity.get("folio_number"):
            parts.append(f"Folio {entity['folio_number']}")
        if entity.get("cadastral_info"):
            parts.append(entity["cadastral_info"])

        return "; ".join(parts) if parts else None

    def _build_ownership_narrative(
        self, rel_type: str, relation: dict, graph: KnowledgeGraph
    ) -> str:
        """Build narrative text for an ownership period."""
        source_entity = graph.get_entity(relation["source"])
        target_entity = graph.get_entity(relation["target"])

        source_name = source_entity.get("name", "Unknown") if source_entity else "Unknown"
        target_name = target_entity.get("name", "the property") if target_entity else "the property"

        date = relation.get("date", "")
        date_str = f" in {date}" if date else ""

        narratives = {
            "OWNS": f"{source_name} owned {target_name}{date_str}.",
            "OWNED": f"{source_name} owned {target_name}{date_str}.",
            "INHERITED": f"{target_name} was inherited by {source_name}{date_str}.",
            "SOLD": f"{source_name} sold {target_name}{date_str}.",
            "SOLD_TO": f"{target_name} was sold to {source_name}{date_str}.",
            "BOUGHT": f"{source_name} purchased {target_name}{date_str}.",
            "CONFISCATED": f"{target_name} was confiscated{date_str}.",
        }

        narrative = narratives.get(rel_type, f"{rel_type}: {source_name} → {target_name}")

        # Add evidence quote if available
        if relation.get("evidence"):
            narrative += f'\n\nEvidence: "{relation["evidence"]}"'

        return narrative

    def _find_entities_in_document(self, graph: KnowledgeGraph, doc_id: str) -> list[str]:
        """Find all entities mentioned in a document."""
        entities = []

        # Check extracted_from field on all entities
        for node_id in graph.graph.nodes():
            entity = graph.get_entity(node_id)
            if not entity:
                continue

            extracted_from = entity.get("extracted_from", "")
            if doc_id in extracted_from:
                name = entity.get("name")
                if name:
                    entities.append(name)

        return entities[:5]  # Limit to 5 for readability

    def _determine_what_document_proves(
        self, graph: KnowledgeGraph, doc_id: str, entity: dict
    ) -> str:
        """Determine what a document proves based on its type and relations."""
        doc_type = entity.get("document_type", "").lower()

        # Type-based defaults
        type_proofs = {
            "deed": "Establishes property ownership",
            "certificate": "Provides official certification",
            "letter": "Personal correspondence",
            "will": "Documents inheritance intentions",
            "contract": "Documents agreement between parties",
            "receipt": "Confirms transaction or payment",
            "notarial": "Notarized legal document",
        }

        for key, proof in type_proofs.items():
            if key in doc_type:
                return proof

        return "Supporting documentation"
