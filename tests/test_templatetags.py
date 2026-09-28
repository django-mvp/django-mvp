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


class TestLogoUrlDefaultResolver:
    def test_light_theme_returns_logo_svg(self):
        result = _render('{% logo_url height=40 theme="light" %}')
        assert result.endswith("logo.svg")

    def test_dark_theme_returns_logo_dark_svg(self):
        result = _render('{% logo_url height=40 theme="dark" %}')
        assert result.endswith("logo_dark.svg")

    def test_dark_theme_falls_back_to_logo_svg_when_no_dark_asset(self, monkeypatch):
        monkeypatch.setattr("mvp.utils.finders.find", lambda path: None)

        result = _render('{% logo_url height=40 theme="dark" %}')

        assert result.endswith("logo.svg")

    def test_no_theme_arg_returns_logo_svg(self):
        result = _render("{% logo_url height=40 %}")
        assert result.endswith("logo.svg")

    def test_unrecognised_theme_returns_logo_svg(self):
        result = _render('{% logo_url height=40 theme="ocean" %}')
        assert result.endswith("logo.svg")

    def test_without_request_in_context_does_not_raise(self):
        result = _render("{% logo_url height=40 %}", context_dict={})
        assert result.endswith("logo.svg")


class TestIconUrlDefaultResolver:
    def test_light_theme_returns_icon_svg(self):
        result = _render('{% icon_url height=32 theme="light" %}')
        assert result.endswith("icon.svg")

    def test_dark_theme_returns_icon_dark_svg(self):
        result = _render('{% icon_url height=32 theme="dark" %}')
        assert result.endswith("icon_dark.svg")

    def test_no_theme_arg_returns_icon_svg(self):
        result = _render("{% icon_url height=32 %}")
        assert result.endswith("icon.svg")

    def test_unrecognised_theme_returns_icon_svg_fallback(self):
        result = _render('{% icon_url height=32 theme="ocean" %}')
        assert result.endswith("icon.svg")
        assert not result.endswith("icon_light.svg")
        assert not result.endswith("icon_dark.svg")

    def test_without_request_in_context_does_not_raise(self):
        result = _render("{% icon_url height=32 %}", context_dict={})
        assert result.endswith("icon.svg")


class TestLogoUrlCustomResolver:
    def test_absent_resolver_setting_uses_default_logo(self):
        result = _render("{% logo_url height=40 %}")
        assert result.endswith("logo.svg")

    def test_custom_resolver_is_called_with_correct_args(self, monkeypatch, rf):
        _patch_logo(monkeypatch, _CUSTOM_LOGO)
        request = rf.get("/")
        result = _render('{% logo_url height=40 theme="dark" %}', {"request": request})
        # _custom_logo_resolver encodes height and theme in the URL
        assert result == "/custom/logo/dark/40.svg"

    def test_custom_resolver_return_value_is_rendered(self, monkeypatch):
        _patch_logo(monkeypatch, _CUSTOM_LOGO)
        result = _render('{% logo_url height=40 theme="light" %}')
        assert result == "/custom/logo/light/40.svg"

    def test_resolver_returning_none_renders_empty_string(self, monkeypatch):
        _patch_logo(monkeypatch, _NONE_RESOLVER)
        result = _render("{% logo_url height=40 %}")
        assert result == ""

    def test_resolver_raising_renders_empty_string_silently(self, monkeypatch):
        _patch_logo(monkeypatch, _RAISING_RESOLVER)
        result = _render("{% logo_url height=40 %}")
        assert result == ""

    def test_bad_import_path_raises_improperly_configured(self, monkeypatch):
        _patch_logo(monkeypatch, _BAD_IMPORT_PATH)
        with pytest.raises(ImproperlyConfigured):
            _render("{% logo_url height=40 %}")

    def test_output_is_plain_str_not_safe_data(self, monkeypatch):
        _patch_logo(monkeypatch, _CUSTOM_LOGO)
        from mvp.templatetags.mvp import logo_url

        result = logo_url(Context({}), height=40, theme="light")
        assert isinstance(result, str)
        assert not isinstance(result, SafeData), "logo_url must not return SafeData"

    def test_both_tags_render_multiple_times_without_error(self, monkeypatch):
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


class TestIconUrlCustomResolver:
    def test_absent_resolver_setting_uses_default_icon(self):
        result = _render('{% icon_url height=32 theme="light" %}')
        assert result.endswith("icon.svg")

    def test_custom_resolver_is_called_with_correct_args(self, monkeypatch, rf):
        _patch_icon(monkeypatch, _CUSTOM_ICON)
        request = rf.get("/")
        result = _render('{% icon_url height=32 theme="dark" %}', {"request": request})
        assert result == "/custom/icon/dark/32.svg"

    def test_custom_resolver_return_value_is_rendered(self, monkeypatch):
        _patch_icon(monkeypatch, _CUSTOM_ICON)
        result = _render('{% icon_url height=32 theme="light" %}')
        assert result == "/custom/icon/light/32.svg"

    def test_resolver_returning_none_renders_empty_string(self, monkeypatch):
        _patch_icon(monkeypatch, _NONE_RESOLVER)
        result = _render("{% icon_url height=32 %}")
        assert result == ""

    def test_resolver_raising_renders_empty_string_silently(self, monkeypatch):
        _patch_icon(monkeypatch, _RAISING_RESOLVER)
        result = _render("{% icon_url height=32 %}")
        assert result == ""

    def test_bad_import_path_raises_improperly_configured(self, monkeypatch):
        _patch_icon(monkeypatch, _BAD_IMPORT_PATH)
        with pytest.raises(ImproperlyConfigured):
            _render("{% icon_url height=32 %}")

    def test_output_is_plain_str_not_safe_data(self, monkeypatch):
        _patch_icon(monkeypatch, _CUSTOM_ICON)
        from mvp.templatetags.mvp import icon_url

        result = icon_url(Context({}), height=32, theme="light")
        assert isinstance(result, str)
        assert not isinstance(result, SafeData), "icon_url must not return SafeData"


