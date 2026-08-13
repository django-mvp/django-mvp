# Feature Specification: Themes that ship with the package

**Feature Branch**: `026-ship-prebuilt-daisyui`

**Created**: 2026-08-13

**Status**: Draft

**Serves**: G8 (theming and branding without forking templates), G6 (no front-end build tooling required), G14 (every front-end asset shipped and versioned with the package)

**Roadmap**: R18 · **Issue**: #230

**Input**: User description: "Ship the prebuilt daisyUI themes inside the package and document writing a fully custom theme. A project selects the applied theme and the set offered by the theme switcher through MVP_CONFIG, with no build step, no third-party fetch and no template override. A project's own theme is a plain CSS file it writes and loads, documented in full."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Apply a prebuilt theme by configuration (Priority: P1)

A developer building on django-mvp wants their application to use one of the design system's prebuilt
themes instead of the stock light and dark pair. They set the theme name in the package's configuration
dictionary and reload the page. The whole application renders in that theme, including every packaged
component, and nothing was installed, built or fetched to make it happen.

**Why this priority**: This is the capability the feature exists for and the smallest slice that delivers
it. Without it a project cannot reach any theme beyond light and dark except by overriding a template,
which is precisely what G8 says should not be necessary. Every other story in this spec builds on the
themes being present and selectable.

**Independent Test**: Set the theme name in configuration in a project with no Node toolchain installed
and no network access, load any page, and confirm the rendered colours are the configured theme's and
that no request left the application for a stylesheet.

**Acceptance Scenarios**:

1. **Given** a project that has set no theme in its configuration, **When** any page is loaded, **Then**
   the theme applied is the same one that applied before this feature, and the switcher behaves as it
   did before.
2. **Given** a project that has set a prebuilt theme name in its configuration, **When** any page is
   loaded, **Then** every packaged component renders in that theme's colours, corner radii and border
   widths.
3. **Given** a project with no front-end build tooling installed, **When** it sets a prebuilt theme name,
   **Then** the theme applies with no build step and no error.
4. **Given** any page of the application, **When** it is loaded, **Then** no stylesheet or theme
   definition is requested from a host outside the project.
5. **Given** a configured theme, **When** a page is loaded, **Then** the theme is applied before the page
   is first painted, so no incorrectly themed frame is shown.

---

### User Story 2 - Let visitors choose from the themes a project offers (Priority: P2)

A project wants to give its users a choice of appearance rather than a single fixed look. It declares
which themes the switcher offers, and the packaged switcher presents exactly that set. A visitor picks
one and it stays applied as they move around the application and when they come back later.

**Why this priority**: A runtime choice is what R18 asks for beyond a fixed default, and it is the visible
half of theming. It ranks below the first story because a project can ship a themed application without
it, and because it depends on the themes being present and configurable first.

**Independent Test**: Declare a set of three themes in configuration, open the switcher, select each in
turn and confirm the application re-renders, then reload and navigate to a second page and confirm the
selection survived both.

**Acceptance Scenarios**:

1. **Given** a project that has declared a set of themes, **When** a visitor opens the theme switcher,
   **Then** the switcher offers exactly the declared set and no others.
2. **Given** a visitor who selects a theme from the switcher, **When** they reload the page, **Then** the
   selected theme is still applied.
3. **Given** a visitor who selected a theme, **When** they navigate to a different page of the
   application, **Then** the selected theme is still applied.
4. **Given** a project that has declared no set, **When** a visitor opens the switcher, **Then** it
   behaves exactly as it did before this feature.
5. **Given** a visitor whose previously selected theme is no longer among those the project offers,
   **When** they load a page, **Then** the project's configured theme is applied rather than a broken or
   unstyled page.

---

### User Story 3 - Write and apply a theme of your own (Priority: P3)

A developer wants their application to carry their organisation's colours rather than any prebuilt theme.
They follow the documentation, which tells them what a theme is, which variables one defines and what each
controls, writes a single CSS file, loads it, and names it in configuration. Their colours apply
throughout, and they never opened a packaged template or installed a build tool.

**Why this priority**: This is the branding half of G8 and the part Sam identified as the weakest today:
the mechanics are not obvious and currently have to be reconstructed from upstream sources. It ranks
third because it is unblocked by the first two stories and because a project can reach a good result with
a prebuilt theme in the meantime.

**Independent Test**: Starting from the documentation and an empty CSS file, produce a working custom
theme in a project, with no packaged template edited and no build tool installed, and confirm the
application renders in the new colours.

**Acceptance Scenarios**:

1. **Given** the documentation, **When** a developer reads the custom theme section, **Then** every
   variable a theme may define is listed with a description of what it controls.
2. **Given** the documentation, **When** a developer reads it, **Then** it states the relationship
   between a hand-written theme file and the design system's theme plugin syntax, including that the
   plugin emits the same variables rather than deriving or computing any of them.
