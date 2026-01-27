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

        # 2. Validate focal entities exist
        self._assert_entity_exists(graph, focal_property_id, expected_type="PROPERTY")
        self._assert_entity_exists(graph, focal_family_member_id, expected_type="PERSON")

        # 3. Load extractions (optional, for richer evidence)
        self._load_extractions()

        # 4. Build sections
        timeline = self._build_timeline(graph)
        family = self._build_family_tree(graph, focal_family_member_id)
        property_data = self._build_property(graph, focal_property_id)
        ownership_history = self._build_ownership_chain(graph, focal_property_id)
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

    def _assert_entity_exists(
        self, graph: KnowledgeGraph, entity_id: str, expected_type: str | None = None
    ) -> None:
        """Verify an entity exists in the graph.

        Args:
            graph: KnowledgeGraph instance
            entity_id: Entity ID to check
            expected_type: Expected entity type (optional)

        Raises:
            PrepareError: If entity not found or wrong type
        """
        entity = graph.get_entity(entity_id)
        if entity is None:
            raise PrepareError(f"Entity not found: {entity_id}")

        if expected_type:
            actual_type = entity.get("entity_type")
            if actual_type != expected_type:
                raise PrepareError(
                    f"Entity {entity_id} is type {actual_type}, expected {expected_type}"
                )

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
                        date_sortable=date_sortable,
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
        events.sort(key=lambda e: (e.date_sortable or "9999-99-99", e.event_type))

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

        # Sort by date
        ownership_events.sort(
            key=lambda r: r.get("date_sortable") or r.get("date") or "0000"
        )

        # Group into periods
        for rel in ownership_events:
            rel_type = rel.get("relation_type", "OWNS")

            # Determine period type
            if rel_type in {"OWNS", "OWNED", "BOUGHT"}:
                period_type = "ACQUISITION" if not periods else "OWNERSHIP"
            elif rel_type == "INHERITED":
                period_type = "INHERITANCE"
            elif rel_type in {"SOLD", "SOLD_TO"}:
                period_type = "SALE"
            elif rel_type == "CONFISCATED":
                period_type = "CONFISCATION"
            else:
                period_type = "OWNERSHIP"

            # Get owner names
            owner_names = []
            source_entity = graph.get_entity(rel["source"])
            if source_entity:
                owner_names.append(source_entity.get("name", "Unknown"))

            # Build evidence citation
            evidence = []
            if rel.get("document_id"):
                verification = rel.get("verification", {})
                tier = self._parse_verification_tier(verification.get("tier", "TIER_3_AI"))
                evidence.append(
                    EvidenceCitation(
                        doc_id=rel["document_id"],
                        doc_title=None,
                        page=None,
                        quote=rel.get("evidence"),
                        verification_tier=tier,
                    )
                )

            # Build narrative
            narrative = self._build_ownership_narrative(rel_type, rel, graph)

            periods.append(
                OwnershipPeriod(
                    period_type=period_type,
                    start_date=rel.get("date"),
                    end_date=None,  # End date would be start of next period
                    owner_names=owner_names,
                    narrative=narrative,
                    evidence=evidence,
                )
            )

        # Fill in end dates from subsequent periods
        for i, period in enumerate(periods[:-1]):
            next_period = periods[i + 1]
            period.end_date = next_period.start_date

        return periods

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
                )
            )

        # Sort by date
        documents.sort(key=lambda d: d.date or "9999")

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

        client = Anthropic()

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
        )

        return response.content[0].text

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
        surname = full_name.split()[-1] if full_name else "Unknown"

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
