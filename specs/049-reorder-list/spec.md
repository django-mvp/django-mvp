# Feature Specification: Reorder a list by dragging

**Feature Branch**: `049-reorder-list`

**Created**: 2026-11-22

**Status**: Draft

**Serves**: G2 (a component library covering what a data-centric web application needs, with
small attribute APIs and deliberately limited variation), G4 (a usable front end for the Django
features that ship backend machinery without one)

**Roadmap**: none. No roadmap item covers reordering. This may be a gap in the roadmap.

**Issue**: https://github.com/django-mvp/django-mvp/issues/689

**Input**: Django formsets can be ordered (`can_order`), and many models carry a position field,
but django-mvp gives a person no way to set that order other than typing numbers. Projects that
need it each wire their own drag and drop.

After this feature, a developer makes a list reorderable and chooses where the order goes: into
a row set's `ORDER` fields, into the surrounding form as the rows in their new order, or straight
to the server each time the order changes. A person then drags a row by its handle while the
others move out of its way, or moves it a place at a time with up and down buttons, from a
mouse, a finger or a keyboard. A list that is normally read rather than edited can instead offer
a reorder mode, switched on by a control and ended by a control or by Escape, the way phone apps
offer an edit mode for reordering a list.

The look and the behaviour are already agreed. How it is built is left to research and planning,
with the notes in `planning-notes.md`.

## Clarifications

### Session 2026-11-22

All answered from the issue and the agreed design. The reasoning for each is in `decisions.md`.

- Q: Where can a new order go? → A: Three places, one per list: a row set's `ORDER` fields, a
  named field of the surrounding form carrying the rows in their new order, or an address posted
  to each time the order changes (D1).
- Q: Does the package also write the order to a model's position field? → A: Yes. A developer
  hands the received order and the records the person may reorder to one helper, which renumbers
  them and refuses anything outside those records (D2).
- Q: Is a list always reorderable, or only in a mode? → A: The developer chooses. In a form the
  list is reorderable whenever it is shown. A list that is read most of the time offers a reorder
  mode (D3).
