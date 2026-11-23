# Implementation Plan: Swipe and menu actions on list rows

**Branch**: `048-row-actions` · **Spec**: [spec.md](spec.md) · **Research**: [research.md](research.md)

## Summary

Two Cotton components under `mvp/templates/cotton/mvp/list/row/`: `c-mvp.list.row` (over daisy-cotton's
`c-list.row`) and `c-mvp.list.row.action` (a thin wrapper of `c-mvp.sheet.menu.item`). One
registered Alpine component, `mvpRowActions`, in `assets/js/row_actions.js`. A block of rules in
`mvp/tailwind/base.css` under `mvp-row-`. One default icon name, `ellipsis`. One template filter
that rejects a second main action. The look is ported from the agreed design, never redrawn: its
structure, its numbers and its animation carry across, its class names become `mvp-row-` and its
colours become theme variables (`research.md`, "What the agreed look is made of").

## Technical context

- Python 3.12+, Django 5.2, 6.0 and 6.1. No new Python or npm dependency.
- Front-end assets are committed build artifacts: `npm run build:js:prod` and
  `uv run invoke build-stylesheet` after editing `assets/js/` or `mvp/tailwind/base.css`.
- Rendered-markup tests with `cotton_render_string_soup` in `tests/test_components/test_list_row.py`.
  Real-browser tests in `tests/test_components/test_list_row_e2e.py`, because the gesture, focus,
  the pointer media queries and the page behind are computed and cannot be read from markup. Touch
  is driven through the DevTools protocol at a phone viewport with touch enabled, as the sheet's
  tests do. A mouse and a keyboard are driven at desktop width.
- The behaviour is a registered Alpine component (ADR 0035). The markup carries configuration only.

## The one declaration, and what is drawn from it (D10, FR-002, FR-005)

A developer writes each action once, as a `c-mvp.list.row.action` in the row's `actions` slot. The
template draws it **once**: as an item of the row's menu. There is no second copy in markup.

The swipe's buttons are built by the row's script from those items when the row starts. Each is a
plain `<button type="button">` with the item's icon (cloned, ids removed) and words, carrying no id,
no form hook and no htmx attribute. Pressing it presses the item (`item.click()`), so the link,
form or htmx request is exactly the item's own. Nothing the developer gave an action appears twice.
Without script the buttons never exist and the menu is the whole interface (FR-027).

Considered and not taken: drawing the actions twice and putting ids on one (a developer's `id`
would then depend on which copy the script reads), and one set of elements restyled between a swipe
layer and a menu (the menu has to sit in a dropdown and a sheet, and the swipe layer under the row).

## The markup contract

