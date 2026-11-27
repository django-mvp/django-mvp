"""The breadcrumb trail fits the box it is in, in a real browser.

Which steps fold at which width is computed from measurements of the rendered
steps, so only a browser settles it. Each case loads a test-only page,
``/trail-test/<name>/``, that draws one trail in a box whose width the test sets.

Source: assets/js/breadcrumbs.js, mvp/templates/cotton/mvp/breadcrumbs/
"""

import pytest
from django.http import HttpResponse
from django.template import engines
from django.urls import path
from django_cotton.compiler_regex import CottonCompiler
from playwright.sync_api import expect

from demo import urls as demo_urls
from mvp.config import MVP_CONFIG
from tests.conftest import requires_browser, urlconf_of, wait_for_alpine
from tests.factories import ProductFactory

pytestmark = [pytest.mark.e2e, requires_browser]

DESKTOP = {"width": 1280, "height": 800}
PHONE = {"width": 390, "height": 844}

LABELS = ["Docs", "Guides", "Setup", "Install", "Linux"]

WITH_ICON = '<c-mvp.breadcrumbs :items="steps" id="trail" />'
STEPS = [
    {"text": "Docs", "href": "/docs/", "icon": "home"},
    {"text": "Guides", "href": "/docs/guides/"},
    {"text": "Setup", "href": "/docs/guides/setup/"},
    {"text": "Install", "href": "/docs/guides/setup/install/"},
    {"text": "Linux"},
]
WITHOUT_ICON = [{k: v for k, v in step.items() if k != "icon"} for step in STEPS]

FROM_A_TEMPLATE = """
<c-mvp.breadcrumbs id="trail">
  <c-mvp.breadcrumbs.item text="Docs" href="/docs/" />
  <c-mvp.breadcrumbs.item text="Guides" href="/docs/guides/" />
  <c-mvp.breadcrumbs.item text="Install" />
</c-mvp.breadcrumbs>
"""


def trail_page(request, name):
    """Draw one trail in a box, inside the shell so its script runs."""
    steps = WITHOUT_ICON if name == "plain" else STEPS
    markup = FROM_A_TEMPLATE if name == "template" else WITH_ICON
    source = (
        '{% extends "mvp/base.html" %}{% block content %}'
        f'<div id="box" style="width: 900px">{markup}</div>'
        "{% endblock %}"
    )
    template = engines["django"].from_string(CottonCompiler().process(source))
    return HttpResponse(template.render({"steps": steps}, request))


@pytest.fixture(autouse=True)
def trail_urls(settings, monkeypatch):
    monkeypatch.setitem(MVP_CONFIG, "icon_stylesheet", "")
    settings.ROOT_URLCONF = urlconf_of(
        path("trail-test/<str:name>/", trail_page),
        *demo_urls.urlpatterns,
    )


def open_trail(page, live_server, name="icon", viewport=DESKTOP):
    page.set_viewport_size(viewport)
    page.goto(f"{live_server.url}/trail-test/{name}/")
    wait_for_alpine(page)
    page.wait_for_selector("#trail.is-enhanced", state="attached")


def state_at(page, width):
    """The trail's layout once the box is ``width`` wide."""
    page.evaluate(f"document.getElementById('box').style.width = '{width}px'")
    page.evaluate(
        "() => new Promise(done => requestAnimationFrame(() =>"
        " requestAnimationFrame(done)))"
    )
    return page.evaluate("""
        () => {
          const trail = document.getElementById('trail');
          const steps = [...trail.querySelectorAll('li[data-mvp-crumb]')];
          const first = steps[0];
          return {
            shown: steps.filter(li => !li.hidden).map(li =>
              li.querySelector('.mvp-crumb-text').textContent),
            compact: first.classList.contains('is-compact'),
            tight: steps.some(li => li.classList.contains('is-tight')),
            fold: !trail.querySelector('[data-mvp-crumbs-fold]').hidden,
            overflow: trail.querySelector('ol').scrollWidth
              > trail.querySelector('ol').clientWidth + 1,
          };
        }
    """)


