# Tasks — 047 Sheets for phones and wide screens

**Branch**: `047-sheet` · **Plan**: [plan.md](plan.md) · **Research**: [research.md](research.md) ·
**Spec**: [spec.md](spec.md)

Every task follows Article I's test-first cycle. A task is done when its tests pass, the tree is
green and the work is committed. Markup tests are in `tests/test_components/test_sheet.py`,
browser tests in `tests/test_components/test_sheet_e2e.py`. Documentation for a public name lands
in `docs/components.md` and `docs/developer/sheets.md` in the last group, with the demo.
Wording, widths and spacing are not tested. `assets/js/sheet.js` and `mvp/tailwind/base.css` are
edited in blocks of their own so a sibling feature's edits merge by keeping both.

## Checklist

- [ ] T001 [US1] The sheet and its view: markup contract, name, description, head, foot, options
- [ ] T002 [US1] The trigger: link with an address, button without, accessible name, open event
- [ ] T003 [US1] The menu and its rows, link or button, with a destructive mark
- [ ] T004 [US1] The sheet's rules in the stylesheet, and the rebuilt stylesheet
- [ ] T005 [US2] `mvpSheet`: open event, views, reset on close, one open sheet, focus return
- [ ] T006 [US2] The keyboard offset, reduced motion and the wide switch
- [ ] T007 [US2] Browser tests for the sheet at phone and desktop width
- [ ] T008 [US3] The two heights, the drag and flick, the grab bar as a control
- [ ] T009 [US3] Browser tests for every height transition and the gesture's edge cases
- [ ] T010 [US1] The demo, the documentation, the README and the changelog
- [ ] T011 [US2] Focus returns to the opener of the sheet that holds a trigger when none is named
- [ ] T012 [US2] Review fixes in the script: focus fallback, flick step, close flash, view name
- [ ] T013 [US2] Review fixes in the browser tests: keyboard path, removed sheet, tuning values, retries
- [ ] T014 [US1] Review fixes in the markup, demo and docs

## Order

T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014.

---

## Phase 1: User Story 1 — A developer puts a menu, a short form or a few steps in a sheet (P1)

Delivers FR-001, FR-002, FR-003, FR-004, FR-005 (markup), FR-009, FR-019 (wide size), FR-020, FR-022.

### Group 1

#### T001 — The sheet and its view

**Files**: `mvp/templates/cotton/mvp/bottom_sheet/index.html`, `mvp/templates/cotton/mvp/bottom_sheet/view.html`,
`tests/test_components/test_sheet.py`

The contract in `plan.md`. Port the sheet from the agreed design into daisy-cotton's `c-modal`
with `modal-bottom sm:modal-middle` in the template text so the stylesheet scan finds it. Grab bar
is a `<button type="button">` with a translated `aria-label`. Head holds the `art` slot (hidden from
assistive technology), icon, title, `lead`. `description` slot becomes the dialog's accessible
description. Foot is the `actions` slot or one closing `type="button"`. `full`, `fixed` and `wide`
set data attributes and the wide size class. Tests: US1 scenarios 1, 2, 7 (markup), 8, 11, 12, 13,
14.

#### T002 — The trigger

**Files**: `mvp/templates/cotton/mvp/bottom_sheet/trigger.html`, `tests/test_components/test_sheet.py`

Link with `href`, button without, `aria-haspopup="dialog"`, name "More for {label}" from `label`,
icon-only when the slot is empty and worded otherwise, a click handler that prevents the link
and dispatches `mvp-sheet-open` on `window` with `{ id, view, returns, opener }`. Scenarios 3, 4
(markup half), 5, 9, 10 (markup half). Confirm the icon name used resolves in the packaged icon set.

#### T003 — The menu and its rows

**Files**: `mvp/templates/cotton/mvp/bottom_sheet/menu/index.html`,
`mvp/templates/cotton/mvp/bottom_sheet/menu/item.html`, `tests/test_components/test_sheet.py`

Wrappers over `c-menu` and `c-menu.item` (D15). `danger` marks a row destructive. Rows are
links or buttons, icons hidden from assistive technology, words as the name. Scenario 6.

#### T004 — The sheet's rules, and the rebuilt stylesheet

**Files**: `mvp/tailwind/base.css`, `mvp/static/css/django-mvp.css`,
`mvp/static/css/django-mvp.css.br`, `tests/test_components/test_responsive_safelist.py` or the
nearest existing coverage test

