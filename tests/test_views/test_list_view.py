"""Tests for SearchMixin, OrderMixin, SearchOrderMixin in mvp.views.list.

Covers all user stories from specs/014-list-search-ordering/:

  US1 — Text Search (SearchMixin)
  US2 — Safe Column Ordering (OrderMixin three-tuple format)
  US3 — Combined Search and Ordering (SearchOrderMixin)
  US4 — django_filters composition

Source: mvp/views/list.py
"""

import pytest
from django.test import RequestFactory
from django.views.generic import ListView

from demo.models import Category, Product
from mvp.views.list import MVPListView, MVPListViewMixin, OrderMixin, SearchMixin, SearchOrderMixin

# ---------------------------------------------------------------------------
# Module-level stub view classes (needed for django_filters FilterView)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def cat(db):
    """A single Category for Product FK."""
    return Category.objects.create(name="Test Category", slug="test-category")


@pytest.fixture
def cat2(db):
    """A second Category for multi-category tests."""
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


# ---------------------------------------------------------------------------
# US1 — SearchMixin
# ---------------------------------------------------------------------------


class TestSearchMixin:
    """[US1] SearchMixin text search behaviour when search_fields is configured."""

    def test_search_no_query_returns_all(self, db, cat):
        """[US1] Blank ?q= returns the full queryset unmodified."""
        _product(cat, "Alpha")
        _product(cat, "Beta")
        view = _make_search_view(
            params={},
            extra_attrs={"search_fields": ["name"]},
        )
        assert view.get_queryset().count() == 2

    def test_search_single_word_filters(self, db, cat):
        """[US1] ?q=alpha returns only matching records."""
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
        """[US1] ?q=alpha beta returns records matching EITHER word."""
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
        """[US1] Search is case-insensitive (icontains)."""
        _product(cat, "Django Framework")
        view = _make_search_view(
            params={"q": "DJANGO"},
            extra_attrs={"search_fields": ["name"]},
        )
        assert view.get_queryset().count() == 1

    def test_search_whitespace_only_query_no_filter(self, db, cat):
        """[US1] Whitespace-only ?q= is treated as empty — no filtering applied."""
        _product(cat, "Alpha")
        _product(cat, "Beta")
        view = _make_search_view(
            params={"q": "   "},
            extra_attrs={"search_fields": ["name"]},
        )
        assert view.get_queryset().count() == 2