class TestHeightForwarding:
    def test_logo_url_forwards_height_40(self, monkeypatch):
        _patch_logo(monkeypatch, _CUSTOM_LOGO)
        result = _render("{% logo_url height=40 %}")
        # _custom_logo_resolver encodes height in path: /custom/logo/{theme}/{height}.svg
        assert "/40." in result

    def test_logo_url_forwards_height_100_and_dark_theme(self, monkeypatch):
        _patch_logo(monkeypatch, _CUSTOM_LOGO)
        result = _render('{% logo_url height=100 theme="dark" %}')
        assert "/100." in result
        assert "dark" in result

    def test_icon_url_forwards_height_32(self, monkeypatch):
        _patch_icon(monkeypatch, _CUSTOM_ICON)
        result = _render("{% icon_url height=32 %}")
        assert "/32." in result


class TestColumnAlignment:
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
        table = self._table()
        assert self._tag()(table.columns["action"], table) == "text-center"

    @pytest.mark.django_db
    def test_unresolvable_orderable_column_gets_no_alignment(self):
        table = self._table()
        assert self._tag()(table.columns["undetermined"], table) == ""

    def test_no_model_gets_no_alignment(self):
        table = self._table_class()([{"name": "a", "price": "1"}])
        assert self._tag()(table.columns["name"], table) == ""


class TestBrandLogoShellIntegration:
    @pytest.mark.django_db
    def test_home_page_renders_brand_logo(self, client):
        html = client.get("/").content.decode()
        srcs = re.findall(r'<img[^>]*\bsrc="([^"]*)"', html)
        logo_srcs = [s for s in srcs if "logo.svg" in s]
        assert logo_srcs, f"No brand logo img rendered on the home page; imgs: {srcs}"

    @pytest.mark.django_db
    def test_home_page_has_no_broken_img_src(self, client):
        html = client.get("/").content.decode()
        assert 'src=""' not in html, (
            "An <img> with an empty src rendered on the home page"
        )


class TestAppIsInstalledFilter:
    def test_installed_app_is_true_inside_an_if(self):
        result = _render('{% if "mvp"|app_is_installed %}yes{% else %}no{% endif %}')
        assert result == "yes"

    def test_absent_app_is_false_inside_an_if(self):
        result = _render(
            '{% if "not_a_real_app_anyone_installed"|app_is_installed %}'
            "yes{% else %}no{% endif %}"
        )
        assert result == "no"


class TestRowHeaderColumns:
    def _table(self, declared=..., **meta):
        pytest.importorskip("django_tables2")
        import django_tables2 as tables

        attrs = {
            "icon": tables.Column(),
            "name": tables.Column(),
            "Meta": type(
                "Meta", (), {} if declared is ... else {"row_headers": declared}
            ),
        }
        table_class = type("RowHeaderTable", (tables.Table,), attrs)
        return table_class([{"icon": "i", "name": "a"}])

    def _tag(self):
        from mvp.templatetags.mvp import row_header_columns

        return row_header_columns

    def test_a_table_declaring_nothing_has_no_row_headers(self):
        assert self._tag()(self._table()) == ()

    def test_a_table_with_no_meta_at_all_has_no_row_headers(self):
        pytest.importorskip("django_tables2")
        import django_tables2 as tables

        class Bare(tables.Table):
            icon = tables.Column()

        assert self._tag()(Bare([{"icon": "i"}])) == ()

    def test_declared_names_are_returned_in_order(self):
        assert self._tag()(self._table(("name", "icon"))) == ("name", "icon")

    def test_a_single_name_may_be_given_as_a_string(self):
        assert self._tag()(self._table("icon")) == ("icon",)

    def test_a_list_is_accepted(self):
        assert self._tag()(self._table(["icon"])) == ("icon",)

    def test_an_unknown_name_is_refused(self):
        from django.core.exceptions import ImproperlyConfigured

        with pytest.raises(ImproperlyConfigured) as raised:
            self._tag()(self._table(("icon", "nonexistent")))
        message = str(raised.value)
        assert "nonexistent" in message
        assert "icon, name" in message
        assert message.index("nonexistent") < message.index("icon, name")

    def test_a_hidden_column_may_still_be_named(self):
        pytest.importorskip("django_tables2")
        import django_tables2 as tables

        class Hidden(tables.Table):
            icon = tables.Column(visible=False)
            name = tables.Column()

            class Meta:
                row_headers = ("icon",)

        assert self._tag()(Hidden([{"icon": "i", "name": "a"}])) == ("icon",)
