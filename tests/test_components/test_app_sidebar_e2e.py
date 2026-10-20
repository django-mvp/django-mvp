"""The sidebar never makes the page taller than the window (issue #562).

Collapsed on a desktop-width window, the default sidebar is hidden by setting
its width to zero. Its height was left alone, and the drawer side lets its
content overflow so the icon rail's tooltips can show, so the full height of
the menu counted towards the page's height. A zero-width box happens not to
add to the scrollable area, but any width at all does: a one-pixel border gave
the page a scrollbar as tall as the menu, with no sidebar in sight. Only
computed layout shows this, so it needs a browser.

The window is short rather than the menu long: the demo menu is taller than
400px, which is all the case needs. The page fills the window by design, so
any height beyond the window's is the sidebar's.
"""

import pytest

from tests.conftest import requires_browser

pytestmark = [pytest.mark.e2e, requires_browser]

PAGE = "/layout/full-page/"
SHORT_DESKTOP = {"width": 1440, "height": 400}


def _measure(page, url, open_):
    """Load a page with the sidebar open or collapsed and report its heights."""
    page.set_viewport_size(SHORT_DESKTOP)
    page.add_init_script(
        f"localStorage.setItem('mvp-app-drawer-open', '{str(open_).lower()}')"
    )
    page.goto(url)
    # The edge a project draws between the sidebar and the page.
    page.add_style_tag(content=".mvp-sidebar { border-right: 1px solid; }")
    return page.evaluate("""
        () => ({
          checked: document.getElementById('mvp-app-toggle').checked,
          viewport: window.innerHeight,
          documentHeight: document.documentElement.scrollHeight,
          menuHeight: document.querySelector('.mvp-sidebar').scrollHeight,
        })
    """)


class TestTheSidebarFitsTheWindow:
    @pytest.mark.parametrize("open_", [True, False], ids=["open", "collapsed"])
    def test_the_page_is_no_taller_than_the_window(self, page, live_server, open_):
        layout = _measure(page, f"{live_server.url}{PAGE}", open_)

        assert layout["checked"] is open_
        assert layout["menuHeight"] > layout["viewport"], (
            "the menu fits in the window — this proves nothing"
        )
        assert layout["documentHeight"] == layout["viewport"]
