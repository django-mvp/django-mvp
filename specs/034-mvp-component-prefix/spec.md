# Feature Specification: Every component this package keeps moves under the mvp. prefix

**Feature Branch**: `034-mvp-component-prefix`

**Created**: 2026-10-05

**Status**: Draft

**Serves**: G11 (a recorded, predictable public surface that becomes safe to depend on across releases), G7 (customization that never dead-ends, from view configuration through component override to a project's own CSS)

**Roadmap**: R29

**Issue**: #434

**Input**: Components tied to Django or the shell (page, app, form, formset, user, brand, actions)
and the three that mean something different from daisy-cotton's (card, modal, avatar) should move
to `<c-mvp.…>`. The icon keeps its name. Once this lands, a bare name always means daisy-cotton's
component, and a reader can tell from the tag which package it comes from.

## Summary

django-mvp and [daisy-cotton](https://github.com/django-mvp/daisy-cotton) both name their
components the plain way, so `<c-card>` resolves to whichever app comes first in `INSTALLED_APPS`.
Three of this package's components share a name with a daisy-cotton component and mean something
else, and a fourth, the menu entry, is called by daisy-cotton's own templates. A project that
installs both today gets one or the other depending on app order, with nothing in the template to
say which.

This feature gives every component the package keeps a name of its own. `<c-card>` becomes
`<c-mvp.card>`, `<c-page.list>` becomes `<c-mvp.page.list>`, and so on for the whole kept set.
Nothing about what a component renders, accepts or does changes. It is a rename.

Two groups keep a bare name:

- The icon stays `<c-icon>` for good. daisy-cotton ships a plain icon and expects a project to
  replace it when it wants icons looked up by name. This package's icon is that replacement, so it
  has to sit at the same name to reach every caller, daisy-cotton's own components included.
- The basic components that #435 removes in favour of daisy-cotton's (button, alert, badge, avatar
  group, breadcrumbs, divider, link, dock, the mockups and the menu container) stay where they are
  until #435 removes them. Renaming them first would mean two breaking changes to the same tags.

The old names are not kept as aliases. The change is breaking and is recorded in the changelog
with a complete old-to-new table.

### What moves and what stays

The lists below describe the component directory on `main` when this was written: 84 component
templates, of which 67 move and 17 stay.

| Moves under `mvp.` | New name |
|---|---|
| `c-actions.*` (language switcher and its dialog, login, search, theme controller) | `c-mvp.actions.*` |
| `c-addons.*` (table, share dropdown) | `c-mvp.addons.*` |
| `c-app` and everything under it (header, navbar, main, footer, dock, sidebar and its parts) | `c-mvp.app`, `c-mvp.app.*` |
| `c-avatar` | `c-mvp.avatar` |
| `c-backdrop`, `c-container`, `c-grid`, `c-group`, `c-rule`, `c-text`, `c-toolbar` | `c-mvp.backdrop`, `c-mvp.container`, `c-mvp.grid`, `c-mvp.group`, `c-mvp.rule`, `c-mvp.text`, `c-mvp.toolbar` |
| `c-brand.*` | `c-mvp.brand.*` |
| `c-card`, `c-card.wrapper` | `c-mvp.card`, `c-mvp.card.wrapper` |
| `c-data-field`, `c-messages`, `c-documentation` | `c-mvp.data-field`, `c-mvp.messages`, `c-mvp.documentation` |
| `c-dropdown` | `c-mvp.dropdown` |
| `c-entrance`, `c-entrance.background` | `c-mvp.entrance`, `c-mvp.entrance.background` |
| `c-form`, `c-form.render`, `c-form.field`, `c-form.formset`, `c-form.formset.row` | `c-mvp.form`, `c-mvp.form.*` |
| `c-layout.sidebar` | `c-mvp.layout.sidebar` |
| `c-menu.item`, `c-menu.group`, `c-menu.collapse`, `c-menu.divider` | `c-mvp.menu.item`, `c-mvp.menu.group`, `c-mvp.menu.collapse`, `c-mvp.menu.divider` |
| `c-modal` | `c-mvp.modal` |
| `c-page` and everything under it | `c-mvp.page`, `c-mvp.page.*` |
| `c-pagination`, `c-pagination.link`, `c-pagination.wrapper` | `c-mvp.pagination`, `c-mvp.pagination.*` |
| `c-placeholder.card` | `c-mvp.placeholder.card` |
| `c-section`, `c-section.hero` | `c-mvp.section`, `c-mvp.section.hero` |
| `c-user.*` | `c-mvp.user.*` |

| Keeps its bare name | Why |
|---|---|
| `c-icon` | Permanent. It replaces daisy-cotton's plain icon by sitting at the same name. |
| `c-alert`, `c-avatar.group`, `c-badge`, `c-breadcrumbs`, `c-breadcrumbs.item`, `c-button`, `c-divider`, `c-dock`, `c-dock.item`, `c-link`, `c-menu`, `c-mockup.*` | Until #435 removes them. |

## Clarifications

### Session 2026-10-05

The coverage scan found five ambiguities. Each was resolved from the issue, roadmap item R29, the
sibling issues #433 and #435 to #440, and the package's constitution. Longer rationale is in
`decisions.md`.

- **Q: The issue says a bare name will always mean daisy-cotton's component once this lands. Is
  that true of the basic components this feature leaves alone?**
  A: Not yet. After this feature, the only bare names the package ships are the icon and the
  components #435 removes. The statement becomes fully true when #435 lands. What this feature
  guarantees on its own is that no component the package keeps shares a name with a daisy-cotton
  component, the icon excepted. Recorded as FR-003, FR-004 and SC-002.

- **Q: Does an old name keep working for a release?**
  A: No. There are no aliases and no deprecation period. The package is pre-1.0, its constitution
  allows component names to change between minor versions when the changelog records it, and an
  alias at the old name is exactly the collision this feature removes. Recorded as FR-005.

- **Q: Some settings take a component by name, the navbar's widget lists being the case today. Do
  those names get the prefix added for them?**
  A: No. A name in a setting is the full component name, written the way it would follow `c-` in a
  template. The package's defaults change to the prefixed names, and a project that lists a
  packaged widget writes the prefixed name. Nothing is added implicitly, because the same list can
  hold a project's own components or daisy-cotton's. Recorded as FR-008 and FR-009.

- **Q: What happens to a template a project wrote to override a component at its old path?**
  A: It stops overriding that component. A project moves the file to the prefixed path, and the
  changelog says so. The package does not look for stale overrides or warn about them. Recorded
  as FR-010 and in the edge cases.

- **Q: Do the testing fixtures the package ships take the new names?**
  A: Yes. The fixtures render whatever component name they are given and are not changed. A test
  that rendered `card` now asks for `mvp.card`. The examples in their documentation are updated.
  Recorded as FR-011.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A template names the package's components under their own prefix (Priority: P1)

A developer writing a page on django-mvp reaches for the page, a card and a form. They write
`<c-mvp.page>`, `<c-mvp.card>` and `<c-mvp.form>`, with the attributes and slots those components
have always taken, and the page renders as it did before. Someone reading that template later can
tell from the tag that these three come from django-mvp, and that a tag with no prefix does not.
The shell's own pages (lists, detail pages, forms, delete confirmations, sign-in, the account area
and the error pages) are written the same way inside the package and look and behave exactly as
they did.

