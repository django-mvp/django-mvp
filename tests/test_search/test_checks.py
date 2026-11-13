"""Tests for the search's start-up checks.

Source: mvp/search/checks.py
"""

from django.core import checks
from django.core.checks.registry import registry
from modelsearch import index

from mvp.search.checks import (
    check_search,
    missing_modelsearch_messages,
    missing_pk_filter_messages,
    unindexed_model_messages,
    unregistered_kind_messages,
)
from mvp.search.kinds import FunctionKind
from mvp.search.model_kind import ModelKind
from tests.testapp_search.models import Note, PlainNote


class NoteKind(ModelKind):
    name = "notes"
    label = "Notes"
    icon = "file-text"
    model = Note


class PlainKind(ModelKind):
    name = "plain"
    label = "Plain"
    icon = "file"
    model = PlainNote


def function_kind(name="pages"):
    return FunctionKind(lambda query, request: [], name, "Pages", "file")


class TestUnregisteredKindMessages:
    def test_a_name_no_kind_is_registered_under_is_error_e004(self):
        messages = unregistered_kind_messages(["pages", "ghost"], {"pages"})

        assert [message.id for message in messages] == ["mvp.E004"]
        assert isinstance(messages[0], checks.Error)
        assert "ghost" in messages[0].msg

    def test_each_unknown_name_is_reported(self):
        messages = unregistered_kind_messages(["one", "two"], set())

        assert len(messages) == 2

    def test_registered_names_and_an_empty_setting_pass(self):
        assert unregistered_kind_messages(["pages"], {"pages"}) == []
        assert unregistered_kind_messages([], {"pages"}) == []


class TestUnindexedModelMessages:
    def test_a_model_that_is_not_indexed_is_error_e006(self):
        messages = unindexed_model_messages([PlainKind()])

        assert [message.id for message in messages] == ["mvp.E006"]
        assert isinstance(messages[0], checks.Error)
        assert "plain" in messages[0].msg

    def test_an_indexed_model_and_a_function_kind_pass(self):
        assert unindexed_model_messages([NoteKind(), function_kind()]) == []


class TestMissingPkFilterMessages:
    def test_an_indexed_model_without_a_filter_on_the_pk_is_error_e007(
        self, monkeypatch
    ):
        monkeypatch.setattr(Note, "search_fields", [index.SearchField("title")])

        messages = missing_pk_filter_messages([NoteKind()])

        assert [message.id for message in messages] == ["mvp.E007"]
        assert isinstance(messages[0], checks.Error)
        assert "notes" in messages[0].msg

    def test_a_filter_field_declared_as_pk_does_not_count(self, monkeypatch):
        monkeypatch.setattr(
            Note,
            "search_fields",
            [index.SearchField("title"), index.FilterField("pk")],
        )

        messages = missing_pk_filter_messages([NoteKind()])

        assert [message.id for message in messages] == ["mvp.E007"]

    def test_a_filter_field_on_the_pk_attname_passes(self):
        assert missing_pk_filter_messages([NoteKind()]) == []

    def test_a_model_that_is_not_indexed_is_left_to_e006(self):
        assert missing_pk_filter_messages([PlainKind(), function_kind()]) == []


class TestMissingModelsearchMessages:
    def test_a_model_kind_without_modelsearch_installed_is_error_e008(self):
        messages = missing_modelsearch_messages([NoteKind()], ["mvp"])

        assert [message.id for message in messages] == ["mvp.E008"]
        assert isinstance(messages[0], checks.Error)

    def test_one_message_however_many_model_kinds(self):
        messages = missing_modelsearch_messages([NoteKind(), PlainKind()], ["mvp"])

        assert len(messages) == 1

    def test_modelsearch_installed_or_only_function_kinds_pass(self):
        assert missing_modelsearch_messages([NoteKind()], ["modelsearch"]) == []
        assert missing_modelsearch_messages([function_kind()], ["mvp"]) == []


class TestSearchCheck:
    def test_the_check_is_registered_with_the_urls_tag(self):
        assert check_search in registry.registered_checks
        assert check_search in registry.get_checks(include_deployment_checks=False)
        assert check_search.tags == (checks.Tags.urls,)

    def test_the_repositorys_own_settings_report_nothing(self):
        assert check_search(None) == []

    def test_a_registered_model_kind_with_a_bad_model_is_reported(
        self, search_registry
    ):
        search_registry.register(PlainKind())

        ids = [message.id for message in check_search(None)]

        assert ids == ["mvp.E006"]

    def test_a_setting_naming_an_unregistered_kind_is_reported(self, monkeypatch):
        from mvp.config import MVP_CONFIG

        monkeypatch.setitem(MVP_CONFIG["search"], "kinds", ["ghost"])

        assert [message.id for message in check_search(None)] == ["mvp.E004"]
