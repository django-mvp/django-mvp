"""Tests for PageObjectMixin and MVPDetailView — US1, US2, US3.

Each test class is tagged with [USn] in its docstring to identify the user story it covers.
Run individual stories with: pytest -k US1, -k US2, -k US3, etc.
"""

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory
from django.urls import NoReverseMatch, reverse
from django.views.generic import TemplateView

from demo.models import Article, Product
from mvp.config import MVP_CONFIG
from mvp.views.detail import CRUDDirectoryMixin, MVPDetailView, PageObjectMixin
from tests.conftest import make_stub_view as _make_stub_view

User = get_user_model()


def make_page_object_view(extra_attrs=None, user=None):
    """Return a configured PageObjectMixin stub with a fake GET request.

    Creates a throwaway concrete subclass of PageObjectMixin + TemplateView
    so Django's MRO works without requiring a real URL dispatch cycle.
    """
    rf = RequestFactory()
    request = rf.get("/")
    request.user = user or User()

    attrs = {"model": Product, **(extra_attrs or {})}
    view_cls = type("StubPageView", (PageObjectMixin, TemplateView), attrs)
    view = view_cls()
    view.request = request
    view.kwargs = {}
    view.args = []
    return view


def make_detail_view(model, obj, extra_attrs=None, user=None):
    """Return a configured MVPDetailView instance with the object pre-set.

    Sets ``view.object`` directly so tests can exercise view methods without
    dispatching through the full URL cycle.
    """
    rf = RequestFactory()
    request = rf.get("/")
    request.user = user or User()

    attrs = {"model": model, **(extra_attrs or {})}
    view_cls = type("StubDetailView", (MVPDetailView,), attrs)
    view = view_cls()
    view.request = request
    view.kwargs = {"pk": obj.pk}
    view.args = []
    view.object = obj
    return view


class TestPageObjectMixin:
    def test_context_contains_page_and_directory_with_list_permission(self):
        view = make_page_object_view(
            extra_attrs={"directory": ["list"], "show_list_action": True}
        )
        ctx = view.get_context_data()
        assert "page" in ctx
        assert "list_url" in ctx["directory"]

    def test_breadcrumb_text_defaults_to_verbose_name_plural(self):
        view = make_page_object_view()
        expected = view.model_meta.verbose_name_plural.title()
        breadcrumbs = view.get_breadcrumbs()
        assert breadcrumbs[0]["text"] == expected

    def test_breadcrumb_text_uses_list_view_title_when_set(self):
        view = make_page_object_view(extra_attrs={"list_view_title": "All Orders"})
        breadcrumbs = view.get_breadcrumbs()
        assert breadcrumbs[0]["text"] == "All Orders"

    def test_get_page_class_without_a_model(self):
        view = make_page_object_view(extra_attrs={"model": None})
        assert view.get_page_class() == "mvp-page"

    def test_get_breadcrumbs_without_a_model_omits_the_list_crumb(self):
        view = make_page_object_view(
            extra_attrs={"model": None, "page_title": "Complex Form"}
        )
        assert view.get_breadcrumbs() == [{"text": "Complex Form"}]

    def test_resolve_crud_url_hidden_action_short_circuits_without_a_model(self):
        view = make_page_object_view(
            extra_attrs={"model": None}
        )  # show_list_action defaults to False
        assert view.resolve_crud_url("list") is None


@pytest.mark.django_db
class TestMVPDetailView:
    def test_page_title_equals_str_of_object(self, product):
        view = make_detail_view(Product, product)
        assert view.get_page_title() == str(product)

    def test_page_class_contains_model_name_and_action_class(self, product):
        view = make_detail_view(Product, product)
        page_class = view.get_page_class()
        assert "product-page" in page_class
        assert "mvp-detail-page" in page_class

    def test_breadcrumbs_are_list_link_then_object_name(self, product):
        view = make_detail_view(
            Product,
            product,
            extra_attrs={"directory": ["list"], "show_list_action": True},
        )
        breadcrumbs = view.get_breadcrumbs()
        assert len(breadcrumbs) == 2
        assert breadcrumbs[0]["href"]
        assert breadcrumbs[1]["text"] == str(product)

    def test_template_names_include_app_specific_then_fallback(self, product):
        view = make_detail_view(Product, product)
        names = view.get_template_names()
        assert names[0] == "demo/product_detail.html"
        assert names[-1] == "detail_view.html"


@pytest.mark.django_db
class TestListViewTitle:
    def test_custom_title_present_even_when_permission_false(self, product):
        view = make_detail_view(
            Product,
            product,
            extra_attrs={
                "list_view_title": "Active Orders",
                "directory": ["list"],
                "show_list_action": False,
            },
        )
        breadcrumbs = view.get_breadcrumbs()
        assert breadcrumbs[0]["text"] == "Active Orders"
        assert breadcrumbs[0]["href"] == ""


def make_stub_view(extra_attrs=None, kwargs=None, user=None):
    """CRUDDirectoryMixin stub bound to the demo Product model."""
    return _make_stub_view(
        CRUDDirectoryMixin,
        extra_attrs={"model": Product, **(extra_attrs or {})},
        kwargs=kwargs,
        user=user,
    )