**Why this priority**: This is the feature. The other stories cover the places a component name
appears outside a tag, and the record of the change.

**Independent Test**: Render every kept component by its prefixed name with the attributes its
existing tests use, and compare the result with what the old name rendered before the change.
Render the packaged pages and compare them the same way.

**Acceptance Scenarios**:

1. **Given** a project with the package installed, **When** a template uses any component the
   package keeps by its prefixed name, **Then** the component renders, and its output for a given
   set of attributes and slot content is the same as the old name produced.
2. **Given** a packaged page of each kind (list, detail, create, update, delete, sign-in, account
   area, error page), **When** it is requested after the change, **Then** the response is the same
   as it was before the change.
3. **Given** a project that does not have daisy-cotton installed, **When** a template uses the old
   bare name of a component that moved, **Then** rendering fails with an error that names the
   missing component, and nothing is rendered in its place.
4. **Given** a template that uses `<c-icon>`, **When** it renders, **Then** the icon is looked up
   by name as before.
5. **Given** a template that uses one of the basic components left for #435 (a button, for
   instance), **When** it renders, **Then** the package's own component of that name renders as
   before.
6. **Given** the full set of component names the package ships after the change, **When** it is
   compared with the set daisy-cotton 0.1.2 ships, **Then** the names they share are the icon and
   the basic components left for #435, and nothing else.

