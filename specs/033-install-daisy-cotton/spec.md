# Feature Specification: Install daisy-cotton alongside the package, with no visible change

**Feature Branch**: `033-install-daisy-cotton`

**Created**: 2026-10-05

**Status**: Draft

**Serves**: G6 (no front-end build tooling required to use the package), G2 (a component library covering what a data-centric web application needs, with small attribute APIs and deliberately limited variation)

**Roadmap**: R29

**Issue**: #433

**Input**: The package should depend on daisy-cotton and install it for every project. The
prebuilt stylesheet, and the build entry point a project generates, should cover every class
daisy-cotton's components can render. Nothing on any page changes yet. This is the ground the rest
of the move to daisy-cotton stands on, and it proves the stylesheet coverage before any component
moves.

## Clarifications

### Session 2026-10-05

The coverage scan found five ambiguities. Each was resolved from the issue, roadmap item R29, the
package's constitution and daisy-cotton 0.1.2 as published. Longer rationale is in `decisions.md`.

- **Q: What does "install it for every project" mean, when a package cannot add itself to a
  project's `INSTALLED_APPS`?**
  A: Installing django-mvp installs daisy-cotton as a dependency, and a project adds
  `daisy_cotton` to `INSTALLED_APPS` as it already does for `django_cotton`, `crispy_forms` and
  `mvp_forms`. The getting-started guide lists it, and the project is told at start-up when the
  entry is missing. Recorded as FR-001, FR-002 and FR-012.

- **Q: Both packages ship a `<c-button>`, a `<c-card>` and a dozen other same-named components.
  Which one does a page get?**
  A: This package's, exactly as before. `daisy_cotton` is listed below `mvp`, and the first app
  that has a component wins. The project is told at start-up when the two are the other way round,
  because that order silently swaps a dozen components. Recorded as FR-003, FR-004 and FR-013.

- **Q: What counts as "every class daisy-cotton's components can render"?**
  A: Every class written out in daisy-cotton's templates, plus every class a component builds
  while it renders from an attribute with a fixed set of choices: each variant, size, placement
  and breakpoint. Two things are outside it. Classes a caller passes in through `class` are the
  caller's own. Icon classes are not styled by this stylesheet, and this package's `<c-icon>`
  resolves icons by name anyway. Recorded as FR-006.

- **Q: The prebuilt stylesheet already carries all of daisyUI. Does the entry a project generates
  for its own build need the same coverage?**
  A: Yes. The issue names both. A project that builds its own stylesheet from the generated entry
  gets every class daisy-cotton's components can render without adding anything by hand,
  including the classes built at render time that a scan of the templates cannot see. Recorded as
  FR-008 and FR-009.

