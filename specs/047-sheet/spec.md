# Feature Specification: Sheets for phones and wide screens

**Feature Branch**: `047-sheet`

**Created**: 2026-11-22

**Status**: Draft

**Serves**: G2 (a component library covering what a data-centric web application needs, with
small attribute APIs and deliberately limited variation), G5 (a polished, modern look and feel
out of the box). It keeps to G6 and G14: the sheet needs no build tooling in a project, and its
script and styles ship inside the package.

**Roadmap**: none. No roadmap item covers a sheet. This may be a gap in the roadmap.

**Issue**: https://github.com/django-mvp/django-mvp/issues/687

**Input**: On a phone, menus and short forms are easiest to reach in a sheet that rises from the
bottom of the screen. On a wider screen the same content reads better as a dialog in the middle
of the page. django-mvp has a modal but nothing that changes between the two, so projects build
their own sheet, each slightly differently.

After this feature, a developer puts a menu, a short form or a few steps in one sheet. On a
narrow screen it rises from the bottom edge with a grab bar, and answers touch the way a phone's
own sheets do: dragged up it grows to the full height of the screen, dragged down it shrinks
back or closes, and a quick flick counts as much as a long drag. On a wide screen it is a dialog
in the middle of the page, with no grab bar and no dragging. It switches between views inside
itself, such as a menu and then a confirmation, and it can open a second sheet from the first and
put focus back where it belongs when that one closes. It closes on Escape and on a tap outside
it, and where scripts do not run its trigger is a plain link to a page that offers the same
thing.

The look is agreed. Its templates and styles are carried into the package at build time and
cleaned to its standards, not redrawn. How it is built is left to research and planning, with the
notes in `planning-notes.md`.

## Clarifications

### Session 2026-11-22

All answered from the issue and the agreed design. The reasoning for each is in `decisions.md`.

- Q: At what width does a sheet change from the bottom of the screen to the middle? → A: One
  width for every sheet, the package's small breakpoint, which is the one daisyUI's own
  responsive modal classes use (D1).
- Q: What are a sheet's heights on a narrow screen? → A: Two, like the platform sheets' resting
  and full detents. It opens at its resting height, which is the height of its content up to a
  limit that leaves the page visible above it. Its full height fills the screen below its top
  edge (D2).
- Q: Can a sheet whose content already shows in full at its resting height be dragged taller? →
  A: Yes. On a phone every sheet can be dragged up to its full height, as the platform sheets'
  resting and full detents can. A developer can fix a sheet at its resting height instead, and
  that sheet follows the finger a little and settles back (D3).
- Q: Where does a drag start? → A: On the grab bar and the sheet's head. A drag inside the body
  scrolls the body, so lists, sliders and fields inside a sheet keep working (D4).
- Q: How does a flick decide where the sheet goes? → A: A release settles at the nearest height,
  or closes, by where the sheet is. A release fast enough to count as a flick moves one step in
  its direction instead: from resting, up to full or down to closed; from full, down to resting
  (D5).
- Q: How does a person who cannot drag reach the full height? → A: The grab bar is also a
  control. Tapping it, or activating it from the keyboard or assistive technology, switches
  between the resting and the full height, as the platform drag handles do (D6).
- Q: What happens to an open sheet when another sheet opens? → A: It closes first. One sheet is
  open at a time. A sheet opened from inside another gives focus, when it closes, to the element
  the developer named, usually the trigger of the first sheet (D7).
- Q: Can a developer open a sheet at its full height? → A: Yes, for content that is long by
  nature, such as a list to pick from. Such a sheet can still be dragged down to its resting
  height or closed (D8).
- Q: What does a trigger do where scripts do not run? → A: Given an address, it is a plain link
  to a page that offers the same thing. Given none, it needs scripts, and the documentation says
  so (D9).
- Q: What closes a sheet? → A: Escape, a tap outside it, its closing control, a drag or flick
  down on a narrow screen, and the developer's own controls. None of them changes anything or
  submits a form the sheet sits inside (D10).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A developer puts a menu, a short form or a few steps in a sheet (Priority: P1)

