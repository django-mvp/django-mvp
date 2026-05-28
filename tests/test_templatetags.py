"""
Tests for mvp templatetags: logo_url and icon_url.

Covers:
  T003 — logo_url default resolver (US1)
  T005 — icon_url default resolver (US2)
  T007 — custom resolver paths (US3)
  T008 — height argument forwarding (US4)
"""

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.template import Context, Template
from django.utils.safestring import SafeData

# ---------------------------------------------------------------------------
# Module-level callables used as custom resolvers in tests.
# Referenced by dotted import path via import_string, e.g.:
#   "tests.test_templatetags._custom_logo_resolver"
# ---------------------------------------------------------------------------


def _custom_logo_resolver(request, height, theme):
    """Deterministic URL — encodes height and theme so tests can assert both."""
    return f"/custom/logo/{theme}/{height}.svg"


def _custom_icon_resolver(request, height, theme):
    """Deterministic URL — encodes height and theme so tests can assert both."""
    return f"/custom/icon/{theme}/{height}.svg"


def _none_returning_resolver(request, height, theme):
    """Returns None — tag must output empty string."""
    return None


def _raising_resolver(request, height, theme):
    """Always raises — tag must output empty string silently."""
    raise RuntimeError("resolver error")


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

_CUSTOM_LOGO = "tests.test_templatetags._custom_logo_resolver"
_CUSTOM_ICON = "tests.test_templatetags._custom_icon_resolver"
_NONE_RESOLVER = "tests.test_templatetags._none_returning_resolver"
_RAISING_RESOLVER = "tests.test_templatetags._raising_resolver"
_BAD_IMPORT_PATH = "tests.test_templatetags.nonexistent_function_xyz_abc"


def _render(template_str, context_dict=None):
    """Render a template fragment with {% load mvp %} prepended."""
    t = Template(f"{{% load mvp %}}{template_str}")
    return t.render(Context(context_dict or {}))


# ---------------------------------------------------------------------------
# Phase 3 [US1]: logo_url default resolver — T003
# ---------------------------------------------------------------------------


class TestLogoUrlDefaultResolver:
    """logo_url zero-config: bundled default resolver returns logo.svg for all themes."""

    def test_light_theme_returns_logo_svg(self):
        result = _render('{% logo_url height=40 theme="light" %}')
        assert result.endswith("logo.svg")

    def test_dark_theme_falls_back_to_logo_svg(self):
        """FR-009/FR-010: No dark logo asset bundled — falls back to logo.svg."""
        result = _render('{% logo_url height=40 theme="dark" %}')
        assert result.endswith("logo.svg")

    def test_no_theme_arg_returns_logo_svg(self):
        """Default theme is 'light'; logo.svg returned without theme kwarg."""
        result = _render("{% logo_url height=40 %}")
        assert result.endswith("logo.svg")

    def test_unrecognised_theme_returns_logo_svg(self):
        result = _render('{% logo_url height=40 theme="ocean" %}')
        assert result.endswith("logo.svg")

    def test_without_request_in_context_does_not_raise(self):
        """SC-006: request absent from context — context.get('request') returns None."""
        result = _render("{% logo_url height=40 %}", context_dict={})
        assert result.endswith("logo.svg")


# ---------------------------------------------------------------------------
# Phase 4 [US2]: icon_url default resolver — T005
# ---------------------------------------------------------------------------


class TestIconUrlDefaultResolver:
    """icon_url zero-config: default resolver routes light/dark/fallback correctly."""

    def test_light_theme_returns_icon_light_svg(self):
        result = _render('{% icon_url height=32 theme="light" %}')
        assert result.endswith("icon_light.svg")

    def test_dark_theme_returns_icon_dark_svg(self):
        result = _render('{% icon_url height=32 theme="dark" %}')
        assert result.endswith("icon_dark.svg")

    def test_no_theme_arg_returns_icon_light_svg(self):
        """Default theme is 'light'."""
        result = _render("{% icon_url height=32 %}")
        assert result.endswith("icon_light.svg")

    def test_unrecognised_theme_returns_icon_svg_fallback(self):
        """FR-010: Unrecognised theme falls back to icon.svg."""
        result = _render('{% icon_url height=32 theme="ocean" %}')
        assert result.endswith("icon.svg")
        assert not result.endswith("icon_light.svg")
        assert not result.endswith("icon_dark.svg")

    def test_without_request_in_context_does_not_raise(self):
        """SC-006: request absent from context — tag renders normally."""
        result = _render("{% icon_url height=32 %}", context_dict={})
        assert result.endswith("icon_light.svg")


