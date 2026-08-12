"""Real-browser test for issue #180 — modal positioning bugs.

Full-width and full-height are live-layout properties: a template-only
assertion (``test_modal.py``) can confirm the right utility classes are
present, but only a rendered browser proves the computed box actually
spans the viewport. Renders the demo's own Position section, since that is
what a maintainer would see and it now has coverage for all four edges
(``top``, ``bottom``, ``start``, ``end`` — see demo/templates/demo/components/
modal.html).
"""

import pytest
from playwright.sync_api import expect

from tests.conftest import requires_browser

pytestmark = [pytest.mark.e2e, requires_browser]

DESKTOP = {"width": 1280, "height": 800}


class TestModalPositioning:
    """The modal-box surface fills the axis its edge position implies."""

    @pytest.mark.parametrize("position", ["top", "bottom"])
    def test_edge_position_spans_full_width(self, page, live_server, position):
        page.set_viewport_size(DESKTOP)
        page.goto(f"{live_server.url}/components/modal/")

        modal_id = f"{position}_modal"
        page.evaluate(f"document.getElementById('{modal_id}').showModal()")
        box = page.locator(f"#{modal_id} .modal-box")
        expect(box).to_be_visible()
        bounding = box.bounding_box()
        assert bounding is not None
        # allow for a scrollbar gutter; the dialog must span the viewport,
        # not be capped to the component's default max-w-2xl (672px)
        assert bounding["width"] >= DESKTOP["width"] - 20, (
            f"{position} modal-box width={bounding['width']}, "
            f"expected close to viewport width {DESKTOP['width']}"
        )

    @pytest.mark.parametrize("position", ["start", "end"])
    def test_edge_position_spans_full_height(self, page, live_server, position):
        page.set_viewport_size(DESKTOP)
        page.goto(f"{live_server.url}/components/modal/")

        modal_id = f"{position}_modal"
        page.evaluate(f"document.getElementById('{modal_id}').showModal()")
        card = page.locator(f"#{modal_id} .modal-box .card")
        expect(card).to_be_visible()
        bounding = card.bounding_box()
        assert bounding is not None
        assert bounding["height"] >= DESKTOP["height"] - 20, (
            f"{position} modal card height={bounding['height']}, "
            f"expected close to viewport height {DESKTOP['height']}"
        )
