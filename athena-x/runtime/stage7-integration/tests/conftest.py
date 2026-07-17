"""Shared fixtures for Stage 7 integration tests."""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "agents", "technical-analysis", "layer2-indicators", "tests"))
from conftest import FakeMarketRepository


@pytest.fixture
def repo():
    return FakeMarketRepository()