A developer building on django-mvp gives an item or a page a sheet. They place a trigger where the
item's actions belong, in its title row, and name the sheet it opens and, optionally, the page
that offers the same actions where scripts do not run. They give the sheet a title and,
optionally, a line under it, an icon or a small piece of art before it, and a description. Inside
it they put a menu of actions, each an icon and words, as links or as buttons that submit a form,
with a destructive action marked as such; or a short form; or several named views, which any
element in the sheet switches between, such as a menu and a confirmation. They choose the buttons
at its foot, or leave the default one that closes it. They can ask for it to open at its full
height, to stay at its resting height, or to be wider on a wide screen. From anywhere on the page they can open a sheet at one of
its views, and from inside a sheet they can open another, naming where focus returns when it
closes.

**Why this priority**: Nothing reaches a user until a developer can build a sheet, and the menu,
the trigger and the views are the surface other features build on, starting with the row actions
of FS-048 (https://github.com/django-mvp/django-mvp/issues/688).

**Independent Test**: In a test template, render a trigger and a sheet holding a menu, a
confirmation view and a form, and assert on the rendered markup: the sheet is a dialog named by
its title, the trigger names it and carries the fallback address, each view is present and only
the first is shown, and the foot holds the developer's buttons in place of the default.

**Acceptance Scenarios**:

1. **Given** a sheet with a title, **When** it renders, **Then** it is a modal dialog whose
   accessible name is that title, and it is closed until something opens it.
2. **Given** a sheet with a line under its title, an icon or art, and a description, **When** it
   renders, **Then** each appears in the sheet's head, the art is hidden from assistive
   technology, and the description is the dialog's accessible description.
3. **Given** a trigger naming a sheet and a fallback address, **When** it renders, **Then** it
   is a link to that address that announces it opens a dialog and carries an accessible name
   saying which item it is for.
4. **Given** a trigger with a fallback address, **When** scripts do not run and a user activates
   it, **Then** the browser follows the link to that address.
5. **Given** a trigger with no fallback address, **When** it renders, **Then** it is a button,
   and the documentation says such a trigger needs scripts.
6. **Given** a menu of actions in a sheet, some links and some buttons that submit a form,
   **When** it renders, **Then** each action is a link or a button with its icon hidden from
   assistive technology and its words as its name, and a destructive action is marked as such.
7. **Given** a sheet with several named views, **When** it renders, **Then** only its first view
   is shown, and an element inside the sheet that names another view switches to it when
   activated.
8. **Given** a sheet with buttons given for its foot, **When** it renders, **Then** they take the
   place of the default closing button. **Given** none, **Then** the foot holds one button that
   closes the sheet.
9. **Given** an element anywhere on the page that asks for a sheet by its id and one of its views,
   **When** it is activated, **Then** that sheet opens showing that view.
10. **Given** a trigger inside a sheet that opens a second sheet and names an element to return
    focus to, **When** the second sheet closes, **Then** focus goes to the named element, or to
    the trigger itself when none is named.
11. **Given** a sheet the developer asks to open at its full height, **When** it opens on a
    narrow screen, **Then** it is at its full height.
12. **Given** a sheet the developer fixes at its resting height, **When** it renders, **Then** its
    grab bar offers no change of height, and it still closes when dragged down.
13. **Given** a sheet the developer asks to be wide, **When** it renders, **Then** it carries the
    package's wide size for the centred dialog, and narrow screens are unaffected.
14. **Given** a sheet placed inside a form, **When** any of its own closing controls is used,
    **Then** the form is not submitted.
15. **Given** a page with a sheet, **When** it loads, **Then** no script, stylesheet or font is
    requested from any origin other than the site's own.

---

### User Story 2 - A user opens a sheet and works in it, on any screen (Priority: P1)

A user taps or clicks an item's trigger. On a narrow screen the sheet rises from the bottom edge;
on a wide screen it opens as a dialog in the middle of the page. Focus moves into it and stays
there while it is open. They pick an action, fill in the short form, or move to a confirmation and
back. They close it with Escape, by tapping outside it, or with its closing button, and nothing
changes. Focus returns to the trigger, or to wherever the developer named, and the next time the
sheet opens it shows its first view again.

**Why this priority**: This is what the sheet is for.

**Independent Test**: In a real browser at a phone's size and at a desktop's size, open a sheet
from its trigger, move to its confirmation view and back, press Escape, and confirm the sheet is
closed, focus is on the trigger, and reopening it shows the menu.

**Acceptance Scenarios**:

1. **Given** a narrow screen, **When** the user opens a sheet, **Then** it is anchored to the
   bottom edge of the screen and shows its grab bar.
2. **Given** a wide screen, **When** the user opens the same sheet, **Then** it is centred on the
   page and shows no grab bar.
3. **Given** a sheet that opened, **When** the user presses Tab repeatedly, **Then** focus moves
   through the sheet's controls and never reaches the page behind it.
4. **Given** an open sheet, **When** the user presses Escape, taps outside the sheet or uses its
   closing button, **Then** it closes, nothing is submitted, and focus returns to the element that
   opened it.
5. **Given** a sheet showing a view other than its first, **When** it closes and is opened again,
   **Then** it shows its first view.
6. **Given** a sheet showing a confirmation view reached from its menu, **When** the user goes
   back, **Then** the sheet shows the menu and stays open.
7. **Given** an open sheet, **When** the user opens a second sheet from a trigger inside it,
   **Then** the first sheet closes, the second opens, and only one sheet is open.
8. **Given** an open sheet, **When** something on the page opens a different sheet, **Then** the
   open one closes first.
9. **Given** a sheet whose content is taller than the space it has, **When** the user scrolls
   its body, **Then** the body scrolls, its head stays in view, and the page behind does not
   scroll.
10. **Given** a short form in a sheet on a phone, **When** the user focuses one of its fields and
    the on-screen keyboard opens, **Then** that field stays visible.
11. **Given** a user who prefers reduced motion, **When** a sheet opens or closes, **Then** it
    appears and disappears without sliding.

---

### User Story 3 - A user on a phone drags a sheet taller to see more of it, or down to close it (Priority: P1)

A user on a phone sees a sheet at its resting height with the page still visible above it. They
drag its grab bar up and the sheet follows their finger to its full height, where its body
scrolls through everything it holds. They drag it down again and it returns to its resting height;
dragged down from there, it closes. A quick flick up or down counts as much as a long drag. A user
who cannot drag taps the grab bar, or activates it from the keyboard or a screen reader, to switch
between the two heights.

**Why this priority**: This is how a phone's own sheets behave, and a sheet that ignores the finger
reads as a web page imitating one. It was asked for in so many words.

**Independent Test**: In a real browser emulating a phone with touch, open a sheet whose content is
taller than its resting height, drag its grab bar up and confirm it is at its full height, flick it
down and confirm it is at its resting height, then drag it down past its resting height and confirm
it is closed.

**Acceptance Scenarios**:

1. **Given** a sheet at its resting height, **When** the user drags the grab bar up and lets go near the top, **Then** the sheet is at its full height.
2. **Given** a sheet at its full height, **When** the user drags it down and lets go nearer the
   resting height than the full one, **Then** the sheet is at its resting height and still open.
3. **Given** a sheet at its resting height, **When** the user drags it down and lets go well below
   that height, **Then** the sheet closes, nothing is submitted, and focus returns to the element
   that opened it.
4. **Given** a sheet at its resting height, **When** the user drags it down only a little and lets
   go slowly, **Then** it settles back at its resting height.
5. **Given** a sheet at its resting height, **When** the user flicks it up a short distance,
   **Then** it is at its full height. **When** the user flicks it down a short distance, **Then**
   it closes.
6. **Given** a sheet at its full height, **When** the user flicks it down a short distance,
   **Then** it is at its resting height and still open.
7. **Given** a sheet whose content already shows in full at its resting height, **When** the user
   drags it up and lets go near the top, **Then** it is at its full height. **Given** a sheet the
   developer fixed at its resting height, **When** the user drags it up and lets go, **Then** it
   settles back at its resting height.
8. **Given** a sheet at its full height, **When** the user drags inside its body, **Then** the body
   scrolls and the sheet keeps its height.
9. **Given** the user is dragging a sheet, **When** the finger moves, **Then** the sheet follows
   it and the page behind does not scroll.
10. **Given** a sheet at either height that the developer has not fixed at its resting height,
    **When**
    the user taps the grab bar or activates it from the keyboard, **Then** the sheet switches to
    the other height, and the grab bar tells assistive technology which height the sheet is at.
11. **Given** a sheet that was at its full height, **When** it closes and opens again, **Then** it
    opens at its resting height, or at its full height when the developer asked for that.
12. **Given** a wide screen, **When** the user presses and moves the pointer on the sheet's head,
    **Then** the sheet does not move.
13. **Given** a user who prefers reduced motion, **When** they let go of a drag, **Then** the sheet
    goes straight to the height or the closed state it settles at, without animating there.

---

### Edge Cases

- A screen that turns from narrow to wide while a sheet is open, such as a tablet rotated, shows
  the sheet as a centred dialog, still open and on the same view. Turned back, it is at its resting
  height.
- A sheet opened while another is being dragged closes the dragged one, like any other open
  sheet.
- A second finger landing during a drag does not move the sheet twice as far. The drag follows the
  first finger.
- A drag that starts on the head and leaves the screen, or is interrupted by the browser, settles
  as a release at the last position.
- A trigger whose sheet is not on the page, such as one left behind after a template change, falls
  back to its address when it has one, and otherwise does nothing rather than raising an error.
- An element that asks for a view the sheet does not have opens the sheet at its first view.
- A sheet with no title is a developer mistake, and the documentation says the title is required
  because it names the dialog.
- A page holding many sheets, such as a list with one per row, opens and closes each on its own,
  and only the open one listens for drags.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The package MUST provide a sheet: a modal dialog with a head holding a required
  title, an optional line under it, an optional icon or art and an optional accessible
  description, a body, and a foot. (US1)
- **FR-002**: The sheet MUST be drawn on daisyUI's modal box inside daisy-cotton's `c-modal`, as
  `c-mvp.modal` is, and MUST take its placement on narrow and wide screens from daisyUI's own
  responsive modal placement. (US1, US2)
- **FR-003**: The package MUST provide a trigger that opens a named sheet, announces that it opens
  a dialog, takes an accessible name for the item it belongs to, and falls back to a plain link
  where scripts do not run when it is given an address. (US1)
- **FR-004**: The package MUST provide a menu for a sheet's body whose actions are each an icon and
  words, as a link or as a button that submits a form, with a way to mark an action destructive.
  The trigger and the menu are public components that other components may place. (US1)
- **FR-005**: A sheet MUST be able to hold several named views, show only its first when it opens,
  switch between them from any element inside it, and return to its first view whenever it
  closes. (US1, US2)
- **FR-006**: Any element on the page MUST be able to open a sheet by its id, at one of its views,
  falling back to the first view when the named one does not exist. (US1)
- **FR-007**: A trigger inside a sheet MUST be able to open another sheet, closing its own first,
  and MUST return focus, when the other closes, to the element the developer named or to itself.
  (US1, US2)
- **FR-008**: At most one sheet MUST be open at a time. Opening a sheet closes any other first.
  (US2)
- **FR-009**: The foot MUST hold the developer's buttons when given, and otherwise one button that
  closes the sheet. (US1)
- **FR-010**: Escape, a tap or click outside the sheet, its closing button and a drag or flick
  that closes it MUST close it without submitting anything, including a form the sheet sits
  inside, and MUST return focus to the element that opened it. (US1, US2, US3)
- **FR-011**: While a sheet is open, focus MUST stay inside it and the page behind it MUST NOT
  scroll. (US2)
- **FR-012**: A body taller than the space it has MUST scroll inside the sheet with the head kept
  in view. (US2, US3)
- **FR-013**: A field focused in a sheet on a phone MUST stay visible when the on-screen keyboard
  opens. (US2)
- **FR-014**: On a narrow screen a sheet MUST have two heights: a resting height that is its
  content's height up to a limit leaving the page visible above it, and a full height filling the
  screen below its top edge. It MUST open at its resting height unless the developer asks for its
  full height. (US1, US3)
- **FR-015**: On a narrow screen, a drag that starts on the grab bar or the head MUST move the
  sheet with the finger, and on release MUST settle it at the nearest of its full height, its
  resting height and closed, except that a release fast enough to be a flick MUST move it one step
  in the flick's direction. (US3)
- **FR-016**: On a narrow screen every sheet MUST be able to reach its full height by a drag, a
  flick or its grab bar, whether or not its content already fits at its resting height, unless the
  developer fixes it at its resting height. A fixed sheet MUST settle back at its resting height
  after a drag up and MUST still close when dragged or flicked down. (US1, US3)
- **FR-017**: A drag inside the body MUST scroll the body and MUST NOT move the sheet. (US3)
- **FR-018**: The grab bar MUST be a control that, on a sheet not fixed at its resting height,
  switches between the two heights when tapped or activated from the keyboard, and MUST tell
  assistive technology which height the sheet is at. (US3)
- **FR-019**: On a wide screen a sheet MUST be centred, MUST NOT show the grab bar and MUST NOT
  respond to dragging. A developer MUST be able to ask for it to be wider there. (US1, US2, US3)
- **FR-020**: Every sheet MUST change between its narrow and wide forms at the same screen width.
  (US2)
- **FR-021**: Where the user prefers reduced motion, opening, closing and settling after a drag
  MUST happen without animation, while a drag still follows the finger. (US2, US3)
- **FR-022**: The sheet's script and styles MUST ship inside the package's own bundled script and
  stylesheet. Nothing it needs is fetched from another origin. (US1)
- **FR-023**: The documentation and the demo MUST show a sheet holding a menu with a confirmation
  view, a sheet holding a short form, a sheet opened from another sheet, and a sheet opened at its
  full height. (US1)

### Key Entities

- **Sheet**: a dialog that rises from the bottom of a narrow screen and sits centred on a wide one.
  Has an id, a title, an optional line under it, optional art, an optional description, a body, a
  foot, a current view and, on a narrow screen, a current height.
- **View**: one named panel of a sheet's body, shown while it is the sheet's current view. The
  first view is the one a sheet opens at.
- **Trigger**: the control that opens a sheet. Names the sheet, the item it is for, optionally the
  page offering the same thing and, inside another sheet, where focus returns.
- **Height**: on a narrow screen, resting or full. A sheet that is neither is closed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer gives an item a sheet of actions with a confirmation view writing only
  template markup: no stylesheet and no script of their own.
- **SC-002**: In real-browser tests at a phone's size with touch, a user reaches each of open at
  resting height, open at full height and closed, by a drag and by a flick, from every state it
  can be reached from.
- **SC-003**: At both a phone's and a desktop's size, a user opens a sheet, uses every action in
  it, moves between its views and closes it with the keyboard alone, and focus ends on the element
  that opened it every time.
- **SC-004**: With scripts turned off, every trigger given an address reaches a page offering the
  same actions.
- **SC-005**: A page holding sheets requests nothing from any origin other than the site's own.

## Assumptions

- The sheet is drawn on daisyUI's own modal box inside daisy-cotton's `c-modal`, the same base
  `c-mvp.modal` was redrawn on (https://github.com/django-mvp/django-mvp/issues/684). This
  feature is built after that merge.
- The browser's own `<dialog>` supplies Escape, the focus trap and, on Android, closing with the
  system back gesture. They are not specified again here, only relied on.
- The row actions feature (https://github.com/django-mvp/django-mvp/issues/688) places this
  feature's trigger and menu on touch screens. Its swipe gestures on list rows are its own and not
  part of this specification.
- The resting height's limit, the distance and speed that count as a flick, and the animation's
  timing are research and planning decisions, taken from the platforms' documented behaviour.
  None of them is pinned here.
- The look, the wording and the sizes come from the agreed design and are ported, not specified
  here.
