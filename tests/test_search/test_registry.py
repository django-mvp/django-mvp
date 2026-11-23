"""Tests for mvp.search.registry."""

import pytest
from django.core.exceptions import ImproperlyConfigured

import mvp.search
from mvp.search.kinds import FunctionKind, Kind
from mvp.search.registry import SearchRegistry


def nothing(query, request):
    return []


class NamedKind(Kind):
    label = "Named"
    icon = "tag"

    def __init__(self, name):
        self.name = name

    def find(self, query, request):
        return []


class TestSearchRegistry:
    def test_registers_a_function_with_its_values(self):
        registry = SearchRegistry()

        registry.register(
            nothing, name="docs", label="Documents", icon="file", description="Text"
        )

        (kind,) = registry.registered()
        assert isinstance(kind, FunctionKind)
        assert (kind.name, str(kind.label), kind.icon, str(kind.description)) == (
            "docs",
            "Documents",
            "file",
            "Text",
        )

    def test_registers_a_kind_instance(self):
        registry = SearchRegistry()
        kind = NamedKind("people")

        registry.register(kind)

        assert registry.registered() == [kind]

    def test_lists_kinds_in_registration_order(self):
        registry = SearchRegistry()
        for name in ("c", "a", "b"):
            registry.register(NamedKind(name))

        assert [kind.name for kind in registry.registered()] == ["c", "a", "b"]

    def test_a_second_kind_under_one_name_raises(self):
        registry = SearchRegistry()
        first = NamedKind("people")
        registry.register(first)

        with pytest.raises(ImproperlyConfigured):
            registry.register(NamedKind("people"))

        assert registry.registered() == [first]

    def test_a_function_without_name_label_and_icon_raises(self):
        with pytest.raises(ImproperlyConfigured):
            SearchRegistry().register(nothing, name="docs")


class TestModuleLevelRegistry:
    def test_register_and_registered_use_the_current_registry(self, search_registry):
        mvp.search.register(nothing, name="docs", label="Docs", icon="file")

        assert [k.name for k in mvp.search.registered()] == ["docs"]
        assert [k.name for k in search_registry.registered()] == ["docs"]
