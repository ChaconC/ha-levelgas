import pytest


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations):
    """Load this repository's custom component in the real HA test harness."""
