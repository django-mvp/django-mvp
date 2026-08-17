"""
Tests for mvp templatetags: logo_url and icon_url.

Covers:
  T003 — logo_url default resolver (US1)
  T005 — icon_url default resolver (US2)
  T007 — custom resolver paths (US3)
  T008 — height argument forwarding (US4)
"""

import re

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


def _patch_logo(monkeypatch, resolver):
    """Monkeypatch MVP_CONFIG['brand']['logo_resolver'] to *resolver*."""
    from mvp.config import MVP_CONFIG

    monkeypatch.setitem(MVP_CONFIG["brand"], "logo_resolver", resolver)


def _patch_icon(monkeypatch, resolver):
    """Monkeypatch MVP_CONFIG['brand']['icon_resolver'] to *resolver*."""
    from mvp.config import MVP_CONFIG

    monkeypatch.setitem(MVP_CONFIG["brand"], "icon_resolver", resolver)


# ---------------------------------------------------------------------------
# Phase 3 [US1]: logo_url default resolver — T003
# ---------------------------------------------------------------------------


class TestLogoUrlDefaultResolver:
    """logo_url zero-config: bundled default resolver routes light/dark/fallback."""

    def test_light_theme_returns_logo_svg(self):
        result = _render('{% logo_url height=40 theme="light" %}')
        assert result.endswith("logo.svg")

    def test_dark_theme_returns_logo_dark_svg(self):
        """FR-009: a dark logo asset is bundled, so dark resolves to it.

        This assertion is the inverse of the one it replaces. When this test was
        written the package shipped no dark lockup and the resolver's dark branch
        could only fall through; the brand delivery added one. The fallback that
        assertion was really covering is still covered, one test down, with the
        asset made absent explicitly instead of by accident of what ships.
        """
        result = _render('{% logo_url height=40 theme="dark" %}')
        assert result.endswith("logo_dark.svg")

    def test_dark_theme_falls_back_to_logo_svg_when_no_dark_asset(self, monkeypatch):
        """FR-010: a project shipping only one lockup gets it for every theme."""
        monkeypatch.setattr("mvp.utils.finders.find", lambda path: None)

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

    def test_light_theme_returns_icon_svg(self):
        result = _render('{% icon_url height=32 theme="light" %}')
        assert result.endswith("icon.svg")

    def test_dark_theme_returns_icon_dark_svg(self):
        result = _render('{% icon_url height=32 theme="dark" %}')
        assert result.endswith("icon_dark.svg")

    def test_no_theme_arg_returns_icon_svg(self):
        """Default theme is 'light'; falls back to icon.svg."""
        result = _render("{% icon_url height=32 %}")
        assert result.endswith("icon.svg")

    def test_unrecognised_theme_returns_icon_svg_fallback(self):
        """FR-010: Unrecognised theme falls back to icon.svg."""
        result = _render('{% icon_url height=32 theme="ocean" %}')
        assert result.endswith("icon.svg")
        assert not result.endswith("icon_light.svg")
        assert not result.endswith("icon_dark.svg")

    def test_without_request_in_context_does_not_raise(self):
        """SC-006: request absent from context — tag renders normally."""
        result = _render("{% icon_url height=32 %}", context_dict={})
        assert result.endswith("icon.svg")


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
        _patch_logo(monkeypatch, _CUSTOM_LOGO)
        request = rf.get("/")
        result = _render('{% logo_url height=40 theme="dark" %}', {"request": request})
        # _custom_logo_resolver encodes height and theme in the URL
        assert result == "/custom/logo/dark/40.svg"

    def test_custom_resolver_return_value_is_rendered(self, monkeypatch):
        """Custom resolver return value appears verbatim in template output."""
        _patch_logo(monkeypatch, _CUSTOM_LOGO)
        result = _render('{% logo_url height=40 theme="light" %}')
        assert result == "/custom/logo/light/40.svg"

    def test_resolver_returning_none_renders_empty_string(self, monkeypatch):
        """Resolver returning None → tag outputs ''."""
        _patch_logo(monkeypatch, _NONE_RESOLVER)
        result = _render("{% logo_url height=40 %}")
        assert result == ""

    def test_resolver_raising_renders_empty_string_silently(self, monkeypatch):
        """Resolver raising exception → tag outputs '' with no re-raise."""
        _patch_logo(monkeypatch, _RAISING_RESOLVER)
        result = _render("{% logo_url height=40 %}")
        assert result == ""

    def test_bad_import_path_raises_improperly_configured(self, monkeypatch):
        """MVP_LOGO_RESOLVER set to non-existent path → ImproperlyConfigured on tag call."""
        _patch_logo(monkeypatch, _BAD_IMPORT_PATH)
        with pytest.raises(ImproperlyConfigured):
            _render("{% logo_url height=40 %}")

    def test_output_is_plain_str_not_safe_data(self, monkeypatch):
        """FR-017/M1: logo_url output is plain str, not SafeData (no mark_safe)."""
        _patch_logo(monkeypatch, _CUSTOM_LOGO)
        from mvp.templatetags.mvp import logo_url

        result = logo_url(Context({}), height=40, theme="light")
        assert isinstance(result, str)
        assert not isinstance(result, SafeData), "logo_url must not return SafeData"

    def test_both_tags_render_multiple_times_without_error(self, monkeypatch):
        """SC-004/M4: template calling logo_url and icon_url four times each renders ok."""
        _patch_logo(monkeypatch, _CUSTOM_LOGO)
        from mvp.config import MVP_CONFIG

        monkeypatch.setitem(MVP_CONFIG["brand"], "icon_resolver", _CUSTOM_ICON)
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
        assert result.endswith("icon.svg")

    def test_custom_resolver_is_called_with_correct_args(self, monkeypatch, rf):
        """Custom resolver receives (request, height, theme) with correct values."""
        _patch_icon(monkeypatch, _CUSTOM_ICON)
        request = rf.get("/")
        result = _render('{% icon_url height=32 theme="dark" %}', {"request": request})
        assert result == "/custom/icon/dark/32.svg"

    def test_custom_resolver_return_value_is_rendered(self, monkeypatch):
        """Custom resolver return value appears verbatim in template output."""
        _patch_icon(monkeypatch, _CUSTOM_ICON)
        result = _render('{% icon_url height=32 theme="light" %}')
        assert result == "/custom/icon/light/32.svg"

    def test_resolver_returning_none_renders_empty_string(self, monkeypatch):
        """Resolver returning None → tag outputs ''."""
        _patch_icon(monkeypatch, _NONE_RESOLVER)
        result = _render("{% icon_url height=32 %}")
        assert result == ""

    def test_resolver_raising_renders_empty_string_silently(self, monkeypatch):
        """Resolver raising exception → tag outputs '' with no re-raise."""
        _patch_icon(monkeypatch, _RAISING_RESOLVER)
        result = _render("{% icon_url height=32 %}")
        assert result == ""

    def test_bad_import_path_raises_improperly_configured(self, monkeypatch):
        """MVP_ICON_RESOLVER set to non-existent path → ImproperlyConfigured on tag call."""
        _patch_icon(monkeypatch, _BAD_IMPORT_PATH)
        with pytest.raises(ImproperlyConfigured):
            _render("{% icon_url height=32 %}")

    def test_output_is_plain_str_not_safe_data(self, monkeypatch):
        """FR-017/M1: icon_url output is plain str, not SafeData (no mark_safe)."""
        _patch_icon(monkeypatch, _CUSTOM_ICON)
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
        _patch_logo(monkeypatch, _CUSTOM_LOGO)
        result = _render("{% logo_url height=40 %}")
        # _custom_logo_resolver encodes height in path: /custom/logo/{theme}/{height}.svg
        assert "/40." in result

    def test_logo_url_forwards_height_100_and_dark_theme(self, monkeypatch):
        """`{% logo_url height=100 theme="dark" %}` → resolver receives height=100, theme='dark'."""
        _patch_logo(monkeypatch, _CUSTOM_LOGO)
        result = _render('{% logo_url height=100 theme="dark" %}')
        assert "/100." in result
        assert "dark" in result

    def test_icon_url_forwards_height_32(self, monkeypatch):
        """`{% icon_url height=32 %}` → resolver receives height=32."""
        _patch_icon(monkeypatch, _CUSTOM_ICON)
        result = _render("{% icon_url height=32 %}")
        assert "/32." in result


