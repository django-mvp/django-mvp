"""A dropdown with no room below it opens upwards instead, in a real browser.

This is the one thing about the placement work that a rendered-markup test
cannot reach, and Article XIV says that is the only thing a browser test is
for. Which side a panel opens on is a function of where the trigger happens to
sit in the viewport at the moment it is clicked, so it does not exist in the
HTML at all: the template's job ends at declaring ``bottom-start``, and
everything after that is measurement. Every other part of the contract — the
hook attribute, the placement string for each pair, the daisyUI classes that
carry the no-JavaScript path — is asserted from rendered markup in
``test_dropdown.py``.

The scenario is the demo's own "Open direction" section, scrolled until the
trigger is against the bottom edge of the window. Its declared placement is
``bottom``, so the panel is asked for room that is not there.
"""

import pytest

from tests.conftest import requires_browser

pytestmark = [pytest.mark.e2e, requires_browser]

VIEWPORT = {"width": 1280, "height": 720}

# assets/js/dropdown.js keeps the panel this far from the trigger and from the
# edges of the window. Restated rather than imported because a Python test
# cannot read a JavaScript constant, and the numbers are only used to prove
# the panel had nowhere to go, never to predict where it landed.
GAP = 8


def open_bottom_dropdown_at_the_foot_of_the_window(page, live_server):
    """Scroll the demo's ``valign="bottom"`` dropdown to the bottom edge, open
    it, and report what the browser laid out.

    ``scrollIntoView({block: "end"})`` rather than a window scroll: it puts the
    trigger against the bottom of the scrollport whichever ancestor is the one
    that scrolls, so the setup does not quietly depend on the app shell's
    current overflow arrangement.
    """
    page.set_viewport_size(VIEWPORT)
    page.goto(f"{live_server.url}/components/dropdown/")

    trigger = page.get_by_role("button", name="Bottom", exact=True)
    trigger.evaluate("element => element.scrollIntoView({block: 'end'})")
    trigger.click()

    return page.evaluate("""() => {
      const trigger = [...document.querySelectorAll('.dropdown > *')]
        .find(el => el.textContent.trim() === 'Bottom');
      const panel = trigger.parentElement
        .querySelector(':scope > .dropdown-content');
      const box = el => {
        const r = el.getBoundingClientRect();
        return {top: r.top, right: r.right, bottom: r.bottom, left: r.left,
                width: r.width, height: r.height};
      };
      return {
        open: panel.matches(':popover-open'),
        placement: trigger.parentElement.dataset.mvpPlacement,
        trigger: box(trigger),
        panel: box(panel),
        viewport: {width: window.innerWidth, height: window.innerHeight},
      };
    }""")


class TestDropdownFlipsWhenTheDeclaredSideDoesNotFit:
    """The panel ends up on screen, and it only could have by flipping."""

    def test_the_panel_stays_inside_the_viewport(self, page, live_server):
        laid_out = open_bottom_dropdown_at_the_foot_of_the_window(page, live_server)

        assert laid_out["open"], (
            "the panel never opened, so nothing below this measures placement"
        )
        assert laid_out["placement"] == "bottom-start", (
            "this scenario is only about a *declared* placement that does not "
            "fit — if the demo stops declaring one, the test proves nothing"
        )

        panel = laid_out["panel"]
        viewport = laid_out["viewport"]

        assert panel["width"] > 0 and panel["height"] > 0, (
            f"the panel has no area ({panel}), so 'inside the viewport' would "
            "be true of a panel nobody can read"
        )
        assert panel["top"] >= 0, f"panel runs off the top: {panel}"
        assert panel["left"] >= 0, f"panel runs off the left: {panel}"
        assert panel["bottom"] <= viewport["height"], (
            f"panel runs off the bottom: {panel} in {viewport} — its declared "
            "bottom placement was honoured with no room for it"
        )
        assert panel["right"] <= viewport["width"], (
            f"panel runs off the right: {panel} in {viewport}"
        )

    def test_the_declared_side_genuinely_had_no_room(self, page, live_server):
        """The control for the test above.

        Without this, a scroll that stopped short would leave the panel opening
        downwards into plenty of space, passing every assertion and proving
        nothing about collisions. Measuring the panel the browser actually laid
        out against the gap below the trigger is what establishes that the
        declared side was impossible before the fact that it was not used
        becomes interesting.
        """
        laid_out = open_bottom_dropdown_at_the_foot_of_the_window(page, live_server)

        room_below = laid_out["viewport"]["height"] - laid_out["trigger"]["bottom"]
        needed = laid_out["panel"]["height"] + GAP

        assert room_below < needed, (
            f"there was {room_below}px below the trigger and the panel needs "
            f"{needed}px, so it would have fitted where it was told to go and "
            "this scenario is not exercising placement at all"
        )
