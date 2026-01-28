"""Test configuration for utils tests.

Override the session-scoped fixture to avoid importing heavy dependencies.
"""

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_domain():
    """Override the domain setup fixture for utils tests.
    
    The utils module doesn't require domain configuration, so we skip it.
    """
    pass