- **Q: Does this feature make daisy-cotton's components ready for a project to use?**
  A: Not all of them yet. A daisy-cotton component that draws another component inside itself
  (an alert drawing its dismiss button, say) gets this package's same-named component while both
  exist, and the two do not take the same attributes. That is settled when this package's copies
  are removed (#435). This feature guarantees that daisy-cotton is installed, that its templates
  are found, and that every class they can render is styled. The documentation says only that.
  Recorded as FR-005 and FR-017.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A project gets daisy-cotton with the package and no page changes (Priority: P1)

A developer upgrades django-mvp in an existing project. daisy-cotton arrives with it, without a
second install command. They add one line to `INSTALLED_APPS`, below `mvp`, as the upgrade note
tells them. Every page in their project then renders exactly as it did before the upgrade: the
shell, the list and detail pages, the forms, their own templates that call `<c-button>` or
`<c-card>`. Nothing they wrote needs to change. A developer starting a new project follows the
getting-started guide and ends up in the same place.

**Why this priority**: This is the feature. The features that follow replace components one at a
time, and each of them needs daisy-cotton present and the pages unchanged as its starting point.

**Independent Test**: Install the package into a clean environment and confirm daisy-cotton is
installed with it. Render the package's pages and components with `daisy_cotton` listed below
`mvp`, and confirm the output is the same as without it.

**Acceptance Scenarios**:

1. **Given** a clean environment, **When** django-mvp is installed, **Then** daisy-cotton is
   installed with it, at a version this package has declared it works with.
2. **Given** a project with `daisy_cotton` listed below `mvp`, **When** a page renders a component
   that both packages ship under the same name, **Then** the component rendered is this package's.
3. **Given** the same project, **When** any page or component this package ships is rendered,
   **Then** its markup is the same as it was before daisy-cotton was added.
4. **Given** the same project, **When** a template calls a daisy-cotton component that this
   package has no same-named component for, **Then** the component is found and rendered.
5. **Given** a developer following the getting-started guide on a new project, **When** they copy
   the list of apps it gives, **Then** `daisy_cotton` is in it, in a position that works.

---

### User Story 2 - The prebuilt stylesheet styles every daisy-cotton component (Priority: P1)

A developer uses the package with no build step of their own, which is how most projects run. A
later release starts drawing the shell with daisy-cotton's components, and the developer starts
calling them in their own templates. Each one arrives styled: its base look, each variant and size
it offers, each breakpoint at which it can change layout. The developer never finds a component
that renders unstyled because the stylesheet they were given did not know about one of its
classes.

**Why this priority**: G6 is the promise that a project needs no build tooling. If one class is
missing from the prebuilt stylesheet, the first component that moves to daisy-cotton breaks that
promise on a page the project did not write. Proving the coverage before any component moves is
what the issue asks for.

**Independent Test**: Work out every class daisy-cotton's components can render from the installed
package, and confirm each one has a rule in the stylesheet shipped in the package.

**Acceptance Scenarios**:

1. **Given** the installed daisy-cotton, **When** every class its components can render is
   compared with the prebuilt stylesheet, **Then** each one is styled by it.
2. **Given** a daisy-cotton component with an attribute that takes a breakpoint, **When** it is
   rendered at each breakpoint the attribute accepts, **Then** the class it writes is styled by
   the prebuilt stylesheet.
3. **Given** the prebuilt stylesheet from before this feature, **When** it is compared with the
   one this feature ships, **Then** no class the earlier one styled has been lost.
4. **Given** a later version of daisy-cotton whose components render a class the prebuilt
   stylesheet lacks, **When** the package's tests run against it, **Then** they fail and name the
   class.

---

### User Story 3 - A project that builds its own stylesheet gets the same coverage (Priority: P2)

A developer writes Tailwind classes in their own templates, so they build their own stylesheet
from the entry file the package generates for them. They re-run the generator after upgrading, as
its header already tells them to, and rebuild. Their stylesheet now styles every daisy-cotton
component as fully as the prebuilt one does. They did not have to find daisy-cotton's install
path, read its templates or add a line by hand. A developer who wires their own entry file
instead asks the generator for its paths and finds daisy-cotton's among them.

**Why this priority**: Fewer projects build their own stylesheet than use the prebuilt one, and
they already expect to re-run the generator on upgrade. Without this story those projects would
be the ones that meet unstyled components.

**Independent Test**: Generate the entry file in a project and confirm that a stylesheet built
from it styles every class daisy-cotton's components can render.

**Acceptance Scenarios**:

1. **Given** a project with the package installed, **When** the developer generates the entry
   file, **Then** it covers daisy-cotton's templates wherever daisy-cotton is installed in that
   environment.
2. **Given** that entry file, **When** a stylesheet is built from it, **Then** every class
   daisy-cotton's components can render is styled, including the ones built at render time.
3. **Given** a developer wiring their own entry file, **When** they ask the generator for its
   paths, **Then** daisy-cotton's location is one of them, and every path printed before this
   feature is still printed in the same position.
4. **Given** the entry file generated before this feature, **When** it is compared with the one
   generated now, **Then** everything the earlier one covered is still covered.

---

### User Story 4 - A project is told when its app list is wrong (Priority: P2)

A developer upgrades and forgets the new `INSTALLED_APPS` line, or adds it above `mvp` because
that is where daisy-cotton's own README shows it. Neither mistake raises an error by itself. The
first would surface later as a missing template on whichever page first uses a daisy-cotton
component. The second would quietly replace this package's button, card, modal and a dozen others
with different components that take different attributes. Instead, the developer is told as soon
as the project starts, in a message that names the app, says what is wrong and says where the line
belongs.

**Why this priority**: The mistakes are easy to make and their symptoms point nowhere near the
cause. The package works without the message when the app list is right, which is why this is not
P1.

**Independent Test**: Run the project's start-up checks with `daisy_cotton` missing, with it
above `mvp`, and with it below `mvp`, and confirm the first two each produce a message and the
third produces none.

**Acceptance Scenarios**:

1. **Given** a project whose `INSTALLED_APPS` has `mvp` but not `daisy_cotton`, **When** the
   project's start-up checks run, **Then** the developer is told that `daisy_cotton` is missing
   and where to add it.
2. **Given** a project that lists `daisy_cotton` above `mvp`, **When** the checks run, **Then**
   the developer is told the order is wrong and which of the two must come first.
3. **Given** a project that lists `daisy_cotton` anywhere below `mvp`, **When** the checks run,
   **Then** nothing is reported about either app.
4. **Given** either message, **When** the developer silences it by its identifier through
   Django's own setting for that, **Then** it is no longer reported.

---

### User Story 5 - A page's variables stay out of a daisy-cotton component (Priority: P3)

A contributor to this package is about to replace a hand-written piece of the shell with a
daisy-cotton component. Many of daisy-cotton's components take attributes with everyday names such
as `text`, `icon`, `items` and `variant`. A page often has a variable with one of those names. If
the contributor's call does not pass that attribute, the component picks up the page's variable
instead and draws something nobody asked for. The package's rule is that every call it makes to a
daisy-cotton component is isolated from the page, and the contributor needs to know two things
before relying on it: that isolation really does keep the page's variables out, and that whatever
they put between the component's tags can still use the page's variables. Both are proved by the
package's tests, and the contributor guide states the rule.

**Why this priority**: No page calls a daisy-cotton component in this feature, so nothing can
leak yet. The proof and the written rule are here so that the seven features that follow start
from a settled convention and do not each rediscover it.

**Independent Test**: Render a daisy-cotton component from a page that has a variable named after
one of the component's attributes, once isolated and once not, with content between its tags that
uses another page variable.

**Acceptance Scenarios**:

1. **Given** a page with a variable named after an attribute of a daisy-cotton component, **When**
   the page calls that component in isolation without passing the attribute, **Then** the
   component renders as though the attribute were unset.
2. **Given** the same page, **When** the content placed inside the isolated component uses a page
   variable, **Then** that content renders with the page's value.
3. **Given** the same page, **When** content is passed to one of the component's named slots,
   **Then** that content also renders with the page's values.
4. **Given** an isolated call that does pass the attribute, **When** it renders, **Then** the
   component uses the value passed.
5. **Given** a contributor reading the contributor guide, **When** they look for how to call a
   daisy-cotton component from this package's templates, **Then** they find the rule and the
   reason for it.

---

### Edge Cases

- A project lists `daisy_cotton` above `mvp`. A dozen components change to daisy-cotton's
  versions. The project is told at start-up (FR-013); the package does not try to correct the
  order itself.
- A project replaces one of this package's components with its own template of the same name. Its
  template still wins, because the project's apps are listed above both `mvp` and `daisy_cotton`.
- A project already depends on daisy-cotton and lists `daisy_cotton` itself. Nothing changes for
  it as long as the entry is below `mvp`. If it is above, the project is told.
- A project pins a daisy-cotton version outside the range this package declares. The installer
  reports the conflict. The package does not widen its range to hide it.
- A daisy-cotton component draws another component inside itself, and this package ships a
  component of that name. It gets this package's version until that copy is removed (#435), and
  may render incorrectly. No page in this package calls such a component in this feature.
- A daisy-cotton component takes an attribute with no fixed set of choices, such as a number.
  Coverage is promised for the choices daisy-cotton documents, not for every value a caller could
  invent.
- The stylesheet is built on a machine where daisy-cotton is not installed. The build must not
  quietly produce a stylesheet that lacks daisy-cotton's classes and pass for a good one: the
  package's tests fail against it (FR-010).
- A project uses `MVP_CONFIG` to turn the prebuilt stylesheet off and supplies its own. Coverage
  of daisy-cotton's classes is then the project's to provide, through the generated entry file.
- The Cotton version this package pins is older than the one daisy-cotton is developed against.
  daisy-cotton's components must render under the pinned version (FR-011).

## Requirements *(mandatory)*

### Functional Requirements

**Installing it**

- **FR-001**: The package MUST declare daisy-cotton as a runtime dependency, at `>=0.1.2,<0.2`, so
  that installing django-mvp installs it.
- **FR-002**: The getting-started guide's list of apps MUST include `daisy_cotton`, placed below
  `mvp`, and MUST say why the order matters. The package's demo project and test project MUST use
  the same order.
- **FR-003**: With `daisy_cotton` below `mvp`, a component that both packages ship under the same
  name MUST resolve to this package's.
- **FR-004**: Every page and component this package ships MUST render the same markup as before
  this feature. No template under the package's components changes.
- **FR-005**: A daisy-cotton component for which this package ships no same-named component MUST
  be found and rendered when a template calls it.

**The prebuilt stylesheet**

- **FR-006**: The prebuilt stylesheet MUST style every class daisy-cotton's components can
  render: every class written out in its templates, and every class a component builds at render
  time from an attribute with a fixed set of choices, including breakpoint-prefixed forms. Classes
  a caller supplies and icon classes are outside this.
- **FR-007**: The prebuilt stylesheet MUST still style every class it styled before this feature.
  It MUST be rebuilt and committed on this branch (Article XV).

**The generated entry file**

- **FR-008**: The entry file the package generates for a project's own build MUST cover
  daisy-cotton's templates, resolved for the environment it is generated in, with no line added by
  hand.
- **FR-009**: A stylesheet built from the generated entry file MUST style every class named in
  FR-006, including those built at render time. It MUST still cover everything the entry file
  covered before this feature.
- **FR-010**: The package's tests MUST work out the classes daisy-cotton's components can render
  from the installed package, and MUST fail, naming the class, when one is missing from the
  prebuilt stylesheet or from what the generated entry file covers.
- **FR-016**: The generator's paths-only output MUST include daisy-cotton's location. The paths it
  printed before this feature MUST keep their positions.

**Compatibility**

- **FR-011**: daisy-cotton's components MUST render under the version of Cotton this package
  requires. If they do not, the requirement on Cotton is moved to a version under which both
  packages' components render, and FR-004 still holds.

**Telling the project**

- **FR-012**: When `mvp` is installed and `daisy_cotton` is absent from `INSTALLED_APPS`, the
  project's start-up checks MUST report an error that names the missing app and says where to add
  it.
- **FR-013**: When `daisy_cotton` is listed above `mvp`, the checks MUST report a warning that
  names both apps and says which comes first.
- **FR-014**: When `daisy_cotton` is listed below `mvp`, the checks MUST report nothing about
  either. Each message MUST carry its own identifier so a project can silence it with Django's
  setting for silencing checks.

**Isolation**

- **FR-015**: The package's tests MUST prove that a daisy-cotton component called in isolation
  does not read a page variable named after one of its attributes, that content placed inside it
  and in its named slots still renders with the page's variables, and that an attribute passed to
  it is used.
- **FR-018**: The contributor guide MUST state that this package's templates call daisy-cotton's
  components in isolation, and why.

**Shipping it**

- **FR-017**: The documentation MUST be updated in this pull request wherever it lists the apps to
  install, describes what the prebuilt stylesheet covers, or describes the generated entry file
  and its paths output, including the README and the shipped skill's quickstart (Articles VI and
  XVII). It MUST describe only what this feature delivers, and MUST NOT present daisy-cotton's
  components as replacing this package's.