def sweep(page):
    """Every layout met while the box narrows from 900px to 60px."""
    return [(width, state_at(page, width)) for width in range(900, 40, -10)]


class TestTheLayoutChoice:
    def test_every_step_shows_where_there_is_room(self, page, live_server):
        open_trail(page, live_server)

        state = state_at(page, 900)

        assert state["shown"] == LABELS
        assert not state["fold"]

    def test_the_current_page_is_never_folded(self, page, live_server):
        open_trail(page, live_server)

        for width, state in sweep(page):
            assert state["shown"][-1] == "Linux", width

    def test_the_middle_folds_before_the_first_step_the_parent_and_the_current_page(
        self, page, live_server
    ):
        open_trail(page, live_server, "plain")

        layouts = [state["shown"] for _, state in sweep(page)]

        assert ["Docs", "Install", "Linux"] in layouts
        assert ["Docs", "Setup", "Install", "Linux"] in layouts

    def test_the_steps_fold_in_order_as_the_box_narrows(self, page, live_server):
        open_trail(page, live_server, "plain")

        counts = [len(state["shown"]) for _, state in sweep(page)]

        assert counts == sorted(counts, reverse=True)

    def test_the_steps_that_stay_never_overflow_the_box(self, page, live_server):
        open_trail(page, live_server)

        # Below about 8rem not even the menu and the current page fit.
        assert not [w for w, state in sweep(page) if state["overflow"] and w >= 120]

    def test_the_narrowest_layout_is_the_menu_and_the_current_page(
        self, page, live_server
    ):
        open_trail(page, live_server)

        state = state_at(page, 60)

        assert state["shown"] == ["Linux"]
        assert state["fold"]

    def test_a_box_wider_again_unfolds_the_steps(self, page, live_server):
        open_trail(page, live_server)
        state_at(page, 80)

        assert state_at(page, 900)["shown"] == LABELS

    def test_it_measures_its_box_and_not_the_window(self, page, live_server):
        open_trail(page, live_server, viewport={"width": 1600, "height": 800})

        assert state_at(page, 140)["fold"]


class TestTheIconOption:
    def test_the_first_step_shrinks_to_its_icon_before_it_folds(
        self, page, live_server
    ):
        open_trail(page, live_server)

        layouts = [state for _, state in sweep(page)]
        shrunk = [s for s in layouts if s["compact"]]

        assert shrunk
        assert all(s["shown"][0] == "Docs" for s in shrunk)
        assert layouts.index(shrunk[0]) < next(
            i for i, s in enumerate(layouts) if "Docs" not in s["shown"]
        )

    def test_a_shrunk_first_step_keeps_its_name_for_a_screen_reader(
        self, page, live_server
    ):
        open_trail(page, live_server)
        for width in range(900, 40, -10):
            if state_at(page, width)["compact"]:
                break

        link = page.locator("#trail li[data-mvp-crumb] >> nth=0").locator("a")

        assert link.locator(".mvp-crumb-text").text_content() == "Docs"
        assert (
            link.locator(".mvp-crumb-text").evaluate(
                "el => el.getBoundingClientRect().width"
            )
            <= 1
        )

    def test_a_trail_with_no_icon_never_shrinks_a_step_to_one(self, page, live_server):
        open_trail(page, live_server, "plain")

        assert not any(state["compact"] for _, state in sweep(page))


