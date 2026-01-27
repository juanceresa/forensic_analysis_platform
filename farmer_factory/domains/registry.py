"""
Domain registry - singleton for managing active domain configuration.

Provides global access to the current domain configuration throughout
the application.
"""

import logging
from typing import Optional, List

from farmer_factory.domains.loader import DomainLoader
from farmer_factory.domains.models import (
    DomainConfig,
    EntityTypeConfig,
    RelationTypeConfig,
)

logger = logging.getLogger(__name__)


class DomainRegistry:
    """
    Singleton registry for the active domain configuration.

    Usage:
        from farmer_factory.domains import domain_registry

        # Set active domain at startup
        domain_registry.set_active("cuban_property")

        # Access configuration anywhere
        config = domain_registry.active
        entity_types = domain_registry.get_entity_types()
    """

    _instance: Optional["DomainRegistry"] = None
    _active_domain: Optional[DomainConfig] = None
    _loader: Optional[DomainLoader] = None

    def __new__(cls) -> "DomainRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._loader = DomainLoader()
        return cls._instance

    def set_active(self, domain_code: str) -> DomainConfig:
        """
        Set the active domain for processing.

        Args:
            domain_code: Domain identifier (e.g., "cuban_property")

        Returns:
            The loaded DomainConfig

        Raises:
            ValueError: If domain not found or invalid
        """
        self._active_domain = self._loader.load(domain_code)
        logger.info(f"Active domain set to: {self._active_domain.name}")
        return self._active_domain

    @property
    def active(self) -> DomainConfig:
        """
        Get the active domain configuration.

        Returns:
            The active DomainConfig

        Raises:
            RuntimeError: If no active domain has been set
        """
        if self._active_domain is None:
            raise RuntimeError(
                "No active domain set. Call domain_registry.set_active('domain_code') first, "
                "or use --domain flag in CLI."
            )
        return self._active_domain

    @property
    def is_active(self) -> bool:
        """Check if a domain is currently active."""
        return self._active_domain is not None

    @property
    def active_code(self) -> Optional[str]:
        """Get the code of the active domain, or None if not set."""
        return self._active_domain.code if self._active_domain else None

    def get_entity_types(self) -> List[str]:
        """
        Get entity type names for the active domain.

        Returns:
            List of entity type names (e.g., ["PERSON", "PROPERTY", ...])
        """
        return list(self.active.entity_types.keys())

    def get_entity_type_config(self, name: str) -> Optional[EntityTypeConfig]:
        """
        Get configuration for an entity type.

        Args:
            name: Entity type name (e.g., "PERSON")

        Returns:
            EntityTypeConfig or None if not found
        """
        return self.active.get_entity_type(name)

    def get_relation_types(self) -> List[str]:
        """
        Get relation type names for the active domain.

        Returns:
            List of relation type names (e.g., ["OWNS", "SOLD", ...])
        """
        return list(self.active.relation_types.keys())

    def get_relation_type_config(self, name: str) -> Optional[RelationTypeConfig]:
        """
        Get configuration for a relation type.

        Args:
            name: Relation type name (e.g., "OWNS")

        Returns:
            RelationTypeConfig or None if not found
        """
        return self.active.get_relation_type(name)

    def get_temporal_relations(self) -> List[str]:
        """
        Get relation types that are events (need dates).

        Returns:
            List of relation type names
        """
        return self.active.get_temporal_relations()

    def get_state_relations(self) -> List[str]:
        """
        Get relation types that are states (dates optional).

        Returns:
            List of relation type names
        """
        return self.active.get_state_relations()

    def get_high_priority_relations(self) -> List[str]:
        """
        Get relation types that should be highlighted in narratives.

        Returns:
            List of relation type names
        """
        return self.active.get_high_priority_relations()

    def list_available_domains(self) -> List[str]:
        """
        List all available domain codes.

        Returns:
            List of domain codes that can be loaded
        """
        return self._loader.list_domains()

    def reload_active(self) -> DomainConfig:
        """
        Reload the active domain configuration from disk.

        Returns:
            The reloaded DomainConfig
        """
        if self._active_domain is None:
            raise RuntimeError("No active domain to reload")
        return self.set_active(self._active_domain.code)


# Global singleton instance
domain_registry = DomainRegistry()
