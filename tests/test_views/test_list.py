"""Tests for SearchMixin, OrderMixin, SearchOrderMixin in mvp.views.list.

Covers all user stories from specs/014-list-search-ordering/:

  US1 — Text Search (SearchMixin)
  US2 — Safe Column Ordering (OrderMixin three-tuple format)
  US3 — Combined Search and Ordering (SearchOrderMixin)
  US4 — django_filters composition

Source: mvp/views/list.py
"""

import pytest
from django.db.models.functions import Lower
from django.test import RequestFactory
from django.views.generic import ListView

from demo.models import Category, Product
from mvp.fixtures import _beautiful_soup
from mvp.views.list import (
    MVPListView,
    MVPListViewMixin,
    OrderMixin,
    SearchMixin,
    SearchOrderMixin,
)
from tests.factories import CategoryFactory, ProductFactory

try:
    from django_filters.views import FilterView as _FilterView

    HAS_DJANGO_FILTERS = True
except ImportError:  # pragma: no cover
    HAS_DJANGO_FILTERS = False

    class _FilterView(ListView):  # type: ignore[no-redef]
        """Fallback stub when django-filter is not installed."""

        pass


CARD = "cards/product_card.html"


class _StubFilterView(SearchOrderMixin, _FilterView):
    """Combined stub for django_filters composition tests (US4).

    Overrides render_to_response to avoid template rendering in unit tests.
    """

    model = Product
    filterset_fields = ["category"]
    search_fields = ["name"]
    order_by = [
        ("name_asc", "Name A-Z", "name"),
        ("name_desc", "Name Z-A", "-name"),
    ]

    def render_to_response(self, context, **kwargs):
        return context  # skip template rendering in unit tests


class _StubFilterViewNoSearch(SearchOrderMixin, _FilterView):
    """Stub for no-op search tests with filterset (US4)."""

    model = Product
    filterset_fields = ["category"]
    search_fields = None
    order_by = None

    def render_to_response(self, context, **kwargs):
        return context


def _make_view(base_mixin, params=None, extra_attrs=None):
    """Return a configured mixin+ListView stub instance with a fake GET request.

    The returned view has ``request``, ``kwargs``, and ``args`` set.
    Call ``get_queryset()`` and then set ``object_list`` before calling
    ``get_context_data()``.
    """
    rf = RequestFactory()
    request = rf.get("/", data=params or {})

    attrs = {
        "model": Product,
        "template_name": "base.html",
        **(extra_attrs or {}),
    }
    view_cls = type("StubView", (base_mixin, ListView), attrs)
    view = view_cls()
    view.request = request
    view.kwargs = {}
    view.args = []
    return view


def _make_search_view(params=None, extra_attrs=None):
    return _make_view(SearchMixin, params=params, extra_attrs=extra_attrs)


def _make_order_view(params=None, extra_attrs=None):
    return _make_view(OrderMixin, params=params, extra_attrs=extra_attrs)


def _make_search_order_view(params=None, extra_attrs=None):
    return _make_view(SearchOrderMixin, params=params, extra_attrs=extra_attrs)


def _make_filter_view(params=None):
    """Return a configured _StubFilterView with a fake GET request."""
    rf = RequestFactory()
    request = rf.get("/", data=params or {})
    view = _StubFilterView()
    view.setup(request)
    return view


def _make_filter_view_no_config(params=None):
    rf = RequestFactory()
    request = rf.get("/", data=params or {})
    view = _StubFilterViewNoSearch()
    view.setup(request)
    return view


@pytest.fixture
def cat(db):
    return CategoryFactory(name="Test Category", slug="test-category")


@pytest.fixture
def cat2(db):
    return CategoryFactory(name="Other Category", slug="other-category")


def _product(cat, name, description="", slug=None, price="9.99", **kwargs):
    """Helper to create a Product with minimal required fields."""
    if slug is None:
        slug = name.lower().replace(" ", "-").replace("/", "-")
    # sku must be unique; derive from slug to avoid constraint violations
    sku = kwargs.pop("sku", slug[:50])
    return ProductFactory(
        name=name,
        slug=slug,
        category=cat,
        description=description,
        price=price,
        sku=sku,
        **kwargs,
    )


class TestSearchMixin:
    def test_search_no_query_returns_all(self, db, cat):
        _product(cat, "Alpha")
        _product(cat, "Beta")
        view = _make_search_view(
            params={},
            extra_attrs={"search_fields": ["name"]},
        )
        assert view.get_queryset().count() == 2

    def test_search_single_word_filters(self, db, cat):
        _product(cat, "Alpha Widget")
        _product(cat, "Beta Widget")
        view = _make_search_view(
            params={"q": "alpha"},
            extra_attrs={"search_fields": ["name"]},
        )
        qs = view.get_queryset()
        assert qs.count() == 1
        assert qs.first().name == "Alpha Widget"

    def test_search_multi_word_or_semantics(self, db, cat):
        _product(cat, "Alpha Product")
        _product(cat, "Beta Product")
        _product(cat, "Gamma Product")
        view = _make_search_view(
            params={"q": "alpha beta"},
            extra_attrs={"search_fields": ["name"]},
        )
        qs = view.get_queryset()
        assert qs.count() == 2
        names = list(qs.values_list("name", flat=True))
        assert "Alpha Product" in names
        assert "Beta Product" in names

    def test_search_case_insensitive(self, db, cat):
        _product(cat, "Django Framework")
        view = _make_search_view(
            params={"q": "DJANGO"},
            extra_attrs={"search_fields": ["name"]},
        )
        assert view.get_queryset().count() == 1

    def test_search_whitespace_only_query_no_filter(self, db, cat):
        _product(cat, "Alpha")
        _product(cat, "Beta")
        view = _make_search_view(
            params={"q": "   "},
            extra_attrs={"search_fields": ["name"]},
        )
        assert view.get_queryset().count() == 2