- Q: What happens to rows swiped open for their actions? → A: While a list is being reordered,
  swiping its rows is off and any open row shuts. This uses the switch the row-actions feature
  (https://github.com/django-mvp/django-mvp/issues/688) provides (D4).
- Q: What happens when a posted order is refused by the server? → A: The list goes back to the
  order it had before that move and the person is told the change was not saved (D5).
- Q: Can a row be dragged from one list into another, or into a nested list? → A: No. A row
  moves within its own list. Lists are vertical (D6).
- Q: What does a person without scripts get? → A: The rows in their saved order. A row set keeps
  its `ORDER` number fields so the order can still be typed (D7).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A developer makes a list reorderable (Priority: P1)

A developer building on django-mvp lets people put a list in the order they want. For a row set
whose formset was built with `can_order`, they need do nothing more than render it with
`c-mvp.form.formset`: the rows become reorderable and the `ORDER` fields are filled from where the
rows sit. For any other list, such as the records shown on a page, they mark the list as
reorderable and choose where the order goes: a field of the surrounding form, which receives the
rows in their new order when the form is submitted, or an address the new order is posted to
each time it changes, whose answer replaces the list. They choose whether the list is
reorderable whenever it is shown or only in a reorder mode, which they start from a control they
place. When the order reaches their view, they save it to the model's position field with one
helper from the package.

**Why this priority**: Nothing can be reordered until a developer has made a list reorderable,
and this is where every safeguard on what may be reordered is decided.

**Independent Test**: In a test project, render a row set built with `can_order`, a list sending
its order with a form, and a list posting its order to an address. Move rows in each, submit or
let it post, and check the view received the rows in their new order and the helper saved it to
the position field.

**Acceptance Scenarios**:

1. **Given** a row set whose formset was built with `can_order`, **When** it is rendered with
   `c-mvp.form.formset`, **Then** each row can be dragged and moved up or down, and its `ORDER`
   value is not offered as a number to type.
2. **Given** that row set after a person has moved rows, **When** the form is submitted, **Then**
   every row's `ORDER` value matches where the row sat, and the formset's ordered rows come back
   in that order.
3. **Given** that row set, **When** a person adds a row, **Then** the new row starts at the end
   and can be moved like the others, and **When** a person removes a row, **Then** the remaining
   rows' order is still the order they sit in.
4. **Given** that row set, **When** a submission is invalid and the page is shown again, **Then**
   the rows appear in the order the person left them.
5. **Given** a list marked as reorderable that sends its order with the surrounding form under a
   name the developer chose, **When** the form is submitted, **Then** the view receives under that
   name the identifier of every row, in the order the rows sat.
6. **Given** a list marked as reorderable with an address to post to, **When** a person moves a
   row, **Then** the new order is posted to that address with the page's CSRF token, and the
   answer replaces the list.
7. **Given** a list the developer made reorderable only in a reorder mode, with a control they
   placed to start it, **When** the page loads, **Then** the list cannot be reordered until that
   control is used.
8. **Given** a received order and the records the person may reorder, **When** the developer
   hands both to the package's helper, **Then** those records' position field is renumbered to
   match, and records outside the list keep their positions.
9. **Given** a received order naming a record that is not among the records the person may
   reorder, or missing one that is, **When** the developer hands it to the helper, **Then** the
   helper refuses it and saves nothing.
10. **Given** a project that loads django-mvp's packaged base template, **When** a page holds a
    reorderable list, **Then** every script and style it needs comes with the package, and
    nothing is fetched from another site.
11. **Given** a page with two reorderable lists, **When** a person reorders one, **Then** the
    other's order and the order sent for it are unchanged.

---

### User Story 2 - A user reorders a list (Priority: P1)

A person using a site built on django-mvp puts the rows of a list in the order they want. With a
mouse or a finger they take hold of a row by its handle: the row lifts and follows the pointer,
the rows it passes move out of its way, and the page scrolls when the pointer nears the top or
bottom of the screen. Letting go drops the row in the gap. Anyone who cannot or would rather not
drag moves a row one place at a time with its up and down buttons, by mouse, finger or keyboard,
and hears where it now sits. On a list that offers a reorder mode, they start it from its
control, reorder, and end it from its control or with Escape.

**Why this priority**: This is what the feature is for.

**Independent Test**: In the demo, reorder a list by dragging with a mouse, by dragging with a
finger at phone width, and with the keyboard alone, then reload and check the saved order
matches.

**Acceptance Scenarios**:

1. **Given** a reorderable list, **When** a person presses a row's handle and moves the pointer,
   **Then** the row follows the pointer, the rows it passes move to make room, and letting go
   places it where the gap is.
2. **Given** a reorderable list on a touch screen, **When** a person drags from a row's handle,
   **Then** the row moves and the page does not scroll, the device gives a short vibration where
   it can, and **When** they drag anywhere else on the row, **Then** the page scrolls as usual.
3. **Given** a row being dragged, **When** the pointer nears the top or bottom edge of the screen,
   **Then** the page scrolls in that direction until the pointer moves away from the edge.
4. **Given** a row being dragged, **When** the person presses Escape, **Then** the drag ends and
   the row goes back to where it started.
5. **Given** a reorderable list, **When** a person uses a row's up or down button, **Then** the
   row swaps places with its neighbour, focus stays with the moved row, and a screen reader
   announces its new position.
6. **Given** the first row, **Then** its up button cannot be used, and **given** the last row,
   **Then** its down button cannot be used.
7. **Given** a reorderable list, **When** a person moves through it with Tab, **Then** they reach
   every row's up and down buttons and can use them with Enter or Space.
8. **Given** a list whose rows show their position, **When** a row moves, **Then** every row's
   position updates to where it now sits.
9. **Given** a person whose system asks for reduced motion, **When** rows move, **Then** they
   take their new places without animation.
10. **Given** a list that offers a reorder mode, **When** the person uses its control, **Then**
    each row shows its handle and its up and down buttons, and **When** they use the control that
    ends it or press Escape, **Then** the mode ends and the handles and buttons go.
11. **Given** a list whose rows can be swiped for their actions, **When** reordering starts,
    **Then** any row swiped open shuts and swiping is off until reordering ends.
12. **Given** a list that posts its order as it changes, **When** the server refuses or cannot be
    reached, **Then** the list goes back to the order it had before that move and the person is
    told the change was not saved.
13. **Given** a reorderable list inside a dialog, **When** the dialog is closed without its form
    being submitted, **Then** the list returns to the order it had when the dialog opened.
14. **Given** a page without scripts, **Then** the rows are shown in their saved order, and a row
    set still offers its `ORDER` fields to type into.

---

### Edge Cases

- A list with one row, or none, offers no handle and no up or down buttons.
- Rows added after the page loads, by a row set's add control or by an htmx swap, are
  reorderable like the rest.
- A row removed from a row set is skipped by the up and down buttons and by dragging.
- A drag let go outside the list puts the row where the gap was when the pointer left.
- A posted order sent while an earlier one is still on its way: the list shows the latest order
  the person made, and the answers do not reapply an older one.
- A long list on a phone stays scrollable by dragging anywhere other than a handle.
- A right click or a second finger on a handle starts no drag.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `c-mvp.form.formset` MUST make the rows of a formset built with `can_order`
  reorderable, and MUST fill each row's `ORDER` value from where the row sits when the form is
  submitted (US1).
- **FR-002**: A row set's reorderable rows MUST keep working with adding and removing rows, and
  MUST appear in the person's order when an invalid submission is shown again (US1).
- **FR-003**: The package MUST offer a way to mark any list as reorderable, with its order sent
  either with the surrounding form under a name the developer chooses, or to an address posted to
  each time the order changes (US1).
- **FR-004**: An order sent with a form or posted MUST carry the identifier of every row in the
  list, in the order the rows sit (US1).
- **FR-005**: An order posted as it changes MUST carry the page's CSRF token, and the answer MUST
  replace the list (US1).
- **FR-006**: A developer MUST be able to choose that a list is reorderable only in a reorder
  mode, started from a control the developer places (US1).
- **FR-007**: The package MUST provide a helper that saves a received order to a model's position
  field for the records a developer gives it, renumbering only those records, and refusing,
  without saving anything, an order that names a record outside them or leaves one of them out
  (US1).
- **FR-008**: Every script and style a reorderable list needs MUST ship with the package. None
  may be fetched from another site (US1).
- **FR-009**: Each reorderable list on a page MUST be independent of the others (US1).
- **FR-010**: A person MUST be able to move a row by dragging its handle with a mouse or a
  finger, with the held row following the pointer and the rows it passes making room (US2).
- **FR-011**: On a touch screen, dragging MUST start only from a handle, and dragging elsewhere on
  a row MUST scroll the page. Where the device supports it, the start of a drag MUST give a short
  vibration (US2).
- **FR-012**: While a row is dragged, the page MUST scroll when the pointer nears the top or
  bottom of the screen (US2).
- **FR-013**: Escape during a drag MUST return the row to where it started (US2).
- **FR-014**: Every row MUST offer up and down buttons that move it one place, reachable and
  usable from the keyboard. Focus MUST stay with the moved row, and its new position MUST be
  announced to assistive technology. A move that is not possible MUST not be offered as usable
  (US2).
- **FR-015**: Positions shown on rows MUST follow the rows as they move (US2).
- **FR-016**: Rows MUST move without animation when the person's system asks for reduced motion
  (US2).
- **FR-017**: A reorder mode MUST end from its own control and on Escape, and the list MUST show no handle and
  no up or down buttons outside it (US2).
- **FR-018**: While a list is being reordered, swiping its rows for their actions MUST be off and
  any row swiped open MUST shut, through the switch the row-actions feature provides (US2).
- **FR-019**: When a posted order is refused or cannot be sent, the list MUST return to its order
  before that move and the person MUST be told it was not saved (US2).
- **FR-020**: A reorderable list in a dialog closed without submitting MUST return to the order
  it had when the dialog opened (US2).
- **FR-021**: Without scripts, rows MUST appear in their saved order, and a row set MUST offer
  its `ORDER` fields to type into (US2).

### Key Entities

- **Reorderable list**: a list whose rows a person can put in a new order, and the place that
  order goes: a row set's `ORDER` fields, a field of the surrounding form, or an address posted to
  as the order changes.
- **Handle**: the part of a row a person takes hold of to drag it.
- **Reorder mode**: a state of a list in which it can be reordered, started by a control and
  ended by its own control or by Escape.
- **Position field**: a model field holding a record's place in its list, renumbered by the
  package's helper from a received order.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer makes an ordered row set reorderable with no code beyond building the
  formset with `can_order` and rendering it with `c-mvp.form.formset`.
- **SC-002**: A developer makes any other list reorderable and saves its order to a position field
  without writing JavaScript or renumbering code of their own.
- **SC-003**: Every reordering a person can do by dragging, they can also do with the keyboard
  alone.
- **SC-004**: A received order that names a record the person may not reorder never changes any
  record's position.
- **SC-005**: A page holding a reorderable list fetches nothing from another site.
- **SC-006**: The demo shows each of the three places an order can go, and a list with a reorder
  mode, each working at phone and desktop width.

## Assumptions

- Lists are vertical, and a row moves only within its own list.
- A list's rows each carry an identifier the developer supplies, usually the record's primary key.
- The position field is a whole number per record. Ties and gaps in the stored positions before a
  save are tolerated, and the helper leaves them consecutive after it.
- Who may reorder which records is the developer's decision, expressed by the records they hand
  the helper.
- The control that starts a reorder mode is placed by the developer, for example in the page's
  actions menu.
