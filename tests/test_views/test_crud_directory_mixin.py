"""Tests for CRUDDirectoryMixin — US1, US2, US3, US4.

Each test is tagged with [USn] in its docstring to identify the user story it covers.
Run individual stories with: pytest -k US1, -k US2, etc.
"""

import pytest
from django.urls import NoReverseMatch, reverse

from demo.models import Product
from mvp.config import MVP_CONFIG
from mvp.views.detail import CRUDDirectoryMixin
from tests.conftest import make_stub_view as _make_stub_view


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
            extra_attrs={"directory": ["list"], "has_list_permission": True},
            kwargs={},
        )
        result = view.get_directory()
        assert "list_url" in result
        assert result["list_url"] == reverse("product-list")

    def test_US1_update_url_resolves_with_pk(self):
        """[US1] directory=['update'] + pk in kwargs + permission → update_url resolved."""
        view = make_stub_view(
            extra_attrs={"directory": ["update"], "has_update_permission": True},
            kwargs={"pk": 1},
        )
        result = view.get_directory()
        assert "update_url" in result
        assert result["update_url"] == reverse("product-update", kwargs={"pk": 1})

    def test_US1_object_action_without_kwargs_excluded(self):
        """[US1] directory=['update'] with no URL kwargs → update_url absent, no error."""
        view = make_stub_view(
            extra_attrs={"directory": ["update"], "has_update_permission": True},
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
        custom_crud = {**MVP_CONFIG["view_names"], "list": "nonexistent-{model_name}-list"}
        view = make_stub_view(
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
        custom_crud = {**MVP_CONFIG["view_names"], "create": "{model_name}-list"}
        view = make_stub_view(
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
        view = make_stub_view(
            extra_attrs={"directory": ["delete"], "has_delete_permission": False},
            kwargs={"pk": 1},
        )
        assert "delete_url" not in view.get_directory()

    def test_US2_has_detail_permission_true_includes_url(self):
        """[US2] has_detail_permission=True → detail_url present (confirms rename from has_read_permission)."""
        # Redirect 'detail' to an existing URL pattern for testing
        custom_crud = {**MVP_CONFIG["view_names"], "detail": "{model_name}-update"}
        view = make_stub_view(
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
        view = make_stub_view(
            extra_attrs={"directory": ["list"], "has_list_permission": True},
            kwargs={},
        )
        assert "list_url" in view.get_directory()

    def test_US2_callable_permission_returning_true_includes_url(self):
        """[US2] Callable has_create_permission returning True → create_url present."""
        # Use staticmethod so the callable is not wrapped as a bound method
        view = make_stub_view(
            extra_attrs={
                "directory": ["create"],
                "has_create_permission": staticmethod(lambda user: True),
            },
            kwargs={},
        )
        assert "create_url" in view.get_directory()

    def test_US2_callable_permission_returning_false_excludes_url(self):
        """[US2] Callable has_create_permission returning False → create_url absent."""
        view = make_stub_view(
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
            extra_attrs={"directory": ["list"], "has_list_permission": staticmethod(bad_perm)},
            kwargs={},
        )
        with pytest.raises(ValueError, match="permission check failed"):
            view.get_directory()

    def test_US2_all_permissions_false_directory_is_empty_dict(self):
        """[US2] All permissions False → context['directory'] is {} (key always present)."""
        view = make_stub_view(
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
# US4: Customize View Name Convention
# ---------------------------------------------------------------------------

# Note: Internal URL naming tests (_get_view_name, token substitution) removed per issue #7.
# They test Django's string formatting, not app behavior. User-facing custom crud_views
# is verified by integration/E2E tests in test_crud_directory_mixin_e2e.py.
