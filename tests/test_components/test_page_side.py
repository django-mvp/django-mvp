"""Tests for `<c-mvp.page.side>` (FS-042, FR-002 to FR-006).

The panel's landmark, its name and every option it takes are markup that a
project's own CSS and templates depend on (Article XIII), so each is asserted
on the rendered HTML. Where the panel sits in a column and how wide it is are
decided by eye and are not tested.

Sources are compiled through the Cotton compiler and invoked as component
tags, as in `test_container.py`.
"""

import pytest
from bs4 import BeautifulSoup
from django import template
from django.template.context import Context
from django.utils import translation
from django_cotton.compiler_regex import CottonCompiler

compiler = CottonCompiler()

BREAKPOINTS = ["lg", "xl", "2xl"]


def render(attrs='label="On this page"', body="<p>links</p>"):
    source = f"<c-mvp.page.side {attrs}>{body}</c-mvp.page.side>"
    html = template.Template(compiler.process(source)).render(Context())
    return BeautifulSoup(html, "html.parser")


def root(soup):
    return soup.find(class_="mvp-page-side")


def classes(soup):
    return " ".join(" ".join(el.get("class", [])) for el in soup.find_all(class_=True))


class TestSidePanelLandmark:
    def test_the_root_carries_the_id_and_the_aside_is_its_panel(self):
        soup = render('label="Filters" id="my-panel"')

        assert root(soup)["id"] == "my-panel"
        aside = root(soup).find("aside")
        assert aside["id"] == "my-panel-panel"

    def test_the_id_defaults_to_page_side(self):
        soup = render()

        assert root(soup)["id"] == "page-side"
        assert root(soup).find("aside")["id"] == "page-side-panel"

    @pytest.mark.parametrize("collapse", ["drawer", "stack"])
    def test_the_aside_is_named_by_an_h2_holding_the_label(self, collapse):
        soup = render(f'label="Filters for products" collapse="{collapse}"')

        aside = root(soup).find("aside")
        heading = soup.find(id=aside["aria-labelledby"])
        assert heading.name == "h2"
        assert heading.get_text(strip=True) == "Filters for products"

    @pytest.mark.parametrize("collapse", ["drawer", "stack"])
    def test_the_aside_is_a_tab_stop_in_both_collapse_modes(self, collapse):
        soup = render(f'label="Filters" collapse="{collapse}"')

        assert root(soup).find("aside")["tabindex"] == "0"

    def test_the_slot_is_inside_the_aside(self):
        soup = render(body='<a id="link" href="#x">x</a>')

        assert root(soup).find("aside").find(id="link") is not None


class TestSidePanelOptions:
    @pytest.mark.parametrize("width", ["sm", "md", "lg"])
    def test_width_lands_as_its_data_attribute(self, width):
        assert (
            root(render(f'label="x" width="{width}"'))["data-mvp-side-width"] == width
        )

    @pytest.mark.parametrize("bp", BREAKPOINTS)
    def test_breakpoint_lands_as_its_data_attribute_and_variant_classes(self, bp):
        soup = render(f'label="x" breakpoint="{bp}"')

        assert root(soup)["data-mvp-side-breakpoint"] == bp
        assert f"{bp}:mvp-page-side-wide" in root(soup)["class"]
        assert f"{bp}:drawer-open" in classes(soup).split()

    def test_the_breakpoint_defaults_to_xl(self):
        soup = render()

        assert root(soup)["data-mvp-side-breakpoint"] == "xl"
        assert "xl:mvp-page-side-wide" in root(soup)["class"]

    def test_no_breakpoint_writes_none_of_its_attribute_or_classes(self):
        soup = render('label="x" :breakpoint="False"')

        assert not root(soup).has_attr("data-mvp-side-breakpoint")
        written = classes(soup)
        assert "mvp-page-side-wide" not in written
        assert "drawer-open" not in written

    @pytest.mark.parametrize("collapse", ["drawer", "stack"])
    def test_collapse_lands_as_its_data_attribute(self, collapse):
        soup = render(f'label="x" collapse="{collapse}"')

        assert root(soup)["data-mvp-side-collapse"] == collapse

    @pytest.mark.parametrize("align", ["title", "content"])
    def test_align_lands_as_its_data_attribute(self, align):
        assert (
            root(render(f'label="x" align="{align}"'))["data-mvp-side-align"] == align
        )

    @pytest.mark.parametrize("position", ["start", "end"])
    def test_position_lands_as_its_data_attribute_and_the_drawer_side(self, position):
        soup = render(f'label="x" position="{position}"')

        assert root(soup)["data-mvp-side-position"] == position
        assert f"drawer-{position}" in classes(soup).split()

    def test_the_panel_is_sticky_by_default(self):
        assert root(render()).has_attr("data-mvp-side-sticky")

    def test_sticky_false_drops_the_attribute(self):
        assert not root(render('label="x" :sticky="False"')).has_attr(
            "data-mvp-side-sticky"
        )

    def test_class_reaches_the_root(self):
        assert "extra" in root(render('label="x" class="extra"'))["class"]


