# Tasks — 048 Swipe and menu actions on list rows

**Branch**: `048-row-actions` · **Plan**: [plan.md](plan.md) · **Research**: [research.md](research.md) ·
**Spec**: [spec.md](spec.md)

Every task follows Article I's test-first cycle. A task is done when its tests pass, the tree is
green and the work is committed. Markup tests are in `tests/test_components/test_list_row.py`,
browser tests in `tests/test_components/test_list_row_e2e.py`. Wording, widths, spacing and colours
are not tested. `assets/js/row_actions.js` and the `Row actions (FS-048)` block of
`mvp/tailwind/base.css` are edited in blocks of their own so a sibling feature's edits merge by
keeping both. The agreed look is carried across, never redrawn: the reference pieces are named in
`research.md`, "What the agreed look is made of".

## Checklist

- [ ] T001 [US1] The default icon name `ellipsis`, the row action and the one-main-action filter
- [ ] T002 [US1] The list row: face, ⋯ control, one menu, sheet, plain row without actions
- [ ] T003 [US2] The row's rules in the stylesheet, and the rebuilt stylesheet
- [ ] T004 [US2] `mvpRowActions`: the layer under the row, the menu in the sheet, registration, bundle
- [ ] T005 [US2] The touch swipe: states, thresholds, flick, resist, edges, direction, one open row
- [ ] T006 [US2] The trackpad, the main action's commit, the fold and its undo
- [ ] T007 [US1] `window.mvpRows`, the reorder announcements, rows that arrive by htmx
- [ ] T008 [US2] The first-time nudge and reduced motion
- [ ] T009 [US1] The demo, the documentation, the glossary, the README, the changelog and the ADR

Design-review rules from `plan.md`, "Rules the design review settled", bind every task. The
feature builds as one sequential chain on one worktree. Extra tests they add: a swapped-in row's
dropdown panel is `:popover-open` after its trigger is clicked (T007); a nested reorder pair, a
button move whose answer replaces the list, and an on-demand mode keep swiping off until the mode
ends (T007); a declined `hx-confirm` leaves the row shown (T006); a list inside a scrolling element
closes an open row on scroll, a sideways touch on a sheet item runs the item and leaves the row,
Escape inside a row in an open sheet keeps the sheet open, a short release closes (T005); opening a
row then `mvpRows.off(list)` closes it (T007); a page requests nothing from another origin, as the
sheet's test does (T004); two main actions through `c-mvp.list.row` raise, as does an empty id (T002).

- [ ] T010 [US2] The mutation pass: tests that could not fail are repaired
- [ ] T011 [US2] Review fix: a declined confirm after a long swipe, the layer stays inert after a fold, nudge needs a shown row, `data-hx-*` requests
- [ ] T012 [US1] Review fix: the examples target the row with `closest [data-mvp-row]`, with a test
- [ ] T013 [US1] Review fix: the row's `id` lands on the item, the ⋯ icon call carries `only`
- [ ] T014 [US1] Review fix: a neutral id in the browser tests' sheet fixture
- [ ] T015 [US2] Review fix: comment length, line length and test tidying
- [ ] T016 [US2] A browser test waits for the menu to return to the dropdown after the sheet closes

## Order

T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015 → T016.

---

## Phase 1: User Story 1 — A developer gives a list row its actions (P1)

Delivers FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-023 (markup), FR-024, FR-025,
FR-026, FR-029, FR-030.

### Group 1

#### T001 — The icon name, the row action and the filter

**Files**: `mvp/utils.py`, `mvp/templates/cotton/mvp/list/row/action.html`,
`mvp/templatetags/mvp.py`, `docs/icons.md`, `docs/developer/list-rows.md`, `docs/index.md`,
`docs/components.md`, `tests/test_utils.py`, `tests/test_components/test_list_row.py`,
`tests/test_templatetags.py`

Documentation lands with the name that introduces it, because the documentation check reads the
diff at every group's exit: this task creates `docs/developer/list-rows.md` (linked from `docs/index.md` and
`docs/components.md`) with the action's properties and the filter. Later tasks add their sections.

Add `"ellipsis": "bi bi-three-dots"` to the default icon names and the icons page. The row
action is a wrapper of `c-mvp.sheet.menu.item`: `text`, `icon`, `href`, `danger`, `type`, `class`
pass through, plus `main` and `leaves` (data attributes `data-mvp-row-main`, `data-mvp-row-leaves`),
`label` (becomes `aria-label`), always `data-mvp-row-action`, and `:attrs` on the link or button.
The filter `single_main_action` takes a rendered string and returns it unchanged when it carries at
most one `data-mvp-row-main`, and raises `ImproperlyConfigured` otherwise, with the row's id passed
as the filter's argument. Scenarios: US1 3 (an id given to an action renders once), 5 (two main
actions are an error), 4 (markup half), 6 (markup half). An icon test renders `c-icon
name="ellipsis"` without `IconNotFoundError`.

