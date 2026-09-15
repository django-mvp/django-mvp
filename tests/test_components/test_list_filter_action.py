"""Tests for the <c-page.list.actions.filter> component's applied-filter badge.

The badge is a daisyUI ``indicator-item`` (issue #287): positioned outside its
own box by design — half above the top edge, at ``z-index: 1``. That is
invisible on an ordinary list page, which has a breadcrumb row and vertical
padding between the action row and the app header above it. It is not
invisible on a table view: ``table_view.html`` spends no vertical budget above
its action bar, so the badge's top half is drawn behind the header, which is
``position: sticky; top: 0; z-index: 10`` with a backdrop filter.

``mvp/tailwind/base.css`` raises the badge's ``z-index`` above the header's,
scoped to ``.mvp-page-fill`` — the layout a table view renders inside, and the
one layout whose own body never scrolls the window. Nothing inside a filled
page is ever carried toward the header the way ordinary page content is, so
that scope is exactly the set of pages where beating the header cannot also
reintroduce the case an unscoped z-index bump would cause: a badge riding
above the header as an ordinary, scrolling page passes underneath it.
"""

import re
from pathlib import Path

import pytest

import mvp
from mvp.fixtures import _beautiful_soup

MVP_ROOT = Path(next(iter(mvp.__path__))).resolve()
BASE_CSS = MVP_ROOT / "tailwind" / "base.css"
HEADER_TEMPLATE = MVP_ROOT / "templates" / "cotton" / "app" / "header" / "index.html"


def _filtered_action_view():
    """A list view composing the list mixin with django-filter's FilterView,
    rendering the filter action's own template in isolation."""
    pytest.importorskip("django_filters")
    from django_filters.views import FilterView

    from demo.models import Product
    from mvp.views.list import MVPListViewMixin

    class ComposedProductView(MVPListViewMixin, FilterView):
        model = Product
        filterset_fields = ["name", "price"]
        search_fields = ["name"]
        template_name = "cotton/page/list/actions/filter.html"

    return ComposedProductView


def _render_action(rf, params=None):
    view = _filtered_action_view()()
    view.setup(rf.get("/", params or {}))
    return view.get(view.request).render().content.decode()


class TestTheOverrideBeatsTheHeader:
    """The stylesheet rule this fix depends on, checked against the source
    preset rather than the built artifact: Article XV's stylesheet build is
    non-deterministic, so only the source is a stable thing to assert against.
    """

    def test_the_badges_z_index_override_outranks_the_headers(self):
        css = BASE_CSS.read_text(encoding="utf-8")
        override = re.search(
            r"\.mvp-page-fill \.indicator-item\s*\{\s*z-index:\s*(\d+)", css
        )
        assert override is not None, (
            "no z-index override for .mvp-page-fill .indicator-item in "
            "mvp/tailwind/base.css"
        )
        badge_z = int(override.group(1))

        header_html = HEADER_TEMPLATE.read_text(encoding="utf-8")
        header_class = re.search(r"\bz-(\d+)\b", header_html)
        assert header_class is not None, (
            "the header's own z-index utility class moved out of "
            "cotton/app/header/index.html"
        )
        header_z = int(header_class.group(1))

        assert badge_z > header_z, (
            f"the override (z-index: {badge_z}) no longer outranks the "
            f"header (z-index: {header_z})"
        )


class TestFilterActionButtonSize:
    """[#328] The trigger and its modal both use the `size` attribute
    `c-button` declares, not the undeclared `small`/`large` the templates used
    to pass — those forward straight through as bare, invalid HTML attributes
    and change nothing about the rendered size."""

    @pytest.mark.django_db
    def test_the_trigger_button_is_small(self, rf):
        html = _render_action(rf, {"name": "Widget", "price": "9.99"})
        soup = _beautiful_soup()(html, "html.parser")
        trigger = soup.find(class_="indicator").find("button")
        assert "btn-sm" in trigger.get("class", [])
        assert not trigger.has_attr("small")

    @pytest.mark.django_db
    def test_the_modal_apply_button_is_large(self, rf):
        html = _render_action(rf, {"name": "Widget", "price": "9.99"})
        soup = _beautiful_soup()(html, "html.parser")
        apply_button = soup.find("button", attrs={"form": "filterForm"})
        assert apply_button is not None
        assert "btn-lg" in apply_button.get("class", [])
        assert not apply_button.has_attr("large")

    @pytest.mark.django_db
    def test_no_element_carries_a_bare_small_or_large_attribute(self, rf):
        html = _render_action(rf, {"name": "Widget", "price": "9.99"})
        soup = _beautiful_soup()(html, "html.parser")
        for element in soup.find_all():
            assert not element.has_attr("small"), element
            assert not element.has_attr("large"), element


