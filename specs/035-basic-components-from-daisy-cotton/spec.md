# Feature Specification: The basic components come from daisy-cotton

**Feature Branch**: `035-basic-components-from-daisy-cotton`

**Created**: 2026-10-05

**Status**: Draft

**Serves**: G2 (a component library covering what a data-centric web application needs, with small attribute APIs and deliberately limited variation), G11 (a recorded, predictable public surface that becomes safe to depend on across releases)

**Roadmap**: R29

**Issue**: #435

**Depends on**: FS-033 (#433), FS-034 (#434)

**Input**: Button, alert, badge, avatar group, breadcrumbs, divider, link, dock and the mockups
should come from [daisy-cotton](https://github.com/django-mvp/daisy-cotton). This package's copies
are removed, and every template, demo page and document that uses them switches to daisy-cotton's
attribute names. Among the changes, `full` becomes `block`, and the divider's `vertical` and
`horizontal` swap meaning. The menu container (`<c-menu>`) goes the same way, so that the sidebar
work in #438 starts from daisy-cotton's menu. The entries inside a menu stay this package's until
then.

## Clarifications

### Session 2026-10-05

The coverage scan found six ambiguities. Each was settled from the issue, roadmap item R29, the
constitution and the two packages' source. Longer rationale is in `decisions.md`.

- **Q: The issue lists nine components. Does the menu container belong to this feature?**
  A: Yes. `<c-menu>` is one of the basic components, daisy-cotton ships a drop-in container, and
  #438 depends on this feature so that it can build on that container. The entries
  (`<c-mvp.menu.item>`, `<c-mvp.menu.group>`, `<c-mvp.menu.collapse>`, `<c-mvp.menu.divider>`) stay
  this package's and keep working inside daisy-cotton's container. Recorded as FR-001, FR-004 and
  FR-015.

- **Q: Some of this package's attributes have no daisy-cotton attribute to move to. What does a
  caller write instead?**
  A: Whatever daisy-cotton documents for the same result. Where that is a class (the overlap of an
  avatar group), the caller passes the class. Where the component's slot does the job (an icon
  after a button's text), the caller uses the slot. Where the attribute did template logic (the
  button's `condition`), the caller writes the `{% if %}` itself. The full table is under FR-006.

- **Q: Demo pages may not use raw utility classes (Article XI). The avatar group's overlap is now a
  class. Which rule gives way?**
  A: The demo passes the class daisy-cotton documents, and nothing more. Article XI's rule exists
  so that this package's components are customized through their attributes. It was never meant to
  stop a demo page from showing another library's component the way that library documents it.
  This is the only raw class the feature adds to a demo page. Recorded as FR-021.

- **Q: Every call this package makes to a daisy-cotton component is isolated from the page's
  context with Cotton's `only`. Does that include the demo pages and the documentation?**
  A: No. The rule covers the templates the package ships, which render inside pages whose variables
  the package cannot know. Demo pages and documented examples show a tag the way a project writes
  it, and the documentation explains when a project needs `only`. Recorded as FR-017 to FR-019.

- **Q: daisy-cotton's alert accepts four colour variants where this package's accepted eight. What
  happens to a message or an alert that asks for one of the other four?**
  A: It renders with the default colour and no variant icon, and nothing raises. No packaged
  template asks for one of the four that went. A Django message with a level tag a project
  invented renders the same way. Recorded as FR-008 and FR-009.

- **Q: What happens to the tests written against the removed templates?**
  A: Tests that assert markup daisy-cotton now owns are removed, because daisy-cotton tests its
  own components. Tests that assert something this package still promises (the breadcrumb trail a
  page declares, the dock's toggle, the sidebar menu's accessible name) are rewritten against the
  markup now rendered. Recorded as FR-023.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A basic component's tag reaches daisy-cotton's component (Priority: P1)

A developer building on django-mvp writes `<c-button>`, `<c-alert>` or `<c-badge>` in a template.
Today they get this package's version, with its own attribute names and a narrower set of options
than daisyUI offers. After this feature the same tag reaches daisy-cotton's component. They read
one set of documentation for the basic components, daisy-cotton's, and every option documented
there works: a dashed or soft button, a badge in five sizes, a divider that turns at a breakpoint.
A tag that starts with `mvp.` is this package's, and a bare tag is daisy-cotton's. Nothing depends
on guessing which package answered.

**Why this priority**: This is the feature. Until the copies are gone, two libraries answer to the
same names and the first one in `INSTALLED_APPS` wins.

**Independent Test**: In a project with the apps in the documented order, render each of the
sixteen tags and confirm the output is daisy-cotton's component, including an option only
daisy-cotton has. Confirm this package no longer ships a template for any of them.

**Acceptance Scenarios**:

1. **Given** a project with the apps in the documented order, **When** a template renders any of
   the sixteen tags listed in FR-001, **Then** the markup comes from daisy-cotton's template and
   this package ships no template at that component path.
2. **Given** a template that passes an option only daisy-cotton's component has, such as a button
   drawn with a dashed outline, **When** it renders, **Then** the option takes effect.
3. **Given** a template that passes one of this package's former attribute names, such as `full`
   on a button, **When** it renders, **Then** the name is not translated: it has no effect on the
   component, and no error is raised.
4. **Given** daisy-cotton's menu container with this package's menu entries inside it, **When** it
   renders, **Then** every entry renders as it did inside this package's container.
5. **Given** daisy-cotton's avatar group with this package's avatars inside it, **When** it
   renders, **Then** each avatar renders as it did inside this package's group.
6. **Given** a project that keeps its own override of one of the sixteen components in its
   templates directory, **When** the tag renders, **Then** the project's override is used, as
   before.

---

### User Story 2 - The package's own pages keep working on daisy-cotton's components (Priority: P1)

Someone uses an application built on django-mvp the day after its developer upgrades. They sign
in, see a confirmation message, open a list, follow the breadcrumb trail back, delete a record and
read the warning about what else goes with it. On a phone they open the sidebar from the dock.
Every one of those pages now draws its buttons, alerts, badges, dividers, links, breadcrumbs, dock
and menus through daisy-cotton. Nothing they rely on has changed: the same controls are there,
they go to the same places, and they work from the keyboard and with a screen reader at least as
well as before.

**Why this priority**: Removing the copies without moving every caller breaks every page the
package ships. The two cannot land apart.

**Independent Test**: Run the package's test project through the shell, a list page, a detail
page, the delete page, the sign-in and sign-out pages and the error pages. Confirm each renders
without error, that the controls, links and conditional states each page had are still present,
and that no former attribute name reaches the page as a stray HTML attribute.

**Acceptance Scenarios**:

1. **Given** any page the package ships, **When** it renders, **Then** it renders without error
   and none of this package's former attribute names for these components appears on an element as
   an HTML attribute.
2. **Given** a button a packaged template used to hide with `condition`, **When** the condition is
   false, **Then** the button is absent from the page, and when it is true the button is present.
3. **Given** a request carrying one Django message at each built-in level, **When** the page
   renders, **Then** each message's text is shown in an alert, and the debug level is shown with
   the same variant as the info level.
4. **Given** a message whose level tag is not one of daisy-cotton's four alert variants, **When**
   the page renders, **Then** the message's text is still shown and nothing raises.
5. **Given** a delete view that sets `related_objects_attrs` to a different variant, **When** the
   delete page renders, **Then** the related-records alert carries that variant.
6. **Given** a page that declares a breadcrumb trail, **When** it renders, **Then** there is one
   crumb per declared entry in the declared order, an entry with an address is a link to it, and
   an entry without one is not a link and is marked as the current page.
7. **Given** a breadcrumb entry that declares extra HTML attributes, **When** it renders, **Then**
   the attributes are on that crumb's list item and `href` is written once.
8. **Given** a breadcrumb trail too long for the header, **When** it renders, **Then** the rule
   that shortens crumb text applies to the crumb markup now rendered.
9. **Given** a project that sets `MVP_CONFIG["layout"]["dock"]["class"]`, **When** the dock
   renders, **Then** the dock carries that class, and with the setting absent it carries the
   package default.
10. **Given** the dock, **When** it renders, **Then** it is a navigation landmark with an
    accessible name, the item that opens the sidebar can be focused and activated from the
    keyboard and has an accessible name, and the item for the current page is marked as current.
11. **Given** the sidebar, **When** it renders, **Then** its menu is inside a navigation landmark
    whose accessible name is the label the menu declares.
12. **Given** the theme chooser, the share menu and the user menu, **When** each renders, **Then**
    each menu that had an accessible name before still has one.
13. **Given** every divider in a packaged template, **When** it renders, **Then** it separates in
    the same direction it did before the swap.
14. **Given** a project that installs the package and uses the prebuilt stylesheet with no build
    step, **When** a packaged page renders, **Then** every class the package's templates pass to
    these components is defined in that stylesheet.

---

### User Story 3 - A page's own variables cannot change a packaged component (Priority: P2)

A developer's view puts a variable called `text`, `icon`, `variant`, `items` or `class` in the
page context, which is an ordinary thing to do. daisy-cotton's components read an attribute they
were not given from the surrounding context, so without care the navbar's buttons would pick up
the page's `text` and the breadcrumb trail the page's `items`. The package isolates every call it
makes to a daisy-cotton component, so the developer's variable names never reach the shell. Content
the package places inside a component, such as the text of a message, still sees the page's
context.

**Why this priority**: The fault only shows on a page that happens to use one of those names, so
it would reach projects as a rare and confusing bug. It needs to be right, but the swap in the
first two stories is what makes it possible at all.

**Independent Test**: Render a packaged page with context variables named after the attributes
these components declare, and confirm the page is identical to the same page rendered without
them. Confirm the check that scans the packaged templates fails when a call is added without
isolation.

**Acceptance Scenarios**:

1. **Given** a page context holding variables named after attributes that daisy-cotton's
   components declare, **When** a packaged page renders, **Then** its packaged components render
   exactly as they do without those variables.
2. **Given** a packaged template that puts page content inside one of these components, **When**
   it renders, **Then** that content can still read the page's context.
3. **Given** a packaged template that calls a daisy-cotton component without isolating it,
   **When** the test suite runs, **Then** a check fails and names the template and the tag.
4. **Given** a daisy-cotton component that itself draws a button or an icon, such as a dismissible
   alert, **When** a packaged template calls it in isolation, **Then** the inner button and icon
   still render, and the icon is still looked up by name.

---

### User Story 4 - A developer upgrading can move their templates from the changelog alone (Priority: P2)

A developer maintains a project, or a package, built on django-mvp. They read the changelog entry
for the release, which is marked breaking. It lists every one of the sixteen tags, every attribute
that was renamed or removed, and what to write in its place. They search their templates for each
old name and change it. The demo pages and the documentation show the new names in use, so they
can copy a working example. Nothing on any documentation page still describes an attribute that
no longer exists.

**Why this priority**: A former attribute name fails quietly: the component ignores it and the
page still renders. The changelog and the demo are the only way a developer finds out, so they
have to be complete. They follow the swap itself.

**Independent Test**: Take a template written against the previous release that uses every former
attribute of these components. Move it using only the changelog entry, and confirm it renders the
same controls. Open each demo page for these components and each documentation page that mentions
them, and confirm no former attribute name appears.

**Acceptance Scenarios**:

1. **Given** the changelog entry for this change, **When** a developer reads it, **Then** it is
   marked breaking and names every tag in FR-001 and every row of the table in FR-006 with its
   replacement.
2. **Given** the demo application, **When** each demo page for these components renders, **Then**
   it renders without error and uses daisy-cotton's attribute names throughout.
3. **Given** the demo pages for these components, **When** their templates are searched for raw
   utility classes, **Then** the only ones found are classes daisy-cotton documents as the way to
   set that option.
4. **Given** the documentation, the README, `CONTEXT.md` and the skill for coding agents that ships
   under `skills/`, **When** they are searched for the former attribute names on these tags and for
   statements that the package provides these components, **Then** none is found.
5. **Given** the component reference, **When** a developer looks up one of the sixteen tags,
   **Then** it tells them the component is daisy-cotton's and links to daisy-cotton's own
   documentation for it.
6. **Given** the documentation, **When** a developer looks for how to stop a page variable reaching
   a component, **Then** it explains Cotton's `only` and when a project needs it.

---

### Edge Cases

- A project lists `daisy_cotton` above `mvp` in `INSTALLED_APPS`. For these sixteen tags the order
  no longer matters, because only one package ships them. The order still matters for the icon,
  and FS-033 warns about it.
- A project overrode one of these components by dropping a template at the same path. Its override
  still wins. It now also answers when one of daisy-cotton's own components draws that tag
  internally, for example the dismiss button inside an alert, so an override with a narrower set of
  attributes than daisy-cotton's can break those components. The upgrade notes say so.
- A project's templates still pass a former attribute name. The component ignores it and writes it
  to the element as an HTML attribute. Nothing raises, which is why the changelog table has to be
  complete.
- A divider that passes `vertical` or `horizontal` and is not updated renders, but in the other
  direction. The changelog calls this one out on its own.
- A link written without an `href` used to point at `#`. It now renders an anchor with no `href`,
  which is not focusable and not a link to assistive technology.
- A code mockup line written without a `prefix` used to show a shell prompt. It now shows none.
- A badge used to drop any attribute it did not declare. Extra attributes now reach the badge
  element.
- A view passes attributes for one of these components from Python as a dictionary. The keys in
  that dictionary are attribute names like any other and move the same way.
- A page context holds a variable with the same name as an attribute. Covered by User Story 3 for
  the package's own calls. A project's own calls are the project's to isolate.
- The page has no messages, the trail has no entries, or the dock menu has no items. Each renders
  as it did before, with no empty alert, crumb or item.

## Requirements *(mandatory)*

### Functional Requirements

**Removing the copies**

- **FR-001**: The package MUST stop shipping its own template for each of these sixteen tags:
  `c-button`, `c-alert`, `c-badge`, `c-avatar.group`, `c-breadcrumbs`, `c-breadcrumbs.item`,
  `c-divider`, `c-link`, `c-dock`, `c-dock.item`, `c-mockup.browser`, `c-mockup.code`,
  `c-mockup.code.line`, `c-mockup.phone`, `c-mockup.window` and `c-menu`.
- **FR-002**: In a project that installs the package as documented, each of those tags MUST render
  daisy-cotton's component of the same name, with every attribute daisy-cotton documents for it.
- **FR-003**: The package MUST NOT ship an alias, a wrapper or a translation layer for any of those
  tags or for any of their former attribute names.
- **FR-004**: Every component the package keeps MUST keep working where it is used with one of
  these tags. This covers the menu entries inside daisy-cotton's menu container and the package's
  avatar inside daisy-cotton's avatar group. This feature does not rename, remove or rebuild any
  component outside the sixteen.
- **FR-005**: A project's own override of one of these tags MUST keep taking precedence over
  daisy-cotton's template.

**Moving the callers**

- **FR-006**: Every use of these tags in the package's templates, in the demo application and in
  the documentation, and every attribute dictionary the package builds in Python for one of them,
  MUST use daisy-cotton's attributes as follows.

  | Tag | Former attribute | What a caller writes now |
  |---|---|---|
  | `c-button` | `full` | `block` |
  | `c-button` | `variant="ghost"`, `variant="link"` | the `ghost` or `link` attribute |
  | `c-button` | `reverse` | the icon placed in the default slot after the text |
  | `c-button` | `align` | nothing: removed with no replacement |
  | `c-button` | `condition` | an `{% if %}` around the tag |
  | `c-alert` | `variant` of `primary`, `secondary`, `accent` or `neutral` | one of `info`, `success`, `warning`, `error`, or no variant |
  | `c-avatar.group` | `size` | the overlap class daisy-cotton documents, passed in `class` |
  | `c-breadcrumbs.item` | extra attributes, which reached the link | extra attributes, which now reach the list item |
  | `c-divider` | `label` | `text` |
  | `c-divider` | `position` | `placement` |
  | `c-divider` | `vertical` | `horizontal`: the two names have swapped meaning |
  | `c-link` | no `href`, which meant `#` | an explicit `href` |
  | `c-dock` | no `class`, which meant the configured dock class | the configured class passed by the caller |
  | `c-mockup.code.line` | no `prefix`, which meant a shell prompt | an explicit `prefix` where a prompt is wanted |
  | `c-menu` | `label` | an accessible name supplied by the caller |
  | `c-menu` | `grow`, `responsive` | `class`, or `horizontal` with a breakpoint |

- **FR-007**: A packaged template or a demo template MUST NOT pass a former attribute name from
  that table to one of these tags, and a rendered packaged page MUST NOT carry one as a stray HTML
  attribute.
- **FR-008**: Every Django message MUST still be shown, one alert per message. The five built-in
  levels MUST each map to a variant daisy-cotton's alert accepts, with debug shown as info.
- **FR-009**: A message or an alert asking for a variant daisy-cotton's alert does not accept MUST
  render its content without raising.
- **FR-010**: A button that a packaged template rendered conditionally MUST still be absent when
  its condition is false.
- **FR-011**: The delete page MUST keep forwarding `related_objects_attrs` to the related-records
  alert, and its documentation MUST name the variants that alert now accepts.
- **FR-012**: A breadcrumb trail a page declares MUST render one crumb per entry in order, as a
  link when the entry has an address and as the current page when it has none. `href` MUST be
  written once per link.
- **FR-013**: The rule in the package's stylesheet that shortens long crumb text MUST match the
  crumb markup daisy-cotton renders, so a long trail behaves as it does today.
- **FR-014**: The dock MUST keep taking its class from `MVP_CONFIG["layout"]["dock"]["class"]` and
  fall back to the package default (Article XII). The dock item that opens the sidebar MUST stay
  focusable and operable from the keyboard and MUST have an accessible name. The current page's
  item MUST be marked as current (Article XIII).
- **FR-015**: The sidebar menu MUST stay inside a navigation landmark named by the label the menu
  declares. The theme chooser, the share menu and the user menu MUST each keep the accessible name
  they have today. The sidebar's footer row MUST stay below the menu as it does today.
- **FR-016**: Every divider, link, badge, mockup and avatar group in a packaged or demo template
  MUST keep the direction, destination and content it had before the swap.

**Keeping the page's variables out**

- **FR-017**: Every call a packaged template makes to a daisy-cotton component MUST be isolated
  from the surrounding template context with Cotton's `only`, so that a page variable named after
  one of the component's attributes cannot change it.
- **FR-018**: Content a packaged template places inside an isolated component MUST still be able to
  read the page's context.
- **FR-019**: The test suite MUST fail, naming the template and the tag, when a packaged template
  calls one of daisy-cotton's components without isolating it.

**The stylesheet**

- **FR-020**: The prebuilt stylesheet MUST be rebuilt and committed with this change (Article XV)
  and MUST define every class the package's templates and demo pages pass to these components. No
  page MAY need a build step it did not need before.

**Demo, documentation and tests**

- **FR-021**: The demo page for each of these components MUST stay and MUST use daisy-cotton's
  attributes. A demo template MAY carry a raw utility class only where daisy-cotton documents that
  class as the way to set the option.
- **FR-022**: The documentation, the README, `CONTEXT.md` and the skill under `skills/` MUST stop
  describing these components as the package's own. The component reference MUST say they come from
  daisy-cotton and link to its documentation. The documentation MUST explain when a project needs
  `only` and what an existing override of one of these tags now affects (Articles VI and XVII).
- **FR-023**: Tests that assert the markup of a removed template MUST be removed. Tests that assert
  something this package still promises MUST be rewritten against the markup now rendered. The
  test that renders every packaged component MUST still cover every component the package ships
  (Articles I and XIII).
- **FR-024**: The change MUST be recorded in the changelog under the unreleased heading, marked
  breaking, with every tag in FR-001 and every row of the table in FR-006 (Article XVI). This
  feature MUST NOT cut a release.

### Requirement coverage

| Story | Requirements |
|---|---|
| US-1: A basic component's tag reaches daisy-cotton's component | FR-001, FR-002, FR-003, FR-004, FR-005, FR-023 |
| US-2: The package's own pages keep working on daisy-cotton's components | FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-020, FR-023 |
| US-3: A page's own variables cannot change a packaged component | FR-017, FR-018, FR-019 |
| US-4: A developer upgrading can move their templates from the changelog alone | FR-006, FR-007, FR-021, FR-022, FR-024 |

US-1 and US-2 cannot merge apart: removing a template without moving its callers breaks the pages
that use it. They are written as two stories because they are proved differently, one by which
template answers a tag and the other by what the package's pages still do.

### Key Entities

- **Basic component**: one of the sixteen tags in FR-001. A daisyUI building block with no tie to
  Django or to the application shell, which daisy-cotton provides for any project.
- **Kept component**: a component this package goes on shipping under the `mvp.` prefix (FS-034),
  plus the icon. It is tied to Django, to the shell or to the pages.
- **Former attribute**: an attribute name this package's copy of a basic component accepted and
  daisy-cotton's component does not, or accepts with a different meaning.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: None of the sixteen component templates remains in the package, and each of the
  sixteen tags renders daisy-cotton's component.
- **SC-002**: Every page the package ships and every demo page renders without error on
  daisy-cotton's components, and the full test suite passes.
- **SC-003**: A search of the package's templates, the demo and the documentation finds no former
  attribute name on any of the sixteen tags.
- **SC-004**: Every call from a packaged template to a daisy-cotton component is isolated from the
  page's context, and a packaged page renders identically whatever attribute-named variables its
  context holds.
- **SC-005**: A developer can move a template that uses every former attribute of these components
  by following the changelog entry alone, without reading either package's source.
- **SC-006**: A project that installs the package and uses the prebuilt stylesheet renders every
  packaged page with no build step, as before.
- **SC-007**: Every acceptance scenario above that a test can decide is proved by a test that
  fails if the behaviour is removed (Articles I and XIII).

## Assumptions

- FS-033 has landed: daisy-cotton is installed with the package, the prebuilt stylesheet covers the
  classes daisy-cotton's templates write, the app-order check exists, and a test already proves
  that content inside an isolated component sees the page's context. This feature relies on that
  proof and does not repeat it beyond FR-018.
- FS-034 has landed: every component the package keeps is under the `mvp.` prefix, and Article XI
  says that the basic daisyUI components come from daisy-cotton. The sixteen templates this
  feature removes were left at their bare paths by FS-034.
- daisy-cotton is the version the package pins (0.1.2 or later, below 0.2). A gap found in one of
  its components while moving a caller is raised on daisy-cotton's tracker, not patched here.
- A like-for-like swap changes small details of how these components are drawn, such as the frame
  around a mockup. Those follow daisy-cotton and are not held to their former look.
- The demo keeps the pages it has for these components. Demo pages for the daisy-cotton components
  this package never had are not part of this feature.
- The change ships with the rest of R29 in one breaking minor release. Packages built on this one
  move their own templates in their own repositories.

## Out of Scope

- Installing daisy-cotton, stylesheet coverage of its templates and the app-order check: #433.
- Renaming the kept components and amending Article XI: #434.
- Rebuilding `<c-mvp.card>`, `<c-mvp.modal>` and `<c-mvp.avatar>` on daisy-cotton's: #436.
- The dropdown: #437.
- The menu entries, the sidebar, the icon rail, the user menu and the drawer: #438.
- Fields written by hand in a template, and removing the single-field component: #439.
- The shell markup still written by hand, including drawing messages as a toast, the navbar, the
  footer and pagination: #440. This feature changes the messages template only as far as the alert
  inside it needs.
- Any change to the `.github/` directory.
