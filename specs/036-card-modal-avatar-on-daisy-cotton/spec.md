# Feature Specification: The package's card, modal and avatar are built on daisy-cotton's

**Feature Branch**: `036-card-modal-avatar-on-daisy-cotton`

**Created**: 2026-10-05

**Status**: Draft

**Serves**: G2 (a component library covering what a data-centric web application needs, with small attribute APIs and deliberately limited variation), G5 (a polished, modern look and feel out of the box)

**Roadmap**: R29

**Issue**: #436

**Depends on**: #434 (the three components carry their `mvp.` names) and #435 (a bare `<c-card>`, `<c-modal>` or `<c-avatar>` reaches daisy-cotton's component)

**Input**: `<c-mvp.card>`, `<c-mvp.modal>` and `<c-mvp.avatar>` should keep what they add for an
application (the header row and footer, the card-shaped dialog, the signed-in user's picture) and
draw everything else through daisy-cotton's components, so they follow its fixes and
accessibility work.

## Summary

Three components in this package share a role with a daisy-cotton component and add something an
application needs on top of it. The card adds a header row (icon, title, badges, actions) and a
footer. The modal is a dialog laid out as that card. The avatar looks up a person's picture,
by default the signed-in user's.

Today each of the three writes the whole daisyUI structure itself: the card surface and body, the
dialog with its box, close control and backdrop, the avatar with its frame and fallbacks. That is
a second copy of markup daisy-cotton already maintains, and a fix made there never arrives here.

After this feature each of the three draws that structure by calling daisy-cotton's component and
adds only its own part. The attributes that overlap with daisy-cotton's take daisy-cotton's names,
so the same word means the same thing on `<c-card>` and `<c-mvp.card>`. The change is breaking for
the renamed attributes and is recorded in the changelog. Pages keep the look they have.

## Clarifications

### Session 2026-10-05

The coverage scan found five ambiguities. Each was resolved from issue #436, roadmap item R29, the
sibling issues #433 to #440 and the two packages' current templates. Longer rationale is in
`decisions.md`.

- **Q: Both cards have an `actions` slot, and they mean different things. Which meaning does
  `<c-mvp.card>` carry?**
  A: This package's. `actions` on `<c-mvp.card>` and `<c-mvp.modal>` stays the end of the header
  row, which is one of the things the issue says the card keeps. daisy-cotton's trailing actions
  row is not offered through these two components, because `footer` and `footer_end` already do
  that job. A page that wants daisy-cotton's row uses `<c-card>` or `<c-modal>` directly.
  Recorded as FR-005 and FR-010.

- **Q: Where the two packages name the same thing differently, which name wins?**
  A: daisy-cotton's, with no alias for the old name. The card's `body_class` becomes
  `content_class`. The modal's `position` becomes `placement` and takes daisy-cotton's values.
  On the modal, `class` lands on the dialog as it does on daisy-cotton's, and `content_class`
  lands on the visible card. R29 already says the move changes attribute names across the library
  and ships once as a breaking release. Recorded as FR-008, FR-013 and FR-016.

- **Q: Which of the avatar's attributes are part of what it adds, and which are daisy-cotton's
  job?**
  A: The lookup is what it adds: `for`, and `size`, which the lookup receives and which sets the
  width. Presence becomes daisy-cotton's `online` and `offline`. Shape and placeholder colour go
  through daisy-cotton's `content_class`, and `shape`, `variant` and `status` are removed. With no
  `content_class` the avatar keeps the frame it draws today. The default alt text is dropped, as
  daisy-cotton's avatar has none. Recorded as FR-018 to FR-022.

- **Q: What happens to `<c-mvp.card.wrapper>`, the bare card surface with no body?**
  A: It stays as it is. daisy-cotton's card always draws a body, so it has no equivalent to build
  on, and the issue names the card, the modal and the avatar only. The wrapper and `<c-mvp.card>`
  keep presenting the same default surface. Recorded as FR-009.

- **Q: The modal's title is drawn in the card's header, not by daisy-cotton's modal. How does the
  dialog get its accessible name?**
  A: A dialog given an id and a title is named by that title for assistive technology, the same
  outcome daisy-cotton's modal gives its own title. A dialog with no title takes whatever name the
  caller passes, and that reaches the dialog element. Recorded as FR-014.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A card with a header row and footer, drawn by daisy-cotton's card (Priority: P1)

A developer building a page writes `<c-mvp.card title="Orders" icon="cart">` with a badge, a
button at the end of the header and a footer. They get the same card they get today. The
difference is underneath: the card surface and its body now come from daisy-cotton's `<c-card>`,
so the attributes that component offers (its size steps, its border and dashed styles) work on
`<c-mvp.card>` too, and a fix to daisy-cotton's card reaches every card in the application. A
project that overrides daisy-cotton's card template changes this package's cards with it.

**Why this priority**: The card is the most used of the three, and the modal is built on it.
Nothing in Story 2 can be finished before this one.

**Independent Test**: Render `<c-mvp.card>` with a title, an icon, each of its slots and an
attribute only daisy-cotton's card declares. Confirm the header row and footer are present, the
daisy-cotton attribute took effect, and that replacing daisy-cotton's card template in a test
project changes the output of `<c-mvp.card>`.

**Acceptance Scenarios**:

1. **Given** a `<c-mvp.card>` with a title, an icon, and content in its `badges` and `actions`
   slots, **When** it renders, **Then** one header row carries the icon and title, the badges
   after them and the actions at the end of the row, above the card's content.
2. **Given** a `<c-mvp.card>` with none of title, icon, badges or actions, **When** it renders,
   **Then** no header row is drawn. **Given** one with neither `footer` nor `footer_end`,
   **Then** no footer row is drawn.
3. **Given** a `<c-mvp.card>` with content in `footer` and `footer_end`, **When** it renders,
   **Then** a footer row below the content carries the first at its start and the second at its
   end.
4. **Given** a test project that replaces daisy-cotton's card template with its own, **When**
   `<c-mvp.card>` renders, **Then** the card surface and body are the project's.
5. **Given** a `<c-mvp.card>` carrying an attribute that daisy-cotton's card declares and this
   package's card does not, **When** it renders, **Then** the attribute has the effect it has on
   `<c-card>`.
6. **Given** a `<c-mvp.card>` with `class` and `content_class`, **When** it renders, **Then** the
   first is added to the card surface alongside the package's default surface, and the second is
   added to the card body.
7. **Given** a `<c-mvp.card tight>`, **When** it renders, **Then** the body has no padding, so a
   table or list inside it reaches the card's edges.
8. **Given** a page whose context holds a variable with the same name as an attribute of
   daisy-cotton's card, and a `<c-mvp.card>` that does not pass that attribute, **When** the page
   renders, **Then** the variable has no effect on the card.
9. **Given** a `<c-mvp.card>` whose content or slots use a variable from the page's context,
   **When** it renders, **Then** the variable resolves as it does anywhere else on the page.
10. **Given** a `<c-mvp.card.wrapper>`, **When** it renders, **Then** it is the bare card surface
    with the caller's content and no body, as before.

---

### User Story 2 - A card-shaped dialog, drawn by daisy-cotton's modal (Priority: P2)

A developer adds `<c-mvp.modal id="confirm" title="Delete this order?" icon="trash" closable>`
with two buttons in the footer. A person using the page opens it and sees the same card-shaped
dialog as today, closes it with the corner control, the backdrop or the Escape key, and a screen
reader announces the dialog by its title. The dialog element, its box, the close control and the
backdrop now come from daisy-cotton's `<c-modal>`. The package's own dialogs (the list page's
create and filter dialogs, the page information dialog and the language switcher) work as before.

**Why this priority**: It depends on Story 1, and the dialogs the package ships are reached
through a click, so they are seen less often than cards. The accessible name is the one behaviour
this story adds for the person using the page.

**Independent Test**: Render `<c-mvp.modal>` with an id, a title, an icon, `closable` and each
slot. Confirm the content is laid out as a `<c-mvp.card>`, the dialog is named by its title, and
the close control and backdrop are present. In a browser, open each of the package's own dialogs
and confirm it opens and closes, and that the edge placements still span the screen edge they are
pinned to.

**Acceptance Scenarios**:

1. **Given** a `<c-mvp.modal>` with a title, an icon and content in its `actions`, `footer` and
   `footer_end` slots, **When** it renders, **Then** its content is laid out as a `<c-mvp.card>`
   with that header row and footer.
2. **Given** a `<c-mvp.modal>` with an id and a title, **When** it renders, **Then** the dialog's
   accessible name is the title.
3. **Given** a `<c-mvp.modal>` with no title and an accessible name passed by the caller,
   **When** it renders, **Then** the dialog element carries that name.
4. **Given** a `<c-mvp.modal closable>`, **When** it renders, **Then** it has a close control that
   closes the dialog without script and has an accessible name. **Given** one without `closable`,
   **Then** there is no close control, and the backdrop still closes the dialog.
5. **Given** a `<c-mvp.modal>` with a `placement` that daisy-cotton's modal accepts, **When** it
   renders, **Then** the dialog is placed as `<c-modal>` places it for that value.
6. **Given** a `<c-mvp.modal>` placed at the top or bottom, **When** it is open in a browser,
   **Then** the visible card spans the full width of the viewport. **Given** one placed at the
   start or end, **Then** the visible card spans the full height of the viewport.
7. **Given** two `<c-mvp.modal>` tags that differ only in `size`, **When** they render with no
   edge placement, **Then** the larger step allows a wider dialog than the smaller one.
8. **Given** a test project that replaces daisy-cotton's modal template with its own, **When**
   `<c-mvp.modal>` renders, **Then** the dialog is the project's.
9. **Given** a `<c-mvp.modal>` with `class` and `content_class`, **When** it renders, **Then** the
   first is on the dialog element and the second is on the visible card.
10. **Given** a page whose context holds a variable with the same name as an attribute of
    daisy-cotton's modal or card, and a `<c-mvp.modal>` that does not pass it, **When** the page
    renders, **Then** the variable has no effect on the dialog.
11. **Given** each dialog the package ships (list create, list filter, page information, language
    switcher), **When** its trigger is used, **Then** the dialog opens with the content it has
    today, and a form inside it submits as before.

---

### User Story 3 - A person's picture, looked up here and drawn by daisy-cotton's avatar (Priority: P3)

A developer writes `<c-mvp.avatar />` in a header and gets the signed-in user's picture, resolved
by the function the project configured. With `:for="order.customer"` they get that person's
picture instead. When no picture resolves, the avatar falls back to placeholder text if any was
given, and otherwise to a silhouette. The lookup is the part this package adds. The avatar
element, its frame, the fallbacks and the presence indicator come from daisy-cotton's
`<c-avatar>`, so `online`, `offline` and `content_class` work as they do there.

**Why this priority**: The avatar has the fewest call sites in the package (the compact user
display) and no other component is built on it.

**Independent Test**: With a test resolver configured, render `<c-mvp.avatar>` for a user it knows
and for one it does not, with and without `src` and `placeholder`. Confirm which picture or
fallback is drawn in each case and that the resolver received the user and the size. Confirm
`online` and `content_class` behave as on `<c-avatar>`.

**Acceptance Scenarios**:

1. **Given** a project with an avatar resolver configured and a signed-in user it has a picture
   for, **When** `<c-mvp.avatar />` renders, **Then** the avatar shows that picture.
2. **Given** the same project, **When** `<c-mvp.avatar :for="other_user" />` renders, **Then** the
   resolver is asked about `other_user`, not the signed-in user.
3. **Given** a `<c-mvp.avatar>` with `src`, **When** it renders, **Then** that picture is shown
   and the resolver is not consulted.
4. **Given** no picture resolves, **When** `<c-mvp.avatar placeholder="AB" />` renders, **Then**
   the avatar shows the placeholder text. **Given** no picture and no placeholder, **Then** it
   shows a silhouette that is hidden from assistive technology.
5. **Given** a `<c-mvp.avatar>` with a `size` from the package's scale, **When** it renders,
   **Then** the resolver receives that size, and a larger step draws a wider avatar than a smaller
   one.
6. **Given** a `<c-mvp.avatar online />` or `<c-mvp.avatar offline />`, **When** it renders,
   **Then** it carries the presence indicator `<c-avatar>` draws for that attribute.
7. **Given** a `<c-mvp.avatar>` with `content_class`, **When** it renders, **Then** the frame
   carries those classes in place of the default frame, as on `<c-avatar>`, and the resolver still
   receives `size`.
8. **Given** a `<c-mvp.avatar>` showing a picture with no `alt` given, **When** it renders,
   **Then** the image has empty alt text. **Given** an `alt`, **Then** the image carries it.
9. **Given** a test project that replaces daisy-cotton's avatar template with its own, **When**
   `<c-mvp.avatar>` renders, **Then** the avatar is the project's, showing the picture this
   package resolved.
10. **Given** a page whose context holds a variable named `src`, `placeholder` or `alt`, and a
    `<c-mvp.avatar>` that does not pass it, **When** the page renders, **Then** the variable has
    no effect on the avatar.
11. **Given** a request with no signed-in user, **When** `<c-mvp.avatar />` renders, **Then** it
    renders a fallback without raising.

---

### Edge Cases

- A project already overrides `cotton/mvp/card/index.html`, `cotton/mvp/modal.html` or
  `cotton/mvp/avatar/index.html`. Its template still wins, and it is not affected by this change
  until it chooses to call daisy-cotton's component itself.
- A caller still passes a removed or renamed attribute (`body_class`, `position`, `shape`,
  `variant`, `status`). There is no alias. The attribute no longer has its old effect, and the
  changelog names its replacement.
- A `<c-mvp.modal>` has a title and no id. It cannot be opened by a trigger without an id, and it
  is not named by its title. The documentation says an id is needed for both.
- A `<c-mvp.card>` is given a title and also an attribute daisy-cotton's card would draw as its
  own title. The package's header row is the only title drawn: one card never shows two headings.
- A `<c-mvp.avatar>` is given both `online` and `offline`. It behaves as `<c-avatar>` does with
  both.
- The avatar resolver returns nothing for a user. The avatar falls back to placeholder text, then
  to the silhouette, as in Story 3.
- A `<c-mvp.avatar>` is given a `size` outside the package's scale. The resolver still receives
  the value as written, and the avatar renders without raising.
- A `<c-mvp.modal>` is given `open`. It is shown on load in the way daisy-cotton's modal documents
  for that attribute, which is not a modal state.
- Slot content inside any of the three calls another component that reads the page's context
  (a form, a menu). It resolves as it does today.

## Requirements *(mandatory)*

### Functional Requirements

#### All three components

- **FR-001** (US1, US2, US3): `<c-mvp.card>`, `<c-mvp.modal>` and `<c-mvp.avatar>` MUST each draw
  the daisyUI structure of their role by calling daisy-cotton's `<c-card>`, `<c-modal>` and
  `<c-avatar>`. A project that replaces one of those daisy-cotton templates MUST see its
  replacement used by the matching component here.
- **FR-002** (US1, US2, US3): A variable in the page's context that shares a name with an
  attribute of the daisy-cotton component MUST NOT reach that component unless the caller passed
  it on the tag.
- **FR-003** (US1, US2): Content given in a component's default slot or a named slot MUST render
  in the calling page's context.
- **FR-004** (US1, US2, US3): An attribute the caller passes that the component here does not
  declare MUST reach the daisy-cotton component it draws, so that daisy-cotton's own attributes
  and plain HTML attributes work on all three.

#### Card

- **FR-005** (US1): `<c-mvp.card>` MUST draw a header row from `title`, `icon` and the `badges`
  and `actions` slots, with the actions at the end of the row, and MUST draw no header row when
  none of the four is given.
- **FR-006** (US1): `<c-mvp.card>` MUST draw a footer row from the `footer` and `footer_end`
  slots, the first at the start and the second at the end, and MUST draw no footer row when
  neither is given.
- **FR-007** (US1): `tight` MUST remove the body's padding.
- **FR-008** (US1): `class` MUST add to the card surface and `content_class` MUST add to the card
  body. `body_class` is removed with no alias.
- **FR-009** (US1): `<c-mvp.card>` MUST present the package's default card surface when the caller
  adds nothing, and `<c-mvp.card.wrapper>` MUST remain the bare surface with no body and present
  the same default.
- **FR-010** (US1): A `<c-mvp.card>` MUST draw at most one heading, the one in its header row.
  daisy-cotton's own title and trailing actions row are not part of this component's contract.

#### Modal

- **FR-011** (US2): `<c-mvp.modal>` MUST lay its content out as a `<c-mvp.card>`, passing it
  `title`, `icon` and the `actions`, `footer` and `footer_end` slots.
- **FR-012** (US2): The dialog element, its box, the close control and the backdrop MUST come
  from daisy-cotton's `<c-modal>`. `closable` MUST add a close control that works without script
  and has an accessible name, and the backdrop MUST close the dialog whether or not `closable` is
  set.
- **FR-013** (US2): `placement` MUST place the dialog, taking the values daisy-cotton's modal
  takes. `position` is removed with no alias.
- **FR-014** (US2): A dialog given an id and a title MUST have that title as its accessible name.
  An accessible name passed by the caller MUST reach the dialog element.
- **FR-015** (US2): `size` MUST keep its scale, with a larger step allowing a wider dialog. A
  dialog placed at the top or bottom MUST span the viewport's width whatever its `size`, and one
  placed at the start or end MUST have its visible card span the viewport's height.
- **FR-016** (US2): `class` MUST land on the dialog element and `content_class` on the visible
  card.
- **FR-017** (US2): The dialogs the package ships (list create, list filter, page information,
  language switcher) MUST open, close and submit as they do today.

#### Avatar

- **FR-018** (US3): `<c-mvp.avatar>` MUST choose its picture in this order: the caller's `src`;
  otherwise the result of the project's configured avatar resolver for the user in `for`, which
  defaults to the signed-in user; otherwise none.
- **FR-019** (US3): `size` MUST be passed to the resolver as written, and a step on the package's
  scale MUST set the avatar's width.
- **FR-020** (US3): With no picture, the avatar MUST show the `placeholder` text when given and a
  silhouette hidden from assistive technology otherwise. It MUST render without raising when
  there is no signed-in user.
- **FR-021** (US3): `online`, `offline` and `content_class` MUST behave as they do on
  `<c-avatar>`. With no `content_class`, the avatar MUST present the frame it presents today.
  `status`, `shape` and `variant` are removed with no alias.
- **FR-022** (US3): The image MUST carry the caller's `alt`, and empty alt text when none is
  given.

#### Callers, documentation and assets

- **FR-023** (US1, US2, US3): Every template in the package, every demo page and every documented
  example that uses one of the three MUST use the attribute names in this specification.
- **FR-024** (US1, US2, US3): The component reference in `docs/` MUST describe each of the three
  as it now behaves, including which attributes come from daisy-cotton's component, and the
  changelog MUST list every removed or renamed attribute with its replacement under the
  unreleased heading. This feature cuts no release.
- **FR-025** (US1, US2, US3): The prebuilt stylesheet MUST cover every class the three components
  can render, and MUST be rebuilt on the branch that changes them.
- **FR-026** (US1, US2, US3): Each of the three MUST have tests that state its rendered contract:
  what each attribute and slot changes in the markup, and its defaults. Tests that assert the
  replaced markup are rewritten against the new contract, not deleted.

### Key Entities

- **`<c-mvp.card>`**: a daisy-cotton card plus a header row (icon, title, badges, actions) and a
  footer row (start and end).
- **`<c-mvp.card.wrapper>`**: the bare card surface with no body. Unchanged by this feature.
- **`<c-mvp.modal>`**: a daisy-cotton modal whose content is a `<c-mvp.card>`, with a width scale
  of its own.
- **`<c-mvp.avatar>`**: a daisy-cotton avatar whose picture is looked up through the project's
  configured avatar resolver.
- **Avatar resolver**: the function a project names in `MVP_CONFIG["brand"]["avatar_resolver"]`.
  It takes a user and a size and returns a picture's address or nothing. Unchanged by this
  feature.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: None of the three components writes its daisyUI structure itself. Replacing
  daisy-cotton's card, modal or avatar template in a test project changes the output of the
  matching component here, in all three cases.
- **SC-002**: Everything each component adds for an application is still there: the header row
  and footer on the card, the card-shaped content on the dialog, and the looked-up picture on the
  avatar are each covered by a passing contract test.
- **SC-003**: Every dialog drawn by `<c-mvp.modal>` with an id and a title has an accessible
  name, and every close control has one. Before this feature no dialog was named by its title.
- **SC-004**: No attribute declared by daisy-cotton's card, modal or avatar can be set on these
  components by a same-named page variable. A test covers every such attribute name.
- **SC-005**: Every page in the package and the demo that renders a card, a dialog or an avatar
  renders without error, and the existing browser tests for dialog placement pass unchanged in
  what they measure.
- **SC-006**: Every attribute this feature removes or renames appears in the changelog with its
  replacement, and the component reference lists no attribute the templates no longer declare.
- **SC-007**: A page that uses any documented attribute of the three renders fully styled with
  only the prebuilt stylesheet.

## Assumptions

- #434 and #435 are merged before this is built. The three components are already named
  `<c-mvp.card>`, `<c-mvp.modal>` and `<c-mvp.avatar>`, and `<c-card>`, `<c-modal>`, `<c-avatar>`
  and `<c-button>` are daisy-cotton's.
- daisy-cotton is installed at 0.1.2 or later and its templates are covered by the prebuilt
  stylesheet, both delivered by #433.
- Pages keep the look they have. Where daisy-cotton's default differs from this package's (the
  card surface's background and shadow, the avatar frame's colouring), the component here supplies
  the package's default.
- The figure slot of daisy-cotton's card is not forwarded by `<c-mvp.card>`. A card that needs a
  figure uses `<c-card>`.
- `<c-avatar.group>` belongs to #435, the dropdown to #437, the sidebar and user menus to #438
  and the rest of the shell's markup to #440. None of them changes here beyond a call site that
  uses a renamed attribute of the three.
- `<c-mvp.card>` stays in this package. Moving it to another package is not part of this feature.
- Packages built on this one that call the old attribute names are updated in their own
  repositories around the release that carries R29. They are not changed here.
- Nothing under `.github/` changes.
