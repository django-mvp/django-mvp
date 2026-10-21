# Decisions: FS-042

## Self-resolved ambiguities (coverage scan, 2026-10-21)

**Drawer open when the window widens past the breakpoint.** Chosen: it closes. Leaving it open
would leave the page dimmed and unreachable behind a panel that is now also a column. Defensible
because nothing the reader chose is lost: the panel's content is the same in both forms.

**Two panels on one page.** Chosen: one. Two columns beside one content area leave too little room
for the content at any common screen width with the app sidebar open, and no request asked for it.
A project needing two writes its own layout with the page layout component's pieces.

**List page with every filter in the toolbar.** Chosen: no panel and no button, matching today's
rule that such a page has no Filter button and no modal (FS-041).

**Panel taller than the screen.** Chosen: it scrolls inside its own column. The alternative,
dropping the stickiness, would make a long filter panel's apply button unreachable without scrolling
the whole page to the bottom. The scrolling region is focusable and named, per ADR 0013.

**Pages that fill the screen's height.** Chosen: a full-height column with no sticking. On such a
page the window does not scroll, so sticking has nothing to do, and the content region already
scrolls inside itself.

## Why the default breakpoint is extra large

At the large width with the app sidebar open, about 760px remains for the page. A 16rem column and
its gap leave about 460px for the content, below a readable line length for body text and too
narrow for a three-column card grid. At extra large about 1020px remains.

## Build decisions (planning, 2026-10-21)

## D1 The layout reads the panel's side off the slot's first element

**Decision:** `<c-mvp.page.layout>` learns the panel's position from the `data-mvp-side-position`
attribute of the side slot's first element, read with a new `root_attr` filter built on
`html.parser`. **Why:** the panel carries its own configuration (FR-001) and reaches the layout as
rendered HTML; the prototype's substring test over the whole slot could be moved by the panel's own
content. **Revisit if:** Cotton gains a way for a slot's component to hand values to its parent.
**ADR:** pending (S5)

## D2 The filter context keys are renamed with the modal

**Decision:** `modal_fields`, `modal_applied_count` and `clear_modal_url` become `panel_fields`,
`panel_applied_count` and `clear_panel_url`. **Why:** the modal is removed (FR-013); a public name
for a thing that no longer exists is a stale name. Pre-1.0, recorded as breaking (Article XVI).
**Revisit if:** a consumer needs a deprecation window.
**ADR:** pending (S5)

## D3 The panel is refreshed out of band after a list swap

**Decision:** every element that swaps the list region also carries
`hx-select-oob="#<filter_panel_id>"`, and the panel's id is a view attribute beside
`list_region_id`. **Why:** the panel sits beside the region, not in it, and its clear link and field
values must follow the response; widening the region to hold the layout would put the title and the
grid inside the swap. **Revisit if:** the region moves to wrap the whole page layout.
**ADR:** pending (S5)

## D4 A swap with the drawer open leaves focus where the modal's did

**Decision:** applying from an open drawer replaces the panel with a closed one. The panel's id is
on the component's root, so the out-of-band swap replaces the whole component, drawer state
included; the old component releases `inert` in `destroy()`, and focus is not moved. **Why:** parity with the filter modal's
Apply, which swapped the region the same way; the spec asks for nothing more. **Revisit if:** a
reader reports losing their place after applying on a phone.
**ADR:** pending (S5)

## D5 Unapplied panel values are not put back

**Decision:** FS-041's handler that restored the modal's fields on close is removed, not carried to
the drawer. **Why:** FR-017 keeps a value set in the panel when the reader applies a change in the
toolbar, and a column is never "closed". **Revisit if:** Sam asks for the drawer to discard on close.
**ADR:** pending (S5)

## D6 Four browser tests that need a CDN are outside this feature

**Decision:** `TestErrorPagesAccessibilityE2E` fails locally because its browser cannot fetch
axe-core through this machine's proxy; CI on `main` passes it. Local verify is read with those four
excluded. **Why:** environmental, unchanged by this branch. **Revisit if:** it fails in CI.
**ADR:** none — a note about this machine, nothing in the code depends on it

## D7 The design review's findings, as applied

**Decision:** the panel's id moves to the component's root and the `<aside>` becomes `{id}-panel`
(a review finding: with the id on the `<aside>`, the out-of-band refresh replaced only the
`<aside>` and left an open drawer open over a refreshed list). The table's heading row joins the
elements that refresh the panel, with the empty state and the table template taking the panel id.
The breakpoint's width reaches the script from `BREAKPOINT_WIDTHS` instead of a second table in
JavaScript. The `<aside>` is always a tab stop. Alignment, widths and stacked order are not
browser-tested, and US-5 adds no tests of its own, its requirement being met by T003 and T007. The
demo page stays: it is where layout work is looked at. **Why:** each removes a defect or a
duplicate; none widens the spec. **Revisit if:** a later feature needs the panel's id on the
`<aside>` itself.
**ADR:** none — corrections to this feature's plan, nothing downstream inherits them

## D8 The drawer wraps Tab itself

**Decision:** `mvpPageSide` wraps Tab and Shift+Tab inside the panel while the drawer is open, in
addition to making the rest of the page `inert`. The panel's width reaches the template through
`{% breakpoint_px breakpoint as ... %}` and `widthratio`, because `breakpoint_px` is a simple tag,
not a filter. **Why:** with everything else inert there is no next control after the last link, so
Tab leaves the document for the browser's own interface and focus is outside the panel (FR-009);
the browser test for it failed until the wrap was added. **Revisit if:** browsers keep focus in the
document when the page is inert past the last control.
**ADR:** none
