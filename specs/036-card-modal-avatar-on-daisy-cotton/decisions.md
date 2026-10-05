# Decisions: The package's card, modal and avatar are built on daisy-cotton's

Rationale too long to inline in `spec.md`, the maintainer's rulings this feature rests on, and
the ambiguities resolved while specifying.

## The reading of #436 this specification was written from

The maintainer was not asked to confirm this reading. It was written from the issue, roadmap item
R29, the sibling issues and both packages' templates, and every gap it filled is listed below as
a decision made while specifying (D1 to D9).

`<c-mvp.card>`, `<c-mvp.modal>` and `<c-mvp.avatar>` stop writing daisyUI's card, dialog and
avatar markup themselves. Each calls daisy-cotton's component for that structure and adds only
what an application needs on top: the header row and footer, the card-shaped dialog with a width
scale, and the lookup of a person's picture. Where an attribute overlaps with daisy-cotton's it
takes daisy-cotton's name, with no alias. Pages look the same afterwards. Call sites, demo pages,
documentation, the changelog, the prebuilt stylesheet and the tests move with the components.
Everything else in R29 belongs to a sibling issue.

## Rulings given by the maintainer

These were settled for the whole of R29 before this specification was written. They are recorded
as given.

### M1. Calls to daisy-cotton's components are isolated at the call site

Many daisy-cotton templates declare attribute names (`title`, `class`, `actions`, `size`) that
pick up a same-named page variable when the caller does not pass them. The fix is at each call
this package makes to a daisy-cotton component, using Cotton's `only`, and not a change upstream.
#433 proves that slot content still sees the page's context when a component is called this way.
FR-002 and FR-003 state the outcome for these three components.

### M2. No compatibility aliases

A renamed tag or attribute is a breaking change recorded in the changelog. All of R29 collects on
the main branch and ships as one breaking minor release. No feature inside R29 cuts a release.
This is why FR-008, FR-013 and FR-021 remove names outright, and why FR-024 says no release.

### M3. The card stays in this package

`<c-mvp.card>` is not moved to another package as part of R29.

### M4. The three keep their role and move under `mvp.`