# ---------------------------------------------------------------------------
# Phase 5 [US3]: logo_url custom resolver — T007
# ---------------------------------------------------------------------------


class TestLogoUrlCustomResolver:
    """logo_url custom resolver: MVP_LOGO_RESOLVER overrides default."""

    def test_absent_resolver_setting_uses_default_logo(self):
        """FR-007/M3: MVP_LOGO_RESOLVER absent → default resolver; no ImproperlyConfigured."""
        result = _render("{% logo_url height=40 %}")
        assert result.endswith("logo.svg")

    def test_custom_resolver_is_called_with_correct_args(self, monkeypatch, rf):
        """Custom resolver receives (request, height, theme) with correct values."""
        monkeypatch.setattr("mvp.templatetags.mvp.MVP_LOGO_RESOLVER", _CUSTOM_LOGO)
        request = rf.get("/")
        result = _render('{% logo_url height=40 theme="dark" %}', {"request": request})
        # _custom_logo_resolver encodes height and theme in the URL
        assert result == "/custom/logo/dark/40.svg"

    def test_custom_resolver_return_value_is_rendered(self, monkeypatch):
        """Custom resolver return value appears verbatim in template output."""
        monkeypatch.setattr("mvp.templatetags.mvp.MVP_LOGO_RESOLVER", _CUSTOM_LOGO)
        result = _render('{% logo_url height=40 theme="light" %}')
        assert result == "/custom/logo/light/40.svg"

    def test_resolver_returning_none_renders_empty_string(self, monkeypatch):
        """Resolver returning None → tag outputs ''."""
        monkeypatch.setattr("mvp.templatetags.mvp.MVP_LOGO_RESOLVER", _NONE_RESOLVER)
        result = _render("{% logo_url height=40 %}")
        assert result == ""

    def test_resolver_raising_renders_empty_string_silently(self, monkeypatch):
        """Resolver raising exception → tag outputs '' with no re-raise."""
        monkeypatch.setattr("mvp.templatetags.mvp.MVP_LOGO_RESOLVER", _RAISING_RESOLVER)
        result = _render("{% logo_url height=40 %}")
        assert result == ""

    def test_bad_import_path_raises_improperly_configured(self, monkeypatch):
        """MVP_LOGO_RESOLVER set to non-existent path → ImproperlyConfigured on tag call."""
        monkeypatch.setattr("mvp.templatetags.mvp.MVP_LOGO_RESOLVER", _BAD_IMPORT_PATH)
        with pytest.raises(ImproperlyConfigured):
            _render("{% logo_url height=40 %}")

    def test_output_is_plain_str_not_safe_data(self, monkeypatch):
        """FR-017/M1: logo_url output is plain str, not SafeData (no mark_safe)."""
        monkeypatch.setattr("mvp.templatetags.mvp.MVP_LOGO_RESOLVER", _CUSTOM_LOGO)
        from mvp.templatetags.mvp import logo_url

        result = logo_url(Context({}), height=40, theme="light")
        assert isinstance(result, str)
        assert not isinstance(result, SafeData), "logo_url must not return SafeData"

    def test_both_tags_render_multiple_times_without_error(self, monkeypatch):
        """SC-004/M4: template calling logo_url and icon_url four times each renders ok."""
        monkeypatch.setattr("mvp.templatetags.mvp.MVP_LOGO_RESOLVER", _CUSTOM_LOGO)
        monkeypatch.setattr("mvp.templatetags.mvp.MVP_ICON_RESOLVER", _CUSTOM_ICON)
        template_str = (
            '{% logo_url height=40 %}{% logo_url height=40 theme="dark" %}'
            '{% logo_url height=32 %}{% logo_url height=32 theme="dark" %}'
            '{% icon_url height=32 %}{% icon_url height=32 theme="dark" %}'
            '{% icon_url height=32 %}{% icon_url height=32 theme="dark" %}'
        )
        result = _render(template_str)
        assert result != ""


# ---------------------------------------------------------------------------
# Phase 5 [US3]: icon_url custom resolver — T007
# ---------------------------------------------------------------------------


