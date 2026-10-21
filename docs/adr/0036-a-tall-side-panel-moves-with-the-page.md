# ADR 0036 — A tall side panel moves with the page

**Status:** accepted

## Decision

A sticky side panel taller than the space under the header has no scrollbar of its own. It moves with the page in whichever direction the reader scrolls until its far end is in view, then holds there. Scrolling down, the panel rises with the content until its foot reaches the foot of the screen. Scrolling up, it sinks with the content until its top sits a gap under the header. A panel that fits stays just under the header, as before.

The panel's sticky offset is a custom property on its root, `--mvp-page-side-top`. The stylesheet falls back to the header's height plus `1rem` when nothing sets it. A registered Alpine component, `mvpPageSideColumn` in `assets/js/page_side_column.js`, sits on the `<aside>` of every sticky panel and keeps the offset between two limits: the header's foot plus a gap, and the screen's height less the panel's own. Each frame after a scroll it moves the offset by what the page's content moved, so the panel follows the page whether it is currently stuck or not.

The component writes the property only while the panel is a sticky column taller than the space. Below the breakpoint, on a filled page and for a panel that fits, the root has no property. It recomputes its limits when the window, the panel or the header changes size. A panel replaced by an htmx swap carries on from the offset of the one it replaces. A control focused by keyboard is brought clear of the header and of the screen's foot.

The `<aside>` of a sticky column no longer scrolls, so the component takes it out of the tab order. It stays a tab stop on a filled page and in a drawer, where it still scrolls (ADR 0013).

## Why

A panel with its own scrollbar puts a second scrollbar beside the page's, which looks poor. A panel that does not stick makes the reader scroll to the foot of the results to reach the last filters. Shops move a tall column with the page instead, and a reader meets that pattern everywhere.

CSS alone can't do it. `position: sticky` has one offset, so a negative one holds the foot in view but leaves the top out of reach on the way back up. Two offsets that depend on the direction of travel need a script. Changing one number is the smallest script that does it: the panel stays in the page's grid, it is not taken out with `position: fixed`, and without the script it is a plain sticky column.

The component measures the content's movement on the page layout, not `scrollY`. When the header grows, the browser scrolls to keep the content where it was, and that scroll is not the reader's.

## Revisit if

CSS gains a native way to stick an element at whichever end is in view.
