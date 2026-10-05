# Decisions: Install daisy-cotton alongside the package, with no visible change

Rationale too long to inline in `spec.md`, and the ambiguities resolved while specifying. D1 to D5
are the maintainer's rulings for the whole of roadmap item R29, recorded as given. D6 onward were
resolved while writing this specification, with no question put to the maintainer, and are open to
his veto.

## Rulings given by the maintainer

### D1. Every call this package makes to a daisy-cotton component is isolated

**Given:** many of daisy-cotton's components declare attributes with everyday names (`text`,
`class`, `icon`, `items`, `variant`). A component called without one of them picks up a page
variable of the same name. This is handled where the component is called, with Cotton's `only`
attribute, on every call this package makes. It is not raised upstream as a defect.

**What this feature owes:** the proof that isolation keeps page variables out and that content
placed inside the component still sees them (FR-015), and the written rule (FR-018).

### D2. Render-time classes in daisy-cotton do not hold this work up

**Given:** [daisy-cotton#119](https://github.com/django-mvp/daisy-cotton/issues/119) reports that
classes daisy-cotton builds while rendering never reach a stylesheet built from a scan. The
prebuilt stylesheet already includes all of daisyUI's components and utilities, so daisyUI's own
classes are present whatever daisy-cotton builds. What needs adding is the plain Tailwind
utilities daisy-cotton's templates write out, and the breakpoint-prefixed forms, which no scan of
daisyUI produces. The issue stays open upstream and this feature does not wait for it.

### D3. One breaking release for the whole of R29, and no release from this feature

**Given:** the eight features under R29 accumulate on the main branch and ship together as one
breaking minor release. Renamed tags and attributes get no compatibility aliases. This feature
records its change under the changelog's unreleased heading and cuts nothing (FR-019).

### D4. The icon stays at `<c-icon>`

**Given:** every other component this package keeps moves under an `mvp.` prefix in #434. The
icon does not, so that it replaces daisy-cotton's plain icon everywhere, including inside
daisy-cotton's own components. daisy-cotton's ADR 0001 describes exactly this arrangement. It is
why `mvp` has to stay above `daisy_cotton` even after the prefix lands, and so why the order check
in this feature is permanent.

### D5. The version range is `>=0.1.2,<0.2`

**Given:** daisy-cotton is pre-1.0 and says its names, attributes and emitted classes can change
between minor versions. 0.1.2 is the first version with everything R29 needs. The upper bound
keeps a new minor from arriving unannounced (FR-001).

## Resolved while specifying

### D6. "Install it for every project" means a dependency, a documented app entry and a check

**Ambiguous:** the issue says the package should "install it for every project". A Python package
can make another one arrive on `pip install`, but it cannot add an app to a project's
`INSTALLED_APPS`.

**Chosen:** daisy-cotton is a runtime dependency; the project adds `daisy_cotton` to
`INSTALLED_APPS`; the getting-started guide lists it; a start-up check reports when it is missing
(FR-001, FR-002, FR-012).

**Rejected:** having this package's app configuration add `daisy_cotton` to the app list itself.
No other dependency of this package is handled that way, the position in the list matters and
would be hidden from the project, and changing a project's settings from inside an app is
something a Django developer does not expect.

**Why defensible:** it is how `django_cotton`, `crispy_forms` and `mvp_forms` already work here,
and 0.26.0 shipped the same kind of upgrade step for `mvp_forms`.

### D7. A missing app is an error; the wrong order is a warning

**Ambiguous:** the investigation behind R29 said the package should warn when `mvp` is below
`daisy_cotton`. It said nothing about `daisy_cotton` being absent, or about how severe either
message is.

**Chosen:** absent is an error (FR-012), wrong order is a warning (FR-013), and both can be
silenced by identifier (FR-014).

**Why defensible:** by the release that carries R29, the shell's own pages call daisy-cotton's
components, so a project without the app cannot render a page. An error at start-up names the
cause; the alternative is a missing-template error on the first request, which names a template
the developer has never heard of. The wrong order still renders pages, and a project might have
reasons of its own for it, so it is a warning.

**Open to veto:** an error stops `runserver` and `migrate` for a project that has upgraded and
not yet added the line. That is the intended effect in a breaking release with an upgrade note,
but it is the strictest reading. Downgrading it to a warning is a one-word change.

### D8. Same-named components resolve to this package's, and that is the whole of "no visible change"

**Ambiguous:** both packages ship `button`, `alert`, `badge`, `card`, `modal`, `avatar`,
`dropdown`, `menu`, `breadcrumbs`, `divider`, `link`, `dock`, `icon` and the mockups under the
same names. The issue says nothing on any page changes, without saying how.

**Chosen:** `daisy_cotton` is listed below `mvp`. Cotton takes the first app that has the
component, so every existing call keeps resolving to this package's template (FR-003, FR-004).
No component template changes in this feature.

**Consequence accepted:** daisy-cotton's own components call `<c-button>`, `<c-menu.item>` and
`<c-icon>` inside themselves. While this package's copies exist, those inner calls get this
package's button and menu item, which take different attributes. So some daisy-cotton components
do not render correctly between this feature and #435. Nothing calls them in that window, and no
release happens inside it (D3). The specification promises only what holds: daisy-cotton is
installed, its templates are found, and its classes are styled (FR-005). The documentation does
not advertise daisy-cotton's components as ready (FR-017).

**Rejected:** moving this package's same-named components out of the way in this feature. That is
#434 and #435, and doing it here would make this feature a visible change.

### D9. What "every class" covers

**Ambiguous:** "every class daisy-cotton's components can render" has no edge in the issue. A
component's `class` attribute accepts anything, and some attributes take a number.

**Chosen:** every class written out in daisy-cotton's templates, plus every class built at render
time from an attribute with a fixed set of choices, including each breakpoint (FR-006). Outside:
classes the caller supplies, icon classes, and values of open-ended attributes beyond the choices
daisy-cotton documents.

**Why defensible:** this is the set a test can work out from the installed package and check, and
it is the set a developer means when they say a component "arrives styled".

### D10. The generated entry file gets the same coverage as the prebuilt stylesheet

**Ambiguous:** D2 covers the prebuilt stylesheet, which already carries all of daisyUI. The entry
file a project generates does not: it scans templates and a short list of named classes. A scan of
daisy-cotton's templates alone would miss every class built at render time (`btn-primary`, each
size, each placement), which is the fault daisy-cotton#119 describes.

