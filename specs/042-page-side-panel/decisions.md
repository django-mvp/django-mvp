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
**ADR:** none — how one component reads one attribute, nothing outside it depends on the method

## D2 The filter context keys are renamed with the modal

**Decision:** `modal_fields`, `modal_applied_count` and `clear_modal_url` become `panel_fields`,
`panel_applied_count` and `clear_panel_url`. **Why:** the modal is removed (FR-013); a public name
for a thing that no longer exists is a stale name. Pre-1.0, recorded as breaking (Article XVI).
**Revisit if:** a consumer needs a deprecation window.
**ADR:** none — a rename recorded as a breaking change in the changelog

## D3 The panel is refreshed out of band after a list swap

**Decision:** every element that swaps the list region also carries
`hx-select-oob="#<filter_panel_id>"`, and the panel's id is a view attribute beside
`list_region_id`. **Why:** the panel sits beside the region, not in it, and its clear link and field
values must follow the response; widening the region to hold the layout would put the title and the
grid inside the swap. **Revisit if:** the region moves to wrap the whole page layout.
**ADR:** docs/adr/0034-what-sits-beside-the-list-region-is-refreshed-out-of-band.md

## D4 A swap with the drawer open leaves focus where the modal's did

**Decision:** applying from an open drawer replaces the panel with a closed one. The panel's id is
on the component's root, so the out-of-band swap replaces the whole component, drawer state
included; the old component releases `inert` in `destroy()`, and focus is not moved. **Why:** parity with the filter modal's
Apply, which swapped the region the same way; the spec asks for nothing more. **Revisit if:** a
reader reports losing their place after applying on a phone.
**ADR:** none — a consequence of D3 and the panel's markup, recorded in ADR 0034

## D5 Unapplied panel values are not put back

**Decision:** FS-041's handler that restored the modal's fields on close is removed, not carried to
the drawer. **Why:** FR-017 keeps a value set in the panel when the reader applies a change in the
toolbar, and a column is never "closed". **Revisit if:** Sam asks for the drawer to discard on close.
**ADR:** none — the removal of one handler with the modal it served

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
**ADR:** none — how this one component contains focus, nothing else builds on it

## D9 The table page's layout draws no row gap, and the modal went with its last user

**Decision:** `table_view.html` draws `<c-mvp.page.layout class="gap-y-0!">`. The layout's own
`gap-3` put a 12px row between the layout's top and the toolbar even though the header slot is
empty, because the empty header row of the grid (and the closed drawer's root, in a column) still
counts for the gap; the filled page meets the shell edges with no space above the toolbar. The
filter modal's component and its test module were deleted with the table page, the last template
that drew them, not in the panel's own commit, so every commit leaves the tree green. The pre-existing
`test_toolbar_stays_when_a_search_matches_nothing` now names `toolbar_filters=["q"]`: with none named,
the search is a panel field, and the old test found it only because the modal sat inside the
toolbar. **Why:** each keeps what the old tests protected without weakening them. **Revisit if:**
the layout component gains its own way to turn off its row gap.
**ADR:** none — a class on one template, and a test kept to the behaviour it guards

## D10 Behaviour lives in registered Alpine components

**Decision:** an Alpine component with real behaviour is a module under `assets/js/`, registered
with `Alpine.data()`; templates pass configuration only. **Why:** Sam's rule from the intake
(planning-notes.md), stated for the package from here on, not this feature alone. **Revisit if:**
the package stops bundling Alpine.
**ADR:** docs/adr/0035-behaviour-lives-in-registered-alpine-components.md

## D11 Sam's changes at the merge gate (2026-10-21)

**Decision:** the list page's filter panel defaults to the end side. Its alignment follows its side
unless the developer sets one: content at the end, title at the start. The table page's layout
draws no gap in either direction. The drawer at the end side slides in from the end. The side
panel demo keeps its long-contents option, off by default. **Why:** Sam, at the merge gate: the
app's sidebar sits at the start, and two panels on the same side look awkward. FR-014 now says so.
**Revisit if:** the app layout stops being sidebar-first.
**ADR:** none — default values and one alignment rule for one component