Card, modal and avatar are kept as `mvp.card`, `mvp.modal` and `mvp.avatar` (#434), and this
feature rebuilds them on daisy-cotton's. `<c-avatar.group>` is replaced by daisy-cotton's in #435.

### M5. The prebuilt stylesheet already carries daisyUI's component classes

The stylesheet scans all of daisyUI's components and utilities, so the classes daisy-cotton's
templates build at render time are present. Plain Tailwind utilities written literally in
daisy-cotton's templates are covered by #433. FR-025 covers what this feature's own templates
add.

## Decisions made while specifying

### D1. `actions` keeps this package's meaning

**Ambiguous:** both cards have an `actions` slot. Here it is the end of the header row. In
daisy-cotton it is a row at the foot of the body. The modals differ the same way.

**Chosen:** `actions` on `<c-mvp.card>` and `<c-mvp.modal>` stays the header row (FR-005, FR-011).
daisy-cotton's trailing row is not offered through these components (FR-010).

**Why defensible:** the issue names the header row as what the card keeps, and every caller in the
package uses `actions` that way. `footer` and `footer_end` already cover trailing buttons, so
offering daisy-cotton's row as well would give one card two places for the same thing.

**Rejected:** renaming this package's slot (for example to `header_actions`) so `actions` could
mean daisy-cotton's. It makes the common case longer to free a name for the rare one.

### D2. Overlapping attributes take daisy-cotton's names

**Ambiguous:** the issue says "draw everything else through daisy-cotton's components" and does
not say whether this package's names for the same things survive.

**Chosen:** `body_class` becomes `content_class` on the card. `position` becomes `placement` on
the modal, with daisy-cotton's values. On the modal `class` moves from the inner card to the
dialog element, and `content_class` addresses the visible card (FR-008, FR-013, FR-016).

**Why defensible:** R29 gives "one attribute vocabulary" as the reason for the move and says it
changes attribute names across the library. Once undeclared attributes pass through to
daisy-cotton's component (FR-004), `content_class` works on the card whether or not it is
declared here, so keeping `body_class` would leave two names for one thing.

**Cost:** the modal's `class` changes target, which is the one rename a caller could miss, since
the attribute still exists. The changelog entry has to say so plainly.

### D3. The avatar keeps the lookup and the size scale, and nothing else of its own

**Ambiguous:** the avatar declares `for`, `src`, `alt`, `size`, `shape`, `variant`, `status` and
`placeholder`. The issue says it keeps "the signed-in user's picture".

**Chosen:** `for` and `size` stay, because the resolver takes a user and a size. `src`, `alt` and
`placeholder` are daisy-cotton's and pass through. `status` becomes `online` and `offline`.
`shape` and `variant` are removed in favour of `content_class`, which replaces the frame's classes
entirely as it does on `<c-avatar>` (FR-018 to FR-021).

**Why defensible:** shape and colour are classes on the frame and daisy-cotton's avatar documents
`content_class` as the way to set them. Removing `variant` also removes the one place in these
components where a class name is assembled at render time from an attribute value, which is the
kind of class a stylesheet scan cannot see.

**Rejected:** keeping `shape` and `variant` as conveniences. They would be a second way to do
what `content_class` does, and R29's purpose is to stop carrying a parallel vocabulary.

### D4. The avatar's default frame does not change

**Ambiguous:** daisy-cotton's avatar colours a placeholder differently from this package's.

**Chosen:** with no `content_class`, `<c-mvp.avatar>` presents the frame it presents today
(FR-021). The same holds for the card's default surface (FR-009).

**Why defensible:** this is structural work. A page should not look different after it, so that
no part of the feature needs a visual judgement. A project that wants daisy-cotton's default can
use `<c-avatar>`.

### D5. No default alt text

**Ambiguous:** the avatar gives every picture the same English alt text unless the caller
overrides it. daisy-cotton's has none by default.

**Chosen:** empty alt text unless the caller gives one (FR-022).

**Why defensible:** the issue asks for the components to follow daisy-cotton's accessibility work.
An avatar usually sits beside the person's name, where repeated alt text is noise to a screen
reader, and the current default is also untranslated.

### D6. `<c-mvp.card.wrapper>` is left alone

**Ambiguous:** the card is built on a second component, the bare surface, which the issue does
not mention.

**Chosen:** it stays, with the same behaviour and the same default surface as `<c-mvp.card>`
(FR-009).

**Why defensible:** daisy-cotton's card always draws a body, so there is nothing to build a
bodiless surface on. The wrapper has one use in the demo and none in the package's own pages
once the card stops using it, so removing it is a separate question for whoever owns the
component surface, not something this feature needs.

### D7. A dialog is named by its title

**Ambiguous:** daisy-cotton's modal names the dialog from its own `title`. This package draws the
title in the card's header instead, so that naming does not happen by itself.

**Chosen:** a dialog with an id and a title has the title as its accessible name, and a name the
caller passes reaches the dialog element (FR-014).

**Why defensible:** it is the outcome daisy-cotton's modal gives, and the issue's stated reason
for the feature is to follow that accessibility work. Without the requirement the rebuilt modal
would use daisy-cotton's dialog and still lose the one thing it does for a screen reader.

### D8. The modal keeps its own `size`

**Ambiguous:** daisy-cotton's modal has no size attribute. Width is set with `content_class`.

**Chosen:** `size` stays, with the full-width and full-height behaviour of the edge placements
(FR-015).

**Why defensible:** the card-shaped dialog is named in the issue as what the modal keeps, and its
width scale is part of that shape. The edge behaviour was a reported defect (#180) with browser
tests, and it has to survive the rebuild.

### D9. No prototype is needed before the build

**Chosen:** this feature is not sketched first.

**Why defensible:** D4 keeps every default as it is, so the work is a like-for-like change of
markup that tests can judge.

## Open items

- #434 and #435 are still open. This feature cannot be built until both are merged.
- `<c-mvp.card.wrapper>` will have no caller inside the package once the card is drawn by
  daisy-cotton's. Whether it stays in the component surface is left for a later decision (D6).
