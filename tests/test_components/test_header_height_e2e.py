"""The header's height is published for whatever has to clear it (FS-042).

Whether an anchor, a focused control or a sticky panel ends up under the
header is computed layout, so only a browser can settle it. The tests add
their own long content to an ordinary page: the claim is about the header and
the document's scroll, not about any one page's markup.
"""

import pytest

from mvp.config import MVP_CONFIG
from tests.conftest import requires_browser

pytestmark = [pytest.mark.e2e, requires_browser]

PAGE = "/layout/store/"
NO_HEADER_PAGE = "/account/login/"

# Pushes the target and the control far below the fold on any page.
TALL_CONTENT = """
    () => {
      const spacer = () => {
        const div = document.createElement('div');
        div.style.height = '3000px';
        return div;
      };
      const target = document.createElement('div');
      target.id = 'far-target';
      target.style.height = '200px';
      const field = document.createElement('input');
      field.id = 'far-field';
      const link = document.createElement('a');
      link.id = 'far-link';
      link.href = '#far-target';
      link.textContent = 'jump';
      document.querySelector('main').append(field, spacer(), target, spacer(), link);
    }
"""


def _header_bottom(page):
    return page.evaluate(
        "() => document.querySelector('.mvp-header').getBoundingClientRect().bottom"
    )


def _published(page):
    return page.evaluate(
        "() => document.documentElement.style.getPropertyValue('--mvp-header-height')"
    )


@pytest.mark.django_db(transaction=True)
class TestHeaderHeight:
    def test_an_anchor_lands_below_the_header(self, page, live_server):
        page.set_viewport_size({"width": 1440, "height": 900})
        page.goto(f"{live_server.url}{PAGE}")
        page.evaluate(TALL_CONTENT)

        page.click("#far-link")

        top = page.evaluate(
            "() => document.getElementById('far-target').getBoundingClientRect().top"
        )
        assert top >= _header_bottom(page)

    def test_a_control_focused_by_keyboard_is_brought_out_from_under_the_header(
        self, page, live_server
    ):
        page.set_viewport_size({"width": 1440, "height": 900})
        page.goto(f"{live_server.url}{PAGE}")
        page.evaluate(TALL_CONTENT)

        # The field sits half under the header, which the browser counts as
        # visible unless scroll-padding-top says the header covers the top.
        page.evaluate("""
            () => {
              const field = document.getElementById('far-field');
              window.scrollBy(0, field.getBoundingClientRect().top - 20);
              document.getElementById('far-link').focus({ preventScroll: true });
            }
        """)
        page.keyboard.press("Shift+Tab")

        assert page.evaluate("() => document.activeElement.id") == "far-field"
        top = page.evaluate(
            "() => document.getElementById('far-field').getBoundingClientRect().top"
        )
        assert top >= _header_bottom(page)

    def test_the_value_follows_the_header_when_it_grows(self, page, live_server):
        page.set_viewport_size({"width": 1440, "height": 900})
        page.goto(f"{live_server.url}{PAGE}")
        before = page.evaluate(
            "() => document.querySelector('.mvp-header').offsetHeight"
        )

        page.evaluate("""
            () => {
              const extra = document.createElement('div');
              extra.style.height = '120px';
              document.querySelector('.mvp-header').append(extra);
            }
        """)

        page.wait_for_function(
            """
            () => document.documentElement.style.getPropertyValue('--mvp-header-height')
              === document.querySelector('.mvp-header').offsetHeight + 'px'
            """
        )
        height = page.evaluate(
            "() => document.querySelector('.mvp-header').offsetHeight"
        )
        assert height > before
        assert _published(page) == f"{height}px"

    def test_a_header_that_does_not_stick_publishes_zero(
        self, page, live_server, monkeypatch
    ):
        monkeypatch.setitem(MVP_CONFIG["layout"]["navbar"], "sticky", False)
        page.goto(f"{live_server.url}{PAGE}")

        assert _published(page) == "0px"

    def test_a_page_with_no_header_publishes_zero(self, page, live_server):
        page.goto(f"{live_server.url}{NO_HEADER_PAGE}")

        assert page.query_selector(".mvp-header") is None
        assert _published(page) == "0px"