#### T002 — The list row

**Files**: `mvp/templates/cotton/mvp/list/row/index.html`, `docs/developer/list-rows.md`,
`docs/components.md`, `tests/test_components/test_list_row.py`

The row's properties and slots go into `docs/developer/list-rows.md` and `docs/components.md` here.

The contract in `plan.md`, "The markup contract". Build on `c-list.row` (FR-004). An empty `actions`
slot renders the plain row (no `x-data`, no ⋯, no sheet). With actions: the face, the content, the
⋯ control (dropdown holding `<c-mvp.sheet.menu data-mvp-row-menu>` once, the sheet trigger, the
sheet with an empty `[data-mvp-row-sheet-body]`), `x-data="mvpRowActions"`, and the actions passed
through `single_main_action`. Tests: US1 1 (every action present once in the row), 2 (no actions:
no menu, no trigger, no `x-data`), 3 (an `id` and a `form` given to an action each appear once in
the whole rendered row, though the sheet is on the page), 4 (the main action carries the mark),
6 (leaves mark). The ⋯ button has an accessible name "More for {label}".

---

## Phase 2: User Story 2 — A user acts on a list row by swiping it or from its ⋯ menu (P1)

Delivers FR-002, FR-008–FR-022, SC-002, SC-003, SC-004.

### Group 2

#### T003 — The row's rules and the rebuilt stylesheet

**Files**: `mvp/tailwind/base.css`, `mvp/static/css/django-mvp.css`,
`mvp/static/css/django-mvp.css.br`, the nearest existing stylesheet coverage test

Port the agreed styles from the reference stylesheet and its pointer rules under `mvp-row-`, as
`plan.md`, "The stylesheet" lists them. The row's offset custom property is `--mvp-row-x`. Colours are theme variables
(`--color-base-content`, `--color-primary`, `--color-error` and their `-content` pairs). The pointer
rules show `.mvp-row-dropdown` for `(pointer: fine)` and, only inside `[data-mvp-row-ready]`, hide it
and show `.mvp-row-sheet-trigger` for `(pointer: coarse)`. One block with a comment header. Rebuild
with `uv run invoke build-stylesheet`. The browser tests cover placement.

#### T004 — `mvpRowActions`: the layer under the row and the menu in the sheet

**Files**: `assets/js/row_actions.js`, `assets/js/index.js`, `mvp/static/js/django-mvp.js`,
`tests/test_components/test_list_row_e2e.py`, `tests/test_frontend_runtime.py`