- **FR-019**: The changelog's unreleased section MUST record the new dependency and the line a
  project adds to `INSTALLED_APPS` on upgrade. This feature MUST NOT cut a release.
- **FR-020**: The new dependency's justification MUST be recorded as an architecture decision
  record (Articles II and VII), and the dependency check MUST pass.

### Requirement coverage

| Story | Requirements |
|---|---|
| US-1 — A project gets daisy-cotton with the package and no page changes | FR-001, FR-002, FR-003, FR-004, FR-005, FR-011, FR-017, FR-019, FR-020 |
| US-2 — The prebuilt stylesheet styles every daisy-cotton component | FR-006, FR-007, FR-010, FR-017 |
| US-3 — A project that builds its own stylesheet gets the same coverage | FR-008, FR-009, FR-010, FR-016, FR-017, FR-019 |
| US-4 — A project is told when its app list is wrong | FR-012, FR-013, FR-014, FR-017 |
| US-5 — A page's variables stay out of a daisy-cotton component | FR-015, FR-018 |

Every story that changes what the *Shipping it* requirements describe carries them: it documents
its own surface and records its change in the changelog. FR-020 lands with the first story.

### Key Entities

- **daisy-cotton**: a separate package of Cotton components, one for each base daisyUI component,
  installed as the Django app `daisy_cotton`. It ships templates only, with no stylesheet and no
  scripts, and expects the project to supply daisyUI.