class TestIconUrlCustomResolver:
    """icon_url custom resolver: MVP_ICON_RESOLVER overrides default."""

    def test_absent_resolver_setting_uses_default_icon(self):
        """FR-007/M3: MVP_ICON_RESOLVER absent → default resolver; no ImproperlyConfigured."""
        result = _render('{% icon_url height=32 theme="light" %}')
        assert result.endswith("icon_light.svg")

    def test_custom_resolver_is_called_with_correct_args(self, monkeypatch, rf):
        """Custom resolver receives (request, height, theme) with correct values."""
        monkeypatch.setattr("mvp.templatetags.mvp.MVP_ICON_RESOLVER", _CUSTOM_ICON)
        request = rf.get("/")
        result = _render('{% icon_url height=32 theme="dark" %}', {"request": request})
        assert result == "/custom/icon/dark/32.svg"

    def test_custom_resolver_return_value_is_rendered(self, monkeypatch):
        """Custom resolver return value appears verbatim in template output."""
        monkeypatch.setattr("mvp.templatetags.mvp.MVP_ICON_RESOLVER", _CUSTOM_ICON)
        result = _render('{% icon_url height=32 theme="light" %}')
        assert result == "/custom/icon/light/32.svg"

    def test_resolver_returning_none_renders_empty_string(self, monkeypatch):
        """Resolver returning None → tag outputs ''."""
        monkeypatch.setattr("mvp.templatetags.mvp.MVP_ICON_RESOLVER", _NONE_RESOLVER)
        result = _render("{% icon_url height=32 %}")
        assert result == ""

    def test_resolver_raising_renders_empty_string_silently(self, monkeypatch):
        """Resolver raising exception → tag outputs '' with no re-raise."""
        monkeypatch.setattr("mvp.templatetags.mvp.MVP_ICON_RESOLVER", _RAISING_RESOLVER)
        result = _render("{% icon_url height=32 %}")
        assert result == ""

    def test_bad_import_path_raises_improperly_configured(self, monkeypatch):
        """MVP_ICON_RESOLVER set to non-existent path → ImproperlyConfigured on tag call."""
        monkeypatch.setattr("mvp.templatetags.mvp.MVP_ICON_RESOLVER", _BAD_IMPORT_PATH)
        with pytest.raises(ImproperlyConfigured):
            _render("{% icon_url height=32 %}")

    def test_output_is_plain_str_not_safe_data(self, monkeypatch):
        """FR-017/M1: icon_url output is plain str, not SafeData (no mark_safe)."""
        monkeypatch.setattr("mvp.templatetags.mvp.MVP_ICON_RESOLVER", _CUSTOM_ICON)
        from mvp.templatetags.mvp import icon_url

        result = icon_url(Context({}), height=32, theme="light")
        assert isinstance(result, str)
        assert not isinstance(result, SafeData), "icon_url must not return SafeData"


# ---------------------------------------------------------------------------
# Phase 6 [US4]: height argument forwarding — T008
# ---------------------------------------------------------------------------


class TestHeightForwarding:
    """Height value supplied in template is forwarded unchanged to the resolver."""

    def test_logo_url_forwards_height_40(self, monkeypatch):
        """`{% logo_url height=40 %}` → resolver receives height=40."""
        monkeypatch.setattr("mvp.templatetags.mvp.MVP_LOGO_RESOLVER", _CUSTOM_LOGO)
        result = _render("{% logo_url height=40 %}")
        # _custom_logo_resolver encodes height in path: /custom/logo/{theme}/{height}.svg
        assert "/40." in result

    def test_logo_url_forwards_height_100_and_dark_theme(self, monkeypatch):
        """`{% logo_url height=100 theme="dark" %}` → resolver receives height=100, theme='dark'."""
        monkeypatch.setattr("mvp.templatetags.mvp.MVP_LOGO_RESOLVER", _CUSTOM_LOGO)
        result = _render('{% logo_url height=100 theme="dark" %}')
        assert "/100." in result
        assert "dark" in result

    def test_icon_url_forwards_height_32(self, monkeypatch):
        """`{% icon_url height=32 %}` → resolver receives height=32."""
        monkeypatch.setattr("mvp.templatetags.mvp.MVP_ICON_RESOLVER", _CUSTOM_ICON)
        result = _render("{% icon_url height=32 %}")
        assert "/32." in result