# -------------------------------------------------------------------------
# Brand logo shell integration
# -------------------------------------------------------------------------


class TestColumnAlignment:
    """``column_alignment_class`` infers a column's alignment from the kind
    of model field behind it: leading for text, trailing for a numeric
    field, centred for boolean, and centred for a column with no resolvable
    field that is not orderable (an action column). Nothing at all when the
    table's data has no model, or when a column is unresolvable but still
    orderable — its kind cannot be determined (FR-017–FR-021, issue #256).
    Red before T024.
    """

    def _table_class(self):
        pytest.importorskip("django_tables2")
        import django_tables2 as tables

        from demo.models import Product

        class AlignmentTable(tables.Table):
            action = tables.Column(orderable=False, empty_values=())
            undetermined = tables.Column(empty_values=())

            class Meta:
                model = Product
                fields = ("name", "price", "stock", "rating", "is_featured")

        return AlignmentTable

    def _table(self):
        """An AlignmentTable over an (empty) Product queryset, so
        ``table.data.model`` resolves to Product."""
        from demo.models import Product

        return self._table_class()(Product.objects.none())

    def _tag(self):
        from mvp.templatetags.mvp import column_alignment_class

        return column_alignment_class

    @pytest.mark.django_db
    def test_text_field_is_leading(self):
        table = self._table()
        assert self._tag()(table.columns["name"], table) == "text-start"

    @pytest.mark.django_db
    def test_integer_field_is_trailing(self):
        table = self._table()
        assert self._tag()(table.columns["stock"], table) == "text-end"

    @pytest.mark.django_db
    def test_decimal_field_is_trailing(self):
        table = self._table()
        assert self._tag()(table.columns["price"], table) == "text-end"

    @pytest.mark.django_db
    def test_float_field_is_trailing(self, monkeypatch):
        """django-tables2 has no numeric column class of its own (research
        R2) — the model field is what distinguishes a number from text, so
        this drives the inference straight off a FloatField rather than
        relying on one of Product's own fields, none of which is a float."""
        from django.db import models

        field = models.FloatField()
        field.set_attributes_from_name("weight")
        monkeypatch.setattr(
            "django_tables2.utils.Accessor.get_field", lambda self, model: field
        )
        table = self._table()
        assert self._tag()(table.columns["name"], table) == "text-end"

    @pytest.mark.django_db
    def test_boolean_field_is_centred(self):
        table = self._table()
        assert self._tag()(table.columns["is_featured"], table) == "text-center"

    @pytest.mark.django_db
    def test_unresolvable_non_orderable_column_is_centred(self):
        """The action-column signal: no field behind it, and not orderable
        (research R2) — what a buttons column looks like."""
        table = self._table()
        assert self._tag()(table.columns["action"], table) == "text-center"

    @pytest.mark.django_db
    def test_unresolvable_orderable_column_gets_no_alignment(self):
        """No field behind it, but orderable — a plain unresolvable text
        column, not an action column. Kind cannot be determined (FR-018)."""
        table = self._table()
        assert self._tag()(table.columns["undetermined"], table) == ""

    def test_no_model_gets_no_alignment(self):
        """A table over non-queryset data has no model to resolve a field
        from (FR-018, FR-021)."""
        table = self._table_class()([{"name": "a", "price": "1"}])
        assert self._tag()(table.columns["name"], table) == ""


class TestBrandLogoShellIntegration:
    """The shell templates wire the brand logo onto a rendered page."""

    @pytest.mark.django_db
    def test_home_page_renders_brand_logo(self, client):
        """GET / renders a brand logo <img> pointing at the bundled logo asset."""
        html = client.get("/").content.decode()
        srcs = re.findall(r'<img[^>]*\bsrc="([^"]*)"', html)
        logo_srcs = [s for s in srcs if "logo.svg" in s]
        assert logo_srcs, f"No brand logo img rendered on the home page; imgs: {srcs}"

    @pytest.mark.django_db
    def test_home_page_has_no_broken_img_src(self, client):
        """No <img> renders with an empty src (which would be a broken image)."""
        html = client.get("/").content.decode()
        assert 'src=""' not in html, (
            "An <img> with an empty src rendered on the home page"
        )