- **Prebuilt stylesheet**: the stylesheet committed in this package and served to every project
  that does not build its own. It is a build output, rebuilt on the branch that changes what goes
  into it.
- **Generated entry file**: the Tailwind entry a project asks the package to write when it builds
  its own stylesheet. It names the locations to scan, resolved for that project's environment.
- **Isolated call**: a call to a Cotton component that gives it only the attributes and content
  passed to it, and none of the calling page's variables.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Installing django-mvp into a clean environment installs daisy-cotton with one
  command and no further step.
- **SC-002**: Every existing test that asserts on a rendered page or component passes without
  being changed.
- **SC-003**: Every class the components of daisy-cotton 0.1.2 can render is styled by the
  prebuilt stylesheet. None is missing.
- **SC-004**: The same holds for a stylesheet a project builds from a freshly generated entry
  file, with no line added by hand.
- **SC-005**: No class the prebuilt stylesheet styled before this feature is unstyled after it.
- **SC-006**: A project with `daisy_cotton` missing, or listed above `mvp`, is told at start-up in
  both cases, and a project with the right order is told nothing.
- **SC-007**: A developer sets up a new project from the getting-started guide alone and its
  start-up checks report nothing about its app list.
- **SC-008**: A page variable named after a component's attribute never reaches a daisy-cotton
  component called in isolation, and content placed inside that component always renders with the
  page's variables.