3. **Given** a project that has written its own theme file and loaded it, **When** a page is loaded,
   **Then** the project's theme applies and overrides any packaged theme, whatever order the stylesheets
   are loaded in.
4. **Given** a project's own theme, **When** it is applied, **Then** it needs no front-end build tooling.
5. **Given** the documentation's worked example, **When** it is followed from an empty file, **Then** it
   produces a rendering application without any step the documentation left out.
6. **Given** a project's own theme, **When** it is named in the switcher's declared set, **Then** the
   switcher offers it alongside prebuilt themes.

---

### Edge Cases

- A project names a theme that neither ships with the package nor is provided by the project itself. No
  block matches, the default theme stays applied, and the page renders normally. The package does not
  validate theme names, because a project's own theme is defined in a file the package never reads, so
  any check would either reject valid custom themes or demand a registration list.
- A project's declared switcher set contains a name that is not available. Same treatment: the entry is
  offered, selecting it changes nothing visible.
- A visitor's stored selection names a theme the project has since stopped offering, covered by US-2
  scenario 5.
- A project already overrides the base template to set the theme by hand. That override must keep
  working, since it is the documented route today.
- A project sets a theme and also loads its own theme file using the same name, intending to replace a
  prebuilt theme's colours. The project's file wins, per US-3 scenario 3.
- A visitor has JavaScript disabled. The configured theme must still apply; only the switching is lost.

## Requirements *(mandatory)*

### Functional Requirements

**Shipping and applying a theme**

- **FR-001**: The package MUST include the theme definitions for every prebuilt theme the design system
  publishes, served from the package's own static files.
- **FR-002**: No page MUST request a theme definition from a host outside the project at page load.
  *(Narrowed 2026-08-13 during planning, from "a theme definition or stylesheet". The wider wording
  was violated on arrival by the icon font the base template already loads from a third party, which
  the approved scope excludes and which is recorded in `decisions.md` as its own change. Narrowing
  restores the requirement to what the gate approved rather than widening the feature.)*
- **FR-003**: A project MUST be able to set the theme that applies through the package's configuration
  dictionary, without overriding any packaged template.
- **FR-004**: Applying a prebuilt theme MUST NOT require any front-end build tooling.
- **FR-005**: The configured theme MUST be applied before the page is first painted.
- **FR-006**: When a project sets no theme, the applied theme and the switcher's behaviour MUST be
  unchanged from the release preceding this feature.

**Choosing a theme at runtime**

- **FR-007**: A project MUST be able to declare which themes the packaged theme switcher offers.
- **FR-008**: The switcher MUST offer exactly the declared set.
- **FR-009**: A visitor's selection MUST persist across page loads and across pages within the
  application.
- **FR-010**: When a visitor's stored selection is not among the themes the project offers, the project's
  configured theme MUST be applied instead.

**A project's own theme**

- **FR-011**: A project MUST be able to apply a theme it wrote itself, loaded from its own static files,
  without overriding a packaged template and without any build tooling.
- **FR-012**: A project's own theme MUST take effect over a packaged theme of the same name regardless of
  the order in which the stylesheets are loaded.
- **FR-013**: A project's own theme MUST be selectable through the same configuration as a prebuilt one,
  both as the applied theme and as a member of the switcher's set.

**Unresolvable names**

- **FR-014**: A theme name that matches nothing MUST leave the default theme applied and the page
  rendering normally. The package MUST NOT validate theme names.

**Documentation**

- **FR-015**: The documentation MUST list every variable a theme may define and state what each one
  controls.
- **FR-016**: The documentation MUST explain that a theme is a block of CSS custom properties applied at
  runtime, requiring no build step, and that the design system's theme plugin syntax emits exactly those
  properties rather than deriving any of them.
- **FR-017**: The documentation MUST explain why a project's own theme overrides a packaged one
  independently of load order.
- **FR-018**: The documentation MUST carry a worked example that takes a reader from an empty file to a
  rendering custom theme, with no step omitted.
- **FR-019**: The documentation MUST no longer instruct readers to load theme CSS from a third-party host.
- **FR-020**: The documentation MUST state that a theme name which matches nothing falls through to the
  default theme without an error, so a reader whose theme does not appear knows where to look.
- **FR-021**: `CONTEXT.md` MUST define *theme* as a domain term, since the vocabulary is currently absent
  from the glossary.

### Requirement to story mapping

| Story | Requirements |
|---|---|
| US-1 — Apply a prebuilt theme by configuration | FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-014, FR-019, FR-020 |
| US-2 — Let visitors choose from the themes a project offers | FR-007, FR-008, FR-009, FR-010 |
| US-3 — Write and apply a theme of your own | FR-011, FR-012, FR-013, FR-015, FR-016, FR-017, FR-018, FR-021 |

### Key Entities

