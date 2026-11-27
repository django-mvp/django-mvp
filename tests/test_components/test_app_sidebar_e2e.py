"""The icon rail stays reachable when the window is shorter than the menu (issue #563).

The rail is the sidebar's own scroll box once it is taller than the window, so
the window here is short enough that the demo menu overflows it.
"""

import pytest

from tests.conftest import requires_browser

pytestmark = [pytest.mark.e2e, requires_browser]

PAGE = "/layout/full-page/"


@pytest.fixture
def icon_rail(page, live_server, monkeypatch):
    """The demo page with ``collapse: icons``, collapsed to the rail (issue #563).

    The rail is the sidebar's own scroll box once it is taller than the window,
    so the window is short enough that the demo menu overflows it.
    """
    from mvp.config import MVP_CONFIG

    monkeypatch.setitem(MVP_CONFIG["layout"]["sidebar"], "collapse", "icons")
    page.set_viewport_size({"width": 1440, "height": 300})
    page.add_init_script("localStorage.setItem('mvp-app-drawer-open', 'false')")
    page.goto(f"{live_server.url}{PAGE}")
    # Let the rail's width transition finish before anything is measured.
    page.wait_for_function(
        "document.querySelector('.mvp-sidebar').getBoundingClientRect().width === 64"
    )
    return page


def can_point_at(page, selector):
    """Return whether the centre of an element can be pointed at.

    A box clipped by a scroll container is still laid out, but nothing in the
    clipped part can be hit, so this is what tells drawn from cut off.
    """
    return page.evaluate(
        """(selector) => {
          const el = document.querySelector(selector);
          const r = el.getBoundingClientRect();
          const hit = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
          return el.contains(hit);
        }""",
        selector,
    )


class TestTheIconRailFitsTheWindow:
    def test_the_last_item_can_be_reached(self, icon_rail):
        last = ".mvp-sidebar nav > ul > li:last-child > :is(a, details > summary)"
        icon_rail.locator(last).scroll_into_view_if_needed()

        assert icon_rail.evaluate("window.scrollY") == 0
        assert can_point_at(icon_rail, last)

    def test_a_tooltip_shows_beside_the_rail_after_it_scrolls(self, icon_rail):
        item = ".mvp-sidebar nav > ul > li:last-child > a[data-tip]"
        icon_rail.locator(item).scroll_into_view_if_needed()
        icon_rail.hover(item)
        icon_rail.wait_for_function(
            f"getComputedStyle(document.querySelector('{item}'), '::before').opacity === '1'"
        )

        tip = icon_rail.evaluate(
            """(selector) => {
              const el = document.querySelector(selector);
              const item = el.getBoundingClientRect();
              const before = getComputedStyle(el, '::before');
              return {
                position: before.position,
                left: parseFloat(before.left),
                top: parseFloat(before.top),
                railRight: document.querySelector('.mvp-sidebar').getBoundingClientRect().right,
                itemCentre: item.top + item.height / 2,
              };
            }""",
            item,
        )

        # Drawn against the window, so it is outside the rail's scroll box and
        # nothing in it is clipped. The arrow and label are centred on the item.
        assert tip["position"] == "fixed"
        assert tip["left"] >= tip["railRight"]
        assert tip["top"] == pytest.approx(tip["itemCentre"], abs=1)

    def test_a_group_opens_beside_the_rail_after_it_scrolls(self, icon_rail):
        # The last group in the menu, below the bottom of the window, left
        # expanded as it is when the reader opened it before collapsing.
        icon_rail.evaluate("""
            () => {
              const li = [...document.querySelectorAll('.mvp-sidebar nav > ul > li')]
                .filter((li) => li.querySelector(':scope > details'))
                .at(-1);
              li.id = 'last-group';
              li.querySelector('details').open = true;
            }
        """)
        group = "#last-group"
        flyout = f"{group} > details > ul"
        icon_rail.locator(f"{group} > details > summary").scroll_into_view_if_needed()
        icon_rail.hover(f"{group} > details > summary")

        box = icon_rail.evaluate(
            """([group, flyout]) => ({
              item: document.querySelector(group).getBoundingClientRect().toJSON(),
              flyout: document.querySelector(flyout).getBoundingClientRect().toJSON(),
            })""",
            [group, flyout],
        )

        assert box["flyout"]["left"] == pytest.approx(box["item"]["right"], abs=1)
        assert box["flyout"]["top"] == pytest.approx(box["item"]["top"], abs=1)
        assert can_point_at(icon_rail, flyout)


class TestACollapsedGroupOpensInTheRail:
    """A group left collapsed in the open sidebar still opens beside the rail (#582).

    A closed ``<details>`` hides everything but its ``<summary>``, so the rail's
    fly-out rule gave the list a box and nothing in it could be seen.
    """

    @pytest.fixture
    def group(self, icon_rail):
        icon_rail.evaluate("""
            () => {
              const li = [...document.querySelectorAll('.mvp-sidebar nav > ul > li')]
                .find((li) => li.querySelector(':scope > details'));
              li.id = 'first-group';
              li.querySelector('details').open = false;
            }
        """)
        return "#first-group"

    @pytest.mark.parametrize("reach", ["hover", "focus"])
    def test_its_items_show_beside_the_rail(self, icon_rail, group, reach):
        summary = f"{group} > details > summary"
        flyout = f"{group} > details > ul"
        getattr(icon_rail, reach)(summary)

        assert icon_rail.evaluate(
            f"document.querySelector('{flyout}').checkVisibility()"
        )
        assert (
            icon_rail.evaluate(f"document.querySelector('{group} > details').open")
            is False
        )
        assert can_point_at(icon_rail, f"{flyout} > li:first-child a")

    def test_its_items_can_be_reached_from_the_keyboard(self, icon_rail, group):
        icon_rail.focus(f"{group} > details > summary")
        icon_rail.keyboard.press("Tab")

        assert icon_rail.evaluate(
            f"document.querySelector('{group} > details > ul').contains(document.activeElement)"
        )
