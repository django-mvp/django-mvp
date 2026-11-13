"""Shared fixtures for the search tests."""

import pytest

from mvp.search import registry as registry_module
from mvp.search.registry import SearchRegistry


@pytest.fixture(autouse=True)
def search_registry(monkeypatch):
    """Swap the module-level registry for an empty one, for one test."""
    fresh = SearchRegistry()
    monkeypatch.setattr(registry_module, "default_registry", fresh)
    return fresh
