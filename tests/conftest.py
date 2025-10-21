"""
Pytest configuration and fixtures.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    """Create a test client for the API."""
    return TestClient(app)
