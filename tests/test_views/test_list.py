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

try:
    from django_filters.views import FilterView as _FilterView

    HAS_DJANGO_FILTERS = True
except ImportError:  # pragma: no cover
    HAS_DJANGO_FILTERS = False

    class _FilterView(ListView):  # type: ignore[no-redef]
        """Fallback stub when django-filter is not installed."""

        pass


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
    return Category.objects.create(name="Test Category", slug="test-category")


@pytest.fixture
def cat2(db):
    return Category.objects.create(name="Other Category", slug="other-category")


def _product(cat, name, description="", slug=None, price="9.99", **kwargs):
    """Helper to create a Product with minimal required fields."""
    if slug is None:
        slug = name.lower().replace(" ", "-").replace("/", "-")
    # sku must be unique; derive from slug to avoid constraint violations
    sku = kwargs.pop("sku", slug[:50])
    return Product.objects.create(
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
        other_cat = Category.objects.create(name="Other Cat", slug="other-cat")
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
        assert breadcrumbs[0] == {"text": "Home", "href": "/"}
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

        expected = f"Add {Product._meta.verbose_name.title()}"
        assert ctx["create_modal_title"] == expected

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

    def test_permission_callable_returns_true_allows_form_injection(self, db, rf):
        from django.contrib.auth.models import User

        from demo.forms import ProductForm

        user = User.objects.create_user(username="testuser", password="password")

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
        empty_state = soup.find("h3").parent
        assert empty_state.find("p") is not None
        assert soup.find("a", href="/products/create/") is not None

    def test_no_message_and_no_button_when_not_permitted(self, rf, db):
        html = _render_empty_list_view(rf, show_create_action=False)
        soup = _beautiful_soup()(html, "html.parser")
        assert soup.find("a", href="/products/create/") is None
        empty_state = soup.find("h3").parent
        assert empty_state.find("p") is None, "no empty paragraph is rendered"


def _render_search_sort_list_view(rf):
    """Render a full, empty MVPListView with search + ordering but no FilterSet."""
    view_cls = type(
        "StubSearchSortListView",
        (MVPListView,),
        {
            "model": Product,
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
    def test_form_referenced_by_search_and_sort_exists_in_the_page(self, rf, db):
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

    def test_no_duplicate_filter_form_when_filterset_is_configured(self, rf, db):
        from django_filters.views import FilterView

        view_cls = type(
            "StubFilteredListView",
            (MVPListViewMixin, FilterView),
            {
                "model": Product,
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
            "StubActionsListView", (MVPListView,), {"model": Product, **attrs}
        )
        view = view_cls()
        view.setup(rf.get("/"))
        response = view.get(view.request)
        response.render()
        return response.content.decode()

    def test_search_follows_search_fields(self, rf, db):
        assert 'name="q"' in self._render(rf, search_fields=["name"])
        assert 'name="q"' not in self._render(rf, search_fields=None)

    def test_sort_follows_order_by(self, rf, db):
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

    def test_filter_follows_the_filterset(self, rf, db):
        from django_filters.views import FilterView

        view_cls = type(
            "StubFilteredActionsView",
            (MVPListViewMixin, FilterView),
            {"model": Product, "filterset_fields": ["category"]},
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