`registerRowActions(Alpine)` with the `mvpRowActions` data component (ADR 0035). `init` builds
`.mvp-row-under` after the face: one `<button type="button" class="mvp-row-button ...">` per
`[data-mvp-row-action]` item, with the item's first icon element cloned and its ids removed, the
item's `aria-label` or words, a tone class (`danger`, `primary` for the main action, `neutral`), and
`data-mvp-row-button`. A button's click presses the item. The layer is `inert`. `init` sets
`data-mvp-row-ready` on the row. The menu moves into `[data-mvp-row-sheet-body]` when
`mvp-sheet-open` on `window` names the row's sheet and back into the dropdown's panel when the
sheet's `close` fires. A click on an action inside the sheet closes the sheet in a `setTimeout`.
Register in `index.js` with a comment as the other modules have, rebuild the bundle with
`npm run build:js:prod`. Tests (real browser): US1 1 (under buttons equal the items, ids and form
hooks still once on the whole page), US2 16 (mouse at desktop width: the dropdown opens and offers
every action), 17 (touch at phone width: the sheet opens with every action, and closes once one is
chosen, the menu is back in the dropdown afterwards), 18 (keyboard: tab reaches the ⋯, opens the
menu, runs every action, and the under buttons are not in the tab order), 20 (a button's name),
and the edge case that without the script the dropdown still opens (the module's removal is
simulated by the row not being set up).

### Group 3

#### T005 — The touch swipe

**Files**: `assets/js/row_actions.js`, `tests/test_components/test_list_row_e2e.py`

Port the reference script's touch half into the component as `plan.md`, "The script", describes:
the constants named at the top, `touch` only (D1), direction from the page's (D2), the face
narrowing through `--mvp-row-x`, release rules (half the buttons, flick speed, 60% with a main
action, the resist with none), the 20 px edge guard, mostly-vertical movement left to the page,
one open row with every close (another row's swipe, tap elsewhere, tap on the row, scroll,
Escape), the swallowed click after a swipe and after a tap on an open row, Escape with focus inside
returning focus to the row's content, `inert` while closed, the 60% vibration cue once. State classes
`is-open`, `is-dragging`, `is-full`. Tests (touch through the protocol): US2 1, 2, 3 (the main action
is pressed), 4 (vibrate called once), 5, 6, 7, 8, 9, 10, 11, 19, a right-to-left page swiping the
mirror way, a swipe the other way giving a little, and a mouse drag not moving the row.

#### T006 — The trackpad, the commit, the fold and its undo

**Files**: `assets/js/row_actions.js`, `tests/test_components/test_list_row_e2e.py`

Port the wheel half: a sideways wheel (`|deltaX| > |deltaY|`) moves the row as a finger does and
settles 140 ms after the last event (US2 12). The commit slides the face out and presses the main
item. A `leaves` item folds the row and a non-leaving one closes it (FR-016). The row observes
`click` on its items: a `leaves` item folds the row from the menu too. `htmx:responseError`,
`htmx:sendError` and `htmx:timeout` from an item unfold the row (US2 14, SC-004). Tests: US1 6,
US2 2 (running an action closes the row), 12, 14 (a failing htmx request puts the row back), and a
main action with no `leaves` closing rather than folding.

### Group 4

#### T007 — `window.mvpRows`, the reorder announcements and rows that arrive by htmx

**Files**: `assets/js/row_actions.js`, `docs/developer/list-rows.md`, `tests/test_components/test_list_row_e2e.py`

The script interface and the announcements it answers go into `docs/developer/list-rows.md` here.

`window.mvpRows = { off(list), on(list), shut() }` as `plan.md` describes, and a `document` listener
for `mvp:reorder-start` and `mvp:reorder-end` that counts per announcing element. The attribute
`data-mvp-rows-off` is present while the count is above zero or the developer's flag is set.
Switching off shuts an open row in that list and leaves the menus working. Rows added by an htmx
swap swipe and open their menus unaided. Tests: US1 7, 8, 9, 10 (a real `c-mvp.reorder` list's own
announcements, including nested pairs, leave swiping off until the outer pair ends), 11. The list a
row sits in is found by `closest`, so a list inside a reorder root counts.

#### T008 — The first-time nudge and reduced motion

**Files**: `assets/js/row_actions.js`, `mvp/tailwind/base.css`, `mvp/static/css/django-mvp.css`,
`mvp/static/css/django-mvp.css.br`, `tests/test_components/test_list_row_e2e.py`

The nudge per `plan.md`: coarse primary pointer, the first swipeable row wholly in view, once per
browser through `localStorage["mvp-row-hinted"]`, at most 4.5 rem open and back. Reduced motion
removes every transition of the row (the stylesheet already carries the rule from T003; the nudge
and the fold are checked here). Tests: US2 13 (nudged once, never again after a reload), 15 (with
reduced motion emulated the face's computed transition duration is effectively zero and the row
still ends in the right state), and no nudge for a mouse or with no row in view.

---

## Phase 3: Documentation (P1)

### Group 5

#### T009 — The demo, the documentation, the glossary, the README, the changelog and the ADR

**Files**: `demo/component_docs.py`, `demo/templates/demo/components/list-row.html`,
`tests/test_demo/test_list_row_demo.py`, `docs/developer/list-rows.md`, `docs/components.md`, `docs/index.md`,
`README.md`, `CHANGELOG.md`, `CONTEXT.md`, `skills/django-mvp/SKILL.md`,
`docs/adr/NNNN-a-rows-actions-are-declared-once-as-its-menu.md`

FR-030. The demo page shows a list of actionable rows: a link action, a button action, an htmx
action that leaves (a demo view that answers and one that fails, so the undo can be seen), a form
hook action, a row with a main action, a row with none, a row with no actions at all, and a list
whose swiping a button switches off and on through `window.mvpRows`. `docs/developer/list-rows.md` describes
how to give a row its actions, how to mark the main action and an action that takes the row out of
the list, the data attributes, the script interface and the reorder announcements it answers, and
why the menu is the keyboard path. `docs/components.md` gains the two components. `CONTEXT.md`
gains **List row**, **Row action**, **Main action** and **Row menu** (D9). ADR number: the next
free on `origin/main` when pushing. Decision: the swipe layer is built from the menu's items, which
are drawn once. Tests for the demo as `test_reorder_demo.py` does.
