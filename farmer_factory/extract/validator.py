"""Schema validator for extracted entities and relations."""

import logging
from typing import List, Tuple, Dict, Any
from pydantic import ValidationError

from farmer_factory.structure.schema import (
    BaseEntity, Person, Property, Organization, Location, Document,
    Relation, EntityType
)

logger = logging.getLogger(__name__)


class SchemaValidator:
    """Validates extracted entities against Pydantic models."""

    def __init__(self):
        """Initialize schema validator."""
        self.entity_type_map = {
            EntityType.PERSON: Person,
            EntityType.PROPERTY: Property,
            EntityType.ORGANIZATION: Organization,
            EntityType.LOCATION: Location,
            EntityType.DOCUMENT: Document,
        }

    def validate_entity(
        self,
        entity_dict: Dict[str, Any],
        entity_type: EntityType
    ) -> BaseEntity:
        """
        Validate and instantiate Pydantic model.

        Args:
            entity_dict: Dictionary containing entity data
            entity_type: Type of entity to validate against

        Returns:
            Validated Pydantic entity model

        Raises:
            ValidationError: If data doesn't match schema
        """
        # Get the appropriate Pydantic model class
        model_class = self.entity_type_map.get(entity_type)

        if model_class is None:
            raise ValueError(f"Unknown entity type: {entity_type}")

        # Validate and instantiate
        return model_class(**entity_dict)

    def validate_extraction(
        self,
        entities: List[Dict[str, Any]],
        relations: List[Dict[str, Any]]
    ) -> Tuple[List[BaseEntity], List[Relation]]:
        """
        Validate entire extraction batch.

        Args:
            entities: List of entity dictionaries to validate
            relations: List of relation dictionaries to validate

        Returns:
            Tuple of (valid_entities, valid_relations)

        Note:
            Invalid entities/relations are logged and skipped.
            Returns only valid items - never fails entire extraction.
        """
        valid_entities = []
        valid_relations = []

        # Validate entities
        for i, entity_dict in enumerate(entities):
            try:
                # Determine entity type
                entity_type_str = entity_dict.get("entity_type")
                if entity_type_str is None:
                    logger.error(f"Entity {i} missing 'entity_type' field")
                    continue

                # Convert string to EntityType enum
                try:
                    entity_type = EntityType[entity_type_str]
                except KeyError:
                    logger.error(f"Entity {i} has invalid entity_type: {entity_type_str}")
                    continue

                # Validate
                validated_entity = self.validate_entity(entity_dict, entity_type)
                valid_entities.append(validated_entity)

            except ValidationError as e:
                logger.error(f"Validation error for entity {i}: {e}")
                # Skip invalid entity, continue with rest

        # Validate relations
        for i, relation_dict in enumerate(relations):
            try:
                validated_relation = Relation(**relation_dict)
                valid_relations.append(validated_relation)

            except ValidationError as e:
                logger.error(f"Validation error for relation {i}: {e}")
                # Skip invalid relation, continue with rest

        logger.info(
            f"Validated {len(valid_entities)}/{len(entities)} entities, "
            f"{len(valid_relations)}/{len(relations)} relations"
        )

        return valid_entities, valid_relations
