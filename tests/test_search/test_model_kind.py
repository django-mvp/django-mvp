"""Tests for ModelKind, the kind that searches a model modelsearch indexes.

Source: mvp/search/kinds.py
"""

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory

from mvp.search.model_kind import ModelKind
from tests.factories import NoteFactory
from tests.testapp_search.models import Note


class NoteKind(ModelKind):
    name = "notes"
    label = "Notes"
    icon = "file-text"
    model = Note

    def get_queryset(self, request):
        return Note.objects.filter(public=True)


@pytest.fixture
def request_(db):
    return RequestFactory().get("/")


@pytest.mark.django_db
class TestModelKindVisibility:
    def test_only_the_visible_records_are_listed_and_counted(self, request_):
        NoteFactory(title="Heat flow", body="Seen")
        NoteFactory(title="Heat map", body="Seen", public=False)
        NoteFactory(title="Heat pump", body="Seen", public=False)

        group = NoteKind().group("heat", request_, 10)

        assert [result.title for result in group.results] == ["Heat flow"]
        assert group.total == 1

    def test_the_model_needs_no_special_manager(self, request_):
        NoteFactory(title="Heat flow")

        assert NoteKind().group("heat", request_, 10).total == 1

    def test_a_kind_without_get_queryset_raises_naming_the_kind(self, request_):
        class Unscoped(ModelKind):
            name = "unscoped"
            label = "Unscoped"
            icon = "x"
            model = Note

        with pytest.raises(ImproperlyConfigured, match="Unscoped"):
            Unscoped().group("heat", request_, 10)


@pytest.mark.django_db
class TestModelKindMatching:
    def test_a_whole_word_in_the_body_is_found(self, request_):
        NoteFactory(title="Field notes", body="Measured the geothermal gradient")

        group = NoteKind().group("geothermal", request_, 10)

        assert [result.title for result in group.results] == ["Field notes"]

    def test_a_partly_typed_word_is_found_through_completion(self, request_):
        NoteFactory(title="Heat flow")

        group = NoteKind().group("hea", request_, 10)

        assert [result.title for result in group.results] == ["Heat flow"]

    def test_a_query_with_a_double_quote_returns_matches_and_does_not_raise(
        self, request_
    ):
        NoteFactory(title="Heat flow")

        group = NoteKind().group('"heat', request_, 10)

        assert [result.title for result in group.results] == ["Heat flow"]

    def test_nothing_found_is_an_empty_group(self, request_):
        NoteFactory(title="Heat flow")

        group = NoteKind().group("zzzz", request_, 10)

        assert group.results == []
        assert group.total == 0

    def test_the_results_are_limited_and_the_total_is_complete(self, request_):
        for n in range(3):
            NoteFactory(title=f"Heat {n}")

        group = NoteKind().group("heat", request_, 2)

        assert len(group.results) == 2
        assert group.total == 3
        assert group.more == 1


@pytest.mark.django_db
class TestModelKindResults:
    def test_the_defaults_come_from_the_record_and_the_model(self, request_):
        note = NoteFactory(title="Heat flow")

        result = NoteKind().group("heat", request_, 10).results[0]

        assert result.title == str(note)
        assert result.url == note.get_absolute_url()
        assert result.where == str(Note._meta.verbose_name)
        assert result.passage == ""

    def test_a_subclass_overrides_what_each_result_carries(self, request_):
        NoteFactory(title="Heat flow", body="Measured")

        class Custom(NoteKind):
            def title(self, obj):
                return f"T:{obj.title}"

            def url(self, obj):
                return "/custom/"

            def where(self, obj):
                return "Somewhere"

            def passage(self, obj):
                return obj.body

            def more_url(self, query):
                return f"/more/?q={query}"

        group = Custom().group("heat", request_, 10)

        result = group.results[0]
        assert (result.title, result.url, result.where, result.passage) == (
            "T:Heat flow",
            "/custom/",
            "Somewhere",
            "Measured",
        )
        assert group.more_url == "/more/?q=heat"