**Chosen:** a stylesheet built from the generated entry file styles the same set as the prebuilt
one (FR-009). How it gets there is for planning.

**Why defensible:** the issue names "the build entry point a project generates" alongside the
prebuilt stylesheet and applies "every class" to both. Covering only literal classes would leave a
project that builds its own stylesheet with unstyled variants on the shell's own pages once
components move.

**How it is reached:** the classes built at render time are listed in this package's own preset,
which the generated entry file already imports. That is how the package covers the render-time
classes of its own components today. The coverage test (D11) keeps the list true against the
installed daisy-cotton. Nothing here waits on daisy-cotton#119.

### D11. The coverage test reads the installed daisy-cotton

**Ambiguous:** coverage could be checked once by hand, or kept true by a test.

**Chosen:** the tests derive the class set from whichever daisy-cotton is installed and fail by
naming the missing class (FR-010).

**Why defensible:** daisy-cotton says its emitted classes can change between minor versions. A
list copied into this repository goes stale on the first upgrade, and the upgrade is exactly when
the check is needed. The existing safelist test in this package already works this way for the
package's own components.

### D12. The stylesheet is rebuilt and committed in this pull request

**Ambiguous:** the contributor notes say the stylesheet is rebuilt at release time and
contributors need not compile it in a pull request. Article XV says both shipped artifacts are
rebuilt and committed on the branch that changes their inputs.

**Chosen:** rebuilt and committed here (FR-007).

**Why defensible:** this feature changes the stylesheet's inputs, so Article XV applies, and the
issue asks for coverage to be proved before any component moves. A test against a stylesheet that
has not been rebuilt proves nothing. Earlier features that added classes did the same.

### D13. No workflow is changed

**Ambiguous:** the `Stylesheet` workflow installs Node and no Python, so anything the stylesheet
build reads from the Python environment is absent there.

**Chosen:** the workflow is left alone. It keeps proving the stylesheet compiles. Coverage is
proved by the test suite against the committed stylesheet, where daisy-cotton is installed.

**Risk carried into planning:** if the build fails outright, and does not merely skip, when
daisy-cotton's location is absent, the workflow would go red on every pull request that touches
the package. Planning has to choose a way of reaching daisy-cotton's templates that compiles
without them. If no such way exists, this is raised as its own issue before anything under
`.github/` is touched.

### D14. The paths-only output grows by one line, at the end

**Ambiguous:** the generator's paths-only output prints three paths, one per line, and a project
may read them by position.

**Chosen:** daisy-cotton's location is added and the three existing paths keep their positions
(FR-016).

**Why defensible:** it is the same change 0.26.0 made when it added the form pack's path, and it
breaks no script that reads the first three lines.

### D15. Cotton stays pinned unless daisy-cotton cannot render under it

**Ambiguous:** this package pins Cotton at 2.6.1. daisy-cotton declares 2.6 or later and is
developed against 2.7.

