"""Tests for the list views in mvp.views.list.

Source: mvp/views/list.py
"""

import django_filters
import pytest
from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory
from django.urls import reverse
from django.views.generic import ListView

from demo.models import Category, Product
from mvp.filters import SearchFilter, SortFilter
from mvp.fixtures import _beautiful_soup
from mvp.views.list import (
    MVPListView,
    MVPListViewMixin,
)
from tests.factories import CategoryFactory, ProductFactory

CARD = "cards/product_card.html"


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


class SearchSortFilter(django_filters.FilterSet):
    q = SearchFilter(fields=["name"])
    o = SortFilter(
        options=[
            ("name_asc", "Name A-Z", "name"),
            ("name_desc", "Name Z-A", "-name"),
        ]
    )

    class Meta:
        model = Product
        fields = ["category"]


class CategoryOnlyFilter(django_filters.FilterSet):
    class Meta:
        model = Product
        fields = ["category"]


def _filtered_object_list(filterset_class, params):
    view_cls = type(
        "StubFilteredListView",
        (MVPListView,),
        {
            "model": Product,
            "filterset_class": filterset_class,
            "render_to_response": lambda self, context, **kwargs: context,
        },
    )
    view = view_cls()
    view.setup(RequestFactory().get("/", data=params))
    return view.get(view.request)["object_list"]


class TestDjangoFiltersComposition:
    def test_filterset_and_search_both_applied(self, db, cat, cat2):
        _product(cat, "Python Widget")
        _product(cat, "Java Widget")
        _product(cat2, "Python Framework")

        object_list = _filtered_object_list(
            SearchSortFilter, {"q": "Python", "category": str(cat.pk)}
        )

        names = list(object_list.values_list("name", flat=True))
        assert "Python Widget" in names
        assert "Java Widget" not in names
        assert "Python Framework" not in names

    def test_filterset_and_ordering_both_applied(self, db, cat):
        _product(cat, "Beta Product")
        _product(cat, "Alpha Product")

        qs = list(
            _filtered_object_list(
                SearchSortFilter, {"category": str(cat.pk), "o": "name_asc"}
            )
        )

        assert len(qs) == 2
        assert qs[0].name == "Alpha Product"
        assert qs[1].name == "Beta Product"

    def test_filterset_search_ordering_all_combined(self, db, cat, cat2):
        _product(cat, "Beta Widget")
        _product(cat, "Alpha Widget")
        _product(cat2, "Widget Other Category")

        qs = list(
            _filtered_object_list(
                SearchSortFilter,
                {"category": str(cat.pk), "q": "Widget", "o": "name_asc"},
            )
        )

        assert len(qs) == 2
        assert qs[0].name == "Alpha Widget"
        assert qs[1].name == "Beta Widget"


class TestDjangoFiltersNoOpCases:
    def test_a_filterset_without_a_search_ignores_q(self, db, cat, cat2):
        _product(cat, "Alpha")
        _product(cat2, "Beta")

        object_list = _filtered_object_list(CategoryOnlyFilter, {"q": "Alpha"})

        assert object_list.count() == 2

    def test_a_filterset_without_a_sort_ignores_o(self, db, cat):
        _product(cat, "Beta")
        _product(cat, "Alpha")
        default = list(Product.objects.all())

        object_list = _filtered_object_list(CategoryOnlyFilter, {"o": "name_asc"})

        assert list(object_list) == default


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


class TestMVPListViewMixinContextKeys:
    def test_mvp_list_view_all_context_keys_present_with_defaults(self, db):
        view = _make_list_view()
        view.object_list = view.get_queryset()
        ctx = view.get_context_data()
        assert "list_item_template" in ctx
        assert "empty_state" in ctx
        assert "grid_config" in ctx
        assert "directory" in ctx
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