class TestSearchMixinWordLimit:
    def test_a_very_long_query_still_returns_a_page(self, db, cat):
        _product(cat, "Alpha", description="widget")
        term = " ".join(f"w{i}" for i in range(4000))
        view = _make_search_view(
            params={"q": term},
            extra_attrs={"search_fields": ["name", "description"]},
        )
        assert list(view.get_queryset()) == []

    def test_only_the_first_words_are_searched(self, db, cat):
        _product(cat, "Alpha")
        _product(cat, "Beta")
        words = ["alpha"] + [f"w{i}" for i in range(SearchMixin.max_search_words)]
        view = _make_search_view(
            params={"q": " ".join([*words, "beta"])},
            extra_attrs={"search_fields": ["name"]},
        )
        qs = view.get_queryset()
        assert list(qs.values_list("name", flat=True)) == ["Alpha"]

    def test_the_limit_is_raisable_per_project(self, db, cat):
        _product(cat, "Alpha")
        _product(cat, "Beta")
        term = " ".join(["alpha", *[f"w{i}" for i in range(20)], "beta"])

        default_view = _make_search_view(
            params={"q": term},
            extra_attrs={"search_fields": ["name"]},
        )
        raised_view = _make_search_view(
            params={"q": term},
            extra_attrs={"search_fields": ["name"], "max_search_words": 50},
        )

        assert default_view.get_queryset().count() == 1
        assert raised_view.get_queryset().count() == 2