---

### User Story 2 - A component named in settings is found under its new name (Priority: P2)

A project chooses which widgets appear at the end of the navbar by listing component names in
`MVP_CONFIG`. A project that never set those lists upgrades and sees the same widgets in the same
places, because the package's defaults now carry the prefixed names. A project that did set them
changes each packaged widget's name to its prefixed form. A project that lists a widget of its own
changes nothing for that entry.

**Why this priority**: A name in a setting is the one place a moved component is referred to
without a tag, so it is the easiest to miss and it affects every page when it is wrong.

**Independent Test**: Render the shell with the default configuration, with a configuration that
lists a packaged widget by its prefixed name, and with one that lists a component defined by the
test project, and check which widgets the navbar contains each time.

**Acceptance Scenarios**:

1. **Given** a project that sets no navbar widget lists, **When** a shell page renders, **Then**
   the navbar holds the same widgets in the same order as before the change.
2. **Given** a project that lists a packaged widget by its prefixed name, **When** a shell page
   renders, **Then** that widget is in the navbar.
3. **Given** a project that lists a component of its own by that component's name, **When** a
   shell page renders, **Then** the project's component is in the navbar, and no prefix was added
   to the name.

---

### User Story 3 - A project upgrading finds every renamed component in one place (Priority: P2)

A developer upgrades a project to the release that carries this change. Before touching a
template they open the changelog and find the entry for it: a statement that the change is
breaking, the rule (everything the package keeps is now under `mvp.`), the names that did not
move, and a table giving the new name for every old one. They search their templates for each old
tag and replace it. They also have one template of their own that overrides the sidebar footer.
The entry tells them an override follows its component, so they move the file to the new path and
the override applies again.

**Why this priority**: The rename is only safe to ship if a project can carry it out from the
record alone. It ranks below the first story because there is nothing to record until the rename
exists.

**Independent Test**: Compare the changelog's table against the set of components that moved.
Place an override at a moved component's new path in a test project and render it, then place one
at the old path and render again.

**Acceptance Scenarios**:

1. **Given** the changelog entry for this change, **When** its table is compared with the set of
   components that moved, **Then** every moved component appears in it once, with its old and new
   name, and the components that kept a bare name are listed as unchanged.
2. **Given** a project template placed at the prefixed path of a packaged component, **When** a
   page that uses the component renders, **Then** the project's template is used.
3. **Given** a project template left at the old path of a component that moved, **When** a
   packaged page that uses the component renders, **Then** the packaged component is used and the
   project's template is not.

---

### User Story 4 - The documentation, the demo and the project's rules describe the new names (Priority: P3)

A developer new to the package reads the component reference and copies an example. Every tag in
it is the current name, so it works. They browse the demo site's component gallery and each page
shows the tag under the name it has now. A contributor adding a component to the package reads the
glossary's naming rules and the constitution's article on components, and both say the same thing:
a component this package owns lives under `mvp.`, the icon is the one exception, and the basic
daisyUI components come from daisy-cotton. If they add a template outside the prefix anyway, the
test suite tells them.