class TestFilterFormFollowsTheFilterset:
    def test_no_filter_form_when_the_view_has_no_filterset(self, rf, db):
        view_cls = type("StubPlainListView", (MVPListView,), {"model": Product})
        view = view_cls()
        view.setup(rf.get("/"))
        response = view.get(view.request)
        response.render()
        soup = _beautiful_soup()(response.content.decode(), "html.parser")

        assert soup.find(id="filterForm") is None

    def test_no_duplicate_filter_form_when_filterset_is_configured(self, rf, cat):
        _product(cat, "Lamp")

        view_cls = type(
            "StubFilteredListView",
            (MVPListView,),
            {
                "model": Product,
                "list_item_template": CARD,
                "filterset_class": SearchSortFilter,
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

    def test_search_follows_the_filterset(self, rf, cat):
        _product(cat, "Lamp")
        assert 'name="q"' in self._render(rf, filterset_class=SearchSortFilter)
        assert 'name="q"' not in self._render(rf, filterset_class=CategoryOnlyFilter)

    def test_sort_follows_the_filterset(self, rf, cat):
        _product(cat, "Lamp")
        assert 'name="o"' in self._render(rf, filterset_class=SearchSortFilter)
        assert 'name="o"' not in self._render(rf, filterset_class=CategoryOnlyFilter)

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
        _product(cat, "Lamp")

        filtered = _beautiful_soup()(
            self._render(rf, filterset_fields=["category"]), "html.parser"
        )

        assert filtered.find(id="filters") is not None
        unfiltered = _beautiful_soup()(self._render(rf), "html.parser")
        assert unfiltered.find(id="filters") is None

    def test_a_bare_list_view_draws_no_controls_at_all(self, rf, db):
        html = self._render(rf)
        soup = _beautiful_soup()(html, "html.parser")

        assert 'name="q"' not in html
        assert 'name="o"' not in html
        assert soup.find(id="filters") is None
        assert soup.find(id="filterForm") is None


class RefinedProductFilter(django_filters.FilterSet):
    q = SearchFilter(fields=["name"])
    price = django_filters.RangeFilter()
    stock = django_filters.NumberFilter()
    categories = django_filters.ModelMultipleChoiceFilter(
        field_name="category", queryset=Category.objects.all()
    )
    o = SortFilter(options=[("name_asc", "Name (A-Z)", "name")])

    class Meta:
        model = Product
        fields = ["name", "status", "category"]


def _refinement_context(rf, query="", **attrs):
    """Return the context of a filtered product list requested with ``query``."""
    view_cls = type(
        "StubRefinedListView",
        (MVPListView,),
        {
            "model": Product,
            "filterset_class": RefinedProductFilter,
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
        assert search["name"] == "q"
        assert search["value"] == "lamp"
        assert search["remove_url"] == "/products/?o=name_asc"

    def test_a_search_is_labelled_by_its_filter(self, rf, db):
        class LabelledSearch(django_filters.FilterSet):
            q = SearchFilter(fields=["name"], label="Find a product")

            class Meta:
                model = Product
                fields: list[str] = []

        context = _refinement_context(rf, "?q=lamp", filterset_class=LabelledSearch)

        [search] = context["refinements"]
        assert search["label"] == "Find a product"

    def test_a_blank_search_is_not_a_refinement(self, rf, db):
        context = _refinement_context(rf, "?q=++")

        assert context["refinements"] == []

    def test_q_is_not_a_refinement_without_a_search_filter(self, rf, db):
        context = _refinement_context(rf, "?q=lamp", filterset_class=CategoryOnlyFilter)

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

    def test_an_empty_multiple_choice_filter_is_not_applied(self, rf, db):
        context = _refinement_context(rf, "?status=draft")

        assert [item["name"] for item in context["refinements"]] == ["status"]
        assert context["applied_filter_count"] == 1

    def test_a_chosen_multiple_choice_filter_is_applied(self, rf, cat):
        context = _refinement_context(rf, f"?categories={cat.pk}")

        assert [item["name"] for item in context["refinements"]] == ["categories"]

    def test_a_zero_number_filter_is_applied(self, rf, db):
        context = _refinement_context(rf, "?stock=0")

        assert [item["name"] for item in context["refinements"]] == ["stock"]

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
        context = _refinement_context(rf, "?price_min=5&price_max=20&o=name_asc")

        assert context["clear_filters_url"] == "/products/?o=name_asc"


class TestTheSortIsNeverAFilter:
    def test_a_search_a_sort_and_two_filters_refine_by_all_but_the_sort(self, rf, cat):
        context = _refinement_context(
            rf, f"?q=lamp&o=name_asc&status=draft&category={cat.pk}"
        )

        names = {item["name"] for item in context["refinements"]}
        assert names == {"q", "status", "category"}
        assert context["applied_filter_count"] == 3
        assert "o" not in context["applied_filters"]

    def test_clear_all_keeps_the_sort(self, rf, cat):
        context = _refinement_context(
            rf, f"?q=lamp&o=name_asc&status=draft&category={cat.pk}"
        )

        assert context["clear_refinements_url"] == "/products/?o=name_asc"

    def test_clearing_the_filters_keeps_the_sort(self, rf, db):
        context = _refinement_context(rf, "?q=lamp&status=draft&o=name_asc")

        assert context["clear_filters_url"] == "/products/?o=name_asc"

    def test_the_chosen_sort_is_named_in_the_context(self, rf, db):
        context = _refinement_context(rf, "?o=name_asc")

        assert context["sort_label"] == "Name (A-Z)"

    @pytest.mark.parametrize("query", ["", "?o=bogus"])
    def test_no_sort_label_when_no_option_is_chosen(self, rf, db, query):
        context = _refinement_context(rf, query)

        assert context["sort_label"] == ""

    def test_search_query_and_is_searchable_leave_the_context(self, rf, db):
        context = _refinement_context(rf, "?q=lamp")

        assert "search_query" not in context
        assert "is_searchable" not in context


class TestListResultCount:
    def _context(self, rf, query="", **attrs):
        view_cls = type(
            "StubCountedListView",
            (MVPListView,),
            {
                "model": Product,
                "filterset_class": ListPageFilter,
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


class ListPageFilter(django_filters.FilterSet):
    q = SearchFilter(fields=["name"])
    o = SortFilter(options=[("name_asc", "Name (A-Z)", "name")])

    class Meta:
        model = Product
        fields: list[str] = []


class FilteredListPageFilter(ListPageFilter):
    class Meta:
        model = Product
        fields = ["name", "status"]


def _list_page(rf, query="", **attrs):
    """Render a product list page requested with ``query`` and return its soup."""
    view_cls = type(
        "StubRenderedListView",
        (MVPListView,),
        {
            "model": Product,
            "list_item_template": CARD,
            "filterset_class": ListPageFilter,
            **attrs,
        },
    )
    view = view_cls()
    view.setup(rf.get(f"/products/{query}"))
    response = view.get(view.request)
    response.render()
    return _beautiful_soup()(response.content.decode(), "html.parser")


def _filtered_list_page(rf, query="", **attrs):
    return _list_page(rf, query, filterset_class=FilteredListPageFilter, **attrs)


class TestListPageToolbar:
    def test_no_toolbar_when_there_are_no_records_and_nothing_is_applied(self, rf, db):
        soup = _list_page(rf)

        assert soup.find(class_="mvp-list-toolbar") is None

    def test_toolbar_stays_when_a_search_matches_nothing(self, rf, cat):
        _product(cat, "Lamp")

        soup = _list_page(rf, "?q=chair", toolbar_filters=["q"])

        assert soup.find(class_="mvp-list-toolbar").find(attrs={"name": "q"})

    def test_add_action_is_in_the_toolbar_and_not_the_title_row(self, rf, cat):
        _product(cat, "Lamp")

        soup = _list_page(rf, show_create_action=True)

        create = soup.find_all("a", href="/products/create/")
        assert len(create) == 1
        assert create[0].find_parent(class_="mvp-list-toolbar") is not None
        assert create[0].find_parent(class_="page-title") is None

    def test_the_create_dialog_is_drawn_with_the_add_action(self, rf, cat):
        from demo.forms import ProductForm

        _product(cat, "Lamp")

        soup = _list_page(rf, show_create_action=True, create_form_class=ProductForm)

        assert len(soup.find_all(id="createModal")) == 1
        assert soup.find(id="createModal").find_parent(class_="mvp-list-toolbar")

    def test_the_create_form_is_not_nested_in_another_form(self, rf, cat):
        from demo.forms import ProductForm

        _product(cat, "Lamp")

        soup = _filtered_list_page(
            rf, show_create_action=True, create_form_class=ProductForm
        )

        assert soup.find("form", id="filterForm") is not None
        assert soup.find("form", id="createForm").find_parent("form") is None
        assert soup.find("form", id="filterForm").find_parent("form") is None

    def test_page_actions_is_in_the_toolbar_and_holds_the_add_action(
        self, rf, cat
    ):
        _product(cat, "Lamp")

        soup = _list_page(
            rf,
            template_name="tests/list_view_block_override.html",
            extra_context={"override": "page.actions"},
            show_create_action=True,
        )

        override = soup.find(id="override")
        assert override.find_parent(class_="mvp-list-toolbar") is not None
        assert override.find_parent(class_="page-title") is None
        assert soup.find("a", href="/products/create/") is None

    def test_a_page_can_keep_the_add_action_and_put_its_own_after_it(
        self, rf, cat
    ):
        _product(cat, "Lamp")

        soup = _list_page(
            rf,
            template_name="tests/list_view_action_after_add.html",
            show_create_action=True,
        )

        toolbar = soup.find(class_="mvp-list-toolbar")
        links = [a.get("id") or a["href"] for a in toolbar.find_all("a")]
        assert links[-2:] == ["/products/create/", "after-add"]

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


class TestListPageOneToolbar:
    def test_the_panels_fields_join_the_one_filter_form_by_attribute(self, rf, cat):
        _product(cat, "Lamp")

        soup = _filtered_list_page(rf, toolbar_filters=["q", "o"])

        forms = soup.find_all(id="filterForm")
        assert len(forms) == 1
        assert forms[0].name == "form"
        panel = soup.find(id="filters")
        assert panel.find_parent("form") is None
        inputs = panel.find("aside").find_all(["input", "select"])
        assert {el["name"] for el in inputs} == {"name", "status"}
        assert all(el["form"] == "filterForm" for el in inputs)

    def test_the_filter_form_sits_in_the_toolbar(self, rf, cat):
        _product(cat, "Lamp")

        soup = _filtered_list_page(rf)

        assert soup.find(id="filterForm").find_parent(class_="mvp-list-toolbar")

    def test_the_create_dialog_is_not_inside_the_filter_form(self, rf, cat):
        from demo.forms import ProductForm

        _product(cat, "Lamp")

        soup = _filtered_list_page(
            rf, show_create_action=True, create_form_class=ProductForm
        )

        assert soup.find(id="createModal").find_parent(id="filterForm") is None

    def test_a_page_without_a_filterset_has_a_toolbar_with_add_and_no_form(
        self, rf, cat
    ):
        _product(cat, "Lamp")

        soup = _list_page(rf, filterset_class=None, show_create_action=True)

        toolbar = soup.find(class_="mvp-list-toolbar")
        assert toolbar.find("a", href="/products/create/") is not None
        assert soup.find(id="filterForm") is None

    def test_the_count_is_drawn_once(self, rf, cat):
        _product(cat, "Lamp")

        for soup in [_list_page(rf), _list_page(rf, filterset_class=None)]:
            assert len(soup.find_all(class_="mvp-list-summary")) == 1


class TestListPageCountRow:
    def _position(self, soup, element):
        return next(i for i, tag in enumerate(soup.find_all(True)) if tag is element)

    def _row(self, soup):
        summary = soup.find(class_="mvp-list-summary")
        return summary, summary.parent

    def test_the_count_leads_the_row_of_refinements(self, rf, cat):
        _product(cat, "Lamp")

        soup = _filtered_list_page(rf, "?q=lamp&o=name_asc", toolbar_filters=["q"])

        summary, row = self._row(soup)
        chips = soup.find(class_="mvp-list-refinements")
        assert chips.parent is row
        assert self._position(soup, summary) < self._position(soup, chips)

    def test_the_sort_in_use_is_named_after_the_count(self, rf, cat):
        _product(cat, "Lamp")

        soup = _filtered_list_page(rf, "?o=name_asc")

        summary, row = self._row(soup)
        [sort] = [p for p in row.find_all("p") if "Name (A-Z)" in p.get_text()]
        assert self._position(soup, summary) < self._position(soup, sort)

    def test_no_sort_is_named_when_none_is_chosen(self, rf, cat):
        _product(cat, "Lamp")

        soup = _filtered_list_page(rf)

        _summary, row = self._row(soup)
        assert "Name (A-Z)" not in row.get_text()

    def test_the_row_sits_above_the_results(self, rf, cat):
        product = _product(cat, "Lamp")

        soup = _filtered_list_page(rf, "?q=lamp")

        _summary, row = self._row(soup)
        result = soup.find("a", href=reverse("product-delete", kwargs={"pk": product.pk}))
        assert result.find_parent(class_="mvp-list-status") is None
        assert self._position(soup, row) < self._position(soup, result)

    def test_the_toolbar_holds_no_count(self, rf, cat):
        _product(cat, "Lamp")

        soup = _filtered_list_page(rf, "?o=name_asc", toolbar_filters=["q", "o"])

        toolbar = soup.find(class_="mvp-list-toolbar")
        assert toolbar.find(class_="mvp-list-summary") is None
        assert not [p for p in toolbar.find_all("p") if "Name (A-Z)" in p.get_text()]


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

    def test_a_search_matching_nothing_is_not_called_a_filter(self, rf, cat):
        _product(cat, "Lamp")

        soup = _list_page(rf, "?q=chair")

        empty = soup.find(class_="mvp-list-empty")
        assert "Try other words or fewer filters." in empty.get_text()
        assert empty.find("a").get_text(strip=True) == "Clear all"

    def test_no_records_opens_the_create_dialog_when_the_page_has_one(self, rf, db):
        from demo.forms import ProductForm

        soup = _list_page(rf, show_create_action=True, create_form_class=ProductForm)

        empty = soup.find(class_="mvp-list-empty")
        assert empty.find("a", href="/products/create/") is None
        assert "createModal.showModal()" in str(empty.find("button"))
        assert len(soup.find_all(id="createModal")) == 1

    def test_the_create_dialog_on_an_empty_list_returns_to_the_list(self, rf, db):
        from demo.forms import ProductForm

        soup = _list_page(rf, show_create_action=True, create_form_class=ProductForm)

        assert soup.find("form", id="createForm")["action"].endswith("?next=/products/")


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


REGION_REQUEST = {"HX-Request": "true", "HX-Target": "mvp-list"}
SWAP = {
    "hx-boost": "true",
    "hx-target": "#mvp-list",
    "hx-select": "#mvp-list",
    "hx-swap": "outerHTML",
}


def _list_page_for_htmx(rf, query="", headers=REGION_REQUEST, **attrs):
    """Render a product list page as htmx requests it and return its soup."""
    view_cls = type(
        "StubHtmxListView",
        (MVPListView,),
        {
            "model": Product,
            "list_item_template": CARD,
            "filterset_class": ListPageFilter,
            **attrs,
        },
    )
    view = view_cls()
    view.setup(rf.get(f"/products/{query}", headers=headers))
    response = view.get(view.request)
    response.render()
    return _beautiful_soup()(response.content.decode(), "html.parser")


def _swaps_the_region(element):
    return all(element.get(name) == value for name, value in SWAP.items())


class TestListPageUpdatesInPlace:
    def test_a_request_for_the_list_region_gets_it_without_the_shell(self, rf, cat):
        _product(cat, "Lamp")

        soup = _list_page_for_htmx(rf, "?q=lamp")

        assert soup.find(id="mvp-list") is not None
        assert soup.find("title") is not None
        assert soup.find("body") is None

    def test_any_other_htmx_request_gets_the_whole_page(self, rf, cat):
        _product(cat, "Lamp")

        soup = _list_page_for_htmx(
            rf, headers={"HX-Request": "true", "HX-Boosted": "true"}
        )

        assert soup.find("body") is not None
        assert soup.find(id="mvp-list") is not None

    def test_the_response_varies_on_the_htmx_target(self, rf, db):
        view_cls = type(
            "VaryListView",
            (MVPListView,),
            {"model": Product, "list_item_template": CARD},
        )
        view = view_cls()
        view.setup(rf.get("/products/"))

        response = view.get(view.request)

        assert "HX-Target" in response["Vary"]

    def test_a_projects_block_override_is_drawn_in_the_region(self, rf, cat):
        _product(cat, "Lamp")

        soup = _list_page_for_htmx(
            rf,
            template_name="tests/list_view_block_override.html",
            extra_context={"override": "page.results"},
        )

        assert soup.find(id="mvp-list").find(id="override") is not None

    def test_the_filter_form_chips_and_pager_swap_the_region(self, rf, cat):
        for number in range(3):
            _product(cat, f"Lamp {number}")

        soup = _list_page(rf, "?q=lamp", paginate_by=2)

        assert _swaps_the_region(soup.find("form", id="filterForm"))
        assert _swaps_the_region(soup.find(class_="mvp-list-refinements"))
        assert _swaps_the_region(soup.find(class_="mvp-list-footer"))

    def test_clear_all_in_the_empty_state_swaps_the_region(self, rf, cat):
        _product(cat, "Lamp")

        soup = _list_page(rf, "?q=chair")

        clear = soup.find(class_="mvp-list-empty").find("a", href="/products/")
        assert _swaps_the_region(clear.parent)

    def test_a_result_inherits_no_swap(self, rf, cat):
        _product(cat, "Lamp")

        soup = _list_page(rf)

        result = soup.find(id="mvp-list").find(string="Lamp").parent
        assert not any(ancestor.get("hx-target") for ancestor in result.find_parents())


PANEL_SWAP = {**SWAP, "hx-select-oob": "#filters"}


def _swaps_the_region_and_the_panel(element):
    return all(element.get(name) == value for name, value in PANEL_SWAP.items())


class TestListPageFilterPanel:
    def test_the_filter_form_chips_and_pager_refresh_the_panel(self, rf, cat):
        for number in range(3):
            _product(cat, f"Lamp {number}")

        soup = _filtered_list_page(rf, "?q=lamp", paginate_by=2)

        assert _swaps_the_region_and_the_panel(soup.find("form", id="filterForm"))
        assert _swaps_the_region_and_the_panel(soup.find(class_="mvp-list-refinements"))
        assert _swaps_the_region_and_the_panel(soup.find(class_="mvp-list-footer"))

    def test_clear_all_in_the_empty_state_refreshes_the_panel(self, rf, cat):
        _product(cat, "Lamp")

        soup = _filtered_list_page(rf, "?q=chair")

        clear = soup.find(class_="mvp-list-empty").find("a", href="/products/")
        assert _swaps_the_region_and_the_panel(clear.parent)

    def test_the_panel_is_beside_the_region_and_comes_back_with_it(self, rf, cat):
        _product(cat, "Lamp")

        soup = _list_page_for_htmx(
            rf, "?name=Lamp", filterset_class=FilteredListPageFilter
        )

        assert soup.find(id="filters") is not None
        assert soup.find(id="filters").find_parent(id="mvp-list") is None

    def test_the_panel_holds_the_fields_the_toolbar_does_not(self, rf, cat):
        _product(cat, "Lamp")

        soup = _filtered_list_page(rf, toolbar_filters=["q"])

        panel = soup.find(id="filters")
        assert panel.find(attrs={"name": "name"}) is not None
        assert panel.find(attrs={"name": "status"}) is not None
        assert panel.find(attrs={"name": "q"}) is None

    def test_the_panel_has_no_form_of_its_own(self, rf, cat):
        _product(cat, "Lamp")

        soup = _filtered_list_page(rf)

        assert soup.find(id="filters").find("form") is None

    def test_the_panel_is_at_the_end_and_level_with_the_content(self, rf, cat):
        _product(cat, "Lamp")

        panel = _filtered_list_page(rf).find(id="filters")

        assert panel["data-mvp-side-position"] == "end"
        assert panel["data-mvp-side-align"] == "content"

    def test_a_subclass_dict_reaches_the_panel(self, rf, cat):
        _product(cat, "Lamp")

        panel = _filtered_list_page(
            rf, filter_panel_attrs={"position": "start", "width": "lg"}
        ).find(id="filters")

        assert panel["data-mvp-side-position"] == "start"
        assert panel["data-mvp-side-width"] == "lg"

    def test_a_subclass_id_names_the_panel_its_button_and_every_refresh(self, rf, cat):
        _product(cat, "Lamp")

        soup = _filtered_list_page(rf, filter_panel_id="refine")

        assert soup.find(id="refine") is not None
        assert soup.find("button", attrs={"aria-controls": "refine"}) is not None
        assert soup.find("form", id="filterForm")["hx-select-oob"] == "#refine"

    def test_the_button_sits_in_the_toolbar_and_counts_the_panels_filters(
        self, rf, cat
    ):
        _product(cat, "Lamp")

        soup = _filtered_list_page(
            rf, "?name=Lamp&status=published", toolbar_filters=["q", "name"]
        )

        button = soup.find("button", attrs={"aria-controls": "filters"})
        assert button.find_parent(class_="mvp-list-toolbar") is not None
        assert button.find(class_="badge").get_text(strip=True) == "1"

    def test_the_button_has_no_badge_while_no_panel_filter_is_applied(self, rf, cat):
        _product(cat, "Lamp")

        soup = _filtered_list_page(rf, "?name=Lamp", toolbar_filters=["q", "name"])

        button = soup.find("button", attrs={"aria-controls": "filters"})
        assert button.find(class_="badge") is None


LIST_PAGE_BLOCKS = [
    "page.actions",
    "page.toolbar",
    "page.filters",
    "page.controls",
    "page.summary",
    "page.refinements",
    "page.results",
    "page.pagination",
]


class TestListPageScript:
    def test_the_page_loads_a_script_the_package_ships(self, rf, cat):
        from django.contrib.staticfiles import finders
        from django.templatetags.static import static

        _product(cat, "Lamp")

        soup = _filtered_list_page(rf)

        src = static("js/list_view.js")
        assert soup.find("script", src=src) is not None
        assert finders.find("js/list_view.js") is not None


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
        view_cls = type(
            "StubDisplayListView",
            (MVPListView,),
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



class ProductListFilter(django_filters.FilterSet):
    q = SearchFilter(fields=["name"])
    status = django_filters.ChoiceFilter(choices=Product.STATUS_CHOICES)
    category = django_filters.ModelChoiceFilter(queryset=Category.objects.all())
    o = SortFilter(options=[("name", "Name", ["name", "pk"])])

    class Meta:
        model = Product
        fields: list[str] = []


class TestListFilterset:
    def _view(self, rf, query="", **attrs):
        view_cls = type(
            "StubFiltersetListView",
            (MVPListView,),
            {
                "model": Product,
                "list_item_template": CARD,
                "render_to_response": lambda self, context, **kwargs: context,
                **attrs,
            },
        )
        view = view_cls()
        view.setup(rf.get(f"/products/{query}"))
        return view

    def _names(self, context):
        return [product.name for product in context["object_list"]]

    def test_the_filterset_narrows_the_list(self, rf, cat, cat2):
        _product(cat, "Lamp", status="draft")
        _product(cat, "Chair", status="published")
        _product(cat2, "Lamp shade", status="draft")
        view = self._view(rf, f"?q=lamp&category={cat.pk}", filterset_class=ProductListFilter)

        context = view.get(view.request)

        assert self._names(context) == ["Lamp"]

    def test_the_filterset_is_in_the_context_under_both_names(self, rf, db):
        view = self._view(rf, filterset_class=ProductListFilter)

        context = view.get(view.request)

        assert isinstance(context["filter"], ProductListFilter)
        assert context["filterset"] is context["filter"]

    def test_the_filterset_is_built_once_per_request(self, rf, db):
        view = self._view(rf, filterset_class=ProductListFilter)

        assert view.get_filterset() is view.get_filterset()

    def test_the_filterset_holds_only_what_the_views_own_queryset_allows(
        self, rf, cat
    ):
        _product(cat, "Lamp mine", is_featured=True)
        _product(cat, "Lamp other", is_featured=False)

        def get_queryset(self):
            return super(type(self), self).get_queryset().filter(is_featured=True)

        view = self._view(
            rf, "?q=lamp", filterset_class=ProductListFilter, get_queryset=get_queryset
        )

        context = view.get(view.request)

        assert [p.name for p in context["filter"].qs] == ["Lamp mine"]
        assert self._names(context) == ["Lamp mine"]

    def test_the_filterset_reads_the_request(self, rf, db):
        view = self._view(rf, "?status=draft", filterset_class=ProductListFilter)

        filterset = view.get_filterset()

        assert filterset.request is view.request
        assert filterset.data["status"] == "draft"

    def test_filterset_fields_alone_get_a_generated_filterset(self, rf, cat):
        _product(cat, "Lamp", status="draft")
        _product(cat, "Chair", status="published")
        view = self._view(rf, "?status=draft", filterset_fields=["status"])

        context = view.get(view.request)

        assert self._names(context) == ["Lamp"]
        assert list(context["filter"].filters) == ["status"]

    def test_a_view_with_no_filterset_has_no_filter_in_its_context(self, rf, cat):
        _product(cat, "Lamp")
        view = self._view(rf)

        context = view.get(view.request)

        assert "filter" not in context
        assert "filterset" not in context
        assert view.get_filterset() is None

    def test_a_page_with_no_filterset_draws_no_filter_form(self, rf, cat):
        _product(cat, "Lamp")
        view_cls = type(
            "StubPlainListView",
            (MVPListView,),
            {"model": Product, "list_item_template": CARD},
        )
        view = view_cls()
        view.setup(rf.get("/products/"))
        response = view.get(view.request)
        response.render()
        soup = _beautiful_soup()(response.content.decode(), "html.parser")

        assert soup.find(id="filterForm") is None
        assert soup.find(id="filters") is None

    def test_a_bad_value_is_ignored_and_the_other_filters_still_apply(
        self, rf, cat, cat2
    ):
        _product(cat, "Lamp", status="draft")
        _product(cat2, "Chair", status="draft")
        view = self._view(
            rf, f"?status=bogus&category={cat.pk}", filterset_class=ProductListFilter
        )

        context = view.get(view.request)

        assert self._names(context) == ["Lamp"]

    def test_a_bad_value_never_empties_the_list(self, rf, cat):
        _product(cat, "Lamp")
        _product(cat, "Chair")
        view = self._view(rf, "?category=99999", filterset_class=ProductListFilter)

        context = view.get(view.request)

        assert sorted(self._names(context)) == ["Chair", "Lamp"]

    def test_an_unknown_sort_key_leaves_the_default_order(self, rf, cat):
        for name in ["Beta", "Alpha", "Gamma"]:
            _product(cat, name, status="draft")
        default = [p.name for p in Product.objects.all()]
        view = self._view(rf, "?o=-price&status=draft", filterset_class=ProductListFilter)

        context = view.get(view.request)

        assert self._names(context) == default


REMOVED_SETTINGS = [
    ("search_fields", ["name"], "SearchFilter"),
    ("max_search_words", 20, "SearchFilter"),
    ("order_by", [("name", "Name", "name")], "SortFilter"),
    ("get_search_fields", lambda self: ["name"], "SearchFilter"),
    ("get_order_by_choices", lambda self: [], "SortFilter"),
]


class TestRemovedSettings:
    @pytest.mark.parametrize(("name", "value", "replacement"), REMOVED_SETTINGS)
    def test_a_list_view_declaring_a_removed_setting_is_refused(
        self, name, value, replacement
    ):
        from django.core.exceptions import ImproperlyConfigured

        with pytest.raises(ImproperlyConfigured) as excinfo:
            type("StaleListView", (MVPListView,), {"model": Product, name: value})

        message = str(excinfo.value)
        assert "StaleListView" in message
        assert name in message
        assert replacement in message

    def test_a_table_view_declaring_order_by_is_pointed_at_its_table(self):
        pytest.importorskip("django_tables2")
        from django.core.exceptions import ImproperlyConfigured

        from mvp.integrations.django_tables.views import MVPTableView

        with pytest.raises(ImproperlyConfigured) as excinfo:
            type(
                "StaleTableView",
                (MVPTableView,),
                {"model": Product, "order_by": [("name", "Name", "name")]},
            )

        message = str(excinfo.value)
        assert "StaleTableView" in message
        assert "Meta.order_by" in message
        assert "SortFilter" not in message

    def test_a_table_view_declaring_search_fields_is_pointed_at_the_filterset(self):
        pytest.importorskip("django_tables2")
        from django.core.exceptions import ImproperlyConfigured

        from mvp.integrations.django_tables.views import MVPTableView

        with pytest.raises(ImproperlyConfigured, match="SearchFilter"):
            type(
                "StaleTableView",
                (MVPTableView,),
                {"model": Product, "search_fields": ["name"]},
            )

    def test_a_list_view_composing_filter_view_is_refused(self):
        from django.core.exceptions import ImproperlyConfigured
        from django_filters.views import FilterView

        with pytest.raises(ImproperlyConfigured) as excinfo:
            type("ComposedListView", (MVPListViewMixin, FilterView), {"model": Product})

        message = str(excinfo.value)
        assert "ComposedListView" in message
        assert "FilterView" in message
        assert "filterset_class" in message

    def test_a_list_view_with_none_of_them_defines_cleanly(self):
        view_cls = type(
            "CleanListView",
            (MVPListView,),
            {"model": Product, "filterset_class": ProductListFilter},
        )

        assert issubclass(view_cls, MVPListView)

    @pytest.mark.parametrize("name", ["search_fields", "order_by"])
    def test_an_empty_removed_setting_is_not_refused(self, name):
        view_cls = type("EmptyListView", (MVPListView,), {"model": Product, name: None})

        assert issubclass(view_cls, MVPListView)

    def test_the_old_mixins_are_gone(self):
        import mvp.views.list

        for name in ["SearchMixin", "OrderMixin", "SearchOrderMixin"]:
            assert not hasattr(mvp.views.list, name)


class FancySelect(forms.Select):
    """A widget a developer chose for a choice filter, in place of its default."""


class FancyInput(forms.TextInput):
    """A widget a developer chose for a text filter, in place of its default."""


class ToolbarProductFilter(django_filters.FilterSet):
    q = SearchFilter(fields=["name"])
    name = django_filters.CharFilter(lookup_expr="icontains")
    status = django_filters.ChoiceFilter(choices=Product.STATUS_CHOICES)
    category = django_filters.ModelChoiceFilter(queryset=Category.objects.all())
    is_featured = django_filters.BooleanFilter()
    statuses = django_filters.MultipleChoiceFilter(
        field_name="status", choices=Product.STATUS_CHOICES
    )
    categories = django_filters.ModelMultipleChoiceFilter(
        field_name="category", queryset=Category.objects.all()
    )
    shelf = django_filters.ModelChoiceFilter(
        field_name="category", queryset=Category.objects.all(), widget=FancySelect
    )
    sku = django_filters.CharFilter(widget=FancyInput)
    price = django_filters.RangeFilter()
    o = SortFilter(
        options=[
            ("name", "Name", ["name", "pk"]),
            ("-name", "Name (Z-A)", ["-name", "-pk"]),
        ]
    )

    class Meta:
        model = Product
        fields: list[str] = []


class TestToolbarPlacement:
    def _context(self, rf, query="", **attrs):
        view_cls = type(
            "StubToolbarListView",
            (MVPListView,),
            {
                "model": Product,
                "list_item_template": CARD,
                "filterset_class": ToolbarProductFilter,
                "render_to_response": lambda self, context, **kwargs: context,
                **attrs,
            },
        )
        view = view_cls()
        view.setup(rf.get(f"/products/{query}"))
        return view.get(view.request)

    def _field(self, rf, name, query=""):
        context = self._context(rf, query, toolbar_filters=[name])
        if context["toolbar_sort"] is not None:
            return context["toolbar_sort"]
        return context["toolbar_fields"][0]

    def test_named_fields_come_back_in_the_order_named(self, rf, db):
        context = self._context(rf, toolbar_filters=["status", "q", "name"])

        assert [field["name"] for field in context["toolbar_fields"]] == [
            "status",
            "q",
            "name",
        ]

    def test_a_toolbar_field_is_not_a_panel_field(self, rf, db):
        context = self._context(rf, toolbar_filters=["status", "q"])

        panel = [field.name for field in context["panel_fields"]]
        assert "status" not in panel
        assert "q" not in panel
        assert "category" in panel

    def test_a_name_listed_twice_is_drawn_once(self, rf, db):
        context = self._context(rf, toolbar_filters=["q", "status", "q"])

        assert [field["name"] for field in context["toolbar_fields"]] == [
            "q",
            "status",
        ]

    def test_the_sort_is_taken_out_to_the_end_of_the_row(self, rf, db):
        context = self._context(rf, toolbar_filters=["o", "q"])

        assert [field["name"] for field in context["toolbar_fields"]] == ["q"]
        assert context["toolbar_sort"]["name"] == "o"
        assert "o" not in [field.name for field in context["panel_fields"]]

    def test_no_sort_named_leaves_no_toolbar_sort(self, rf, db):
        context = self._context(rf, toolbar_filters=["q"])

        assert context["toolbar_sort"] is None

    @pytest.mark.parametrize(
        ("name", "kind"),
        [
            ("q", "search"),
            ("o", "sort"),
            ("is_featured", "toggle"),
            ("statuses", "multichoice"),
            ("categories", "multichoice"),
            ("status", "choice"),
            ("category", "choice"),
            ("name", "text"),
            ("shelf", "widget"),
            ("sku", "widget"),
        ],
    )
    def test_each_filter_is_drawn_as_its_kind(self, rf, db, name, kind):
        field = self._field(rf, name)

        assert field["kind"] == kind
        assert field["name"] == name

    def test_every_field_carries_its_filters_label(self, rf, db):
        context = self._context(rf, toolbar_filters=["q", "status", "o"])
        filterset = context["filter"]

        for field in [*context["toolbar_fields"], context["toolbar_sort"]]:
            assert field["label"] == str(filterset.form[field["name"]].label)

    def test_the_search_and_a_text_field_carry_the_value_sent(self, rf, db):
        context = self._context(rf, "?q=lamp&name=oak", toolbar_filters=["q", "name"])

        assert [field["value"] for field in context["toolbar_fields"]] == [
            "lamp",
            "oak",
        ]

    def test_a_choice_offers_every_choice_but_the_empty_one(self, rf, db):
        field = self._field(rf, "status", "?status=published")

        assert field["value"] == "published"
        assert [(key, selected) for key, _label, selected in field["choices"]] == [
            ("draft", False),
            ("published", True),
            ("archived", False),
        ]

    def test_grouped_choices_offer_their_leaf_values(self, rf, db):
        class GroupedFilter(django_filters.FilterSet):
            status = django_filters.ChoiceFilter(
                choices=[
                    ("Live", [("published", "Published")]),
                    ("Old", [("archived", "Archived")]),
                ]
            )

            class Meta:
                model = Product
                fields: list[str] = []

        context = self._context(
            rf,
            "?status=archived",
            filterset_class=GroupedFilter,
            toolbar_filters=["status"],
        )

        field = context["toolbar_fields"][0]
        assert [(key, selected) for key, _label, selected in field["choices"]] == [
            ("published", False),
            ("archived", True),
        ]

    def test_a_model_choice_offers_each_record_by_its_key(self, rf, cat, cat2):
        field = self._field(rf, "category", f"?category={cat2.pk}")

        assert [(key, selected) for key, _label, selected in field["choices"]] == [
            (str(category.pk), category == cat2)
            for category in Category.objects.all()
        ]

    def test_the_sort_marks_the_option_chosen(self, rf, db):
        field = self._field(rf, "o", "?o=-name")

        assert field["value"] == "-name"
        assert [(key, selected) for key, _label, selected in field["choices"]] == [
            ("name", False),
            ("-name", True),
        ]

    def test_a_multichoice_marks_each_value_chosen(self, rf, db):
        field = self._field(rf, "statuses", "?statuses=draft&statuses=archived")

        assert [(key, selected) for key, _label, selected in field["choices"]] == [
            ("draft", True),
            ("published", False),
            ("archived", True),
        ]

    @pytest.mark.parametrize(
        ("query", "checked"),
        [("", False), ("?is_featured=true", True), ("?is_featured=false", False)],
    )
    def test_a_toggle_is_checked_only_when_set(self, rf, db, query, checked):
        field = self._field(rf, "is_featured", query)

        assert field["checked"] is checked

    def test_a_developers_widget_is_handed_over_as_its_bound_field(self, rf, db):
        field = self._field(rf, "shelf")

        assert field["bound"].name == "shelf"
        assert isinstance(field["bound"].field.widget, FancySelect)

    @pytest.mark.parametrize(
        ("name", "control"), [("shelf", "select"), ("sku", "input")]
    )
    def test_a_developers_widget_gains_the_class_of_its_control(
        self, rf, db, name, control
    ):
        field = self._field(rf, name)

        assert field["bound"].field.widget.attrs["class"].split() == [
            control,
            "w-full",
        ]

    def test_a_developers_widget_is_named_by_the_filters_label(self, rf, db):
        field = self._field(rf, "shelf")

        assert field["bound"].field.widget.attrs["aria-label"] == field["label"]

    def test_a_developers_own_class_and_name_are_kept(self, rf, db):
        class OwnAttrsFilter(django_filters.FilterSet):
            shelf = django_filters.ModelChoiceFilter(
                field_name="category",
                queryset=Category.objects.all(),
                widget=FancySelect(attrs={"class": "mine", "aria-label": "Mine"}),
            )

            class Meta:
                model = Product
                fields: list[str] = []

        context = self._context(
            rf, filterset_class=OwnAttrsFilter, toolbar_filters=["shelf"]
        )

        attrs = context["toolbar_fields"][0]["bound"].field.widget.attrs
        assert attrs["class"] == "mine"
        assert attrs["aria-label"] == "Mine"

    def test_a_sort_with_a_widget_of_its_own_is_still_the_sort(self, rf, db):
        class WidgetSortFilter(django_filters.FilterSet):
            o = SortFilter(options=[("name", "Name", "name")], widget=FancySelect)

            class Meta:
                model = Product
                fields: list[str] = []

        context = self._context(
            rf, filterset_class=WidgetSortFilter, toolbar_filters=["o"]
        )

        assert context["toolbar_sort"]["kind"] == "sort"

    def test_every_field_listed_leaves_nothing_for_the_panel(self, rf, db):
        class NoRangeFilter(ToolbarProductFilter):
            price = None

        names = list(NoRangeFilter.base_filters)

        context = self._context(
            rf, filterset_class=NoRangeFilter, toolbar_filters=names
        )

        assert context["panel_fields"] == []

    def test_an_unknown_name_is_refused_naming_the_view_the_name_and_the_filterset(
        self, rf, db
    ):
        with pytest.raises(ImproperlyConfigured) as excinfo:
            self._context(rf, toolbar_filters=["q", "colour"])

        message = str(excinfo.value)
        assert "StubToolbarListView" in message
        assert "colour" in message
        assert "ToolbarProductFilter" in message

    def test_a_filter_the_toolbar_cannot_draw_is_refused_naming_it(self, rf, db):
        with pytest.raises(ImproperlyConfigured) as excinfo:
            self._context(rf, toolbar_filters=["q", "price"])

        message = str(excinfo.value)
        assert "StubToolbarListView" in message
        assert "price" in message
        assert "RangeFilter" in message

    def test_a_view_can_draw_a_filter_the_package_cannot(self, rf, db):
        def get_toolbar_field(self, filterset, name):
            if name == "price":
                return {"kind": "range", "name": name, "label": "Price"}
            return MVPListView.get_toolbar_field(self, filterset, name)

        context = self._context(
            rf, toolbar_filters=["q", "price"], get_toolbar_field=get_toolbar_field
        )

        assert [field["kind"] for field in context["toolbar_fields"]] == [
            "search",
            "range",
        ]


class TestFilterPanelCountAndClear:
    def _context(self, rf, query="", **attrs):
        view_cls = type(
            "StubPanelListView",
            (MVPListView,),
            {
                "model": Product,
                "filterset_class": ToolbarProductFilter,
                "toolbar_filters": ["q", "name", "o"],
                "render_to_response": lambda self, context, **kwargs: context,
                **attrs,
            },
        )
        view = view_cls()
        view.setup(rf.get(f"/products/{query}"))
        return view.get(view.request)

    def test_the_count_is_only_the_panels_applied_filters(self, rf, db):
        context = self._context(rf, "?name=oak&status=draft")

        assert context["applied_filter_count"] == 2
        assert context["panel_applied_count"] == 1

    def test_no_panel_filter_applied_counts_none_and_offers_no_clear(self, rf, db):
        context = self._context(rf, "?q=lamp&name=oak&o=name")

        assert context["panel_applied_count"] == 0
        assert "clear_panel_url" not in context

    def test_clearing_the_panel_keeps_the_toolbar_the_search_and_the_sort(self, rf, db):
        context = self._context(
            rf, "?q=lamp&name=oak&status=draft&price_min=5&price_max=9&o=name&page=1"
        )

        assert context["clear_panel_url"] == "/products/?q=lamp&name=oak&o=name"

    def test_clearing_the_panel_keeps_the_sort_when_the_sort_is_in_the_panel(
        self, rf, db
    ):
        context = self._context(rf, "?status=draft&o=-name", toolbar_filters=[])

        assert context["clear_panel_url"] == "/products/?o=-name"

    def test_clear_all_drops_the_search_and_every_filter_and_keeps_the_sort(
        self, rf, db
    ):
        context = self._context(rf, "?q=lamp&name=oak&status=draft&o=name&page=1")

        assert context["clear_refinements_url"] == "/products/?o=name"


class TestFilterPanelContext:
    def _context(self, rf, **attrs):
        view_cls = type(
            "StubPanelContextListView",
            (MVPListView,),
            {
                "model": Product,
                "filterset_class": ToolbarProductFilter,
                "toolbar_filters": ["q", "status"],
                "render_to_response": lambda self, context, **kwargs: context,
                **attrs,
            },
        )
        view = view_cls()
        view.setup(rf.get("/products/"))
        return view.get(view.request)

    def _panel(self, rf, name):
        context = self._context(rf)
        return next(field for field in context["panel_fields"] if field.name == name)

    @pytest.mark.parametrize(
        "name",
        [
            "name",
            "is_featured",
            "statuses",
            "categories",
            "shelf",
            "sku",
            "price",
        ],
    )
    def test_a_panel_field_joins_the_toolbar_form(self, rf, db, name):
        bound = self._panel(rf, name)

        assert bound.field.widget.attrs["form"] == "filterForm"

    def test_a_range_reaches_the_form_through_each_of_its_inputs(self, rf, db):
        bound = self._panel(rf, "price")

        html = str(bound)
        assert html.count('form="filterForm"') == 2

    def test_a_widget_the_developer_chose_keeps_its_own_attributes(self, rf, db):
        bound = self._panel(rf, "sku")

        assert isinstance(bound.field.widget, FancyInput)
        assert 'form="filterForm"' in str(bound)

    def test_a_toolbar_field_does_not_join_the_form_by_attribute(self, rf, db):
        context = self._context(rf)

        bound = context["filter"].form["status"]
        assert "form" not in bound.field.widget.attrs

    def test_the_panel_is_at_the_end_by_default(self, rf, db):
        context = self._context(rf)

        assert context["filter_panel_attrs"] == {"position": "end"}

    def test_the_panel_is_called_filters_by_default(self, rf, db):
        context = self._context(rf)

        assert context["filter_panel_id"] == "filters"

    def test_a_subclass_dict_replaces_the_default_attributes(self, rf, db):
        context = self._context(rf, filter_panel_attrs={"width": "lg"})

        assert context["filter_panel_attrs"] == {"width": "lg"}

    def test_a_subclass_can_rename_the_panel(self, rf, db):
        context = self._context(rf, filter_panel_id="refine")

        assert context["filter_panel_id"] == "refine"


class TestSortInTheFilterPanel:
    def test_an_unbound_panel_sort_has_the_default_order_selected(self, rf, cat):
        _product(cat, "Lamp")

        soup = _filtered_list_page(rf, toolbar_filters=[])

        select = soup.find(id="filters").find("select", attrs={"name": "o"})
        options = select.find_all("option")
        selected = [o for o in options if o.has_attr("selected")]
        assert options[0]["value"] == ""
        assert selected in ([], [options[0]])


class TestAYesNoFilterSetToNo:
    def _context(self, rf, query):
        view_cls = type(
            "StubYesNoListView",
            (MVPListView,),
            {
                "model": Product,
                "filterset_class": ToolbarProductFilter,
                "toolbar_filters": ["q", "o"],
                "render_to_response": lambda self, context, **kwargs: context,
            },
        )
        view = view_cls()
        view.setup(rf.get(f"/products/{query}"))
        return view.get(view.request)

    def test_a_no_is_among_the_refinements(self, rf, db):
        context = self._context(rf, "?is_featured=false&status=published")

        assert [r["name"] for r in context["refinements"]] == ["status", "is_featured"]

    def test_a_no_in_the_panel_counts_on_the_panel_button(self, rf, db):
        context = self._context(rf, "?is_featured=false&status=published")

        assert context["panel_applied_count"] == 2

    def test_clear_all_drops_a_no(self, rf, db):
        context = self._context(rf, "?is_featured=false&status=published")

        assert context["clear_refinements_url"] == "/products/"

    def test_a_filter_left_untouched_is_not_applied(self, rf, db):
        context = self._context(rf, "?status=published")

        assert [r["name"] for r in context["refinements"]] == ["status"]


class TestListPageToolbarRow:
    def _names_in_form(self, soup):
        form = soup.find("form", id="filterForm")
        names = [el["name"] for el in form.find_all(attrs={"name": True})]
        return list(dict.fromkeys(names))

    def _position(self, soup, element):
        return next(i for i, tag in enumerate(soup.find_all(True)) if tag is element)

    def test_toolbar_fields_are_in_the_filter_form_in_the_order_named(self, rf, cat):
        _product(cat, "Lamp")

        soup = _filtered_list_page(rf, toolbar_filters=["status", "q", "name"])

        assert self._names_in_form(soup) == ["status", "q", "name"]

    def test_toolbar_fields_are_not_in_the_panel(self, rf, cat):
        _product(cat, "Lamp")

        soup = _filtered_list_page(rf, toolbar_filters=["status", "q"])

        panel = soup.find(id="filters")
        assert panel.find(attrs={"name": "status"}) is None
        assert panel.find(attrs={"name": "q"}) is None
        assert panel.find(attrs={"name": "name"}) is not None

    def test_sort_filter_and_add_end_the_row_in_that_order(self, rf, cat):
        _product(cat, "Lamp")

        soup = _filtered_list_page(
            rf, toolbar_filters=["o", "q"], show_create_action=True
        )

        sort = soup.find("input", attrs={"name": "o"})
        filter_button = soup.find("button", attrs={"aria-controls": "filters"})
        add = soup.find("a", href="/products/create/")
        form = soup.find("form", id="filterForm")
        for element in (sort, filter_button, add):
            assert element.find_parent("form", id="filterForm") is None
        assert sort["form"] == "filterForm"
        assert (
            self._position(soup, form)
            < self._position(soup, sort)
            < self._position(soup, filter_button)
            < self._position(soup, add)
        )

    def test_the_sort_is_drawn_once(self, rf, cat):
        _product(cat, "Lamp")

        soup = _filtered_list_page(rf, toolbar_filters=["o", "q"])

        assert len(soup.find_all(attrs={"name": "o"})) == 1

    def test_every_field_in_the_toolbar_leaves_no_panel_and_no_panel_button(
        self, rf, cat
    ):
        _product(cat, "Lamp")

        soup = _filtered_list_page(rf, toolbar_filters=["q", "o", "name", "status"])

        assert soup.find("button", attrs={"aria-controls": "filters"}) is None
        assert soup.find(id="filters") is None
        assert soup.find("form", id="filterForm") is not None