Port the agreed styles: grab bar, head, art tile, menu rows, safe-area padding at the foot, the
column box with a pinned head and a scrolling body, the grab bar hidden from `sm` up, the wide
size. Custom properties `--mvp-sheet-rest` and `--mvp-sheet-full`. One block with a comment
header. Rebuild with `uv run invoke build-stylesheet`. The browser tests cover the placement.

---

## Phase 2: User Story 2 — A user opens a sheet and works in it, on any screen (P1)

Delivers FR-005–FR-008, FR-010–FR-013, FR-019–FR-021, SC-003, SC-005.

### Group 2

#### T005 — `mvpSheet`: open event, views, reset on close, one open sheet, focus return

**Files**: `assets/js/sheet.js`, `assets/js/index.js`, `mvp/static/js/django-mvp.js`,
`tests/test_components/test_sheet_e2e.py`

`registerSheet(Alpine)` with the `mvpSheet({ id })` data component per ADR 0035. It listens for
`mvp-sheet-open` on `window` and, for its own id: closes every other open sheet, sets the view
(the named one, or the first when it does not exist), calls `showModal()` and remembers where
focus returns (the named element, else the opener). On the dialog's `close` event it returns to
the first view, resets the height and moves focus to the remembered element. A trigger whose sheet
is not on the page does nothing (the link then follows its address). Views are found from
`[data-mvp-sheet-view]`; `view` and `show(name)` are in scope. Rebuild the bundle
(`npm run build:js:prod`). Tests, first: scenarios of US2 3–8 at phone and desktop width (4–6 once by keyboard alone), US1 9 and 10, an unknown view opening the first, a trigger whose sheet is absent following its link, and two sheets each opening and closing alone. `mvpSheetTrigger` is registered here and reads `for`, `view` and `returns` from `data-` attributes.

#### T006 — The keyboard offset, reduced motion and the wide switch

**Files**: `assets/js/sheet.js`, `mvp/tailwind/base.css`, `mvp/static/js/django-mvp.js`,
`mvp/static/css/django-mvp.css`, `mvp/static/css/django-mvp.css.br`,
`tests/test_components/test_sheet_e2e.py`