class TestStackedSidePanel:
    def test_draws_no_drawer_checkbox_or_close_button(self):
        soup = render('label="x" collapse="stack"')

        assert soup.find(class_="drawer") is None
        assert soup.find("input", type="checkbox") is None
        assert soup.find("button") is None

    def test_still_draws_the_aside_with_its_content(self):
        soup = render('label="x" collapse="stack"', body='<a id="link">x</a>')

        assert root(soup).find("aside").find(id="link") is not None


class TestDrawerSidePanel:
    def test_draws_a_checkbox_and_a_close_button(self):
        soup = render('label="x" collapse="drawer"')

        assert soup.find("input", type="checkbox") is not None
        assert soup.find("button", type="button") is not None

    def test_the_close_buttons_label_is_translated(self, monkeypatch):
        from django.utils.translation import trans_real

        def gettext(self, message):
            if message == "Close %(label)s":
                return "Schliessen: %(label)s"
            return message

        monkeypatch.setattr(trans_real.DjangoTranslation, "gettext", gettext)

        with translation.override("de"):
            soup = render('label="Filter"')

        assert soup.find("button")["aria-label"] == "Schliessen: Filter"


class TestDrawerConfiguration:
    def test_a_drawer_root_carries_its_id_and_the_breakpoint_in_rem(self):
        soup = render('label="x" id="filters" breakpoint="lg"')

        assert (
            root(soup)["x-data"] == "mvpPageSide({ id: 'filters', breakpointRem: 64 })"
        )

    @pytest.mark.parametrize(("bp", "rem"), [("lg", 64), ("xl", 80), ("2xl", 96)])
    def test_the_breakpoint_comes_from_the_shared_width_table(self, bp, rem):
        soup = render(f'label="x" breakpoint="{bp}"')

        assert f"breakpointRem: {rem} " in root(soup)["x-data"]

    def test_no_breakpoint_leaves_out_the_width(self):
        soup = render('label="x" id="filters" :breakpoint="False"')

        assert root(soup)["x-data"] == "mvpPageSide({ id: 'filters' })"

    def test_a_stacked_panel_carries_no_x_data(self):
        soup = render('label="x" collapse="stack"')

        assert not root(soup).has_attr("x-data")

    def test_the_root_holds_configuration_and_no_behaviour(self):
        root_el = root(render())

        assert not [name for name in root_el.attrs if name.startswith(("@", "x-on"))]


def render_toggle(attrs='text="Filters"'):
    source = f"<c-mvp.page.side.toggle {attrs} />"
    html = template.Template(compiler.process(source)).render(Context())
    return BeautifulSoup(html, "html.parser").find("button")


class TestSidePanelToggle:
    def test_it_is_a_button_that_does_not_submit(self):
        assert render_toggle()["type"] == "button"

    def test_it_names_the_panel_it_controls_and_starts_collapsed(self):
        button = render_toggle('text="Filters" for="filters"')

        assert button["aria-controls"] == "filters"
        assert button["aria-expanded"] == "false"

    def test_the_panel_defaults_to_page_side(self):
        assert render_toggle()["aria-controls"] == "page-side"

    def test_it_carries_its_text(self):
        assert "Contents" in render_toggle('text="Contents"').get_text()

    def test_it_draws_its_icon(self):
        assert (
            render_toggle('text="Filters" icon="list"').find("i", class_="bi")
            is not None
        )

    @pytest.mark.parametrize("count", [0, 3])
    def test_the_badge_shows_only_above_zero(self, count):
        badge = render_toggle(f'text="Filters" :count="{count}"').find(class_="badge")

        assert (badge is not None) is (count > 0)
        if count:
            assert badge.get_text(strip=True) == str(count)

    def test_no_count_draws_no_badge(self):
        assert render_toggle().find(class_="badge") is None

    def test_it_is_configured_with_the_panel_id_and_nothing_else(self):
        button = render_toggle('text="Filters" for="filters"')

        assert button["x-data"] == "mvpPageSideToggle('filters')"

    def test_extra_classes_reach_the_button(self):
        assert "extra" in render_toggle('text="Filters" class="extra"')["class"]