- **Theme**: A named set of colour, corner radius, border width and depth values that the packaged
  components read at render time. Applied to the whole document at once. A theme carries no structure or
  layout, which is why changing one never requires a template change. Themes come from two places: those
  shipped with the package, and those a project writes for itself.
- **Offered set**: The themes a project chooses to present to its visitors through the switcher. A subset
  of what is available, declared by the project, and independent of which theme applies by default.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A project changes one configuration value, reloads, and the application renders in a
  different prebuilt theme, on a machine with no front-end build tooling installed.
- **SC-002**: Loading any page of the demo application issues zero requests to hosts outside the project
  for a theme definition.
- **SC-003**: The compressed stylesheet payload a project downloads grows by no more than 8 KB against
  the release preceding this feature.
- **SC-004**: A visitor selects a theme, reloads, and navigates to a second page, and the selected theme
  is applied on both.
- **SC-005**: A developer following the custom theme documentation reaches a rendering custom theme from
  an empty file without editing a packaged template, installing build tooling, or consulting a source
  outside the documentation.
- **SC-006**: A project that upgrades and changes no configuration sees the same theme and the same
  switcher behaviour as before.
- **SC-007**: Every variable a theme may define appears in the documentation with a description, checked
  against the shipped theme definitions rather than by hand.
- **SC-008**: Naming a theme that matches nothing leaves the application rendering in its default theme,
  with no error raised and no unstyled page.

## Assumptions

- The applied theme is chosen per browser, not per user account. Selection persists in browser storage,
  which is how the switcher already works. Tying a theme to a signed-in user's profile is a separate
  feature and stays out of scope.
- The operating system's light or dark preference is not consulted. The package does not honour it today,
  and changing that would alter behaviour for every existing project. It stays out of scope here.
- The package's own default theme, and whether it meets contrast requirements, is settled by R18's
  predecessor R11 (issue #136) rather than here. This feature must not change which theme applies when a
  project configures nothing, so the two do not collide.
- Which prebuilt themes exist is the design system's decision, not the package's. The package ships what
  the pinned version publishes and does not curate the list.
- A project loading its own theme file is doing so through the existing mechanism for adding a stylesheet
  to the page. This feature does not introduce a new asset pipeline.
- Guidance on where theming stops and component overrides take over, named in R18's deliverables, is
  documentation this feature writes. It does not imply any new override mechanism.

## Clarifications

### Session 2026-08-13

- **Q: When a project configures no theme, should the shipped themes change what applies?**
  A: No. The applied theme with no configuration is unchanged from the preceding release (FR-006,
  SC-006). Existing projects must see no visual change on upgrade. Which theme *should* be the default,
  and whether it meets the contrast bar, is R11's question and is deliberately not reopened here.

- **Q: Does the switcher offer all shipped themes by default, or stay at light and dark?**
  A: Light and dark, unchanged, until a project declares a set (FR-006, FR-008). Presenting thirty-five
  themes to the visitors of every upgrading project would be a visible behaviour change nobody asked for,
  and the offered set is a product decision that belongs to the project, not the package.

- **Q: What happens when a configured theme name is not available?**
  A: Nothing. The name is applied, no theme block matches it, and the default theme stays in effect
  (FR-014, FR-020, SC-008). *Revised 2026-08-13 on the maintainer's ruling at the Spec gate; the original
  answer required a start-up error.* The check cannot be built honestly: a project's own theme is a
  block of custom properties in a CSS file the package never reads, so the package has no way to know
  whether a name will resolve. Validating against the shipped set alone would reject every custom theme,
  and the alternative is a registration list, which is configuration a project has to keep in step with
  its own stylesheet for no benefit. Silent fall-through is also benign rather than broken: the default
  theme is bound to `:where(:root)` at zero specificity, so an unmatched name renders the default rather
  than an unstyled page. The documentation carries the behaviour instead, so a developer whose theme does
  not appear knows where to look.

- **Q: Is a project's own theme required to work without a build step, or may it require one?**
  A: Without one (FR-011). A theme is a block of custom properties that the browser reads at runtime, and
  the design system's plugin syntax is a pass-through that emits the same properties rather than computing
  anything. There is no build-time step to require, so requiring one would be an artificial restriction
  and would make G8 conditional on G6 being given up.

- **Q: Does a project's own theme need to load after the packaged stylesheet to take effect?**
  A: No, and the documentation must say why (FR-012, FR-017). The packaged theme definitions sit inside a
  cascade layer while a project's plain theme file does not, and unlayered rules beat layered ones
  regardless of source order. A reader who does not know this will reasonably assume load order matters
  and will write fragile ordering into their templates.

- **Q: How much larger may the download get?**
  A: No more than 8 KB compressed (SC-003). The measured cost of every prebuilt theme is about 5 KB
  compressed, because themes are variable declarations and add no component or utility rules. The bound
  exists so that a later change which does add rules is caught rather than absorbed.