**Chosen:** the pin stays if daisy-cotton's components render under it. If they do not, it moves
to a version under which both render, provided no page changes (FR-011).

**Why defensible:** moving a pinned dependency is a change with its own risk to rendered markup,
and this feature's promise is that nothing visible changes. It is done only when needed.

### D16. No sketch

**Chosen:** this feature goes to planning without a design prototype.

**Why defensible:** it changes no page. There is nothing for an eye to judge that a test cannot
assert.

### D17. No new glossary terms

**Chosen:** `CONTEXT.md` is not changed by this feature.

**Why defensible:** the feature introduces a dependency and a rule for contributors. Neither is a
concept a project works with. The glossary's component list and naming rules change in #434 and #435, when
the components themselves do.

## D18. The stylesheet is built with daisyUI 5.7.0

**Decision:** the build tool moves from `daisyui` 5.6.18 to 5.7.0.

**Why:** daisy-cotton's menu writes `menu-paged`, and daisyUI has no such class before 5.7.0. FR-006
needs every class daisy-cotton can render to be styled. 5.7.0 is the smallest version that has
them all. Measured against the same inputs, it adds one class selector to the stylesheet and
removes none. A later 5.7 release would be a larger change for no requirement.

**Revisit if:** a rule that 5.7.0 changed shows on a page. The answer is then a later patch
release of daisyUI, not a return to 5.6.

**ADR:** none — a build tool's version, recorded in the changelog and in `package.json`.

## D19. The package's own build finds daisy-cotton through the build task

**Decision:** `invoke build-stylesheet` composes the entry it gives Tailwind: `assets/tailwind.css`
plus one `@source` line with daisy-cotton's templates directory, resolved from the imported
module. `assets/tailwind.css` itself does not point into the Python environment.

**Why:** the path contains the Python version, and Tailwind does not follow a glob or a symlink
into a git-ignored directory (research R3). The `Stylesheet` workflow runs the `npm` script, which
is unchanged, so it compiles as before and nothing under `.github/` needs editing (D13).

**Rejected:** listing one exact path per supported Python version in `assets/tailwind.css`. It
works today and goes quiet on the first Python release nobody added a line for. Copying
daisy-cotton's literal utilities into the preset was rejected for the same reason: a hand-kept
copy of something the scan can read.

**Revisit if:** Tailwind gains a way to name a source outside the project that does not depend on
the Python version.

**ADR:** none — how one build task is wired, local to `tasks.py`.

## D20. The classes are read from daisy-cotton's templates, not from rendering them

**Decision:** the coverage tests work the class set out by reading the installed templates:
literal classes, `variation` calls, `responsive` calls, and one table for a class built from a
template variable. An unknown construction fails the test by name.

**Why:** daisy-cotton builds every render-time class through two tags with their choices written
in the call, so reading is exact and needs no list of attribute values for 82 components.
Rendering every component with every combination of attributes would need that list, and the list
would be the thing that goes stale.

**Revisit if:** daisy-cotton starts building classes some other way. The test says so when it
meets one.

**ADR:** none — a test's method, local to this feature's tests.

## D21. "Nothing is lost" is proved against two fixtures

**Decision:** the classes the 0.26.0 stylesheet styled, and the classes the 0.26.0 preset
declared, are committed as two text fixtures. Tests assert both are still covered.

**Why:** SC-005 and SC-009 ask for a test, and a test cannot read a stylesheet that is no longer
in the tree. The cost is that a later feature which removes a class on purpose deletes a line.
That is the point: the class cannot leave by accident.

**Revisit if:** the fixtures are edited more often than they catch anything.

**ADR:** none — test fixtures, local to this feature's tests.

## D22. The check lives in `mvp/checks.py` and is not tagged

**Decision:** a new module holds the check and its ordering rule. The identifiers are `mvp.E002`
(missing) and `mvp.W001` (above `mvp`). It is registered with no tag.

**Why:** `mvp/mounted.py` holds the one existing check because that check is about mounted apps.
This one is about the app list. `mvp.E001` is taken, and no warning identifier was in use. Django
has no tag for the app list, and an untagged check runs with every `check`, `runserver` and
`migrate`, which is what FR-012 asks for.

**ADR:** none — where one function lives.

## D23. Cotton stays pinned at 2.6.1

**Decision:** the pin does not move (D15).

**Why:** all 60 components only daisy-cotton ships render under 2.6.1, and `only` behaves as the
rule needs (research R5, R6). A test keeps both true.

**ADR:** none — a pin left alone.

## D24. The foundation is the first task of the first story

**Decision:** adding the dependency and the app-list line is T001 of US-1, not a phase of its own.

**Why:** it is one command and two lines, and US-1's tests are what prove it.

**ADR:** none — task ordering.