**Why this priority**: The package's constitution requires the documentation to change in the same
pull request as the surface it describes. It is last because it describes the other three.

**Independent Test**: Search the documentation, the README, the demo templates and the assistant
skill for the old tag of every moved component. Add a component template outside the prefix in a
scratch branch and run the test suite.

**Acceptance Scenarios**:

1. **Given** the README, the pages under `docs/`, the demo application's templates and the
   assistant skill, **When** they are searched for the old tag of any component that moved,
   **Then** none is found.
2. **Given** a component template added to the package outside the prefix whose name is not on
   the recorded list of exceptions, **When** the test suite runs, **Then** it fails and names the
   template.
3. **Given** the glossary's component library and naming rules, **When** a reader looks up any
   component the package ships, **Then** it is listed under the name it has after the change, and
   the rules state the prefix and its exceptions.
4. **Given** the constitution's article on components, **When** it is read after the change,
   **Then** it states that the package's own components live under the prefix, that the icon is
   the exception, and that basic daisyUI components come from daisy-cotton.

---

### Edge Cases

- A project has daisy-cotton installed and still uses `<c-card>`, `<c-modal>`, `<c-avatar>`,
  `<c-dropdown>` or `<c-menu.item>` expecting this package's version. The tag now resolves to
  daisy-cotton's component, which takes different attributes, so the page renders something
  different without raising an error. The changelog entry names these five as the ones to check
  first. Nothing in the package detects it.
- A project keeps an override at the old path of one of those five. Once daisy-cotton is
  installed, that file overrides daisy-cotton's component of the same name everywhere, including
  inside daisy-cotton's own templates. The changelog entry says so. The package does not detect
  it.
- A project lists a packaged navbar widget under its old name in `MVP_CONFIG`. The name is not
  translated. Every shell page fails to render with an error naming the missing component until
  the setting is corrected.
- A component directory holds both a component that moves and one that stays. The avatar moves
  and the avatar group stays; the menu entry, group, collapse and divider move and the menu
  container stays; the application's dock region moves and the dock component it draws stays.
  Each half is reached under the name the tables above give it, and a moved component that calls
  a staying one keeps calling it by its bare name.
- Markup inside a moved component: class names, element ids, `data-` attributes, Alpine store
  names and the hooks the shipped JavaScript and stylesheet select on are untouched. Only the name
  a template uses to reach the component changes.
- A template path under the `mvp/` template directory that is not a component (the packaged page
  templates, the partials named with a leading underscore) does not move.
- The demo application's own components, which exist to lay out the gallery, belong to the demo
  and keep their names.
- A test written by a project with the package's testing fixtures asks for a component by name.
  It passes the prefixed name for a moved component and gets the same result.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every component the package keeps MUST be reachable under the `mvp.` prefix, at the
  name the table in *What moves and what stays* gives it. (US1)
- **FR-002**: A moved component MUST render the same output, accept the same attributes and slots,
  and behave the same way as it did under its old name. (US1)
- **FR-003**: The icon MUST stay at its bare name and keep looking icons up by name. (US1)
- **FR-004**: The basic components that #435 removes (alert, avatar group, badge, breadcrumbs and
  its item, button, divider, dock and its item, link, the menu container, and the mockups) MUST
  stay at their bare names and render as before. (US1)
- **FR-005**: The package MUST NOT ship a moved component under its old name, as an alias or
  otherwise. (US1)
- **FR-006**: Every template the package ships MUST call a moved component by its prefixed name,
  so that no packaged page depends on the order of `INSTALLED_APPS` to find a component the
  package keeps. (US1)
- **FR-007**: After the change, the component names the package shares with daisy-cotton 0.1.2
  MUST be exactly the icon and the components listed in FR-004. (US1)
- **FR-008**: The package's default for every setting that holds a component name MUST be the
  prefixed name, so that a project which sets none of them sees no change. (US2)