class TestSearchMixinNoConfig:
    def test_search_no_fields_configured_is_noop(self, db, cat):
        _product(cat, "Alpha")
        _product(cat, "Beta")
        view = _make_search_view(
            params={"q": "alpha"},
            extra_attrs={"search_fields": None},
        )
        assert view.get_queryset().count() == 2

    def test_search_is_searchable_false_when_unconfigured(self, db, cat):
        view = _make_search_view(
            params={},
            extra_attrs={"search_fields": None},
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["is_searchable"] is False

    def test_search_context_always_injected_when_unconfigured(self, db, cat):
        view = _make_search_view(
            params={"q": "anything"},
            extra_attrs={"search_fields": None},
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert "is_searchable" in ctx
        assert "search_query" in ctx
        assert ctx["search_query"] == "anything"

    def test_search_context_always_injected_when_configured(self, db, cat):
        view = _make_search_view(
            params={"q": "test"},
            extra_attrs={"search_fields": ["name"]},
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["is_searchable"] is True
        assert ctx["search_query"] == "test"

    def test_search_query_stripped_in_context(self, db, cat):
        view = _make_search_view(
            params={"q": "  hello  "},
            extra_attrs={"search_fields": ["name"]},
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        # search_query should be the raw GET value (not stripped)
        # per FR-002: context always injects the raw value
        assert ctx["search_query"] == "  hello  "


class TestSearchMixinAdvanced:
    def test_search_related_field_traversal(self, db, cat):
        _product(cat, "Widget A", description="")
        # Create a product whose category name does NOT match
        other_cat = CategoryFactory(name="Other Cat", slug="other-cat")
        _product(other_cat, "Widget B", description="")
        view = _make_search_view(
            params={"q": "Test"},  # matches cat.name = "Test Category"
            extra_attrs={"search_fields": ["category__name"]},
        )
        qs = view.get_queryset()
        assert qs.count() == 1
        assert qs.first().name == "Widget A"

    def test_search_distinct_deduplicates(self, db, cat):
        # A product with "python" in both name and description
        _product(cat, "Python Widget", description="python tools for developers")
        _product(cat, "Java Widget", description="java tools")
        view = _make_search_view(
            params={"q": "python"},
            extra_attrs={"search_fields": ["name", "description"]},
        )
        qs = view.get_queryset()
        assert qs.count() == 1  # not 2 even though it matched both fields


_ORDER_CHOICES = [
    ("name_asc", "Name A-Z", "name"),
    ("name_desc", "Name Z-A", "-name"),
    ("price_asc", "Price Low-High", "price"),
]


class TestOrderMixin:
    def test_order_valid_key_applies_orm_expression(self, db, cat):
        _product(cat, "Beta", price="5.00")
        _product(cat, "Alpha", price="10.00")
        view = _make_order_view(
            params={"o": "name_asc"},
            extra_attrs={"order_by": _ORDER_CHOICES},
        )
        qs = list(view.get_queryset())
        assert qs[0].name == "Alpha"
        assert qs[1].name == "Beta"

    def test_order_invalid_key_ignored(self, db, cat):
        _product(cat, "Zeta")
        _product(cat, "Alpha")
        view = _make_order_view(
            params={"o": "arbitrary_field"},
            extra_attrs={"order_by": _ORDER_CHOICES},
        )
        # Just verify it returns without error and doesn't crash
        qs = view.get_queryset()
        assert qs.count() == 2

    def test_order_absent_parameter_no_override(self, db, cat):
        _product(cat, "Zeta")
        _product(cat, "Alpha")
        view = _make_order_view(
            params={},
            extra_attrs={"order_by": _ORDER_CHOICES},
        )
        # get_queryset() should not crash and should return all records
        qs = view.get_queryset()
        assert qs.count() == 2

    def test_order_descending_orm_expression(self, db, cat):
        _product(cat, "Alpha", price="5.00")
        _product(cat, "Beta", price="10.00")
        view = _make_order_view(
            params={"o": "name_desc"},
            extra_attrs={"order_by": _ORDER_CHOICES},
        )
        qs = list(view.get_queryset())
        assert qs[0].name == "Beta"
        assert qs[1].name == "Alpha"


class TestOrderMixinTiebreak:
    def test_a_sequence_orm_expression_applies_every_field(self, db, cat):
        _product(cat, "Charlie", price="5.00")
        _product(cat, "Alpha", price="5.00")
        choices = [("name_asc", "Name (A-Z)", [Lower("name"), "pk"])]
        view = _make_order_view(
            params={"o": "name_asc"}, extra_attrs={"order_by": choices}
        )
        qs = list(view.get_queryset())
        assert [p.name for p in qs] == ["Alpha", "Charlie"]

    def test_tiebreak_breaks_the_tie_deterministically_and_completely(self, db, cat):
        tied = [_product(cat, "Same", slug=f"same-{i}") for i in range(3)]
        choices = [("name_asc", "Name (A-Z)", [Lower("name"), "pk"])]
        view = _make_order_view(
            params={"o": "name_asc"}, extra_attrs={"order_by": choices}
        )
        qs = list(view.get_queryset())
        assert [p.pk for p in qs] == [p.pk for p in tied]


class TestOrderMixinSecurity:
    def test_order_public_key_not_equal_orm_expression(self, db, cat):
        _product(cat, "Alpha", price="5.00")
        _product(cat, "Beta", price="10.00")
        choices = [
            ("cheapest", "Cheapest First", "price"),  # public_key ≠ orm_expression
        ]
        view = _make_order_view(
            params={"o": "cheapest"},
            extra_attrs={"order_by": choices},
        )
        qs = list(view.get_queryset())
        assert qs[0].price < qs[1].price


class TestOrderMixinNoConfig:
    def test_order_no_config_is_noop(self, db, cat):
        _product(cat, "Alpha")
        _product(cat, "Beta")
        view = _make_order_view(
            params={"o": "name_asc"},
            extra_attrs={"order_by": None},
        )
        qs = view.get_queryset()
        assert qs.count() == 2

    def test_order_context_not_injected_when_unconfigured(self, db, cat):
        view = _make_order_view(
            params={},
            extra_attrs={"order_by": None},
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert "order_by_choices" not in ctx
        assert "current_ordering" not in ctx

    def test_order_empty_list_is_noop(self, db, cat):
        _product(cat, "Alpha")
        view = _make_order_view(
            params={"o": "name_asc"},
            extra_attrs={"order_by": []},
        )
        qs = view.get_queryset()
        assert qs.count() == 1


class TestOrderMixinContext:
    def test_order_context_choices_full_three_tuple_list(self, db, cat):
        view = _make_order_view(
            params={},
            extra_attrs={"order_by": _ORDER_CHOICES},
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["order_by_choices"] == _ORDER_CHOICES

    def test_order_context_current_ordering_is_public_key(self, db, cat):
        view = _make_order_view(
            params={"o": "name_asc"},
            extra_attrs={"order_by": _ORDER_CHOICES},
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert (
            ctx["current_ordering"] == "name_asc"
        )  # public_key, not "name" (orm_expression)

    def test_order_context_current_ordering_empty_on_invalid(self, db, cat):
        view = _make_order_view(
            params={"o": "bogus_key"},
            extra_attrs={"order_by": _ORDER_CHOICES},
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["current_ordering"] == ""

    def test_order_context_current_ordering_empty_when_absent(self, db, cat):
        view = _make_order_view(
            params={},
            extra_attrs={"order_by": _ORDER_CHOICES},
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["current_ordering"] == ""


_SEARCH_ORDER_CHOICES = [
    ("name_asc", "Name A-Z", "name"),
    ("name_desc", "Name Z-A", "-name"),
]


class TestSearchOrderMixin:
    def test_combined_search_and_ordering(self, db, cat):
        _product(cat, "Alpha Widget", description="")
        _product(cat, "Beta Widget", description="")
        _product(cat, "Gamma Tool", description="")
        view = _make_search_order_view(
            params={"q": "widget", "o": "name_desc"},
            extra_attrs={
                "search_fields": ["name"],
                "order_by": _SEARCH_ORDER_CHOICES,
            },
        )
        qs = list(view.get_queryset())
        assert len(qs) == 2
        assert qs[0].name == "Beta Widget"
        assert qs[1].name == "Alpha Widget"

    def test_combined_search_only_retains_default_ordering(self, db, cat):
        _product(cat, "Alpha Widget")
        _product(cat, "Beta Tool")
        view = _make_search_order_view(
            params={"q": "widget"},
            extra_attrs={
                "search_fields": ["name"],
                "order_by": _SEARCH_ORDER_CHOICES,
            },
        )
        qs = view.get_queryset()
        assert qs.count() == 1
        assert qs.first().name == "Alpha Widget"

    def test_combined_ordering_only_returns_all_records(self, db, cat):
        _product(cat, "Beta Product")
        _product(cat, "Alpha Product")
        view = _make_search_order_view(
            params={"o": "name_asc"},
            extra_attrs={
                "search_fields": ["name"],
                "order_by": _SEARCH_ORDER_CHOICES,
            },
        )
        qs = list(view.get_queryset())
        assert len(qs) == 2
        assert qs[0].name == "Alpha Product"


class TestSearchOrderMixinMROOrder:
    def test_ordering_applied_before_distinct(self, db, cat):
        # Product matches "python" in both name and description
        p = _product(cat, "Python Widget", description="python tools for developers")
        _product(cat, "Java Tool", description="java tools")
        view = _make_search_order_view(
            params={"q": "python", "o": "name_asc"},
            extra_attrs={
                "search_fields": ["name", "description"],
                "order_by": [("name_asc", "Name A-Z", "name")],
            },
        )
        qs = view.get_queryset()
        # Must return exactly one result (distinct deduplicates multi-field matches)
        assert qs.count() == 1
        assert qs.first().pk == p.pk


requires_django_filters = pytest.mark.skipif(
    not HAS_DJANGO_FILTERS,
    reason="django-filter is not installed",
)


@requires_django_filters
class TestDjangoFiltersComposition:
    def test_filterset_and_search_both_applied(self, db, cat, cat2):
        _product(cat, "Python Widget")
        _product(cat, "Java Widget")
        _product(cat2, "Python Framework")

        view = _make_filter_view(params={"q": "Python", "category": str(cat.pk)})
        view.get(view.request)  # sets object_list via FilterView.get()

        names = list(view.object_list.values_list("name", flat=True))
        assert "Python Widget" in names
        assert "Java Widget" not in names
        assert "Python Framework" not in names

    def test_filterset_and_ordering_both_applied(self, db, cat):
        _product(cat, "Beta Product")
        _product(cat, "Alpha Product")

        view = _make_filter_view(
            params={"category": str(cat.pk), "o": "name_asc"},
        )
        view.get(view.request)

        qs = list(view.object_list)
        assert len(qs) == 2
        assert qs[0].name == "Alpha Product"
        assert qs[1].name == "Beta Product"

    def test_filterset_search_ordering_all_combined(self, db, cat, cat2):
        _product(cat, "Beta Widget")
        _product(cat, "Alpha Widget")
        _product(cat2, "Widget Other Category")

        view = _make_filter_view(
            params={"category": str(cat.pk), "q": "Widget", "o": "name_asc"},
        )
        view.get(view.request)

        qs = list(view.object_list)
        assert len(qs) == 2
        assert qs[0].name == "Alpha Widget"
        assert qs[1].name == "Beta Widget"


@requires_django_filters
class TestDjangoFiltersNoOpCases:
    def test_no_search_fields_search_is_noop_with_filterset(self, db, cat, cat2):
        _product(cat, "Alpha")
        _product(cat2, "Beta")

        view = _make_filter_view_no_config(
            params={"q": "Alpha"},  # should have no effect
        )
        view.get(view.request)

        # No search_fields means no filtering on ?q= — all products returned
        assert view.object_list.count() == 2

    def test_no_order_by_ordering_is_noop_with_filterset(self, db, cat):
        _product(cat, "Beta")
        _product(cat, "Alpha")

        view = _make_filter_view_no_config(params={"o": "name_asc"})
        view.get(view.request)

        # No order_by means ?o= has no effect — model default ordering is used
        assert view.object_list.count() == 2


def _make_list_view(params=None, extra_attrs=None):
    """Return a configured MVPListViewMixin+ListView stub with a fake GET request.

    The returned view has ``request``, ``kwargs``, and ``args`` set.
    Call ``get_queryset()`` and then set ``object_list`` before calling
    ``get_context_data()``.
    """
    rf = RequestFactory()
    request = rf.get("/", data=params or {})

    attrs = {
        "model": Product,
        "template_name": "base.html",
        **(extra_attrs or {}),
    }
    view_cls = type("StubListView", (MVPListViewMixin, ListView), attrs)
    view = view_cls()
    view.request = request
    view.kwargs = {}
    view.args = []
    return view


class TestMVPListViewMixinZeroConfig:
    def test_default_page_title_from_model(self, db):
        view = _make_list_view()
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        expected = Product._meta.verbose_name_plural.title()
        assert ctx["page"]["title"] == expected

    def test_default_list_item_template_convention(self, db):
        view = _make_list_view()
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["list_item_template"] == "demo/product_list_item.html"


class TestMVPListViewMixinItemTemplate:
    def test_explicit_list_item_template_overrides_convention(self, db):
        view = _make_list_view(extra_attrs={"list_item_template": "shared/item.html"})
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["list_item_template"] == "shared/item.html"

    def test_list_item_template_convention_uses_app_label_and_model_name(self, db):
        view = _make_list_view(extra_attrs={"model": Category})
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["list_item_template"] == "demo/category_list_item.html"

    def test_empty_string_list_item_template_falls_back_to_convention(self, db):
        view = _make_list_view(extra_attrs={"list_item_template": ""})
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["list_item_template"] == "demo/product_list_item.html"

    def test_get_list_item_template_override_takes_full_precedence(self, db):
        rf = RequestFactory()
        request = rf.get("/")
        view_cls = type(
            "StubListView",
            (MVPListViewMixin, ListView),
            {
                "model": Product,
                "list_item_template": "should/be/ignored.html",
                "template_name": "base.html",
                "get_list_item_template": lambda self: "custom/override.html",
            },
        )
        view = view_cls()
        view.request = request
        view.kwargs = {}
        view.args = []
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["list_item_template"] == "custom/override.html"

    def test_missing_model_and_template_raises_error(self):
        rf = RequestFactory()
        request = rf.get("/")
        view_cls = type(
            "StubListView",
            (MVPListViewMixin, ListView),
            {"model": None, "list_item_template": None, "template_name": "base.html"},
        )
        view = view_cls()
        view.request = request
        view.kwargs = {}
        view.args = []
        with pytest.raises(AttributeError):
            view.get_list_item_template()


class TestMVPListViewMixinEmptyState:
    def test_empty_state_present_in_context_with_defaults(self, db):
        view = _make_list_view(extra_attrs={"show_create_action": True})
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert "empty_state" in ctx
        assert ctx["empty_state"]["heading"]
        assert ctx["empty_state"]["message"]

    def test_empty_state_heading_override(self, db):
        view = _make_list_view(extra_attrs={"empty_state_heading": "No products found"})
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["empty_state"]["heading"] == "No products found"

    def test_empty_state_message_none_suppresses_message(self, db):
        view = _make_list_view(extra_attrs={"empty_state_message": None})
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["empty_state"]["message"] is None

    def test_empty_state_heading_none_suppresses_heading(self, db):
        view = _make_list_view(extra_attrs={"empty_state_heading": None})
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["empty_state"]["heading"] is None

    def test_empty_state_message_invites_creation_when_permitted(self, db):
        view = _make_list_view(extra_attrs={"show_create_action": True})
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["empty_state"]["message"] == MVPListViewMixin.empty_state_message

    def test_empty_state_message_dropped_when_not_permitted(self, db):
        view = _make_list_view()  # show_create_action=False by default
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["empty_state"]["message"] is None
        assert ctx["empty_state"]["heading"], "the heading still explains the page"

    def test_custom_empty_state_message_also_dropped_when_not_permitted(self, db):
        view = _make_list_view(
            extra_attrs={
                "empty_state_message": "Custom copy.",
                "show_create_action": False,
            }
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["empty_state"]["message"] is None


class TestMVPListViewMixinDirectory:
    def test_create_url_absent_when_permission_false(self, db):
        view = _make_list_view()  # show_create_action=False by default
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert "create_url" not in ctx["directory"]

    def test_no_detail_update_delete_urls_in_directory(self, db):
        view = _make_list_view()  # show_create_action=False avoids URL resolution
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert "detail_url" not in ctx["directory"]
        assert "update_url" not in ctx["directory"]
        assert "delete_url" not in ctx["directory"]


class TestMVPListViewMixinGridConfig:
    def test_grid_config_passthrough(self, db):
        grid = {"sm": 1, "md": 2, "lg": 3}
        view = _make_list_view(extra_attrs={"grid": grid})
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["grid_config"] == {"sm": 1, "md": 2, "lg": 3}

    def test_grid_config_empty_dict_when_not_configured(self, db):
        view = _make_list_view()  # grid defaults to {}
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["grid_config"] == {}


class TestMVPListViewMixinSearchOrdering:
    def test_search_query_in_context_when_search_active(self, db):
        view = _make_list_view(
            params={"q": "foo"},
            extra_attrs={"search_fields": ["name"]},
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["search_query"] == "foo"

    def test_search_query_empty_when_not_configured(self, db):
        view = _make_list_view(extra_attrs={"search_fields": None})
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["search_query"] == ""

    def test_current_ordering_in_context_when_ordering_active(self, db):
        view = _make_list_view(
            params={"o": "name_asc"},
            extra_attrs={
                "order_by": [
                    ("name_asc", "Name A-Z", "name"),
                    ("name_desc", "Name Z-A", "-name"),
                ],
            },
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["current_ordering"] == "name_asc"

    def test_mvp_list_view_all_context_keys_present_with_defaults(self, db):
        view = _make_list_view()
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert "list_item_template" in ctx
        assert "empty_state" in ctx
        assert "grid_config" in ctx
        assert "directory" in ctx
        assert "search_query" in ctx
        assert "is_searchable" in ctx
        assert "page" in ctx
        assert "title" in ctx["page"]


class TestMVPListViewMixinPageMetadata:
    def test_default_breadcrumbs_include_home_and_page_title(self, db):
        view = _make_list_view()
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        breadcrumbs = ctx["page"]["breadcrumbs"]
        assert breadcrumbs[0]["href"] == "/"
        expected_title = Product._meta.verbose_name_plural.title()
        assert breadcrumbs[1] == {"text": expected_title}

    def test_page_title_attribute_overrides_model_derived_title(self, db):
        view = _make_list_view(extra_attrs={"page_title": "Our Catalogue"})
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["page"]["title"] == "Our Catalogue"


class TestListViewInlineCreate:
    def test_create_form_in_context_when_configured_and_permitted(self, db):
        from demo.forms import ProductForm

        view = _make_list_view(
            extra_attrs={
                "create_form_class": ProductForm,
                "show_create_action": True,
            }
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()

        assert "create_form" in ctx
        assert isinstance(ctx["create_form"], ProductForm)

    def test_create_modal_title_auto_derived_from_verbose_name(self, db):
        from demo.forms import ProductForm

        view = _make_list_view(
            extra_attrs={
                "create_form_class": ProductForm,
                "show_create_action": True,
                "create_modal_title": None,
            }
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()

        expected = Product._meta.verbose_name.title()
        assert ctx["create_modal_title"].endswith(expected)

    def test_create_modal_title_override_attribute(self, db):
        from demo.forms import ProductForm

        view = _make_list_view(
            extra_attrs={
                "create_form_class": ProductForm,
                "show_create_action": True,
                "create_modal_title": "Custom Create Title",
            }
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()

        assert ctx["create_modal_title"] == "Custom Create Title"

    def test_get_create_form_hook_allows_custom_instantiation(self, db):
        from demo.forms import ProductForm

        custom_form = ProductForm(initial={"name": "Custom Initial"})

        view = _make_list_view(
            extra_attrs={
                "create_form_class": ProductForm,
                "show_create_action": True,
            }
        )

        # Override get_create_form to return custom instance
        view.get_create_form = lambda: custom_form
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()

        assert ctx["create_form"] is custom_form
        assert ctx["create_form"].initial["name"] == "Custom Initial"

    def test_permission_boolean_false_prevents_form_injection(self, db):
        from demo.forms import ProductForm

        view = _make_list_view(
            extra_attrs={
                "create_form_class": ProductForm,
                "show_create_action": False,
            }
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()

        assert "create_form" not in ctx
        assert "create_modal_title" not in ctx

    def test_permission_callable_returns_false_prevents_form_injection(self, db, rf):
        from django.contrib.auth.models import AnonymousUser

        from demo.forms import ProductForm

        view = _make_list_view(
            extra_attrs={
                "create_form_class": ProductForm,
                "show_create_action": staticmethod(lambda user: False),
            }
        )
        view.request.user = AnonymousUser()
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()

        assert "create_form" not in ctx
        assert "create_modal_title" not in ctx

    def test_permission_callable_returns_true_allows_form_injection(
        self, db, rf, make_user
    ):
        from demo.forms import ProductForm

        user = make_user(username="testuser", password="password")

        view = _make_list_view(
            extra_attrs={
                "create_form_class": ProductForm,
                "show_create_action": staticmethod(lambda user: user.is_authenticated),
            }
        )
        view.request.user = user
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()

        assert "create_form" in ctx
        assert isinstance(ctx["create_form"], ProductForm)

    def test_backward_compat_no_form_class_no_change(self, db):
        # View without create_form_class should work exactly as before
        view = _make_list_view(
            extra_attrs={
                "create_form_class": None,
                "show_create_action": False,
            }
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()

        # Should not have create_form in context
        assert "create_form" not in ctx
        # Should not have create_modal_title in context
        assert "create_modal_title" not in ctx
        # All other context keys should still be present
        assert "list_item_template" in ctx
        assert "directory" in ctx
        assert "page" in ctx


def _render_empty_list_view(rf, show_create_action):
    """Instantiate, dispatch and fully render an empty MVPListView, as HTML."""
    view_cls = type(
        "StubEmptyStateListView",
        (MVPListView,),
        {
            "model": Product,
            "show_create_action": show_create_action,
        },
    )
    view = view_cls()
    view.setup(rf.get("/"))
    response = view.get(view.request)
    response.render()
    return response.content.decode()


class TestEmptyStateMessageRendering:
    def test_cta_message_and_button_render_when_permitted(self, rf, db):
        html = _render_empty_list_view(rf, show_create_action=True)
        soup = _beautiful_soup()(html, "html.parser")
        empty_state = soup.find(class_="mvp-list-empty")
        assert empty_state.find("p") is not None
        assert soup.find("a", href="/products/create/") is not None

    def test_no_message_and_no_button_when_not_permitted(self, rf, db):
        html = _render_empty_list_view(rf, show_create_action=False)
        soup = _beautiful_soup()(html, "html.parser")
        assert soup.find("a", href="/products/create/") is None
        empty_state = soup.find(class_="mvp-list-empty")
        assert empty_state.find("p") is None, "no empty paragraph is rendered"


def _render_search_sort_list_view(rf):
    """Render a full, empty MVPListView with search + ordering but no FilterSet."""
    view_cls = type(
        "StubSearchSortListView",
        (MVPListView,),
        {
            "model": Product,
            "list_item_template": CARD,
            "search_fields": ["name"],
            "order_by": [("name_asc", "Name (A-Z)", "name")],
        },
    )
    view = view_cls()
    view.setup(rf.get("/"))
    response = view.get(view.request)
    response.render()
    return response.content.decode()


class TestSearchSortControlsWithoutFilterSet:
    def test_form_referenced_by_search_and_sort_exists_in_the_page(self, rf, cat):
        _product(cat, "Lamp")
        html = _render_search_sort_list_view(rf)
        soup = _beautiful_soup()(html, "html.parser")

        form_ids = {form.get("id") for form in soup.find_all("form") if form.get("id")}
        referring_ids = {el.get("form") for el in soup.find_all(attrs={"form": True})}

        assert referring_ids, "expected search/sort controls to reference a form"
        orphaned = referring_ids - form_ids
        assert not orphaned, (
            f"controls reference form ids that do not exist: {orphaned}"
        )

    def test_no_fallback_form_when_neither_search_nor_sort_configured(self, rf, db):
        view_cls = type("StubPlainListView", (MVPListView,), {"model": Product})
        view = view_cls()
        view.setup(rf.get("/"))
        response = view.get(view.request)
        response.render()
        soup = _beautiful_soup()(response.content.decode(), "html.parser")

        assert soup.find(id="filterForm") is None

    def test_no_duplicate_filter_form_when_filterset_is_configured(self, rf, cat):
        from django_filters.views import FilterView

        _product(cat, "Lamp")

        view_cls = type(
            "StubFilteredListView",
            (MVPListViewMixin, FilterView),
            {
                "model": Product,
                "list_item_template": CARD,
                "filterset_fields": ["category"],
                "search_fields": ["name"],
                "order_by": [("name_asc", "Name (A-Z)", "name")],
            },
        )
        view = view_cls()
        view.setup(rf.get("/"))
        response = view.get(view.request)
        response.render()
        soup = _beautiful_soup()(response.content.decode(), "html.parser")

        assert len(soup.find_all(id="filterForm")) == 1


class TestActionsFollowViewConfiguration:
    def _render(self, rf, **attrs):
        view_cls = type(
            "StubActionsListView",
            (MVPListView,),
            {"model": Product, "list_item_template": CARD, **attrs},
        )
        view = view_cls()
        view.setup(rf.get("/"))
        response = view.get(view.request)
        response.render()
        return response.content.decode()

    def test_search_follows_search_fields(self, rf, cat):
        _product(cat, "Lamp")
        assert 'name="q"' in self._render(rf, search_fields=["name"])
        assert 'name="q"' not in self._render(rf, search_fields=None)

    def test_sort_follows_order_by(self, rf, cat):
        _product(cat, "Lamp")
        orderings = [("name_asc", "Name (A-Z)", "name")]
        assert "ordering-option" in self._render(rf, order_by=orderings)
        assert "ordering-option" not in self._render(rf, order_by=None)

    def test_create_follows_show_create_action(self, rf, db):
        shown = self._render(rf, show_create_action=True)
        hidden = self._render(rf, show_create_action=False)
        assert (
            _beautiful_soup()(shown, "html.parser").find("a", href="/products/create/")
            is not None
        )
        assert (
            _beautiful_soup()(hidden, "html.parser").find("a", href="/products/create/")
            is None
        )

    def test_filter_follows_the_filterset(self, rf, cat):
        from django_filters.views import FilterView

        _product(cat, "Lamp")

        view_cls = type(
            "StubFilteredActionsView",
            (MVPListViewMixin, FilterView),
            {
                "model": Product,
                "list_item_template": CARD,
                "filterset_fields": ["category"],
            },
        )
        view = view_cls()
        view.setup(rf.get("/"))
        response = view.get(view.request)
        response.render()
        filtered = _beautiful_soup()(response.content.decode(), "html.parser")

        assert filtered.find(id="filterModal") is not None
        unfiltered = _beautiful_soup()(self._render(rf), "html.parser")
        assert unfiltered.find(id="filterModal") is None

    def test_a_bare_list_view_draws_no_controls_at_all(self, rf, db):
        html = self._render(rf)
        soup = _beautiful_soup()(html, "html.parser")

        assert 'name="q"' not in html
        assert "ordering-option" not in html
        assert soup.find(id="filterModal") is None
        assert soup.find(id="filterForm") is None


def _refinement_context(rf, query="", **attrs):
    """Return the context of a filtered product list requested with ``query``."""
    import django_filters
    from django_filters.views import FilterView

    class ProductFilterSet(django_filters.FilterSet):
        price = django_filters.RangeFilter()

        class Meta:
            model = Product
            fields = ["name", "status", "category"]

    view_cls = type(
        "StubRefinedListView",
        (MVPListViewMixin, FilterView),
        {
            "model": Product,
            "filterset_class": ProductFilterSet,
            "search_fields": ["name"],
            "order_by": [("name_asc", "Name (A-Z)", "name")],
            "paginate_by": 10,
            "render_to_response": lambda self, context, **kwargs: context,
            **attrs,
        },
    )
    view = view_cls()
    view.setup(rf.get(f"/products/{query}"))
    return view.get(view.request)


class TestListRefinements:
    def test_an_unrefined_list_has_no_refinements_and_no_clear_url(self, rf, db):
        context = _refinement_context(rf, "?o=name_asc&page=1")

        assert context["refinements"] == []
        assert "clear_refinements_url" not in context

    def test_a_search_is_a_refinement_removed_by_dropping_q(self, rf, db):
        context = _refinement_context(rf, "?q=lamp&o=name_asc&page=1")

        [search] = context["refinements"]
        assert search["kind"] == "search"
        assert search["value"] == "lamp"
        assert search["remove_url"] == "/products/?o=name_asc"

    def test_a_blank_search_is_not_a_refinement(self, rf, db):
        context = _refinement_context(rf, "?q=++")

        assert context["refinements"] == []

    def test_a_search_is_not_a_refinement_without_search_fields(self, rf, db):
        context = _refinement_context(rf, "?q=lamp", search_fields=None)

        assert context["refinements"] == []

    def test_each_applied_filter_is_a_refinement_labelled_by_its_field(self, rf, db):
        context = _refinement_context(rf, "?name=Lamp&status=draft")

        by_name = {item["name"]: item for item in context["refinements"]}
        assert set(by_name) == {"name", "status"}
        assert by_name["name"]["kind"] == "filter"
        assert by_name["name"]["label"] == "Name"
        assert by_name["name"]["value"] == "Lamp"

    def test_a_choice_filter_shows_the_choice_label_not_the_stored_value(self, rf, db):
        context = _refinement_context(rf, "?status=draft")

        [status] = context["refinements"]
        expected = dict(Product._meta.get_field("status").flatchoices)["draft"]
        assert status["value"] == expected

    def test_a_related_filter_shows_the_related_record(self, rf, cat):
        context = _refinement_context(rf, f"?category={cat.pk}")

        [category] = context["refinements"]
        assert category["value"] == str(cat)

    def test_removing_a_filter_keeps_every_other_refinement_and_the_sort(self, rf, db):
        context = _refinement_context(
            rf, "?q=lamp&name=Lamp&status=draft&o=name_asc&page=1"
        )

        by_name = {item["name"]: item for item in context["refinements"]}
        assert by_name["name"]["remove_url"] == (
            "/products/?q=lamp&status=draft&o=name_asc"
        )

    def test_a_range_filter_is_one_refinement_removed_by_both_its_params(self, rf, db):
        context = _refinement_context(rf, "?price_min=5&price_max=20&q=lamp")

        by_name = {item["name"]: item for item in context["refinements"]}
        assert "5" in by_name["price"]["value"]
        assert "20" in by_name["price"]["value"]
        assert by_name["price"]["remove_url"] == "/products/?q=lamp"

    def test_clear_url_drops_search_filters_and_page_and_keeps_the_sort(self, rf, db):
        context = _refinement_context(
            rf, "?q=lamp&name=Lamp&price_min=5&o=name_asc&page=1"
        )

        assert context["clear_refinements_url"] == "/products/?o=name_asc"

    def test_clear_filters_url_drops_both_params_of_a_range_filter(self, rf, db):
        context = _refinement_context(rf, "?price_min=5&price_max=20&q=lamp")

        assert context["clear_filters_url"] == "/products/?q=lamp"

    def test_a_list_without_a_filterset_still_reports_its_search(self, rf, db):
        view_cls = type(
            "StubSearchOnlyListView",
            (MVPListView,),
            {
                "model": Product,
                "search_fields": ["name"],
                "render_to_response": lambda self, context, **kwargs: context,
            },
        )
        view = view_cls()
        view.setup(rf.get("/products/?q=lamp"))

        context = view.get(view.request)

        assert [item["name"] for item in context["refinements"]] == ["q"]
        assert context["clear_refinements_url"] == "/products/"


class TestListResultCount:
    def _context(self, rf, query="", **attrs):
        view_cls = type(
            "StubCountedListView",
            (MVPListView,),
            {
                "model": Product,
                "search_fields": ["name"],
                "render_to_response": lambda self, context, **kwargs: context,
                **attrs,
            },
        )
        view = view_cls()
        view.setup(rf.get(f"/products/{query}"))
        return view.get(view.request)

    def test_counts_every_page_of_a_paginated_list(self, rf, cat):
        for number in range(5):
            _product(cat, f"Lamp {number}")

        context = self._context(rf, paginate_by=2)

        assert context["result_count"] == 5

    def test_counts_an_unpaginated_list(self, rf, cat):
        for number in range(3):
            _product(cat, f"Lamp {number}")

        context = self._context(rf, paginate_by=None)

        assert context["result_count"] == 3

    def test_counts_only_what_the_search_matches(self, rf, cat):
        _product(cat, "Lamp")
        _product(cat, "Chair")

        context = self._context(rf, "?q=lamp")

        assert context["result_count"] == 1


def _list_page(rf, query="", bases=(MVPListView,), **attrs):
    """Render a product list page requested with ``query`` and return its soup."""
    view_cls = type(
        "StubRenderedListView",
        bases,
        {
            "model": Product,
            "list_item_template": CARD,
            "search_fields": ["name"],
            "order_by": [("name_asc", "Name (A-Z)", "name")],
            **attrs,
        },
    )
    view = view_cls()
    view.setup(rf.get(f"/products/{query}"))
    response = view.get(view.request)
    response.render()
    return _beautiful_soup()(response.content.decode(), "html.parser")


def _filtered_list_page(rf, query="", **attrs):
    from django_filters.views import FilterView

    return _list_page(
        rf,
        query,
        bases=(MVPListViewMixin, FilterView),
        filterset_fields=["name", "status"],
        **attrs,
    )


class TestListPageToolbar:
    def test_no_toolbar_when_there_are_no_records_and_nothing_is_applied(self, rf, db):
        soup = _list_page(rf)

        assert soup.find(class_="mvp-list-toolbar") is None

    def test_toolbar_stays_when_a_search_matches_nothing(self, rf, cat):
        _product(cat, "Lamp")

        soup = _list_page(rf, "?q=chair")

        assert soup.find(class_="mvp-list-toolbar").find(attrs={"name": "q"})

    def test_add_action_is_outside_the_toolbar(self, rf, cat):
        _product(cat, "Lamp")

        soup = _list_page(rf, show_create_action=True)

        create = soup.find("a", href="/products/create/")
        assert create is not None
        assert create.find_parent(class_="mvp-list-toolbar") is None

    def test_summary_names_one_record_in_the_singular(self, rf, cat):
        _product(cat, "Lamp")

        summary = _list_page(rf).find(class_="mvp-list-summary").get_text(" ")

        assert summary.split() == ["1", str(Product._meta.verbose_name)]

    def test_summary_names_several_records_in_the_plural(self, rf, cat):
        _product(cat, "Lamp")
        _product(cat, "Chair")

        summary = _list_page(rf).find(class_="mvp-list-summary").get_text(" ")

        assert summary.split() == ["2", str(Product._meta.verbose_name_plural)]

    def test_summary_counts_results_when_the_list_is_narrowed(self, rf, cat):
        _product(cat, "Lamp")
        _product(cat, "Chair")

        summary = _list_page(rf, "?q=lamp").find(class_="mvp-list-summary")

        assert "1" in summary.get_text(" ").split()
        assert str(Product._meta.verbose_name) not in summary.get_text(" ").split()


class TestListPageRefinements:
    def test_nothing_is_drawn_for_a_list_that_is_not_narrowed(self, rf, cat):
        _product(cat, "Lamp")

        assert _list_page(rf).find(class_="mvp-list-refinements") is None

    def test_each_refinement_links_to_the_page_without_it(self, rf, cat):
        _product(cat, "Lamp")

        soup = _filtered_list_page(rf, "?q=lamp&name=Lamp&o=name_asc")

        hrefs = {
            link["href"]
            for link in soup.find(class_="mvp-list-refinements").find_all("a")
        }
        assert "/products/?name=Lamp&o=name_asc" in hrefs
        assert "/products/?q=lamp&o=name_asc" in hrefs

    def test_several_refinements_get_one_link_that_clears_them_all(self, rf, cat):
        _product(cat, "Lamp")

        soup = _filtered_list_page(rf, "?q=lamp&name=Lamp&o=name_asc")

        refinements = soup.find(class_="mvp-list-refinements")
        assert refinements.find("a", href="/products/?o=name_asc") is not None

    def test_a_single_refinement_gets_no_separate_clear_link(self, rf, cat):
        _product(cat, "Lamp")

        soup = _filtered_list_page(rf, "?q=lamp")

        assert len(soup.find(class_="mvp-list-refinements").find_all("a")) == 1

    def test_a_refinement_value_is_escaped(self, rf, cat):
        _product(cat, "Lamp")

        soup = _list_page(rf, "?q=%3Cscript%3Ealert(1)%3C/script%3E")

        assert soup.find(class_="mvp-list-refinements").find("script") is None


class TestListPageEmptyState:
    def test_empty_state_is_not_a_grid_item(self, rf, db):
        soup = _list_page(rf, grid={"md": 2})

        assert soup.find(class_="mvp-list-empty").find_parent(class_="grid") is None

    def test_no_records_offers_the_create_action(self, rf, db):
        soup = _list_page(rf, show_create_action=True)

        empty = soup.find(class_="mvp-list-empty")
        assert empty.find("a", href="/products/create/") is not None

    def test_nothing_matching_offers_to_clear_and_not_to_create(self, rf, cat):
        _product(cat, "Lamp")

        soup = _list_page(rf, "?q=chair&o=name_asc", show_create_action=True)

        empty = soup.find(class_="mvp-list-empty")
        assert empty.find("a", href="/products/?o=name_asc") is not None
        assert empty.find("a", href="/products/create/") is None

    def test_no_records_opens_the_create_dialog_when_the_page_has_one(self, rf, db):
        from demo.forms import ProductForm

        soup = _list_page(rf, show_create_action=True, create_form_class=ProductForm)

        empty = soup.find(class_="mvp-list-empty")
        assert empty.find("a", href="/products/create/") is None
        assert "createModal" in empty.find("button")["onclick"]
        assert soup.find(id="createModal") is not None


class TestListPagePagination:
    def test_one_page_draws_no_pager(self, rf, cat):
        _product(cat, "Lamp")

        soup = _list_page(rf, paginate_by=5)

        assert soup.find(class_="mvp-list-footer") is None

    def test_a_middle_page_links_to_its_neighbours(self, rf, cat):
        for number in range(6):
            _product(cat, f"Lamp {number}")

        soup = _list_page(rf, "?page=2&o=name_asc", paginate_by=2)

        footer = soup.find(class_="mvp-list-footer")
        assert footer.find("a", rel="prev")["href"] == "?page=1&o=name_asc"
        assert footer.find("a", rel="next")["href"] == "?page=3&o=name_asc"

    def test_the_first_page_has_no_link_back(self, rf, cat):
        for number in range(4):
            _product(cat, f"Lamp {number}")

        footer = _list_page(rf, paginate_by=2).find(class_="mvp-list-footer")

        assert footer.find("a", rel="prev") is None
        assert footer.find("a", rel="next") is not None

    def test_the_last_page_has_no_link_forward(self, rf, cat):
        for number in range(4):
            _product(cat, f"Lamp {number}")

        footer = _list_page(rf, "?page=2", paginate_by=2).find(class_="mvp-list-footer")

        assert footer.find("a", rel="next") is None

    def test_the_document_title_carries_the_page_number(self, rf, cat):
        for number in range(6):
            _product(cat, f"Lamp {number}")

        first = _list_page(rf, "?page=1", paginate_by=2).find("title").get_text()
        second = _list_page(rf, "?page=2", paginate_by=2).find("title").get_text()

        assert "2" in second
        assert first != second

    def test_the_document_title_has_no_page_number_for_one_page(self, rf, cat):
        _product(cat, "Lamp")

        title = _list_page(rf, paginate_by=5).find("title").get_text()

        assert not any(character.isdigit() for character in title)


LIST_PAGE_BLOCKS = [
    "page.actions",
    "page.toolbar",
    "page.search",
    "page.summary",
    "page.controls",
    "page.refinements",
    "page.results",
    "page.pagination",
]


class TestListPageBlocks:
    @pytest.mark.parametrize("block", LIST_PAGE_BLOCKS)
    def test_a_project_can_replace_one_part_of_the_page(self, rf, cat, block):
        for number in range(3):
            _product(cat, f"Lamp {number}")

        soup = _list_page(
            rf,
            "?q=lamp",
            template_name="tests/list_view_block_override.html",
            paginate_by=2,
            extra_context={"override": block},
        )

        assert soup.find(id="override") is not None

    def test_a_project_can_replace_the_empty_state(self, rf, db):
        soup = _list_page(
            rf,
            template_name="tests/list_view_block_override.html",
            extra_context={"override": "page.empty"},
        )

        assert soup.find(id="override") is not None
        assert soup.find(class_="mvp-list-empty") is None

    def test_replacing_nothing_leaves_the_page_as_packaged(self, rf, cat):
        _product(cat, "Lamp")

        soup = _list_page(rf, template_name="tests/list_view_block_override.html")

        assert soup.find(id="override") is None
        assert soup.find(class_="mvp-list-toolbar") is not None


class TestFilterDisplay:
    def _view(self, rf, filterset_class):
        from django_filters.views import FilterView

        view_cls = type(
            "StubDisplayListView",
            (MVPListViewMixin, FilterView),
            {"model": Product, "filterset_class": filterset_class},
        )
        view = view_cls()
        view.setup(rf.get("/products/"))
        return view, filterset_class({}, queryset=Product.objects.none())

    def _filterset_class(self):
        import django_filters

        class ProductFilterSet(django_filters.FilterSet):
            price = django_filters.RangeFilter()
            is_available = django_filters.BooleanFilter()
            status = django_filters.MultipleChoiceFilter(
                choices=Product._meta.get_field("status").flatchoices
            )

            class Meta:
                model = Product
                fields = ["name"]

        return ProductFilterSet

    def test_a_range_with_only_a_lower_bound_names_that_bound(self, rf, db):
        view, filterset = self._view(rf, self._filterset_class())

        display = view.get_filter_display(filterset, "price", slice(5, None))

        assert "5" in display

    def test_a_range_with_only_an_upper_bound_names_that_bound(self, rf, db):
        view, filterset = self._view(rf, self._filterset_class())

        display = view.get_filter_display(filterset, "price", slice(None, 20))

        assert "20" in display
        assert "None" not in display

    def test_a_boolean_is_not_shown_as_a_python_literal(self, rf, db):
        view, filterset = self._view(rf, self._filterset_class())

        yes = view.get_filter_display(filterset, "is_available", True)
        no = view.get_filter_display(filterset, "is_available", False)

        assert yes != no
        assert {yes, no}.isdisjoint({"True", "False"})

    def test_several_choices_show_each_choice_label(self, rf, db):
        view, filterset = self._view(rf, self._filterset_class())
        labels = dict(Product._meta.get_field("status").flatchoices)
        first, second = list(labels)[:2]

        display = view.get_filter_display(filterset, "status", [first, second])

        assert display == f"{labels[first]}, {labels[second]}"

    def test_a_filter_drawn_with_plain_split_inputs_reads_one_param_each(self, rf, db):
        import django_filters
        from django import forms

        class SplitWidget(forms.MultiWidget):
            def __init__(self):
                super().__init__([forms.TextInput, forms.TextInput])

            def decompress(self, value):
                return [None, None]

        class ProductFilterSet(django_filters.FilterSet):
            name = django_filters.CharFilter(widget=SplitWidget())

            class Meta:
                model = Product
                fields = ["name"]

        view, filterset = self._view(rf, ProductFilterSet)

        assert view.get_filter_params(filterset, "name") == ["name_0", "name_1"]
