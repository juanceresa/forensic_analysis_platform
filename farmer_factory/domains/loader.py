"""
Domain configuration loader.

Loads and validates domain configurations from YAML files.
"""

import logging
from pathlib import Path
from typing import Dict, Optional

import yaml

from farmer_factory.domains.models import (
    DomainConfig,
    EntityTypeConfig,
    RelationTypeConfig,
    FieldDefinition,
    KnownEntity,
    RelationCategory,
    TemporalRange,
    GeographicFocus,
    SuccessCriteria,
)

logger = logging.getLogger(__name__)


class DomainLoader:
    """Load and validate domain configurations from YAML files."""

    def __init__(self, domains_dir: Optional[Path] = None):
        """
        Initialize domain loader.

        Args:
            domains_dir: Directory containing domain configurations.
                        Defaults to the domains directory in farmer_factory.
        """
        if domains_dir is None:
            domains_dir = Path(__file__).parent
        self.domains_dir = Path(domains_dir)
        self._cache: Dict[str, DomainConfig] = {}

    def load(self, domain_code: str) -> DomainConfig:
        """
        Load a domain configuration by code.

        Args:
            domain_code: Domain identifier (e.g., "cuban_property")

        Returns:
            Validated DomainConfig

        Raises:
            ValueError: If domain not found or invalid
        """
        if domain_code in self._cache:
            logger.debug(f"Returning cached domain config: {domain_code}")
            return self._cache[domain_code]

        domain_path = self.domains_dir / domain_code
        if not domain_path.exists():
            available = self.list_domains()
            raise ValueError(
                f"Domain '{domain_code}' not found. Available domains: {available}"
            )

        logger.info(f"Loading domain configuration: {domain_code}")

        # Load main domain.yaml
        domain_yaml = domain_path / "domain.yaml"
        if not domain_yaml.exists():
            raise ValueError(f"Domain '{domain_code}' missing domain.yaml")

        with open(domain_yaml) as f:
            domain_data = yaml.safe_load(f)

        # Extract domain section
        if "domain" in domain_data:
            config_data = domain_data["domain"]
        else:
            config_data = domain_data

        # Load entities.yaml if exists
        entities_yaml = domain_path / "entities.yaml"
        if entities_yaml.exists():
            with open(entities_yaml) as f:
                entities_data = yaml.safe_load(f)
            config_data["entity_types"] = self._parse_entity_types(
                entities_data.get("entity_types", {})
            )

        # Load relations.yaml if exists
        relations_yaml = domain_path / "relations.yaml"
        if relations_yaml.exists():
            with open(relations_yaml) as f:
                relations_data = yaml.safe_load(f)
            config_data["relation_types"] = self._parse_relation_types(
                relations_data.get("relation_types", {})
            )
            if "categories" in relations_data:
                config_data["relation_categories"] = self._parse_categories(
                    relations_data["categories"]
                )

        # Parse nested objects
        if "temporal_range" in config_data:
            config_data["temporal_range"] = TemporalRange(
                **config_data["temporal_range"]
            )

        if "geographic_focus" in config_data:
            config_data["geographic_focus"] = GeographicFocus(
                **config_data["geographic_focus"]
            )

        if "success_criteria" in config_data:
            config_data["success_criteria"] = SuccessCriteria(
                **config_data["success_criteria"]
            )

        # Set prompts directory
        config_data["prompts_dir"] = str(domain_path / "prompts")

        # Validate with Pydantic
        try:
            domain_config = DomainConfig(**config_data)
        except Exception as e:
            raise ValueError(f"Invalid domain configuration for '{domain_code}': {e}")

        self._cache[domain_code] = domain_config
        logger.info(
            f"Loaded domain '{domain_config.name}' v{domain_config.version} "
            f"({len(domain_config.entity_types)} entity types, "
            f"{len(domain_config.relation_types)} relation types)"
        )

        return domain_config

    def _parse_entity_types(
        self, entity_types_data: Dict
    ) -> Dict[str, EntityTypeConfig]:
        """Parse entity type configurations from YAML data."""
        result = {}

        for name, config in entity_types_data.items():
            # Parse fields
            core_fields = [FieldDefinition(**f) for f in config.get("core_fields", [])]
            domain_fields = [
                FieldDefinition(**f) for f in config.get("domain_fields", [])
            ]

            # Parse known entities
            known_entities = [
                KnownEntity(**e) for e in config.get("known_entities", [])
            ]

            result[name] = EntityTypeConfig(
                description=config.get("description", ""),
                icon=config.get("icon", ""),
                color=config.get("color", "#6B7280"),
                core_fields=core_fields,
                domain_fields=domain_fields,
                known_entities=known_entities,
            )

        return result

    def _parse_relation_types(
        self, relation_types_data: Dict
    ) -> Dict[str, RelationTypeConfig]:
        """Parse relation type configurations from YAML data."""
        result = {}

        for name, config in relation_types_data.items():
            result[name] = RelationTypeConfig(
                description=config.get("description", ""),
                category=config.get("category", "other"),
                source_types=config.get("source_types", []),
                target_types=config.get("target_types", []),
                temporal=config.get("temporal", "state"),
                color=config.get("color", "#6B7280"),
                icon=config.get("icon"),
                symmetric=config.get("symmetric", False),
                creates_inverse=config.get("creates_inverse"),
                high_priority=config.get("high_priority", False),
                fallback=config.get("fallback", False),
                extraction_hints=config.get("extraction_hints", []),
                narrative_template=config.get("narrative_template"),
            )

        return result

    def _parse_categories(self, categories_data: Dict) -> Dict[str, RelationCategory]:
        """Parse relation category configurations from YAML data."""
        result = {}

        for name, config in categories_data.items():
            result[name] = RelationCategory(
                label=config.get("label", name),
                description=config.get("description", ""),
                high_priority=config.get("high_priority", False),
            )

        return result

    def list_domains(self) -> list[str]:
        """
        List available domain codes.

        Returns:
            List of domain codes that can be loaded
        """
        domains = []
        for item in self.domains_dir.iterdir():
            if item.is_dir() and (item / "domain.yaml").exists():
                domains.append(item.name)
        return sorted(domains)

    def reload(self, domain_code: str) -> DomainConfig:
        """
        Force reload a domain configuration (bypass cache).

        Args:
            domain_code: Domain identifier

        Returns:
            Freshly loaded DomainConfig
        """
        if domain_code in self._cache:
            del self._cache[domain_code]
        return self.load(domain_code)

    def clear_cache(self) -> None:
        """Clear all cached domain configurations."""
        self._cache.clear()