- **FR-009**: A component name given in a setting MUST be used as written, with no prefix added,
  so that a project can list a component of its own or one from another package. (US2)
- **FR-010**: A project's template override MUST apply when it sits at the component's prefixed
  path, and a template left at the old path of a moved component MUST NOT be used in its place.
  (US3)
- **FR-011**: The testing fixtures the package ships MUST render a moved component when given its
  prefixed name, with no change to the fixtures' own interface. (US3)
- **FR-012**: The changelog MUST record the change as breaking under the unreleased heading, with
  the rule, the names that did not move, the five names that now collide with daisy-cotton's when
  both are installed, a note that template overrides and component names in settings move too,
  and a table giving the new name for every component that moved. (US3)
- **FR-013**: The README, every page under `docs/`, the demo application's templates and the
  assistant skill MUST use the new names wherever they show or mention a moved component. (US4)
- **FR-014**: The glossary in `CONTEXT.md` MUST list every component under its current name, and
  its naming rules MUST state the prefix, the icon exception and the components waiting on #435.
  (US4)
- **FR-015**: The constitution's article on components MUST be amended to state that the
  package's own components live under the `mvp.` prefix, that the icon is the one exception and
  why, and that basic daisyUI components come from daisy-cotton and are not written again here.
  Its version and amendment date are updated with it. (US4)
- **FR-016**: The test suite MUST fail when a component template exists in the package outside
  the prefix and is not on a recorded list of exceptions, and that list MUST hold exactly the
  icon and the components listed in FR-004. (US4)
- **FR-017**: The change MUST NOT cut a release. It lands under the unreleased heading and ships
  with the rest of roadmap item R29 in one minor version. (US3)

### Key Entities

- **Kept component**: a component this package goes on owning after roadmap item R29 is
  delivered. It is tied to Django, to the application shell or to a page, or it means something
  different from daisy-cotton's component of the same name.
- **Basic component**: a component that wraps one daisyUI component and nothing else. daisy-cotton
  provides these. The package's own copies are removed by #435 and are not touched here.
- **Prefix exception**: a component the package ships at a bare name. The icon is the only
  permanent one.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every component the package keeps is reachable under the prefix, and none of them
  is reachable under its old name from the package alone.
- **SC-002**: The package and daisy-cotton 0.1.2 share no component name other than the icon and
  the basic components waiting on #435. Of the names a reader could previously mistake for either
  package's (card, modal, avatar, dropdown, menu entry), none is ambiguous any more.
- **SC-003**: Every packaged page returns the same response before and after the change, and the
  existing component tests pass with no change other than the names they ask for.
- **SC-004**: A project that sets no component names in its settings and uses no packaged
  component directly in its own templates upgrades with no change of its own.
- **SC-005**: A developer can carry out the upgrade from the changelog entry alone: every old
  name they can find in their templates has a row in its table.
- **SC-006**: No old tag of a moved component remains in the README, the documentation, the demo
  templates or the assistant skill.
- **SC-007**: A component added outside the prefix by mistake is caught by the test suite before
  it is merged.

## Assumptions

- The component directory on `main` is as described in *What moves and what stays*. A component
  added to `main` before this is built is treated by the same rule: it moves unless it is the icon
  or one #435 removes.
- This feature does not need daisy-cotton installed and does not depend on #433. It can land
  before or after it. Nothing here calls a daisy-cotton component.
- #435 removes the basic components and shortens the exception list in FR-016 as it does. #436
  rebuilds the card, modal and avatar under the names this feature gives them. #437 decides the
  dropdown's future, #438 the menu entry, group, collapse and divider, and #439 removes the
  single-field form component. Each of those works on the prefixed name.
- The packages built on this one move to the new names in their own repositories and are capped
  below the release that carries the change. That is outside this feature.
- Nothing a person sees on any page changes, so there is no design to review ahead of the build.
- No workflow or other file under `.github/` needs to change.