class TestTheMenu:
    def open_menu(self, page, live_server):
        open_trail(page, live_server, "plain")
        width = next(
            w
            for w, state in sweep(page)
            if state["shown"] == ["Docs", "Install", "Linux"]
        )
        state_at(page, width)
        page.locator("[data-mvp-crumbs-fold-button]").click()
        return page.locator("[data-mvp-crumbs-menu]")

    def test_it_lists_the_folded_steps_in_order_as_links(self, page, live_server):
        menu = self.open_menu(page, live_server)

        names = [text.strip() for text in menu.locator("li").all_inner_texts()]
        hrefs = menu.locator("a").evaluate_all("els => els.map(e => e.pathname)")

        assert names == ["Guides", "Setup"]
        assert hrefs == ["/docs/guides/", "/docs/guides/setup/"]

    def test_the_button_says_how_many_steps_it_holds(self, page, live_server):
        self.open_menu(page, live_server)

        button = page.locator("[data-mvp-crumbs-fold-button]")

        assert button.get_attribute("aria-label") == "Show 2 more levels"

    def test_it_takes_focus_and_closes_on_escape(self, page, live_server):
        menu = self.open_menu(page, live_server)

        expect(menu.locator("a").first).to_be_focused()
        page.keyboard.press("Escape")

        expect(menu).to_be_hidden()

    def test_a_folded_step_is_not_drawn_twice_for_the_markup_reader(
        self, page, live_server
    ):
        menu = self.open_menu(page, live_server)

        assert menu.locator("[itemprop]").count() == 0


class TestTheMarkupTheScriptLeaves:
    def test_the_current_page_keeps_aria_current_at_every_width(
        self, page, live_server
    ):
        open_trail(page, live_server)

        for width in (900, 300, 60):
            state_at(page, width)
            current = page.locator("#trail [aria-current='page']")
            assert current.text_content().strip() == "Linux", width
            expect(current).to_be_visible()

    def test_steps_from_an_items_list_are_numbered_from_one(self, page, live_server):
        open_trail(page, live_server)

        assert page.locator("#trail meta[itemprop='position']").evaluate_all(
            "metas => metas.map(m => m.content)"
        ) == ["1", "2", "3", "4", "5"]

    def test_steps_written_in_a_template_are_numbered_too(self, page, live_server):
        open_trail(page, live_server, "template")

        assert page.locator("#trail meta[itemprop='position']").evaluate_all(
            "metas => metas.map(m => m.content)"
        ) == ["1", "2", "3"]


class TestWithNoScript:
    def test_every_step_is_shown_and_the_fold_is_not(self, browser, live_server):
        context = browser.new_context(viewport=PHONE, java_script_enabled=False)
        page = context.new_page()
        page.goto(f"{live_server.url}/trail-test/icon/")

        steps = page.locator("#trail li[data-mvp-crumb]")
        texts = [text.strip() for text in steps.all_inner_texts()]
        fold = page.locator("#trail [data-mvp-crumbs-fold]")
        folds = fold.count()
        fold_shown = fold.is_visible()
        context.close()

        assert texts == LABELS
        assert folds == 1
        assert not fold_shown


class TestRightToLeft:
    def test_the_steps_run_from_the_right(self, page, live_server):
        open_trail(page, live_server)
        page.evaluate("document.documentElement.dir = 'rtl'")
        state_at(page, 900)

        boxes = page.locator("#trail li[data-mvp-crumb]").evaluate_all(
            "els => els.map(e => e.getBoundingClientRect().left)"
        )

        assert boxes == sorted(boxes, reverse=True)


@pytest.mark.django_db(transaction=True)
class TestTheHeaderTrail:
    def test_a_long_name_never_overflows_the_header_at_any_width(
        self, page, live_server
    ):
        product = ProductFactory(name="A product named at really quite some length")

        for viewport in (DESKTOP, PHONE, {"width": 320, "height": 700}):
            page.set_viewport_size(viewport)
            page.goto(f"{live_server.url}/products/{product.pk}/edit/")
            page.wait_for_selector(".mvp-header .mvp-crumbs.is-enhanced")
            fit = page.evaluate("""
                () => {
                  const ol = document.querySelector('.mvp-header .mvp-crumbs > ol');
                  return ol.scrollWidth <= ol.clientWidth + 1;
                }
            """)
            assert fit, viewport

    def test_the_current_page_is_still_named_on_a_phone(self, page, live_server):
        product = ProductFactory(name="A product named at really quite some length")
        page.set_viewport_size({"width": 320, "height": 700})

        page.goto(f"{live_server.url}/products/{product.pk}/edit/")
        page.wait_for_selector(".mvp-header .mvp-crumbs.is-enhanced")

        current = page.locator(".mvp-header .mvp-crumbs [aria-current='page']")
        expect(current).to_be_visible()
