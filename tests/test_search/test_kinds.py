"""Tests for mvp.search.kinds."""

import dataclasses

import pytest
from django.utils.functional import Promise

from mvp.search.kinds import FunctionKind, Group, Kind, Result


class SevenItemKind(Kind):
    name = "sevens"
    label = "Sevens"
    icon = "star"

    def find(self, query, request):
        return [
            Result(title=f"{query} {n}", url=f"/s/{n}/", where="Sevens")
            for n in range(7)
        ]


class TestResult:
    def test_result_is_immutable(self):
        result = Result(title="A", url="/a/", where="Pages")

        with pytest.raises(dataclasses.FrozenInstanceError):
            result.title = "B"

    def test_passage_defaults_to_empty(self):
        assert Result(title="A", url="/a/", where="Pages").passage == ""


class TestGroup:
    def test_more_is_the_count_not_shown(self):
        group = Group(kind=SevenItemKind(), results=[1, 2], total=7, more_url=None)

        assert group.more == 5


class TestKind:
    def test_group_cuts_results_to_the_limit_and_counts_the_rest(self, rf):
        kind = SevenItemKind()

        group = kind.group("x", rf.get("/"), limit=4)

        assert (len(group.results), group.total, group.more) == (4, 7, 3)
        assert group.kind is kind

    def test_group_keeps_the_kinds_own_order(self, rf):
        group = SevenItemKind().group("x", rf.get("/"), limit=3)

        assert [r.url for r in group.results] == ["/s/0/", "/s/1/", "/s/2/"]

    def test_group_has_no_more_url_by_default(self, rf):
        assert SevenItemKind().group("x", rf.get("/"), limit=4).more_url is None

    def test_group_uses_the_kinds_own_more_url(self, rf):
        class OwnAddress(SevenItemKind):
            def more_url(self, query):
                return f"/elsewhere/?q={query}"

        group = OwnAddress().group("x", rf.get("/"), limit=4)

        assert group.more_url == "/elsewhere/?q=x"

    def test_result_turns_an_item_into_a_result(self, rf):
        class Words(Kind):
            name = "words"
            label = "Words"
            icon = "type"

            def find(self, query, request):
                return ["alpha"]

            def result(self, item):
                return Result(title=item, url="/w/", where="Words")

        group = Words().group("a", rf.get("/"), limit=4)

        assert group.results == [Result(title="alpha", url="/w/", where="Words")]

    def test_find_must_be_defined(self, rf):
        class Bare(Kind):
            name = "bare"
            label = "Bare"
            icon = "x"

        with pytest.raises(NotImplementedError):
            Bare().group("a", rf.get("/"), limit=4)


class TestFunctionKind:
    def test_holds_the_values_it_was_given(self):
        kind = FunctionKind(
            lambda query, request: [],
            name="docs",
            label="Documents",
            icon="file",
            description="Things written down",
        )

        assert (kind.name, str(kind.label), kind.icon, str(kind.description)) == (
            "docs",
            "Documents",
            "file",
            "Things written down",
        )

    def test_find_calls_the_function_with_query_and_request(self, rf):
        seen = []

        def function(query, request):
            seen.append((query, request))
            return [Result(title="A", url="/a/", where="Docs")]

        request = rf.get("/")
        kind = FunctionKind(function, name="docs", label="Docs", icon="file")

        group = kind.group("abc", request, limit=4)

        assert seen == [("abc", request)]
        assert group.results == [Result(title="A", url="/a/", where="Docs")]

    def test_label_and_description_are_lazy(self):
        kind = FunctionKind(
            lambda query, request: [], name="d", label="D", icon="i", description="x"
        )

        assert isinstance(kind.label, Promise)
        assert isinstance(kind.description, Promise)