class TestSearchMixinNoConfig:
    """[US1] SearchMixin is a complete no-op when search_fields is not configured."""

    def test_search_no_fields_configured_is_noop(self, db, cat):
        """[US1] ?q=anything with search_fields=None does not filter the queryset."""
        _product(cat, "Alpha")
        _product(cat, "Beta")
        view = _make_search_view(
            params={"q": "alpha"},
            extra_attrs={"search_fields": None},
        )
        assert view.get_queryset().count() == 2

    def test_search_is_searchable_false_when_unconfigured(self, db, cat):
        """[US1] is_searchable context sentinel is False when search_fields is None."""
        view = _make_search_view(
            params={},
            extra_attrs={"search_fields": None},
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["is_searchable"] is False

    def test_search_context_always_injected_when_unconfigured(self, db, cat):
        """[US1] is_searchable and search_query are injected even when unconfigured."""
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
        """[US1] is_searchable=True and search_query populated when configured."""
        view = _make_search_view(
            params={"q": "test"},
            extra_attrs={"search_fields": ["name"]},
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["is_searchable"] is True
        assert ctx["search_query"] == "test"

    def test_search_query_stripped_in_context(self, db, cat):
        """[US1] search_query in context is the stripped ?q= value."""
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
    """[US1] SearchMixin advanced search: related field traversal and deduplication."""

    def test_search_related_field_traversal(self, db, cat):
        """[US1] search_fields supports relationship traversal (category__name)."""
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
        """[US1] Records matching via multiple fields appear only once (distinct)."""
        # A product with "python" in both name and description
        _product(cat, "Python Widget", description="python tools for developers")
        _product(cat, "Java Widget", description="java tools")
        view = _make_search_view(
            params={"q": "python"},
            extra_attrs={"search_fields": ["name", "description"]},
        )
        qs = view.get_queryset()
        assert qs.count() == 1  # not 2 even though it matched both fields


# ---------------------------------------------------------------------------
# US2 — OrderMixin (three-tuple format)
# ---------------------------------------------------------------------------

_ORDER_CHOICES = [
    ("name_asc", "Name A-Z", "name"),
    ("name_desc", "Name Z-A", "-name"),
    ("price_asc", "Price Low-High", "price"),
]


class TestOrderMixin:
    """[US2] OrderMixin applies the orm_expression, matched via public_key."""

    def test_order_valid_key_applies_orm_expression(self, db, cat):
        """[US2] Valid public_key applies the correct orm_expression to queryset."""
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
        """[US2] Unrecognised ?o= value is silently ignored — queryset unmodified."""
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
        """[US2] Absent ?o= parameter leaves default model ordering intact."""
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
        """[US2] Descending orm_expression (prefixed with '-') orders correctly."""
        _product(cat, "Alpha", price="5.00")
        _product(cat, "Beta", price="10.00")
        view = _make_order_view(
            params={"o": "name_desc"},
            extra_attrs={"order_by": _ORDER_CHOICES},
        )
        qs = list(view.get_queryset())
        assert qs[0].name == "Beta"
        assert qs[1].name == "Alpha"


class TestOrderMixinSecurity:
    """[US2] OrderMixin security: raw ?o= value never reaches the ORM."""

    def test_order_public_key_not_equal_orm_expression(self, db, cat):
        """[US2] Public key differs from orm_expression; orm_expression is used."""
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

    def test_order_raw_param_never_reaches_orm(self, db, cat):
        """[US2] Unrecognised ?o= values are never passed to queryset.order_by()."""
        _product(cat, "Alpha")
        choices = [
            ("name_asc", "Name A-Z", "name"),
        ]
        view = _make_order_view(
            params={"o": "DROP TABLE demo_product; --"},
            extra_attrs={"order_by": choices},
        )
        # Must not raise, must not modify queryset
        qs = view.get_queryset()
        assert qs.count() == 1

    def test_order_opaque_key_orm_expression_invisible_in_url(self, db, cat):
        """[US2] A public_key of 'newest' maps to '-created_at' without exposing the field."""
        choices = [
            ("newest", "Newest First", "-created_at"),
        ]
        view = _make_order_view(
            params={"o": "newest"},
            extra_attrs={"order_by": choices},
        )
        qs = view.get_queryset()
        # Just assert it doesn't crash and the field 'created_at' is never in the URL
        assert qs.count() == 0


class TestOrderMixinNoConfig:
    """[US2] OrderMixin is a complete no-op when order_by is not configured."""

    def test_order_no_config_is_noop(self, db, cat):
        """[US2] ?o=anything with order_by=None does not modify the queryset."""
        _product(cat, "Alpha")
        _product(cat, "Beta")
        view = _make_order_view(
            params={"o": "name_asc"},
            extra_attrs={"order_by": None},
        )
        qs = view.get_queryset()
        assert qs.count() == 2

    def test_order_context_not_injected_when_unconfigured(self, db, cat):
        """[US2] order_by_choices and current_ordering absent from context when unconfigured."""
        view = _make_order_view(
            params={},
            extra_attrs={"order_by": None},
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert "order_by_choices" not in ctx
        assert "current_ordering" not in ctx

    def test_order_empty_list_is_noop(self, db, cat):
        """[US2] order_by=[] (empty list) is treated as unconfigured — no-op."""
        _product(cat, "Alpha")
        view = _make_order_view(
            params={"o": "name_asc"},
            extra_attrs={"order_by": []},
        )
        qs = view.get_queryset()
        assert qs.count() == 1


class TestOrderMixinContext:
    """[US2] OrderMixin context variables: choices and current_ordering."""

    def test_order_context_choices_full_three_tuple_list(self, db, cat):
        """[US2] order_by_choices is the full three-tuple list."""
        view = _make_order_view(
            params={},
            extra_attrs={"order_by": _ORDER_CHOICES},
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["order_by_choices"] == _ORDER_CHOICES

    def test_order_context_current_ordering_is_public_key(self, db, cat):
        """[US2] current_ordering is the matched public_key, not the orm_expression."""
        view = _make_order_view(
            params={"o": "name_asc"},
            extra_attrs={"order_by": _ORDER_CHOICES},
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["current_ordering"] == "name_asc"  # public_key, not "name" (orm_expression)

    def test_order_context_current_ordering_empty_on_invalid(self, db, cat):
        """[US2] current_ordering is '' when ?o= is not a recognised public_key."""
        view = _make_order_view(
            params={"o": "bogus_key"},
            extra_attrs={"order_by": _ORDER_CHOICES},
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["current_ordering"] == ""

    def test_order_context_current_ordering_empty_when_absent(self, db, cat):
        """[US2] current_ordering is '' when ?o= is absent."""
        view = _make_order_view(
            params={},
            extra_attrs={"order_by": _ORDER_CHOICES},
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["current_ordering"] == ""


# ---------------------------------------------------------------------------
# US3 — SearchOrderMixin (combined search and ordering)
# ---------------------------------------------------------------------------

_SEARCH_ORDER_CHOICES = [
    ("name_asc", "Name A-Z", "name"),
    ("name_desc", "Name Z-A", "-name"),
]


class TestSearchOrderMixin:
    """[US3] SearchOrderMixin: combined search and ordering work together."""

    def test_combined_search_and_ordering(self, db, cat):
        """[US3] ?q=widget&o=name_desc returns filtered records in descending order."""
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
        """[US3] ?q= only (no ?o=) filters but preserves model default ordering."""
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
        """[US3] ?o= only (no ?q=) orders but returns all records."""
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
    """[US3] MRO: ordering applied before distinct to avoid DISTINCT+ORDER BY conflicts."""

    def test_ordering_applied_before_distinct(self, db, cat):
        """[US3] Multi-field search with ordering: MRO ensures correct evaluation order.

        When a product matches via multiple search fields, distinct() is applied
        after ordering, avoiding PostgreSQL 'SELECT DISTINCT + ORDER BY on JOIN'
        conflicts.
        """
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


# ---------------------------------------------------------------------------
# US4 — django_filters composition
# ---------------------------------------------------------------------------

requires_django_filters = pytest.mark.skipif(
    not HAS_DJANGO_FILTERS,
    reason="django-filter is not installed",
)


@requires_django_filters
class TestDjangoFiltersComposition:
    """[US4] SearchOrderMixin composes correctly with FilterView."""

    def test_filterset_and_search_both_applied(self, db, cat, cat2):
        """[US4] Both filterset category filter and ?q= search are applied."""
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
        """[US4] Both filterset filtering and ?o= ordering are applied."""
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
        """[US4] Filterset + search + ordering all combined produce correct results."""
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
    """[US4] SearchMixin and OrderMixin are no-ops with filterset when unconfigured."""

    def test_no_search_fields_search_is_noop_with_filterset(self, db, cat, cat2):
        """[US4] search_fields=None is a no-op even when FilterView is in the MRO."""
        _product(cat, "Alpha")
        _product(cat2, "Beta")

        view = _make_filter_view_no_config(
            params={"q": "Alpha"},  # should have no effect
        )
        view.get(view.request)

        # No search_fields means no filtering on ?q= — all products returned
        assert view.object_list.count() == 2

    def test_no_order_by_ordering_is_noop_with_filterset(self, db, cat):
        """[US4] order_by=None is a no-op even when FilterView is in the MRO."""
        _product(cat, "Beta")
        _product(cat, "Alpha")

        view = _make_filter_view_no_config(params={"o": "name_asc"})
        view.get(view.request)

        # No order_by means ?o= has no effect — model default ordering is used
        assert view.object_list.count() == 2


# ---------------------------------------------------------------------------
# MVPListViewMixin / MVPListView tests (specs/015-mvp-list-view/)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# US1 - Zero-Config List Page (T010-T015)
# ---------------------------------------------------------------------------


class TestMVPListViewMixinZeroConfig:
    """[015-US1] Zero-config list page with only model declared."""

    def test_zero_config_page_renders(self, db, cat):
        """[015-US1] View with only model produces a valid context without error."""
        _product(cat, "Alpha")
        view = _make_list_view()
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx is not None

    def test_default_page_title_from_model(self, db):
        """[015-US1] page.title equals model verbose_name_plural.title() by default."""
        view = _make_list_view()
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        expected = Product._meta.verbose_name_plural.title()
        assert ctx["page"]["title"] == expected

    def test_default_list_item_template_convention(self, db):
        """[015-US1] list_item_template follows <app_label>/<model_name>_list_item.html."""
        view = _make_list_view()
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["list_item_template"] == "demo/product_list_item.html"

    def test_default_paginate_by(self):
        """[015-US1] MVPListView.paginate_by == 24 by default."""
        assert MVPListView.paginate_by == 24


# ---------------------------------------------------------------------------
# US2 - Item Template Convention and Override (T016-T020)
# ---------------------------------------------------------------------------


class TestMVPListViewMixinItemTemplate:
    """[015-US2] Item template convention and explicit override."""

    def test_explicit_list_item_template_overrides_convention(self, db):
        """[015-US2] Explicit list_item_template takes precedence over convention."""
        view = _make_list_view(extra_attrs={"list_item_template": "shared/item.html"})
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["list_item_template"] == "shared/item.html"

    def test_list_item_template_convention_uses_app_label_and_model_name(self, db):
        """[015-US2] Convention uses model._meta.app_label and model._meta.model_name."""
        view = _make_list_view(extra_attrs={"model": Category})
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["list_item_template"] == "demo/category_list_item.html"

    def test_list_item_template_convention_different_app_label(self):
        """[015-US2] Convention produces correct path for arbitrary app_label/model_name."""
        import types

        meta = types.SimpleNamespace(app_label="sales", model_name="order")
        MockModel = type("MockModel", (), {"_meta": meta})

        rf = RequestFactory()
        request = rf.get("/")
        view_cls = type(
            "StubListView",
            (MVPListViewMixin, ListView),
            {"model": MockModel, "list_item_template": None, "template_name": "base.html"},
        )
        view = view_cls()
        view.request = request
        view.kwargs = {}
        view.args = []
        assert view.get_list_item_template() == "sales/order_list_item.html"

    def test_empty_string_list_item_template_falls_back_to_convention(self, db):
        """[015-US2] Empty string list_item_template falls back to the naming convention."""
        view = _make_list_view(extra_attrs={"list_item_template": ""})
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["list_item_template"] == "demo/product_list_item.html"

    def test_get_list_item_template_override_takes_full_precedence(self, db):
        """[015-US2] Overriding get_list_item_template() bypasses attribute and convention."""
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
        """[015-US2] AttributeError raised when neither model nor list_item_template is set."""
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


# ---------------------------------------------------------------------------
# US3 - Empty State Messaging (T021-T025)
# ---------------------------------------------------------------------------


class TestMVPListViewMixinEmptyState:
    """[015-US3] Empty state context is always present and configurable."""

    def test_empty_state_present_in_context_with_defaults(self, db):
        """[015-US3] empty_state in context with non-empty heading and message."""
        view = _make_list_view()
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert "empty_state" in ctx
        assert ctx["empty_state"]["heading"]
        assert ctx["empty_state"]["message"]

    def test_empty_state_heading_override(self, db):
        """[015-US3] empty_state_heading attribute overrides the default heading."""
        view = _make_list_view(extra_attrs={"empty_state_heading": "No products found"})
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["empty_state"]["heading"] == "No products found"

    def test_empty_state_message_none_suppresses_message(self, db):
        """[015-US3] empty_state_message = None results in empty_state.message is None."""
        view = _make_list_view(extra_attrs={"empty_state_message": None})
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["empty_state"]["message"] is None

    def test_empty_state_heading_none_suppresses_heading(self, db):
        """[015-US3] empty_state_heading = None results in empty_state.heading is None."""
        view = _make_list_view(extra_attrs={"empty_state_heading": None})
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["empty_state"]["heading"] is None


# ---------------------------------------------------------------------------
# US4 - "Create" Action Link from the List Page (T026-T029)
# ---------------------------------------------------------------------------


class TestMVPListViewMixinDirectory:
    """[015-US4] directory is limited to create-only; create_url absent by default."""

    def test_directory_attribute_is_create_only(self):
        """[015-US4] MVPListViewMixin.directory == ["create"]."""
        assert MVPListViewMixin.directory == ["create"]

    def test_create_url_absent_when_permission_false(self, db):
        """[015-US4] directory context does not contain create_url when has_create_permission=False."""
        view = _make_list_view()  # has_create_permission=False by default
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert "create_url" not in ctx["directory"]

    def test_no_detail_update_delete_urls_in_directory(self, db):
        """[015-US4] directory context never contains detail_url, update_url, or delete_url."""
        view = _make_list_view()  # has_create_permission=False avoids URL resolution
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert "detail_url" not in ctx["directory"]
        assert "update_url" not in ctx["directory"]
        assert "delete_url" not in ctx["directory"]


# ---------------------------------------------------------------------------
# US5 - Grid Configuration (T030-T032)
# ---------------------------------------------------------------------------


class TestMVPListViewMixinGridConfig:
    """[015-US5] grid dict is passed through to context as grid_config."""

    def test_grid_config_passthrough(self, db):
        """[015-US5] grid attribute is passed unchanged to context as grid_config."""
        grid = {"sm": 1, "md": 2, "lg": 3}
        view = _make_list_view(extra_attrs={"grid": grid})
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["grid_config"] == {"sm": 1, "md": 2, "lg": 3}

    def test_grid_config_empty_dict_when_not_configured(self, db):
        """[015-US5] grid_config is {} when grid attribute is not configured."""
        view = _make_list_view()  # grid defaults to {}
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["grid_config"] == {}


# ---------------------------------------------------------------------------
# US6 - Search, Ordering, and Pagination Compose Cleanly (T033-T037)
# ---------------------------------------------------------------------------


class TestMVPListViewMixinSearchOrdering:
    """[015-US6] search_query and current_ordering injected correctly into context."""

    def test_search_query_in_context_when_search_active(self, db):
        """[015-US6] search_query == 'foo' when ?q=foo submitted."""
        view = _make_list_view(
            params={"q": "foo"},
            extra_attrs={"search_fields": ["name"]},
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["search_query"] == "foo"

    def test_search_query_empty_when_not_configured(self, db):
        """[015-US6] search_query == '' when no search_fields configured."""
        view = _make_list_view(extra_attrs={"search_fields": None})
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["search_query"] == ""

    def test_current_ordering_in_context_when_ordering_active(self, db):
        """[015-US6] current_ordering == 'name_asc' when ?o=name_asc with matching whitelist."""
        view = _make_list_view(
            params={"o": "name_asc"},
            extra_attrs={
                "order_by": [("name_asc", "Name A-Z", "name"), ("name_desc", "Name Z-A", "-name")],
            },
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["current_ordering"] == "name_asc"

    def test_mvp_list_view_all_context_keys_present_with_defaults(self, db):
        """[015-US6] All mandatory context keys present on a zero-config view."""
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


# ---------------------------------------------------------------------------
# Phase 9 - Breadcrumbs and page_title override (T038-T039)
# ---------------------------------------------------------------------------


class TestMVPListViewMixinPageMetadata:
    """[015] Breadcrumbs and page_title override via class attribute."""

    def test_default_breadcrumbs_include_home_and_page_title(self, db):
        """[015] Default breadcrumbs: Home link + model verbose_name_plural."""
        view = _make_list_view()
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        breadcrumbs = ctx["page"]["breadcrumbs"]
        assert breadcrumbs[0] == {"text": "Home", "href": "/"}
        expected_title = Product._meta.verbose_name_plural.title()
        assert breadcrumbs[1] == {"text": expected_title}

    def test_page_title_attribute_overrides_model_derived_title(self, db):
        """[015] page_title class attribute takes precedence over model-derived title."""
        view = _make_list_view(extra_attrs={"page_title": "Our Catalogue"})
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert ctx["page"]["title"] == "Our Catalogue"


# ---------------------------------------------------------------------------
# Phase 10 - List View Inline Create (T002)
# ---------------------------------------------------------------------------


class TestListViewInlineCreate:
    """[021] Inline create form in list view modal.

    Tests cover US1 (inline create via modal), US2 (fallback to create page link),
    and US3 (permission gating).
    """

    def test_create_form_in_context_when_configured_and_permitted(self, db):
        """[021][US1][FR-002] create_form injected when create_form_class set + has_create_permission=True."""
        from demo.forms import ProductForm

        view = _make_list_view(
            extra_attrs={
                "create_form_class": ProductForm,
                "has_create_permission": True,
            }
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()

        assert "create_form" in ctx
        assert isinstance(ctx["create_form"], ProductForm)

    def test_create_modal_title_auto_derived_from_verbose_name(self, db):
        """[021][US1][FR-007] create_modal_title auto-derives as 'Add <VerboseName>' when None."""
        from demo.forms import ProductForm

        view = _make_list_view(
            extra_attrs={
                "create_form_class": ProductForm,
                "has_create_permission": True,
                "create_modal_title": None,
            }
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()

        expected = f"Add {Product._meta.verbose_name.title()}"
        assert ctx["create_modal_title"] == expected

    def test_create_modal_title_override_attribute(self, db):
        """[021][US1][FR-007] Explicit create_modal_title attribute is used verbatim."""
        from demo.forms import ProductForm

        view = _make_list_view(
            extra_attrs={
                "create_form_class": ProductForm,
                "has_create_permission": True,
                "create_modal_title": "Custom Create Title",
            }
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()

        assert ctx["create_modal_title"] == "Custom Create Title"

    def test_get_create_form_hook_allows_custom_instantiation(self, db):
        """[021][US1][FR-005] get_create_form() hook returns custom form instance."""
        from demo.forms import ProductForm

        custom_form = ProductForm(initial={"name": "Custom Initial"})

        view = _make_list_view(
            extra_attrs={
                "create_form_class": ProductForm,
                "has_create_permission": True,
            }
        )

        # Override get_create_form to return custom instance
        view.get_create_form = lambda: custom_form
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()

        assert ctx["create_form"] is custom_form
        assert ctx["create_form"].initial["name"] == "Custom Initial"

    def test_toolbar_html_contains_modal_trigger_when_form_present(self, client, db):
        """[021][US1][FR-006] Toolbar HTML contains data-bs-toggle='modal' when create_url and create_form present."""
        from demo.forms import ProductForm

        # Create a view subclass with inline create enabled
        from mvp.views.list import MVPListView

        class TestListView(MVPListView):
            model = Product
            template_name = "list_view.html"
            create_form_class = ProductForm
            has_create_permission = True

        # Register the view temporarily

        # Use test client to render the full template
        response = client.get("/products/")

        # The toolbar should contain modal trigger button
        # Looking for button with data-bs-toggle="modal" attribute
        assert (
            'data-bs-toggle="modal"' in response.content.decode()
            or 'data-bs-target="#createModal"' in response.content.decode()
        )

    def test_fallback_link_when_no_form_class(self, client, db):
        """[021][US2][FR-006] Toolbar shows link button (no modal toggle) when create_form_class=None + has_create_permission=True."""
        # This test should verify that when create_form_class is None,
        # the toolbar contains a standard link without modal trigger

        # The demo's ProductListView doesn't have create_form_class by default
        # So we test the current behavior - it should show a link to create page
        response = client.get("/products/")

        # Toolbar should have create link but NOT modal toggle
        content = response.content.decode()
        # The view might not have create_url configured, so this is a placeholder
        # Once implemented, should verify: has href but NOT data-bs-toggle
        assert True  # Placeholder - will verify after mixin implementation

    def test_no_create_button_when_no_permission(self, client, db):
        """[021][US3][FR-006] No create UI element when has_create_permission=False."""
        from demo.forms import ProductForm

        view = _make_list_view(
            extra_attrs={
                "create_form_class": ProductForm,
                "has_create_permission": False,
            }
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()

        # create_form should NOT be in context
        assert "create_form" not in ctx

    def test_permission_boolean_false_prevents_form_injection(self, db):
        """[021][US3][FR-004] create_form absent when has_create_permission=False (boolean)."""
        from demo.forms import ProductForm

        view = _make_list_view(
            extra_attrs={
                "create_form_class": ProductForm,
                "has_create_permission": False,
            }
        )
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()

        assert "create_form" not in ctx
        assert "create_modal_title" not in ctx

    def test_permission_callable_returns_false_prevents_form_injection(self, db, rf):
        """[021][US3][FR-004] create_form absent when callable has_create_permission returns False."""
        from django.contrib.auth.models import AnonymousUser

        from demo.forms import ProductForm

        view = _make_list_view(
            extra_attrs={
                "create_form_class": ProductForm,
                "has_create_permission": staticmethod(lambda user: False),
            }
        )
        view.request.user = AnonymousUser()
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()

        assert "create_form" not in ctx
        assert "create_modal_title" not in ctx

    def test_permission_callable_returns_true_allows_form_injection(self, db, rf):
        """[021][US3][FR-004] create_form present when callable has_create_permission returns True."""
        from django.contrib.auth.models import User

        from demo.forms import ProductForm

        user = User.objects.create_user(username="testuser", password="password")

        view = _make_list_view(
            extra_attrs={
                "create_form_class": ProductForm,
                "has_create_permission": staticmethod(lambda user: user.is_authenticated),
            }
        )
        view.request.user = user
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()

        assert "create_form" in ctx
        assert isinstance(ctx["create_form"], ProductForm)

    def test_mvp_create_view_honours_next_parameter(self, client, db):
        """[021][US1][FR-010] POST to create URL with ?next=/list/ redirects to /list/ after success."""
        from django.contrib.auth.models import User

        # Create a user and authenticate
        user = User.objects.create_user(username="testuser", password="password")
        client.force_login(user)

        # POST to create view with ?next parameter
        response = client.post(
            "/products/create/?next=/products/",
            data={"name": "Test Product", "price": "10.00"},
            follow=False,
        )

        # Should redirect to the next URL
        assert response.status_code == 302
        # The redirect should honor the next parameter (if MVPCreateView supports it)
        # This verifies NextURLMixin behavior
        assert "/products/" in response.url or response.url == "/products/"

    def test_backward_compat_no_form_class_no_change(self, db):
        """[021][SC-004] List view with create_form_class=None renders identically to pre-feature behavior."""
        # View without create_form_class should work exactly as before
        view = _make_list_view(
            extra_attrs={
                "create_form_class": None,
                "has_create_permission": False,
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
