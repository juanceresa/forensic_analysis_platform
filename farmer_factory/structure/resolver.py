"""Entity resolution using machine learning-based deduplication."""

import logging
import dedupe
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from .dedupe_config import FIELD_CONFIG
from .schema import BaseEntity, EntityType
from .graph import KnowledgeGraph

logger = logging.getLogger(__name__)


class DedupeEntityResolver:
    """Machine learning-based entity resolution using dedupe library."""

    def __init__(self, model_dir: Path = None, threshold: float = 0.5):
        """
        Initialize resolver with trained models.

        Args:
            model_dir: Directory containing trained dedupe models
            threshold: Match probability threshold (0.0-1.0), default 0.5
        """
        self.model_dir = model_dir or Path(__file__).parent / "models"
        self.model_dir.mkdir(exist_ok=True)
        self.threshold = threshold

        # Separate deduper for each entity type
        self.dedupers: Dict[str, dedupe.StaticDedupe] = {}
        self._load_models()

    def _load_models(self):
        """Load pre-trained models from disk."""
        for entity_type in ["PERSON", "LOCATION", "PROPERTY", "ORGANIZATION"]:
            settings_path = self.model_dir / f"{entity_type.lower()}_settings"

            if settings_path.exists():
                logger.info(f"Loading {entity_type} deduplication model...")
                try:
                    with open(settings_path, 'rb') as f:
                        deduper = dedupe.StaticDedupe(f)
                    self.dedupers[entity_type] = deduper
                except Exception as e:
                    logger.warning(f"Failed to load {entity_type} model: {e}")
            else:
                logger.debug(f"No trained model for {entity_type}, will skip deduplication")

    def find_similar_entity(
        self,
        entity: BaseEntity,
        graph: KnowledgeGraph
    ) -> Optional[str]:
        """
        Find matching entity using dedupe.

        Args:
            entity: New entity to match
            graph: KnowledgeGraph to search

        Returns:
            Entity ID if match found, None otherwise
        """
        entity_type_str = entity.entity_type.value

        # Check if we have a trained model for this type
        if entity_type_str not in self.dedupers:
            return None

        # Handle None graph gracefully
        if graph is None:
            return None

        # Get all entities of same type from graph
        candidates = []
        for node_id, node_data in graph.graph.nodes(data=True):
            if node_data.get("entity_type") == entity_type_str:
                candidates.append((node_id, node_data))

        if not candidates:
            return None

        # Prepare data for dedupe
        data_dict = {}

        # Add new entity
        new_entity_data = self._prepare_entity_data(entity)
        data_dict[entity.id] = new_entity_data

        # Add candidates
        for candidate_id, candidate_data in candidates:
            candidate_entity_data = self._prepare_entity_data_from_dict(
                candidate_data,
                entity_type_str
            )
            data_dict[candidate_id] = candidate_entity_data

        # Get deduper for this entity type
        deduper = self.dedupers[entity_type_str]

        # Find clusters
        try:
            clustered_dupes = deduper.partition(data_dict, threshold=self.threshold)
        except Exception as e:
            logger.warning(f"Dedupe partition failed for {entity_type_str}: {e}")
            return None

        # Find cluster containing new entity
        for cluster_id, (record_ids, scores) in enumerate(clustered_dupes):
            if entity.id in record_ids:
                # Found a match - return first existing entity in cluster
                for record_id in record_ids:
                    if record_id != entity.id:
                        logger.debug(f"Matched {entity.id} with {record_id}")
                        return record_id

        return None

    def _prepare_entity_data(self, entity: BaseEntity) -> Dict[str, Any]:
        """Extract fields for dedupe based on entity type."""
        entity_type = entity.entity_type.value

        if entity_type == "PERSON":
            return {
                'name': entity.name or '',
                'birth_date': entity.birth_date or '',
                'death_date': entity.death_date or '',
                'residence': entity.residence or '',
                'profession': entity.profession or '',
                'nationality': entity.nationality or '',
            }
        elif entity_type == "LOCATION":
            return {
                'name': entity.name or '',
                'location_type': entity.location_type or '',
                'country': entity.country or '',
                'parent_location_id': entity.parent_location_id or '',
            }
        elif entity_type == "PROPERTY":
            return {
                'name': entity.name or '',
                'property_type': entity.property_type or '',
                'location_id': entity.location_id or '',
                'area': str(entity.area or ''),
            }
        elif entity_type == "ORGANIZATION":
            return {
                'name': entity.name or '',
                'org_type': entity.org_type or '',
                'location_id': entity.location_id or '',
            }
        else:
            return {}

    def _prepare_entity_data_from_dict(
        self,
        entity_data: Dict[str, Any],
        entity_type: str
    ) -> Dict[str, Any]:
        """Extract fields from graph node data."""
        if entity_type == "PERSON":
            return {
                'name': entity_data.get('name') or '',
                'birth_date': entity_data.get('birth_date') or '',
                'death_date': entity_data.get('death_date') or '',
                'residence': entity_data.get('residence') or '',
                'profession': entity_data.get('profession') or '',
                'nationality': entity_data.get('nationality') or '',
            }
        elif entity_type == "LOCATION":
            return {
                'name': entity_data.get('name') or '',
                'location_type': entity_data.get('location_type') or '',
                'country': entity_data.get('country') or '',
                'parent_location_id': entity_data.get('parent_location_id') or '',
            }
        elif entity_type == "PROPERTY":
            return {
                'name': entity_data.get('name') or '',
                'property_type': entity_data.get('property_type') or '',
                'location_id': entity_data.get('location_id') or '',
                'area': str(entity_data.get('area') or ''),
            }
        elif entity_type == "ORGANIZATION":
            return {
                'name': entity_data.get('name') or '',
                'org_type': entity_data.get('org_type') or '',
                'location_id': entity_data.get('location_id') or '',
            }
        else:
            return {}

    def merge_entities(
        self,
        existing: Dict[str, Any],
        new: BaseEntity,
        match_confidence: float = 0.8
    ) -> Dict[str, Any]:
        """
        Merge entities using confidence-weighted approach.

        For high-confidence matches (≥0.8), prefer higher quality data.
        For lower confidence, create conflict lists with provenance.

        Args:
            existing: Existing entity data from graph
            new: New entity to merge
            match_confidence: Dedupe match confidence (0.0-1.0)

        Returns:
            Merged entity data dictionary
        """
        merged = existing.copy()
        new_data = new.model_dump()

        # Always combine sources (preserve order for conflict provenance)
        existing_sources = existing.get("extracted_from", "")
        new_source = new_data.get("extracted_from", "")

        if isinstance(existing_sources, str):
            existing_sources = [existing_sources] if existing_sources else []
        if isinstance(new_source, str):
            new_source = [new_source] if new_source else []

        # Preserve order while removing duplicates
        all_sources = existing_sources + new_source
        seen = set()
        merged["extracted_from"] = [s for s in all_sources if not (s in seen or seen.add(s))]

        # Merge other fields
        for field, new_value in new_data.items():
            if field in ("id", "entity_type", "extracted_from", "created_at", "updated_at"):
                continue

            existing_value = existing.get(field)

            if new_value is None:
                continue
            if existing_value is None:
                merged[field] = new_value
                continue

            # Handle list fields (union)
            if isinstance(new_value, list):
                if isinstance(existing_value, list):
                    merged[field] = list(set(existing_value + new_value))
                else:
                    merged[field] = new_value
                continue

            # Both have values - decide merge strategy
            if existing_value != new_value:
                if match_confidence >= 0.8:
                    # High confidence - choose better value
                    merged[field] = self._choose_better_value(
                        existing_value,
                        new_value,
                        existing.get('verification', {}).get('confidence', 0.5),
                        new.verification.confidence
                    )
                else:
                    # Lower confidence - create conflict list
                    merged[field] = self._create_conflict_list(
                        existing_value,
                        new_value,
                        merged["extracted_from"]
                    )

        return merged

    def _choose_better_value(
        self,
        existing_value: Any,
        new_value: Any,
        existing_confidence: float,
        new_confidence: float
    ) -> Any:
        """Choose better value based on confidence and completeness."""
        # Confidence difference > 0.1 is significant
        if new_confidence - existing_confidence > 0.1:
            return new_value
        if existing_confidence - new_confidence > 0.1:
            return existing_value

        # Confidence similar - prefer more complete
        if isinstance(existing_value, str) and isinstance(new_value, str):
            if len(new_value) > len(existing_value) * 1.2:
                return new_value
            return existing_value

        return existing_value

    def _create_conflict_list(
        self,
        existing_value: Any,
        new_value: Any,
        sources: List[str]
    ) -> List[str]:
        """Create conflict list with provenance."""
        if isinstance(existing_value, list):
            # Already a conflict list
            return existing_value + [f"{new_value} ({sources[-1]})"]
        else:
            return [
                f"{existing_value} ({sources[0] if sources else 'unknown'})",
                f"{new_value} ({sources[-1] if len(sources) > 1 else 'unknown'})"
            ]
