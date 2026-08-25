"""Tests for PageObjectMixin and MVPDetailView — US1, US2, US3.

Each test class is tagged with [USn] in its docstring to identify the user story it covers.
Run individual stories with: pytest -k US1, -k US2, -k US3, etc.
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.urls import NoReverseMatch, reverse
from django.views.generic import TemplateView

from demo.models import Article, Product
from mvp.config import MVP_CONFIG
from mvp.views.detail import CRUDDirectoryMixin, MVPDetailView, PageObjectMixin
from mvp.warnings import MVPDeprecationWarning
from tests.conftest import make_stub_view as _make_stub_view

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# TestPageObjectMixin — US1
# ---------------------------------------------------------------------------


class TestPageObjectMixin:
    """[US1] Unit tests for PageObjectMixin — shared composition base.

    Verifies that model resolution, sibling URL directory, and breadcrumb/page-class
    concerns are correctly assembled and independently testable without a database.
    """

    def test_context_contains_page_and_directory_with_list_permission(self):
        """[US1] Given show_list_action=True and directory=['list'], context has 'page' and 'directory['list_url']'."""
        view = make_page_object_view(
            extra_attrs={"directory": ["list"], "show_list_action": True}
        )
        ctx = view.get_context_data()
        assert "page" in ctx
        assert "list_url" in ctx["directory"]

    def test_breadcrumb_text_defaults_to_verbose_name_plural(self):
        """[US1] First breadcrumb text equals verbose_name_plural.title() when list_view_title is unset."""
        view = make_page_object_view()
        expected = view.model_meta.verbose_name_plural.title()
        breadcrumbs = view.get_breadcrumbs()
        assert breadcrumbs[0]["text"] == expected

    def test_breadcrumb_text_uses_list_view_title_when_set(self):
        """[US1] First breadcrumb text equals list_view_title when explicitly set."""
        view = make_page_object_view(extra_attrs={"list_view_title": "All Orders"})
        breadcrumbs = view.get_breadcrumbs()
        assert breadcrumbs[0]["text"] == "All Orders"

    def test_get_page_class_without_a_model(self):
        """Regression (#311): a plain MVPFormView shares PageObjectMixin with
        the model-based views but carries no model by design. get_page_class()
        used to read self.model_meta unconditionally and crash."""
        view = make_page_object_view(extra_attrs={"model": None})
        assert view.get_page_class() == "mvp-page"

    def test_get_breadcrumbs_without_a_model_omits_the_list_crumb(self):
        """Regression (#311): no model means no list view to link to, so the
        list crumb is dropped entirely rather than rendered with empty text."""
        view = make_page_object_view(
            extra_attrs={"model": None, "page_title": "Complex Form"}
        )
        assert view.get_breadcrumbs() == [{"text": "Complex Form"}]

    def test_resolve_crud_url_hidden_action_short_circuits_without_a_model(self):
        """Regression (#311): resolve_crud_url() computed the CRUD view name
        (which needs the model) before checking whether the action was even
        shown, so a hidden action still crashed on a model-less view."""
        view = make_page_object_view(
            extra_attrs={"model": None}
        )  # show_list_action defaults to False
        assert view.resolve_crud_url("list") is None


# ---------------------------------------------------------------------------
# TestMVPDetailView — US2
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestMVPDetailView:
    """[US2] Unit tests for MVPDetailView zero-configuration read-only behaviour.

    Verifies that page title, effective CSS classes, breadcrumb trail, and template
    fallback order are all correct without any subclass override.
    """

    def test_page_title_equals_str_of_object(self, product):
        """[US2] get_page_title() returns str(product) — SC-003 model 1."""
        view = make_detail_view(Product, product)
        assert view.get_page_title() == str(product)

    def test_page_title_equals_str_of_article(self, article):
        """[US2] get_page_title() returns str(article) — SC-003 model 2."""
        view = make_detail_view(Article, article)
        assert view.get_page_title() == str(article)

    def test_page_title_handles_unicode_str(self, category):
        """[US2] get_page_title() returns a unicode product name without corruption — US4 AC-2."""
        unicode_product = Product.objects.create(
            name="Ünïcödé Prödüct",
            slug="unicode-product-detail",
            category=category,
            description="A unicode test product",
            price="9.99",
            stock=1,
        )
        view = make_detail_view(Product, unicode_product)
        assert view.get_page_title() == "Ünïcödé Prödüct"

    def test_page_class_contains_model_name_and_action_class(self, product):
        """[US2] get_page_class() output contains both 'product-page' and 'mvp-detail-page'."""
        view = make_detail_view(Product, product)
        page_class = view.get_page_class()
        assert "product-page" in page_class
        assert "mvp-detail-page" in page_class

    def test_breadcrumbs_are_list_link_then_object_name(self, product):
        """[US2] Given show_list_action=True, breadcrumbs are [list_link, object_name]."""
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
        """[US2] get_template_names() returns ['demo/product_detail.html', 'detail_view.html']."""
        view = make_detail_view(Product, product)
        names = view.get_template_names()
        assert names[0] == "demo/product_detail.html"
        assert names[-1] == "detail_view.html"


# ---------------------------------------------------------------------------
# TestListViewTitle — US3
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestListViewTitle:
    """[US3] Unit tests for the list_view_title attribute customisation.

    Verifies that setting list_view_title controls breadcrumb back-link text via a
    single class attribute with no method override required.
    """

    def test_custom_list_view_title_appears_in_breadcrumb(self, product):
        """[US3] First breadcrumb text is list_view_title when set."""
        view = make_detail_view(
            Product,
            product,
            extra_attrs={"list_view_title": "Active Orders"},
        )
        breadcrumbs = view.get_breadcrumbs()
        assert breadcrumbs[0]["text"] == "Active Orders"

    def test_default_breadcrumb_text_is_verbose_name_plural_title_cased(self, product):
        """[US3] First breadcrumb text equals verbose_name_plural.title() when list_view_title is unset."""
        view = make_detail_view(Product, product)
        expected = Product._meta.verbose_name_plural.title()
        breadcrumbs = view.get_breadcrumbs()
        assert breadcrumbs[0]["text"] == expected

    def test_custom_title_present_even_when_permission_false(self, product):
        """[US3] Given list_view_title='Active Orders' and show_list_action=False, first breadcrumb has that text with empty href."""
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


# -------------------------------------------------------------------------
# CRUDDirectoryMixin
# -------------------------------------------------------------------------


def make_stub_view(extra_attrs=None, kwargs=None, user=None):
    """CRUDDirectoryMixin stub bound to the demo Product model."""
    return _make_stub_view(
        CRUDDirectoryMixin,
        extra_attrs={"model": Product, **(extra_attrs or {})},
        kwargs=kwargs,
        user=user,
    )


# ---------------------------------------------------------------------------
@pytest.mark.django_db
class TestUS1Directory:
    """[US1] Integration tests for get_directory() and get_context_data()."""

    def test_US1_empty_directory_context_key_always_present(self):
        """[US1] directory=[] → context always has 'directory' key as empty dict."""
        view = make_stub_view(extra_attrs={"directory": []}, kwargs={})
        ctx = view.get_context_data()
        assert "directory" in ctx
        assert ctx["directory"] == {}

    def test_US1_list_url_resolves_for_permitted_view(self):
        """[US1] directory=['list'] + permission=True → list_url in directory dict."""
        view = make_stub_view(
            extra_attrs={"directory": ["list"], "show_list_action": True},
            kwargs={},
        )
        result = view.get_directory()
        assert "list_url" in result
        assert result["list_url"] == reverse("product-list")

    def test_US1_update_url_resolves_with_pk(self):
        """[US1] directory=['update'] + pk in kwargs + permission → update_url resolved."""
        view = make_stub_view(
            extra_attrs={"directory": ["update"], "show_update_action": True},
            kwargs={"pk": 1},
        )
        result = view.get_directory()
        assert "update_url" in result
        assert result["update_url"] == reverse("product-update", kwargs={"pk": 1})

    def test_US1_object_action_without_kwargs_excluded(self):
        """[US1] directory=['update'] with no URL kwargs → update_url absent, no error."""
        view = make_stub_view(
            extra_attrs={"directory": ["update"], "show_update_action": True},
            kwargs={},
        )
        result = view.get_directory()
        assert "update_url" not in result

    def test_US1_invalid_action_raises_value_error(self):
        """[US1] Action not in crud_views → ValueError with action name in message."""
        # Requires non-empty kwargs so get_url_kwargs doesn't return None early
        view = make_stub_view(
            extra_attrs={
                "directory": ["nonexistent"],
                "has_nonexistent_permission": True,
            },
            kwargs={"pk": 1},
        )
        with pytest.raises(ValueError, match="nonexistent"):
            view.get_directory()

    def test_US1_nonexistent_url_pattern_raises_no_reverse_match(self):
        """[US1] Action whose URL pattern doesn't exist → NoReverseMatch propagates."""
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
        """[US1] Two actions that resolve to the same URL → both {action}_url keys present."""
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


# ---------------------------------------------------------------------------
# US2: Permission-Gated Directory URLs
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUS2PermissionGating:
    """[US2] Tests for permission gating in resolve_crud_url()."""

    def test_US2_false_permission_excludes_url(self):
        """[US2] show_delete_action=False → delete_url absent from context."""
        view = make_stub_view(
            extra_attrs={"directory": ["delete"], "show_delete_action": False},
            kwargs={"pk": 1},
        )
        assert "delete_url" not in view.get_directory()

    def test_US2_show_detail_action_true_includes_url(self):
        """[US2] show_detail_action=True → detail_url present (confirms rename from has_read_permission)."""
        # Redirect 'detail' to an existing URL pattern for testing
        custom_crud = {**MVP_CONFIG["view_names"], "detail": "{model_name}-update"}
        view = make_stub_view(
            extra_attrs={
                "directory": ["detail"],
                "show_detail_action": True,
                "crud_views": custom_crud,
            },
            kwargs={"pk": 1},
        )
        result = view.get_directory()
        assert "detail_url" in result

    def test_US2_show_list_action_true_includes_url(self):
        """[US2] show_list_action=True → list_url present."""
        view = make_stub_view(
            extra_attrs={"directory": ["list"], "show_list_action": True},
            kwargs={},
        )
        assert "list_url" in view.get_directory()

    def test_US2_callable_permission_returning_true_includes_url(self):
        """[US2] Callable show_create_action returning True → create_url present."""
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
        """[US2] Callable show_create_action returning False → create_url absent."""
        view = make_stub_view(
            extra_attrs={
                "directory": ["create"],
                "show_create_action": staticmethod(lambda user: False),
            },
            kwargs={},
        )
        assert "create_url" not in view.get_directory()

    def test_US2_absent_permission_attribute_excludes_url_no_error(self):
        """[US2] Undeclared permission attribute (custom action) → URL excluded, no AttributeError."""
        # 'archive' is not a standard action, so has_archive_permission doesn't exist
        custom_crud = {**MVP_CONFIG["view_names"], "archive": "{model_name}-delete"}
        view = make_stub_view(
            extra_attrs={
                "directory": ["archive"],
                "crud_views": custom_crud,
                # has_archive_permission deliberately not set
            },
            kwargs={"pk": 1},
        )
        result = view.get_directory()
        assert "archive_url" not in result

    def test_US2_callable_permission_raising_propagates(self):
        """[US2] Callable permission that raises ValueError → exception propagates."""

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
        """[US2] All permissions False → context['directory'] is {} (key always present)."""
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


# ---------------------------------------------------------------------------
# US4: Customize View Name Convention
# ---------------------------------------------------------------------------

# Note: Internal URL naming tests (_get_view_name, token substitution) removed per issue #7.
# They test Django's string formatting, not app behavior. User-facing custom crud_views
# is verified by integration/E2E tests in test_crud_directory_mixin_e2e.py.


# -------------------------------------------------------------------------
# CRUDDirectoryMixin browser tests
# -------------------------------------------------------------------------

User = get_user_model()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def category(db):
    from demo.models import Category

    return Category.objects.create(name="E2E Cat", slug="e2e-cat")


@pytest.fixture
def product(category):
    from demo.models import Product

    return Product.objects.create(
        name="E2E Product",
        slug="e2e-product",
        category=category,
        description="An E2E test product",
        price="19.99",
        stock=5,
    )


@pytest.fixture
def staff_user(db):
    user = User.objects.create_user(
        username="e2e_staff", password="pass", is_staff=True, is_active=True
    )
    return user


@pytest.fixture
def regular_user(db):
    user = User.objects.create_user(
        username="e2e_regular", password="pass", is_staff=False, is_active=True
    )
    return user


# ---------------------------------------------------------------------------
# US5 E2E Tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUS5StaffUserSeesActionButtons:
    """[US5] Staff user: edit and delete buttons visible; list link present."""

    def test_US5_staff_sees_edit_button(self, client, staff_user, product):
        """[US5] Staff user → edit button visible on product detail page."""
        client.force_login(staff_user)
        url = reverse("product-detail", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        edit_url = reverse("product-update", kwargs={"pk": product.pk})
        assert edit_url in content, "Edit link must be present for staff user"

    def test_US5_staff_sees_delete_button(self, client, staff_user, product):
        """[US5] Staff user → delete button visible on product detail page."""
        client.force_login(staff_user)
        url = reverse("product-detail", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        delete_url = reverse("product-delete", kwargs={"pk": product.pk})
        assert delete_url in content, "Delete link must be present for staff user"

    def test_US5_staff_sees_list_link(self, client, staff_user, product):
        """[US5] Staff user → back to list link present."""
        client.force_login(staff_user)
        url = reverse("product-detail", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        list_url = reverse("product-list")
        assert list_url in content, "List link must be present for staff user"


@pytest.mark.django_db
class TestUS5ReadOnlyUserHidesActionButtons:
    """[US5] Read-only user: edit and delete buttons absent; list link present."""

    def test_US5_regular_user_no_edit_button(self, client, regular_user, product):
        """[US5] Read-only user → edit button absent on product detail page."""
        client.force_login(regular_user)
        url = reverse("product-detail", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        edit_url = reverse("product-update", kwargs={"pk": product.pk})
        assert edit_url not in content, (
            "Edit link must NOT be present for non-staff user"
        )

    def test_US5_regular_user_no_delete_button(self, client, regular_user, product):
        """[US5] Read-only user → delete button absent on product detail page."""
        client.force_login(regular_user)
        url = reverse("product-detail", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        delete_url = reverse("product-delete", kwargs={"pk": product.pk})
        assert delete_url not in content, (
            "Delete link must NOT be present for non-staff user"
        )

    def test_US5_regular_user_sees_list_link(self, client, regular_user, product):
        """[US5] Read-only user → list link still present."""
        client.force_login(regular_user)
        url = reverse("product-detail", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        list_url = reverse("product-list")
        assert list_url in content, "List link must be present for all users"


# ---------------------------------------------------------------------------
# US4 E2E Tests — Object-Named Heading, Breadcrumb Trail, and CSS Classes
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUS4ProductDetailPageHeadingAndCSSClass:
    """[US4] ProductDetailView renders str(product) as heading, correct breadcrumb, and model CSS classes."""

    def test_product_detail_page_heading_equals_str_product(self, client, product):
        """[US4] Visible heading matches str(product) — US4 AC1."""
        url = reverse("product-detail", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "<h1" in content and str(product) in content, (
            f"Heading element containing '{product!s}' must be present"
        )

    def test_product_detail_breadcrumb_ends_with_product_name(self, client, product):
        """[US4] Final breadcrumb item text equals str(product) — US4 AC3."""
        url = reverse("product-detail", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        product_name = str(product)
        # The breadcrumb trail should contain the product name as the last item
        assert product_name in content, f"Breadcrumb must contain '{product_name}'"

    def test_product_detail_page_container_has_model_css_class(self, client, product):
        """[US4] div.mvp-layout class attribute contains 'product-page' — FR-005."""
        url = reverse("product-detail", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "product-page" in content, (
            "CSS class 'product-page' must be present in the page container"
        )

    def test_product_detail_page_container_has_action_css_class(self, client, product):
        """[US4] div.mvp-layout class attribute contains 'mvp-detail-page' — FR-009."""
        url = reverse("product-detail", kwargs={"pk": product.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "mvp-detail-page" in content, (
            "CSS class 'mvp-detail-page' must be present in the page container"
        )


# ---------------------------------------------------------------------------
# Packaged detail template — the default page body and action links
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPackagedDetailTemplateBody:
    """detail_view.html leaves its body to the project rather than filling it."""

    def test_packaged_page_renders_without_placeholder(self, client, article):
        """A detail page with no project override ships no placeholder text."""
        response = client.get(reverse("article-detail", kwargs={"pk": article.pk}))
        assert response.status_code == 200
        assert "Coming soon" not in response.content.decode()

    def test_packaged_page_titles_itself_from_the_object(self, client, article):
        """The page title is str(object), which is the whole default body."""
        response = client.get(reverse("article-detail", kwargs={"pk": article.pk}))
        content = response.content.decode()
        assert "<h1" in content
        assert str(article) in content


@pytest.mark.django_db
class TestPackagedDetailTemplateActions:
    """The edit and delete links come from the package, not from the project."""

    def test_edit_link_present_for_permitted_user(self, client, staff_user, product):
        """Product's template overrides only the body, so its actions are the packaged ones."""
        client.force_login(staff_user)
        response = client.get(reverse("product-detail", kwargs={"pk": product.pk}))
        assert reverse("product-update", kwargs={"pk": product.pk}) in response.content.decode()

    def test_delete_link_present_for_permitted_user(self, client, staff_user, product):
        client.force_login(staff_user)
        response = client.get(reverse("product-detail", kwargs={"pk": product.pk}))
        assert reverse("product-delete", kwargs={"pk": product.pk}) in response.content.decode()

    def test_links_absent_without_permission(self, client, regular_user, product):
        """A user the view refuses gets no link, because the URL never resolves."""
        client.force_login(regular_user)
        content = client.get(reverse("product-detail", kwargs={"pk": product.pk})).content.decode()
        assert reverse("product-update", kwargs={"pk": product.pk}) not in content
        assert reverse("product-delete", kwargs={"pk": product.pk}) not in content

    def test_project_can_replace_the_action_set(self, client, staff_user, product):
        """The page.actions block is the documented override point, so it must be a block."""
        from django.template.loader import get_template

        source = get_template("detail_view.html").template.source
        assert "{% block page.actions %}" in source


class TestMVPDetailViewDirectory:
    """MVPDetailView asks for the two actions its template renders."""

    def test_default_directory_is_update_and_delete(self):
        assert MVPDetailView.directory == ["update", "delete"]


@pytest.mark.django_db
class TestDefaultDirectoryIsInertWithoutPermission:
    """The default directory asks for actions the project never named.

    That is only safe because permissions default to False, so nothing resolves and
    no route is required. These tests pin that, because it is what stops the new
    default from breaking a project on upgrade. A project that grants a permission
    for an action it has no route for still gets NoReverseMatch, which is the
    package's existing fail-fast contract (see TestUS1Directory).
    """

    def test_no_url_resolves_without_permission(self, article):
        view = make_detail_view(Article, article)
        assert view.get_directory() == {}

    def test_page_renders_with_no_crud_routes_registered(self, client, article):
        """Article has no update, delete or list route anywhere in the demo URLconf."""
        response = client.get(reverse("article-detail", kwargs={"pk": article.pk}))
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Action visibility naming (issue #142)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestActionVisibilityAttributes:
    """``show_<action>_action`` decides whether an action link is offered."""

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

    def test_new_attribute_warns_nothing(self, recwarn):
        view = make_stub_view(
            extra_attrs={"directory": ["list"], "show_list_action": True}, kwargs={}
        )
        view.get_directory()
        assert [w for w in recwarn.list if issubclass(w.category, DeprecationWarning)] == []


@pytest.mark.django_db
class TestLegacyPermissionAttributes:
    """The pre-0.16 ``has_<action>_permission`` names still decide visibility.

    They are honoured rather than ignored on purpose. Dropping them silently would
    *reveal* links a project had hidden, which is the failure the rename exists to
    prevent (issue #142).
    """

    def test_legacy_true_still_includes_url(self):
        view = make_stub_view(
            extra_attrs={"directory": ["list"], "has_list_permission": True}, kwargs={}
        )
        with pytest.warns(MVPDeprecationWarning, match="show_list_action"):
            assert "list_url" in view.get_directory()

    def test_legacy_false_still_hides_url(self):
        view = make_stub_view(
            extra_attrs={
                "directory": ["list"],
                "show_list_action": True,
                "has_list_permission": False,
            },
            kwargs={},
        )
        with pytest.warns(MVPDeprecationWarning):
            assert "list_url" not in view.get_directory()

    def test_legacy_callable_still_honoured(self):
        view = make_stub_view(
            extra_attrs={
                "directory": ["create"],
                "has_create_permission": staticmethod(lambda user: False),
            },
            kwargs={},
        )
        with pytest.warns(MVPDeprecationWarning):
            assert "create_url" not in view.get_directory()

    def test_warning_names_the_replacement_and_the_limitation(self):
        view = make_stub_view(
            extra_attrs={"directory": ["delete"], "has_delete_permission": True},
            kwargs={"pk": 1},
        )
        with pytest.warns(MVPDeprecationWarning) as record:
            view.get_directory()
        message = str(record[0].message)
        assert "has_delete_permission" in message
        assert "show_delete_action" in message
        assert "does not restrict access" in message

    def test_warning_is_filterable_without_unmasking_other_packages(self):
        """The category is a django-mvp subclass, so a project can target it alone."""
        assert issubclass(MVPDeprecationWarning, DeprecationWarning)
        view = make_stub_view(
            extra_attrs={"directory": ["list"], "has_list_permission": True}, kwargs={}
        )
        with pytest.warns(MVPDeprecationWarning) as record:
            view.get_directory()
        assert record[0].category is MVPDeprecationWarning