`<c-mvp.list.row id label lead face_class class>` with slots: default (the row's content) and `actions`.

- `id` is required when there are actions: it names the sheet (`{id}-sheet`) and the menu. `label`
  is the row's name: the sheet's title and the ⋯ button's accessible name ("More for {label}").
  `lead` is the line under the sheet's title. `face_class` classes the face. `class` the item.
- **No actions** (empty `actions` slot): renders `c-list.row` with the content and nothing else, no
  `x-data`, no ⋯ (FR-003).
- **With actions**: `<c-list.row class="mvp-row" x-data="mvpRowActions" data-mvp-row>` holding
  1. `div.mvp-row-face` (carries `list-row` and `face_class`): the content, then the ⋯ control,
  2. `c-mvp.sheet id="{id}-sheet" title="{label}" lead="{lead}"` whose body holds an empty
     `div[data-mvp-row-sheet-body]`.
  The under layer is not in markup. The script adds `div.mvp-row-under` after the face.
- **The ⋯ control** (`.mvp-row-more`, inside the face): a `c-mvp.dropdown` (`class="mvp-row-dropdown"`,
  `halign="end"`, trigger a ghost square small button with `c-icon name="ellipsis"` and
  `aria-label="More for {label}"`) whose panel holds `<c-mvp.sheet.menu data-mvp-row-menu>{{ actions }}</c-mvp.sheet.menu>`,
  and a `c-mvp.sheet.trigger for="{id}-sheet" label="{label}" icon="ellipsis" class="mvp-row-sheet-trigger"`.
  CSS: the dropdown shows for `(pointer: fine)` and the sheet trigger is hidden. For
  `(pointer: coarse)`, and only inside a row carrying `data-mvp-row-ready`, the dropdown is hidden and
  the sheet trigger shown. A page with no script therefore shows the dropdown everywhere (FR-027).
- **The menu moves, it is not copied.** The script moves `[data-mvp-row-menu]` into the sheet's
  body when `mvp-sheet-open` names this row's sheet, and back into the dropdown's panel when the
  sheet's `close` event fires. A click on an action inside the sheet closes the sheet after the
  action's own click has run (a `setTimeout`, so a link or form still proceeds).
- `<c-mvp.list.row.action text icon href danger main leaves label type class>`: renders
  `c-mvp.sheet.menu.item` with `data-mvp-row-action`, `data-mvp-row-main` when `main`,
  `data-mvp-row-leaves` when `leaves`, `aria-label="{label}"` when given (FR-023), and `:attrs`.
  `id`, `form`, `hx-*` and the rest land on the link or button as the sheet menu item already does.
- **A second main action** (FR-006): the row passes its rendered `actions` through a template filter
  `single_main_action` (in `mvp/templatetags/mvp.py`) that counts `data-mvp-row-main` and raises
  `ImproperlyConfigured` naming the row's `id` when it finds more than one. A template cannot raise,
  so a filter is the least machinery.
- A dangerous action is `danger`, as the sheet menu has it. Tone of an under button: `danger` when
  the item is marked so, `primary` for the main action otherwise, `neutral` for the rest.

## The script (`assets/js/row_actions.js`, exported `registerRowActions(Alpine)`)

`Alpine.data("mvpRowActions", rowActions)`. State lives in the factory's closure as the reorder
module does, and module-level state for what is shared by every row: the one open row, the drag in
progress, and the set of lists switched off.

- **Setup (`init`)**: build `.mvp-row-under` from the items (icon cloned with ids removed, the item's
  words or `aria-label` as the name), set `inert` on it, set `data-mvp-row-ready` on the row, register
  the row, wire the menu move (above). `destroy` removes the row's listeners and shuts it if open.
- **Constants** (named, at the top): slop 8 px, edge guard 20 px, full share 0.6, flick 0.45 px/ms,
  resting width of a button 4.75 rem, vibration 8 ms, hint key `mvp-row-hinted`.
- **Which pointers move a row (D1)**: `pointerType === "touch"` only. A mouse never drags. A wheel
  with `|deltaX| > |deltaY|` (a trackpad's two-finger swipe) moves it as a finger does and settles
  after 140 ms without wheel events.
- **Direction (D2)**: every offset is measured *towards the start of the line*. `dir` is `+1` on a
  left-to-right page and `-1` on a right-to-left one, read from the row's computed `direction`
  at the start of each gesture. Travel = `-dir * dx`. A swipe the other way gives at most 16 px
  (a fifth of the movement) and settles. The face narrows and the layer widens through the custom
  property `--mvp-row-x` and logical CSS, which already mirror.
- **Release (FR-009, FR-010, FR-011)**: past 60% of the row's width with a main action: commit. A flick
  (above the flick speed) opens or closes whatever the offset. Otherwise open when past half the
  buttons' width, else close. With no main action the drag resists past the buttons (a quarter of
  the extra) and settles open. The vibration cue fires once as 60% is passed.
- **Commit**: slide the face out, then press the main item. A main action that `leaves` folds the
  row first. Otherwise the row closes after the item's click.
- **One open row (FR-012)**: module state `open`. A pointerdown elsewhere, another row's drag, a
  page scroll (`scroll` on `window`, passive), `Escape` and a tap on the open row itself close it;
  the tap's click is swallowed so its link is not followed. A drag's ending click is swallowed
  for 400 ms (FR-013).
- **Edges and axis (FR-014)**: a touch starting within 20 px of either screen edge is ignored. A
  movement that is mostly vertical hands over to the page, which scrolls (`touch-action: pan-y`).
- **Fold and restore (FR-016, FR-017)**: the item's click is observed on the row. A `leaves` item folds
  the row (height to 0). `htmx:responseError`, `htmx:sendError` and `htmx:timeout` from an item
  in the row unfold it. A closed non-leaving action closes the row.
- **Focus (FR-021, FR-022)**: the under layer is `inert` while the row is closed, so a keyboard user
  reaches actions through the menu. `Escape` with focus inside the row closes it and focuses the
  first focusable thing in the face that is not in `.mvp-row-more`.
- **The nudge (FR-018)**: on a coarse primary pointer, when the first swipeable row of the page is
  wholly in view and `localStorage["mvp-row-hinted"]` is unset, set it and open the row by at most
  4.5 rem and back once. Reduced motion shortens the transitions to nothing, so it jumps.
- **The interface (FR-024, FR-025)**: `window.mvpRows = { off(list), on(list), shut() }`, the only
  global. `off` writes `data-mvp-rows-off` on the list element and shuts an open row inside it.
  `on` removes it. A row ignores gestures when `row.closest("[data-mvp-rows-off]")` finds one.
  A `document` listener answers `mvp:reorder-start` and `mvp:reorder-end` on `event.target` by
  counting: the attribute is present while the count is above zero or the developer's own flag
  is set. The menu is never switched off.
- **Rows that arrive by htmx (FR-026)**: Alpine runs `init` on each. The nudge also looks again.

## The stylesheet (`mvp/tailwind/base.css`, block `/* Row actions (FS-048) */`)

Ported from the agreed design under `mvp-row-`: `.mvp-row` (position, isolation, `touch-action: pan-y`,
the height and opacity transition for folding), `.mvp-row-face` (the face narrows:
`width: calc(100% + var(--mvp-row-x))`), `.mvp-row-under` (`inset-inline-end: 0`, `width:
calc(-1 * var(--mvp-row-x))`), `.mvp-row-button` and its three tones, the full button's growth past
60%, state classes `is-open`, `is-dragging`, `is-hinting`, `is-committing`, `is-folded`, `is-full`,
clipping only while moving so the dropdown can open past the row, hover moved to the face, reduced
motion, and the pointer rules for `.mvp-row-dropdown` and `.mvp-row-sheet-trigger`. Colours are
daisyUI theme variables. The face carries `list-row`; the outer item is reset to a block with no
padding so the list's own divider stays on the item.

## Icons (FR-029)

`mvp/utils.py` default names gain `"ellipsis": "bi bi-three-dots"`. `docs/icons.md` lists it.

## Rules the design review settled

These sit beside the sections above and bind the build.

- **The row upgrades its own dropdown (htmx swaps).** `index.js` re-runs the dropdown setup only
  when a swap targets the body, and list pages swap the list region. `assets/js/dropdown.js` exports
  a per-wrapper upgrade that skips a panel already promoted, and `mvpRowActions.init` calls it for
  the row's dropdown, so rows that arrive by htmx open their menu in the top layer.
- **Reordering switches swiping off by state, not by counting.** A row is off while
  `row.closest("[data-mvp-rows-off], [data-reordering]")` finds one. The announcement listener shuts
  an open row on a start and abandons a drag in progress inside that list. A list replaced during a
  mode hands the mode on without a start, so no cross-element count is kept and none can go
  negative. `data-mvp-rows-off` is the one source of truth, not module state.
- **The drag-end click guard ignores clicks the script dispatches itself** (`isTrusted` false), so
  the commit's own press of the main item is not swallowed.
- **Fold on the request, not the click, for an htmx item.** A `leaves` item carrying an `hx-`
  request folds the row on `htmx:beforeSend` from that item, so a declined `hx-confirm` leaves the
  row shown. Other `leaves` items fold on click. Failure events unfold as before.
- **Scroll** is listened for on `document` in the capture phase, passive, so a scrolling container
  closes an open row.
- **A touch or wheel that starts inside the row's own dialog or dropdown panel starts no gesture.**
- **Escape** shuts the row and calls `preventDefault` so a containing dialog stays open. Focus
  returns to the first focusable thing in the face, else to the row's visible ⋯ control.
- **Choosing an action** closes the sheet and also hides the dropdown panel when open.
- **Every internal call to a Cotton component carries `only`** (ADR 0032), passing `:attrs` where
  attributes must reach the element.
- **One divider:** the item's own `list-row` divider is kept and the face's `::after` is set to
  `content: none`, matching the reference, where the item carries no `list-row` of its own.
- **The port is rule for rule.** The reference stylesheet and script are copied with its class prefix renamed
  `mvp-row-` and its custom property `--mvp-row-x`, including the radius rules, `user-select`, the per-state
  durations, the under layer's radius and the icon size. The only departures are the defects in
  `research.md` and the ones this plan lists. The built button keeps the reference button's structure:
  the tone class, `data-mvp-row-main`, the cloned icon, the words in a span, and `aria-label` only
  when the item has one.
- `single_main_action` also raises when the row's id is empty. The nudge guards `localStorage`
  against a throw. The feature builds as one sequential chain on one worktree, groups 1 to 5.

## Constitution check

| Article | How |
|---|---|
| I Testing | Test-first per task. Wording and design preferences (widths, spacing, colours) are not tested. Roles, names, focus, one open row, thresholds reached by gestures, ids once and the failure path are |
| II Simplicity | One script module, two templates, one filter, one icon name. No setting, no dependency, no new model |
| III Anti-abstraction | The action component has a present second use: the menu and the swipe layer both read it |
| V Security | Text and labels are escaped by the template layer. The script reads attributes and text, never markup from a request |
| VI Documentation | `docs/components.md` and `docs/developer/list-rows.md` land with the demo in the last group, with README, CHANGELOG, `CONTEXT.md` terms |
| VIII i18n | "More for {label}" comes from the sheet trigger and a `blocktranslate`; no other new string |
| XI Components are the public API | The two components, their properties, `window.mvpRows` and the data attributes the script reads are documented |
| XV Built artifacts | The JS bundle and the stylesheet are rebuilt and committed in the groups that edit their sources |

## Risks the design review should look at

- The swipe layer is built by script from the menu's items and presses them (`item.click()`).
- The one menu moves between the dropdown's panel and the sheet's body.
- The outer item stays `list-row` while the face also carries `list-row` (the divider is the item's).