class TestAppliedFilterCount:
    """The action's own markup: unchanged in shape from before this fix — the
    badge is still a sibling of the button, not drawn inside it. The fix lives
    entirely in the stylesheet, scoped by ancestor, so nothing about this
    component's own output should move."""

    @pytest.mark.django_db
    def test_the_badge_is_an_indicator_item_beside_the_button(self, rf):
        soup = _beautiful_soup()(
            _render_action(rf, {"name": "Widget", "price": "9.99"}), "html.parser"
        )
        button = soup.find("button")
        assert button is not None

        badge = soup.find(class_="indicator-item")
        assert badge is not None, "no applied-filter badge was drawn"
        assert badge.get_text(strip=True) == "2"
        assert badge.find_parent("button") is None, (
            "the badge moved inside the button — the stylesheet fix expects "
            "it to stay a sibling"
        )

    @pytest.mark.django_db
    def test_no_badge_is_drawn_when_no_filter_is_applied(self, rf):
        soup = _beautiful_soup()(_render_action(rf), "html.parser")
        assert soup.find("button") is not None
        assert soup.find(class_="indicator-item") is None


class TestAppliedFilterCountOnATableView:
    """[#287] The reported page, end to end: the badge that needs the
    stylesheet override is actually reachable by the selector that raises it.
    """

    @pytest.mark.django_db
    def test_the_badge_sits_inside_the_filled_page_the_override_targets(
        self, rf, product
    ):
        pytest.importorskip("django_filters")
        pytest.importorskip("django_tables2")
        from demo.views import DataTablesView

        view = DataTablesView()
        view.setup(rf.get("/", {"name": "Widget", "status": "active"}))
        response = view.get(view.request)
        response.render()
        soup = _beautiful_soup()(response.content.decode(), "html.parser")

        badge = soup.find(class_="indicator-item")
        assert badge is not None, "no applied-filter badge on the table view"
        filled_page = badge.find_parent(class_="mvp-page-fill")
        assert filled_page is not None, (
            ".mvp-page-fill .indicator-item cannot reach this badge — the "
            "override does not apply here"
        )


class TestAppliedFilterCountOnAnOrdinaryListView:
    """The override's scoping only matters if it is genuinely narrower than
    'everywhere'. An ordinary list page (not a table view) never marks
    itself `.mvp-page-fill`, so its badge is exactly where it always was and
    the override does not reach it — which is the point: that page already
    has room for the badge, and reaching it anyway is what would let the
    badge ride above the header while the page scrolls underneath it."""

    @pytest.mark.django_db
    def test_the_badge_is_not_inside_a_filled_page(self, rf, product):
        pytest.importorskip("django_filters")
        from django_filters.views import FilterView

        from demo.models import Product
        from mvp.views.list import MVPListViewMixin

        class ComposedProductView(MVPListViewMixin, FilterView):
            model = Product
            filterset_fields = ["name", "price"]
            search_fields = ["name"]

        view = ComposedProductView()
        view.setup(rf.get("/", {"name": "Widget"}))
        response = view.get(view.request)
        response.render()
        soup = _beautiful_soup()(response.content.decode(), "html.parser")

        badge = soup.find(class_="indicator-item")
        assert badge is not None, "no applied-filter badge on the list view"
        assert badge.find_parent(class_="mvp-page-fill") is None, (
            "an ordinary list page should not render .mvp-page-fill"
        )
