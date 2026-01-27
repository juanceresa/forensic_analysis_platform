"""
Domain configuration system for Civic Table.

Enables the platform to serve multiple documentary recovery domains
from a shared technical core.

Usage:
    from farmer_factory.domains import domain_registry

    # Set active domain
    domain_registry.set_active("cuban_property")

    # Access domain configuration
    config = domain_registry.active
    print(config.name)  # "Cuban Property Restitution"

    # Get entity types for this domain
    entity_types = domain_registry.get_entity_types()

    # Get relation types for this domain
    relation_types = domain_registry.get_relation_types()
"""

from farmer_factory.domains.registry import domain_registry
from farmer_factory.domains.loader import DomainLoader
from farmer_factory.domains.models import DomainConfig

__all__ = ["domain_registry", "DomainLoader", "DomainConfig"]
