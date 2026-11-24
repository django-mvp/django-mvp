"""Template tags behind the ``<c-layout>`` components."""

import uuid

from django import template

from daisy_cotton_layout.view import LayoutView

register = template.Library()

STATES = {"open", "closed"}
COLLAPSES = {"offcanvas", "icons", "none"}
BEHAVIORS = {"auto", "docked", "overlay"}
BREAKPOINTS = {"sm", "md", "lg", "xl", "2xl"}
COOKIE_PREFIX = "dcl-"


@register.simple_tag
def layout_view(code):
    """Read a layout code. A wrong code raises, naming the rules."""
    return LayoutView.parse(code)


@register.simple_tag
def layout_uid(prefix="dcl"):
    """An id for an element that was not given one."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


@register.simple_tag(takes_context=True)
def layout_sidebar(context, side, collapse, breakpoint, behavior, persist, closed):
    """Settle a sidebar's options and the state the server draws it in.

    The state is the one the reader left it in, read from the cookie the
    layout script writes, so a sidebar the reader closed is drawn closed and
    never opens and snaps shut on load.
    """
    collapse = collapse if collapse in COLLAPSES else "offcanvas"
    behavior = behavior if behavior in BEHAVIORS else "auto"
    breakpoint = breakpoint if breakpoint in BREAKPOINTS else ("lg" if side != "right" else "xl")
    state = "closed" if closed else "open"
    request = context.get("request")
    if persist and request is not None:
        remembered = request.COOKIES.get(COOKIE_PREFIX + persist)
        if remembered in STATES:
            state = remembered
    if collapse == "none":
        state = "open"
    return {
        "side": "right" if side == "right" else "left",
        "collapse": collapse,
        "behavior": behavior,
        "breakpoint": breakpoint,
        "state": state,
        "rail": state == "closed" and collapse == "icons" and behavior != "overlay",
    }
