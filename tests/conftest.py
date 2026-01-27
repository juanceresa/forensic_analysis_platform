"""Pytest configuration and fixtures for Civic Table tests."""

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_domain():
    """Set up the cuban_property domain for all tests.

    This fixture runs once at the start of the test session and sets
    up the domain configuration before any tests run. This ensures
    that EntityType and RelationType enums are properly populated.
    """
    from farmer_factory.domains import domain_registry
    from farmer_factory.structure.schema import refresh_type_enums

    # Set the active domain
    domain_registry.set_active("cuban_property")

    # Refresh the type enums to match domain config
    refresh_type_enums()

    yield

    # No cleanup needed - domain stays active for entire session