- **SC-009**: Every acceptance scenario above is proved by a test that fails if the behaviour is
  removed (Articles I and XIII).

## Assumptions

- Every feature under roadmap item R29 lands on the main branch before the next release, and they
  ship together as one breaking minor release. No release goes out with daisy-cotton installed and
  this package's same-named components still in place, so the state in which a daisy-cotton
  component can draw this package's button inside itself never reaches a project.
- A project adds `daisy_cotton` to `INSTALLED_APPS` itself. The package does not add apps to a
  project's settings on its behalf, which matches how `django_cotton`, `crispy_forms` and
  `mvp_forms` are already handled.
- daisy-cotton stays within the declared version range for the life of that release. A new minor
  version of daisy-cotton is adopted deliberately, with the coverage tests run against it.
- The `Stylesheet` workflow keeps doing what it does today, which is proving that the stylesheet
  compiles. It installs no Python, so it cannot see daisy-cotton's templates and proves nothing
  about coverage. Coverage is proved by the package's tests against the committed stylesheet. This
  feature does not change any workflow.
- No page, component, demo page or test in this package calls a daisy-cotton component after this
  feature, apart from the tests this feature adds. Which components move, and when, belongs to the
  features that follow: the `mvp.` prefix (#434), the basic components (#435), the card, modal and
  avatar (#436), the dropdown (#437), the sidebar and user menus (#438), hand-written fields
  (#439) and the rest of the shell's markup (#440).
- This package's `<c-icon>` stays where it is and keeps resolving icons by name. With `mvp` above
  `daisy_cotton` it already takes the place of daisy-cotton's plain icon, including inside
  daisy-cotton's own components.
- The packages built on this one are not changed here. They add `daisy_cotton` to their own
  example projects when they move to the release that carries R29.
