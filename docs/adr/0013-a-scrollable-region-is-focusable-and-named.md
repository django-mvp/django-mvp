# 0013 — A scrollable region the package ships is focusable and named

**Status:** accepted

**Date:** 2026-08-17

## Context

The full-screen table layout puts the rows in a container that scrolls on both axes, so the window
never does. That container is an ordinary `div` with `overflow: auto`, and it holds the only copy
of most of the page's content.

A `div` that scrolls is reachable by wheel and trackpad everywhere. It is reachable by keyboard in
Chromium only. Firefox and Safari give a scroll container keyboard focus only when it is an
explicit tab stop, and a read-only table has nothing focusable inside its rows to tab to instead.
So on two of the three engines, a keyboard-only reader could not move past the first screen of a
table at all — not a degraded experience, no access to the data.

Nothing about the markup announces the container either. Assistive technology reads a bare `div`
as a grouping with no name and no role, so a reader arriving in it has no way to know what it
holds or that it scrolls.

## Decision

Any scrollable region this package ships carries `tabindex="0"`, a region role, and an accessible
name. The name is a component attribute with a translatable default, so a page holding two of them
can distinguish them.

This is a rule about scrollable regions, not about tables. The table area is the first one the
package ships; it will not be the last.

## Consequences

The region joins the tab order, which is the point — it is a place a reader needs to be able to
stand. It also means one more stop before the content after it, which is the accepted cost and the
reason the name matters: a stop announced as "Scrollable table region" is navigation, an unnamed
stop is an obstacle.

Article XIII already required this. What was missing was anyone noticing that a scroll container
is a case it covers, because the markup looks inert.

## The general form

The failure here is that the accessibility defect is invisible in the browser most development
happens in. Chromium's convenience — focusing scroll containers automatically — hides a gap that
the specification does not require it to fill, so testing in one engine returns a clean answer to
a question that was never asked. Where a behaviour is engine-discretionary, the packaged markup
states it rather than inheriting it.