@pytest.mark.django_db
class TestCRUDDirectoryContext:
    def test_US1_empty_directory_context_key_always_present(self):
        view = make_stub_view(extra_attrs={"directory": []}, kwargs={})
        ctx = view.get_context_data()
        assert "directory" in ctx
        assert ctx["directory"] == {}

    def test_US1_list_url_resolves_for_permitted_view(self):
        view = make_stub_view(
            extra_attrs={"directory": ["list"], "show_list_action": True},
            kwargs={},
        )
        result = view.get_directory()
        assert "list_url" in result
        assert result["list_url"] == reverse("product-list")

    def test_US1_update_url_resolves_with_pk(self):
        view = make_stub_view(
            extra_attrs={"directory": ["update"], "show_update_action": True},
            kwargs={"pk": 1},
        )
        result = view.get_directory()
        assert "update_url" in result
        assert result["update_url"] == reverse("product-update", kwargs={"pk": 1})

    def test_US1_object_action_without_kwargs_excluded(self):
        view = make_stub_view(
            extra_attrs={"directory": ["update"], "show_update_action": True},
            kwargs={},
        )
        result = view.get_directory()
        assert "update_url" not in result

    def test_US1_invalid_action_raises_value_error(self):
        # Requires non-empty kwargs so get_url_kwargs doesn't return None early
        view = make_stub_view(
            extra_attrs={
                "directory": ["nonexistent"],
                "show_nonexistent_action": True,
            },
            kwargs={"pk": 1},
        )
        with pytest.raises(ValueError, match="nonexistent"):
            view.get_directory()

    def test_US1_nonexistent_url_pattern_raises_no_reverse_match(self):
        custom_crud = {
            **MVP_CONFIG["view_names"],
            "list": "nonexistent-{model_name}-list",
        }
        view = make_stub_view(
            extra_attrs={
                "directory": ["list"],
                "show_list_action": True,
                "crud_views": custom_crud,
            },
            kwargs={},
        )
        with pytest.raises(NoReverseMatch):
            view.get_directory()

    def test_US1_two_actions_resolving_same_url_both_keys_present(self):
        # Point 'create' to 'product-list' (same URL as 'list')
        custom_crud = {**MVP_CONFIG["view_names"], "create": "{model_name}-list"}
        view = make_stub_view(
            extra_attrs={
                "directory": ["list", "create"],
                "show_list_action": True,
                "show_create_action": True,
                "crud_views": custom_crud,
            },
            kwargs={},
        )
        result = view.get_directory()
        assert "list_url" in result
        assert "create_url" in result
        assert result["list_url"] == result["create_url"]


@pytest.mark.django_db
class TestDirectoryPermissionGating:
    def test_US2_callable_permission_returning_true_includes_url(self):
        # Use staticmethod so the callable is not wrapped as a bound method
        view = make_stub_view(
            extra_attrs={
                "directory": ["create"],
                "show_create_action": staticmethod(lambda user: True),
            },
            kwargs={},
        )
        assert "create_url" in view.get_directory()

    def test_US2_callable_permission_returning_false_excludes_url(self):
        view = make_stub_view(
            extra_attrs={
                "directory": ["create"],
                "show_create_action": staticmethod(lambda user: False),
            },
            kwargs={},
        )
        assert "create_url" not in view.get_directory()

    def test_US2_absent_permission_attribute_excludes_url_no_error(self):
        # 'archive' is not a standard action, so show_archive_action doesn't exist
        custom_crud = {**MVP_CONFIG["view_names"], "archive": "{model_name}-delete"}
        view = make_stub_view(
            extra_attrs={
                "directory": ["archive"],
                "crud_views": custom_crud,
                # show_archive_action deliberately not set
            },
            kwargs={"pk": 1},
        )
        result = view.get_directory()
        assert "archive_url" not in result

    def test_US2_callable_permission_raising_propagates(self):

        def bad_perm(user):
            raise ValueError("permission check failed")

        view = make_stub_view(
            extra_attrs={
                "directory": ["list"],
                "show_list_action": staticmethod(bad_perm),
            },
            kwargs={},
        )
        with pytest.raises(ValueError, match="permission check failed"):
            view.get_directory()

    def test_US2_all_permissions_false_directory_is_empty_dict(self):
        view = make_stub_view(
            extra_attrs={
                "directory": ["list", "create", "update", "delete"],
                "show_list_action": False,
                "show_create_action": False,
                "show_update_action": False,
                "show_delete_action": False,
            },
            kwargs={"pk": 1},
        )
        ctx = view.get_context_data()
        assert "directory" in ctx
        assert ctx["directory"] == {}


# Note: Internal URL naming tests (_get_view_name, token substitution) removed per issue #7.
# They test Django's string formatting, not app behavior. User-facing custom crud_views
# is verified by integration/E2E tests in test_crud_directory_mixin_e2e.py.


