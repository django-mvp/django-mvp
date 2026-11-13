"""Tests for the search across kinds."""

import pytest

import mvp.search
from mvp.config import MVP_CONFIG
from mvp.search.kinds import Kind, Result


class RecordingKind(Kind):
    """A kind that remembers the queries it was asked and returns a few results."""

    icon = "tag"

    def __init__(self, name, count=2):
        self.name = name
        self.label = name.title()
        self.count = count
        self.queries = []

    def find(self, query, request):
        self.queries.append(query)
        return [
            Result(title=f"{self.name} {n}", url=f"/{self.name}/{n}/", where=self.name)
            for n in range(self.count)
        ]


@pytest.fixture
def kinds(search_registry):
    """Three registered kinds, a, b and c, in that order."""
    return [search_registry.register(RecordingKind(name)) for name in "abc"]


@pytest.fixture
def kinds_setting(monkeypatch):
    """Set MVP_CONFIG["search"]["kinds"] for one test."""

    def set_kinds(names):
        monkeypatch.setitem(MVP_CONFIG["search"], "kinds", names)

    return set_kinds


class TestSearchConfig:
    def test_kinds_default_to_empty(self):
        assert MVP_CONFIG["search"]["kinds"] == []


class TestActiveKinds:
    def test_every_registered_kind_in_registration_order_without_a_setting(
        self, search_registry, kinds
    ):
        assert [k.name for k in search_registry.active()] == ["a", "b", "c"]

    def test_the_setting_picks_kinds_and_their_order(
        self, search_registry, kinds, kinds_setting
    ):
        kinds_setting(["c", "a"])

        assert [k.name for k in search_registry.active()] == ["c", "a"]

    def test_unknown_names_are_skipped(self, search_registry, kinds, kinds_setting):
        kinds_setting(["b", "missing"])

        assert [k.name for k in search_registry.active()] == ["b"]


class TestSearch:
    def test_one_group_per_active_kind_in_the_setting_order(
        self, rf, kinds, kinds_setting
    ):
        kinds_setting(["c", "a"])

        groups = mvp.search.search(rf.get("/"), "word", 4)

        assert [g.kind.name for g in groups] == ["c", "a"]

    def test_a_kind_left_out_of_the_setting_is_never_asked(
        self, rf, kinds, kinds_setting
    ):
        kinds_setting(["c", "a"])

        mvp.search.search(rf.get("/"), "word", 4)

        assert kinds[1].queries == []
        assert kinds[0].queries == ["word"]

    def test_every_registered_kind_is_used_without_a_setting(self, rf, kinds):
        groups = mvp.search.search(rf.get("/"), "word", 4)

        assert [g.kind.name for g in groups] == ["a", "b", "c"]

    def test_each_group_is_limited_and_counted(self, rf, search_registry):
        search_registry.register(RecordingKind("a", count=7))

        (group,) = mvp.search.search(rf.get("/"), "word", 4)

        assert (len(group.results), group.total, group.more) == (4, 7, 3)

    @pytest.mark.parametrize("query", ["", "   ", "\t \n"])
    def test_an_empty_query_returns_no_groups(self, rf, kinds, query):
        assert mvp.search.search(rf.get("/"), query, 4) == []
        assert all(kind.queries == [] for kind in kinds)

    def test_the_query_is_stripped(self, rf, kinds):
        mvp.search.search(rf.get("/"), "  word  ", 4)

        assert kinds[0].queries == ["word"]

    def test_a_long_query_is_cut_before_it_reaches_the_kinds(self, rf, kinds):
        mvp.search.search(rf.get("/"), "x" * 300, 4)

        assert all(kind.queries == ["x" * 100] for kind in kinds)

    def test_an_error_from_a_kind_is_not_caught(self, rf, search_registry):
        class Failing(RecordingKind):
            def find(self, query, request):
                raise RuntimeError("boom")

        search_registry.register(Failing("bad"))

        with pytest.raises(RuntimeError):
            mvp.search.search(rf.get("/"), "word", 4)

    def test_a_kinds_own_more_url_is_kept(self, rf, search_registry):
        class Own(RecordingKind):
            def more_url(self, query):
                return f"/own/?q={query}"

        search_registry.register(Own("own"))

        (group,) = mvp.search.search(rf.get("/"), "word", 4)

        assert group.more_url == "/own/?q=word"

    def test_there_is_no_more_url_when_the_kind_gives_none(self, rf, kinds):
        groups = mvp.search.search(rf.get("/"), "word", 4)

        assert [g.more_url for g in groups] == [None, None, None]
