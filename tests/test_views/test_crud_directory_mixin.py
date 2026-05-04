"""Tests for CRUDDirectoryMixin — US1, US2, US3, US4.

Each test is tagged with [USn] in its docstring to identify the user story it covers.
Run individual stories with: pytest -k US1, -k US2, etc.
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.urls import NoReverseMatch, reverse
from django.views.generic import TemplateView

from demo.models import Product
from mvp.config import MVP_DEFAULT_VIEW_NAMES
from mvp.views.detail import CRUDDirectoryMixin

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_view(extra_attrs=None, kwargs=None, user=None):
    """Return a configured CRUDDirectoryMixin instance with a fake GET request.

    Creates a throwaway concrete subclass of CRUDDirectoryMixin + TemplateView
    so Django's MRO works without requiring a real URL dispatch cycle.
    """
    rf = RequestFactory()
    request = rf.get("/")
    request.user = user or User()

    attrs = {"model": Product, **(extra_attrs or {})}
    view_cls = type("StubView", (CRUDDirectoryMixin, TemplateView), attrs)
    view = view_cls()
    view.request = request
    view.kwargs = kwargs or {}
    view.args = []
    return view


# ---------------------------------------------------------------------------
# US1: Declarative URL Resolution Without URL Wiring
# ---------------------------------------------------------------------------


class TestUS1GetUrlKwargs:
    """[US1] Unit tests for the get_url_kwargs() default implementation."""

    def test_US1_list_returns_empty_dict(self):
        """[US1] get_url_kwargs('list') returns {} — collection action needs no object."""
        view = make_view(kwargs={})
        assert view.get_url_kwargs("list") == {}

    def test_US1_create_returns_empty_dict(self):
        """[US1] get_url_kwargs('create') returns {} — collection action needs no object."""
        view = make_view(kwargs={})
        assert view.get_url_kwargs("create") == {}

    def test_US1_object_action_with_kwargs_returns_dict(self):
        """[US1] Object-level actions return dict(self.kwargs) when kwargs are present."""
        view = make_view(kwargs={"pk": 42})
        assert view.get_url_kwargs("detail") == {"pk": 42}
        assert view.get_url_kwargs("update") == {"pk": 42}
        assert view.get_url_kwargs("delete") == {"pk": 42}

    def test_US1_object_action_with_empty_kwargs_returns_none(self):
        """[US1] Object-level actions return None when self.kwargs is empty."""
        view = make_view(kwargs={})
        assert view.get_url_kwargs("detail") is None
        assert view.get_url_kwargs("update") is None
        assert view.get_url_kwargs("delete") is None

    def test_US1_custom_action_with_kwargs_returns_dict(self):
        """[US1] Custom action (not list/create) uses same fallback: dict(self.kwargs) or None."""
        view = make_view(kwargs={"pk": 7})
        assert view.get_url_kwargs("archive") == {"pk": 7}

    def test_US1_custom_action_with_empty_kwargs_returns_none(self):
        """[US1] Custom action with empty self.kwargs returns None."""
        view = make_view(kwargs={})
        assert view.get_url_kwargs("archive") is None


@pytest.mark.django_db
class TestUS1Directory:
    """[US1] Integration tests for get_directory() and get_context_data()."""

    def test_US1_empty_directory_context_key_always_present(self):
        """[US1] directory=[] → context always has 'directory' key as empty dict."""
        view = make_view(extra_attrs={"directory": []}, kwargs={})
        ctx = view.get_context_data()
        assert "directory" in ctx
        assert ctx["directory"] == {}

    def test_US1_list_url_resolves_for_permitted_view(self):
        """[US1] directory=['list'] + permission=True → list_url in directory dict."""
        view = make_view(
            extra_attrs={"directory": ["list"], "has_list_permission": True},
            kwargs={},
        )
        result = view.get_directory()
        assert "list_url" in result
        assert result["list_url"] == reverse("product-list")

    def test_US1_update_url_resolves_with_pk(self):
        """[US1] directory=['update'] + pk in kwargs + permission → update_url resolved."""
        view = make_view(
            extra_attrs={"directory": ["update"], "has_update_permission": True},
            kwargs={"pk": 1},
        )
        result = view.get_directory()
        assert "update_url" in result
        assert result["update_url"] == reverse("product-update", kwargs={"pk": 1})

    def test_US1_object_action_without_kwargs_excluded(self):
        """[US1] directory=['update'] with no URL kwargs → update_url absent, no error."""
        view = make_view(
            extra_attrs={"directory": ["update"], "has_update_permission": True},
            kwargs={},
        )
        result = view.get_directory()
        assert "update_url" not in result

    def test_US1_invalid_action_raises_value_error(self):
        """[US1] Action not in crud_views → ValueError with action name in message."""
        # Requires non-empty kwargs so get_url_kwargs doesn't return None early
        view = make_view(
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
        custom_crud = {**MVP_DEFAULT_VIEW_NAMES, "list": "nonexistent-{model_name}-list"}
        view = make_view(
            extra_attrs={
                "directory": ["list"],
                "has_list_permission": True,
                "crud_views": custom_crud,
            },
            kwargs={},
        )
        with pytest.raises(NoReverseMatch):
            view.get_directory()

    def test_US1_two_actions_resolving_same_url_both_keys_present(self):
        """[US1] Two actions that resolve to the same URL → both {action}_url keys present."""
        # Point 'create' to 'product-list' (same URL as 'list')
        custom_crud = {**MVP_DEFAULT_VIEW_NAMES, "create": "{model_name}-list"}
        view = make_view(
            extra_attrs={
                "directory": ["list", "create"],
                "has_list_permission": True,
                "has_create_permission": True,
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
        """[US2] has_delete_permission=False → delete_url absent from context."""
        view = make_view(
            extra_attrs={"directory": ["delete"], "has_delete_permission": False},
            kwargs={"pk": 1},
        )
        assert "delete_url" not in view.get_directory()

    def test_US2_has_detail_permission_true_includes_url(self):
        """[US2] has_detail_permission=True → detail_url present (confirms rename from has_read_permission)."""
        # Redirect 'detail' to an existing URL pattern for testing
        custom_crud = {**MVP_DEFAULT_VIEW_NAMES, "detail": "{model_name}-update"}
        view = make_view(
            extra_attrs={
                "directory": ["detail"],
                "has_detail_permission": True,
                "crud_views": custom_crud,
            },
            kwargs={"pk": 1},
        )
        result = view.get_directory()
        assert "detail_url" in result

    def test_US2_has_list_permission_true_includes_url(self):
        """[US2] has_list_permission=True → list_url present."""
        view = make_view(
            extra_attrs={"directory": ["list"], "has_list_permission": True},
            kwargs={},
        )
        assert "list_url" in view.get_directory()

    def test_US2_callable_permission_returning_true_includes_url(self):
        """[US2] Callable has_create_permission returning True → create_url present."""
        # Use staticmethod so the callable is not wrapped as a bound method
        view = make_view(
            extra_attrs={
                "directory": ["create"],
                "has_create_permission": staticmethod(lambda user: True),
            },
            kwargs={},
        )
        assert "create_url" in view.get_directory()

    def test_US2_callable_permission_returning_false_excludes_url(self):
        """[US2] Callable has_create_permission returning False → create_url absent."""
        view = make_view(
            extra_attrs={
                "directory": ["create"],
                "has_create_permission": staticmethod(lambda user: False),
            },
            kwargs={},
        )
        assert "create_url" not in view.get_directory()

    def test_US2_absent_permission_attribute_excludes_url_no_error(self):
        """[US2] Undeclared permission attribute (custom action) → URL excluded, no AttributeError."""
        # 'archive' is not a standard action, so has_archive_permission doesn't exist
        custom_crud = {**MVP_DEFAULT_VIEW_NAMES, "archive": "{model_name}-delete"}
        view = make_view(
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

        view = make_view(
            extra_attrs={"directory": ["list"], "has_list_permission": staticmethod(bad_perm)},
            kwargs={},
        )
        with pytest.raises(ValueError, match="permission check failed"):
            view.get_directory()

    def test_US2_all_permissions_false_directory_is_empty_dict(self):
        """[US2] All permissions False → context['directory'] is {} (key always present)."""
        view = make_view(
            extra_attrs={
                "directory": ["list", "create", "update", "delete"],
                "has_list_permission": False,
                "has_create_permission": False,
                "has_update_permission": False,
                "has_delete_permission": False,
            },
            kwargs={"pk": 1},
        )
        ctx = view.get_context_data()
        assert "directory" in ctx
        assert ctx["directory"] == {}


# ---------------------------------------------------------------------------
# US3: Override URL Kwargs for Nested Resource URLs
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUS3NestedKwargs:
    """[US3] Tests for overriding get_url_kwargs() for nested URL patterns."""

    def test_US3_override_returns_correct_kwargs_per_action(self):
        """[US3] Override get_url_kwargs → correct kwargs per action, URLs resolve."""

        class NestedView(CRUDDirectoryMixin, TemplateView):
            model = Product
            directory = ["list", "update"]
            has_list_permission = True
            has_update_permission = True

            def get_url_kwargs(self, action):
                if action in {"list", "create"}:
                    return {}
                pk = self.kwargs.get("pk")
                if pk is None:
                    return None
                return {"pk": pk}

        rf = RequestFactory()
        view = NestedView()
        view.request = rf.get("/")
        view.request.user = User()
        view.kwargs = {"pk": 1}
        view.args = []

        result = view.get_directory()
        assert "list_url" in result
        assert "update_url" in result
        assert result["list_url"] == reverse("product-list")
        assert result["update_url"] == reverse("product-update", kwargs={"pk": 1})

    def test_US3_get_url_kwargs_returning_none_silently_excludes(self):
        """[US3] get_url_kwargs returning None → action excluded, no NoReverseMatch."""

        class AlwaysNoneView(CRUDDirectoryMixin, TemplateView):
            model = Product
            directory = ["update"]
            has_update_permission = True

            def get_url_kwargs(self, action):
                return None

        rf = RequestFactory()
        view = AlwaysNoneView()
        view.request = rf.get("/")
        view.request.user = User()
        view.kwargs = {}
        view.args = []

        result = view.get_directory()
        assert "update_url" not in result

    def test_US3_default_list_kwargs_resolves_flat_url(self):
        """[US3] Default get_url_kwargs('list') returns {} → flat list URL resolves correctly."""
        view = make_view(
            extra_attrs={"directory": ["list"], "has_list_permission": True},
            kwargs={},
        )
        result = view.get_directory()
        assert "list_url" in result

    def test_US3_custom_action_with_no_kwargs_excluded_no_error(self):
        """[US3] Custom action with empty self.kwargs → get_url_kwargs returns None → absent."""
        custom_crud = {**MVP_DEFAULT_VIEW_NAMES, "archive": "{model_name}-delete"}
        view = make_view(
            extra_attrs={
                "directory": ["archive"],
                "has_archive_permission": True,
                "crud_views": custom_crud,
            },
            kwargs={},  # empty — get_url_kwargs("archive") returns None
        )
        result = view.get_directory()
        assert "archive_url" not in result


# ---------------------------------------------------------------------------
# US4: Customize View Name Convention
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUS4CustomCrudViews:
    """[US4] Tests for custom crud_views URL name mapping."""

    def test_US4_custom_crud_views_resolves_using_custom_names(self):
        """[US4] Custom crud_views with non-default name pattern → URLs use custom names."""
        # Remap 'list' to 'product-delete' URL (which accepts no kwargs)
        # In practice, remapping to the delete URL of a product is artificial,
        # but it proves the custom mapping is used instead of the default.
        custom_crud = {**MVP_DEFAULT_VIEW_NAMES, "list": "{model_name}-list"}
        view = make_view(
            extra_attrs={
                "directory": ["list"],
                "has_list_permission": True,
                "crud_views": custom_crud,
            },
            kwargs={},
        )
        result = view.get_directory()
        assert "list_url" in result
        assert result["list_url"] == reverse("product-list")

    def test_US4_model_name_token_substituted(self):
        """[US4] {model_name} token substituted with model_meta.model_name."""
        view = make_view(kwargs={})
        view_name = view._get_view_name("list")
        assert "product" in view_name

    def test_US4_app_name_token_substituted(self):
        """[US4] Default crud_views 'list' template → resolves to '{model_name}-list'."""
        view = make_view(kwargs={})
        view_name = view._get_view_name("list")
        assert view_name == "product-list"

    def test_US4_action_not_in_custom_crud_views_raises_value_error(self):
        """[US4] Action in directory not present in custom crud_views → ValueError."""
        custom_crud = {"list": "{model_name}-list"}  # only 'list' defined
        view = make_view(
            extra_attrs={
                "directory": ["update"],
                "has_update_permission": True,
                "crud_views": custom_crud,
            },
            kwargs={"pk": 1},
        )
        with pytest.raises(ValueError, match="update"):
            view.get_directory()

    def test_US4_custom_pattern_with_app_name_token(self):
        """[US4] {app_name} token in custom pattern substituted with model app_label."""
        custom_crud = {**MVP_DEFAULT_VIEW_NAMES, "list": "{model_name}-list"}
        view = make_view(
            extra_attrs={"crud_views": custom_crud},
            kwargs={},
        )
        # Product model is in 'demo' app; app_name token available for custom patterns
        assert view.model_meta.app_label == "demo"
        view_name = view._get_view_name("list")
        assert view_name == "product-list"