While open, read `window.visualViewport` and set `--mvp-sheet-keyboard` on the dialog (D17); the box
takes it as a bottom offset and shrinks its maximum height; `focusin` scrolls the field into view
in the body. Only the open sheet listens. `prefers-reduced-motion` removes the open and close
slide. A sheet open across a change from narrow to wide stays open on the same view and returns to
its resting height when turned back. Tests: US2 10 (the field placed below the faked keyboard line first, `visualViewport` height and offset redefined, `resize` fired on `window.visualViewport`, and the field's rectangle asserted above the faked keyboard) and 11, and the rotate edge case.

#### T007 — Browser tests for the sheet at phone and desktop width

**Files**: `tests/test_components/test_sheet_e2e.py`, `demo/templates/demo/components/sheet.html`
(a minimal fixture page if T010's is not yet there)

US2 scenarios 1, 2, 9 (1 and 2 also at 639 and 640 px wide); US1 scenario 15 (no request to another origin while a page with a sheet
loads and opens it); the fallback link with scripts turned off (US1 scenario 4, SC-004); the
body scrolls while the head stays and the page behind does not; Tab never leaves the sheet; Escape,
tap outside and the closing button close without submitting a form the sheet sits in; reopening
shows the first view.

---

## Phase 3: User Story 3 — A user on a phone drags a sheet taller to see more of it, or down to close it (P1)

Delivers FR-014–FR-018, FR-019 (no drag), FR-021, SC-002.

### Group 3

#### T008 — The two heights, the drag and flick, the grab bar as a control

**Files**: `assets/js/sheet.js`, `mvp/tailwind/base.css`, `mvp/static/js/django-mvp.js`,
`mvp/static/css/django-mvp.css`, `mvp/static/css/django-mvp.css.br`,
`tests/test_components/test_sheet_e2e.py`

`data-height="rest|full"`; resting height is content up to `--mvp-sheet-rest`, full is
`--mvp-sheet-full`; `full` opens at full; `fixed` stays at rest and follows a drag up by a quarter,
capped, and settles back. Pointer capture on pointerdown on the grab bar or head, first pointer
only, a cancelled or lost pointer settles at the last position. The numbers of D16 are named
constants. Release: nearest height by the top edge, a flick one step in its direction. Closing
animates off the bottom, then closes and returns focus. The grab bar button toggles rest and full
(not on a fixed sheet) and tells assistive technology the height. A drag inside the body scrolls
the body. At and above `sm` nothing responds to a drag. Reduced motion settles without animating.
Tests first, as in T009.

#### T009 — Browser tests for every height transition and the gesture's edge cases

**Files**: `tests/test_components/test_sheet_e2e.py`

At a phone viewport with touch, driving touch events with real timing: US3 scenarios 1–11, 13;
open→full, full→rest, rest→closed and full→closed by drag and by flick, with geometry asserted at each height (box top and bottom, not constants), explicit timestamps on every touch event; a fixed sheet settles back and still
closes; a drag inside the body scrolls it; the page behind does not scroll during a drag; the grab
bar by tap and by keyboard (`aria-expanded` flips), a mouse drag that ends on it; a second sheet opened mid-drag; a second finger does not move the sheet twice as far; an interrupted
drag settles at its last position; full again after reopen is rest unless `full` was asked. At desktop
width with the mouse, scenario 12: the sheet does not move.

---

## Phase 4: Documentation and the demo (P1)

Delivers FR-023, SC-001.

### Group 4

#### T010 — The demo, the documentation, the README and the changelog

**Files**: `demo/templates/demo/components/sheet.html`, the demo's component registration,
`tests/test_demo/test_sheet_demo.py`, `docs/components.md`, `docs/developer/sheets.md`,
`docs/index.md`, `README.md`, `CHANGELOG.md`, `docs/adr/` only if S5 finds a decision that clears the bar

The demo page shows a sheet holding a menu with a confirmation view, a sheet holding a short form,
a sheet opened from another sheet with focus returning, and a sheet opened at its full height; a
fixed sheet too. The guide documents every property of the five components, the `mvp-sheet-open`
event with its `id`, `view` and `returns`, `show(name)`, that a trigger with no address needs
scripts, and that a sheet's title is required because it names the dialog. A demo test renders each
example. Bundle and stylesheet are rebuilt if anything above changed them.

#### T011 — Focus returns to the opener of the sheet that holds a trigger when none is named

**Files**: `assets/js/sheet.js`, `mvp/static/js/django-mvp.js`,
`tests/test_components/test_sheet_e2e.py`, `docs/developer/sheets.md`

Found while building the drag: a trigger inside a sheet cannot take focus once its sheet has
closed, so FR-007's "the trigger itself" is impossible there. When a trigger inside a sheet names
no `returns`, focus goes to the element that opened the sheet that holds it, and to the trigger
itself only for a trigger outside every sheet. Test first at phone and desktop width. Recorded as
a review-stage fix task with decision D21.

#### T012 — Review fixes in the script

**Files**: `assets/js/sheet.js`, `mvp/static/js/django-mvp.js`, `tests/test_components/test_sheet_e2e.py`

Focus falls back to the element focused when the sheet opened when neither `returns` nor an opener
is given. A flick's starting step is the nearest height at release, not the height at press. A
sheet closed by drag or flick does not flash back before it closes. A view's visibility compares
the element's own attribute rather than a name written into a script string. Tests first.

#### T013 — Review fixes in the browser tests

**Files**: `tests/test_components/test_sheet_e2e.py`

The keyboard-only path runs at both widths and reaches each control with Tab. A sheet replaced by
an identical copy opens once with no page error. The two tests that pin the rest limit and the
fixed sheet's follow distance assert the requirement instead. Focus checks retry. Lines fit 88.

#### T014 — Review fixes in the markup, demo and docs

**Files**: `mvp/templates/cotton/mvp/bottom_sheet/index.html`, `demo/templates/demo/components/sheet.html`,
`tests/test_components/test_sheet.py`, `tests/test_demo/test_sheet_demo.py`,
`docs/components.md`, `mvp/tailwind/base.css`, `mvp/static/css/django-mvp.css`,
`mvp/static/css/django-mvp.css.br`

The sheet's names wrapper is a `div`. A fixed sheet's grab bar is not a button. The demo's form
test looks inside its own dialog, the demo form's Save closes the sheet, and the demo lays out with
the package's components. The stylesheet comment is three lines. The components page keeps the
attributes and links to the guide.