@pytest.mark.django_db
class TestDetailPageForStaffUser:
    def test_US5_staff_sees_list_link(self, client, staff_user, product):
        client.force_login(staff_user)
        url = reverse("product-detail", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        list_url = reverse("product-list")
        assert list_url in content, "List link must be present for staff user"


@pytest.mark.django_db
class TestDetailPageForRegularUser:
    def test_US5_regular_user_sees_list_link(self, client, user, product):
        client.force_login(user)
        url = reverse("product-detail", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        list_url = reverse("product-list")
        assert list_url in content, "List link must be present for all users"


@pytest.mark.django_db
class TestProductDetailPageHeadingAndCSSClass:
    def test_product_detail_page_heading_equals_str_product(self, client, product):
        url = reverse("product-detail", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "<h1" in content and str(product) in content, (
            f"Heading element containing '{product!s}' must be present"
        )

    def test_product_detail_page_container_has_model_css_class(self, client, product):
        url = reverse("product-detail", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "product-page" in content, (
            "CSS class 'product-page' must be present in the page container"
        )

    def test_product_detail_page_container_has_action_css_class(self, client, product):
        url = reverse("product-detail", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "mvp-detail-page" in content, (
            "CSS class 'mvp-detail-page' must be present in the page container"
        )


@pytest.mark.django_db
class TestPackagedDetailTemplateBody:
    def test_packaged_page_titles_itself_from_the_object(self, client, article):
        response = client.get(reverse("article-detail", kwargs={"pk": article.pk}))
        content = response.content.decode()
        assert "<h1" in content
        assert str(article) in content


@pytest.mark.django_db
class TestPackagedDetailTemplateActions:
    def test_edit_link_present_for_permitted_user(self, client, staff_user, product):
        client.force_login(staff_user)
        response = client.get(reverse("product-detail", kwargs={"pk": product.pk}))
        assert (
            reverse("product-update", kwargs={"pk": product.pk})
            in response.content.decode()
        )

    def test_delete_link_present_for_permitted_user(self, client, staff_user, product):
        client.force_login(staff_user)
        response = client.get(reverse("product-detail", kwargs={"pk": product.pk}))
        assert (
            reverse("product-delete", kwargs={"pk": product.pk})
            in response.content.decode()
        )

    def test_links_absent_without_permission(self, client, user, product):
        client.force_login(user)
        content = client.get(
            reverse("product-detail", kwargs={"pk": product.pk})
        ).content.decode()
        assert reverse("product-update", kwargs={"pk": product.pk}) not in content
        assert reverse("product-delete", kwargs={"pk": product.pk}) not in content


@pytest.mark.django_db
class TestDefaultDirectoryIsInertWithoutPermission:
    def test_no_url_resolves_without_permission(self, article):
        view = make_detail_view(Article, article)
        assert view.get_directory() == {}

    def test_page_renders_with_no_crud_routes_registered(self, client, article):
        response = client.get(reverse("article-detail", kwargs={"pk": article.pk}))
        assert response.status_code == 200


@pytest.mark.django_db
class TestActionVisibilityAttributes:
    def test_true_includes_url(self):
        view = make_stub_view(
            extra_attrs={"directory": ["list"], "show_list_action": True}, kwargs={}
        )
        assert "list_url" in view.get_directory()

    def test_false_excludes_url(self):
        view = make_stub_view(
            extra_attrs={"directory": ["delete"], "show_delete_action": False},
            kwargs={"pk": 1},
        )
        assert "delete_url" not in view.get_directory()

    def test_callable_is_passed_the_user(self):
        seen = []

        def show(user):
            seen.append(user)
            return True

        view = make_stub_view(
            extra_attrs={
                "directory": ["create"],
                "show_create_action": staticmethod(show),
            },
            kwargs={},
        )
        assert "create_url" in view.get_directory()
        assert seen == [view.request.user]


@pytest.mark.django_db
class TestLegacyPermissionAttributes:
    def test_a_legacy_name_raises_instead_of_deciding_visibility(self):
        view = make_stub_view(
            extra_attrs={"directory": ["list"], "has_list_permission": True}, kwargs={}
        )
        with pytest.raises(ImproperlyConfigured):
            view.get_directory()

    def test_a_hidden_link_is_never_revealed_by_the_removal(self):
        view = make_stub_view(
            extra_attrs={
                "directory": ["list"],
                "show_list_action": True,
                "has_list_permission": False,
            },
            kwargs={},
        )
        with pytest.raises(ImproperlyConfigured):
            view.get_directory()

    def test_a_legacy_callable_raises_too(self):
        view = make_stub_view(
            extra_attrs={
                "directory": ["create"],
                "has_create_permission": staticmethod(lambda user: False),
            },
            kwargs={},
        )
        with pytest.raises(ImproperlyConfigured):
            view.get_directory()

    def test_the_error_names_the_view_the_replacement_and_the_limitation(self):
        view = make_stub_view(
            extra_attrs={"directory": ["delete"], "has_delete_permission": True},
            kwargs={"pk": 1},
        )
        with pytest.raises(ImproperlyConfigured) as exc:
            view.get_directory()
        message = str(exc.value)
        assert "has_delete_permission" in message
        assert "show_delete_action" in message
        assert type(view).__name__ in message
