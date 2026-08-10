# Roadmap — django-mvp

**Date:** 2026-08-03

This document was designed against [GOALS.md](../GOALS.md). See also [CONTEXT.md](../CONTEXT.md) for domain terminology and [memory/constitution.md](../memory/constitution.md) for project standards.

The package is at 0.15.0, so the early items below are already delivered and are carried here to keep the build sequence whole.

## Versioning

| Version | What it means |
|---|---|
| `0.x` | Building toward the Essential goals. Import paths and component APIs may still change between minors. |
| **`1.0.0`** | **All Essential goals delivered.** The first release safe to depend on: the public surface is recorded and a deprecation policy is in force. |
| `1.x` | Advancing the Expected goals, at whatever granularity the work takes. Additive features and fixes only. |
| **`2.0.0`** | The next major. Breaking changes wait for it. |

Aspirational goals may be developed against v2 or v1 as required.

Two rules govern the mapping. A goal is not one minor: some goals take several minors to reach, and one minor can move two goals at once. Once 1.0 ships, a breaking change never goes out as a 1.x release, it waits for the next major.

## Essential goals: v1.0.0

Everything needed to reach a release that is safe to depend on.

### R1 — A configurable application shell

*Delivered · needs verification · advances G1, G5*

Sidebar, navbar, content area, footer and mobile dock render around every page, with the collapse behaviour, breakpoint and navbar widgets chosen from project settings rather than assembled by hand.

Serves G1 and G5.

### R2 — A component library on a modern design system

*Delivered · needs verification · advances G2, G5*

A library of reusable page and content components with small attribute APIs, built on DaisyUI 5 and Tailwind CSS v4 after the move off the earlier Bootstrap-era look.

Serves G2 and G5.

### R3 — Navigation declared in Python

*Delivered · needs verification · advances G1, G3*

Sidebar and mobile-dock navigation is declared in Python, with active states, icons and badges resolved for the developer instead of hand-written per template.

Serves G1 and G3.

### R4 — List, create, update and delete pages from a model

*Delivered · needs verification · advances G3*

A model reaches a working set of pages through view configuration: list pages with search, whitelisted ordering and pagination, form pages for create and update, and a delete flow that shows what else would be removed and can require typed confirmation.

Serves G3.

### R5 — Styled error pages

*Delivered · needs verification · advances G1, G5*

The 400, 403, 404 and 500 responses render inside the application shell instead of falling back to Django's unstyled defaults.

Serves G1 and G5.

### R6 — Installation without front-end build tooling

*Delivered · needs verification · advances G6*

A prebuilt stylesheet ships inside the package, so a project installs and runs with no Node toolchain. Projects that add their own utility classes can generate a build entry point that scans both their templates and the package's.

Serves G6.

### R7 — The object detail page

*Delivered · advances G3, G2*

The detail page is the one stop on the model-to-pages path that does not arrive: the view class exists and resolves its object, but the page it renders is a placeholder. A project that configures a list, a create form and a delete flow gets nothing for the read view, not even the header the other pages have.

What the page owes a project is narrower than it first appears. The body of a detail page is layout, and layout is where an application's design lives, so it is written per project rather than generated. The part that does repeat is the header: the view has already worked out which of the edit and delete pages this user may reach, and every project turns those URLs into the same row of buttons by hand.

**Deliverables:**

- Links onward to the edit and delete flows, shown according to the permissions the view already resolves, in a consistent position and style.
- A packaged page that stands on its own without a placeholder, carrying the object's title and leaving its body to the project.
- A documented override point for a project that wants a different set of actions.

Serves G3, and G2 for the components the page needs. A field-rendering API on the view is explicitly out of scope and is recorded as such in `docs/adr/0001-detail-views-do-not-take-a-field-list.md`.

### R8 — Formsets that render and work — **delivered**

*feature · advances G4*

~~G4 is the only Essential goal with nothing behind it, and formsets are the example the package's own scope statement uses: Django ships the backend machinery and leaves you with nothing to render or drive it with. Nothing in the package refers to formsets today. Until this lands, the claim that the package fills in where Django stops has no instance to point at.~~

Delivered. `<c-form.formset>` and `<c-form.formset.row>` render any Django formset with the packaged look, `MVPInlineCreateView` and `MVPInlineUpdateView` put a parent record and its related rows on one page, and [Formsets](formsets.md) walks the path from two models to a rendered page. G4 now has an instance to point at.

**Deliverables:**

- A form page that renders a formset with the same look and error handling as a single form.
- Support for a parent object edited alongside its related rows, which is the common case this gap blocks.
- Adding and removing rows in the browser without a page reload and without a build step.
- Validation errors surfaced per row and at the formset level, not collapsed into one message.
- Documentation showing the whole path from a model to a working page.

Serves G4. Formsets rendered outside the packaged form components stay out of scope.

### R9 — Components honour the attributes passed to them

*feature · advances G7, G2*

Four open reports are one defect: a component hardcodes an attribute and also spreads the attributes it was given, so the browser silently drops the duplicate and the passed value disappears. A class passed to a text or breadcrumb component does nothing, and a boolean that was never given a default quietly picks up an unrelated value from the surrounding page. Three of the four reports independently ask for the rest of the library to be checked for the same shape. This blocks G7 at its second step: when the packaged look is not right, passing your own classes is supposed to be the next move, and today it fails without an error.

**Deliverables:**

- The defect fixed wherever it occurs, found by a sweep of the library rather than report by report.
- Every component declaring the attributes it consumes, so nothing is emitted twice.
- Boolean attributes given explicit defaults, so no component inherits a value from the page around it.
- A check that fails when a component reintroduces either shape.

Serves G7 and G2. Widening any component's attribute API beyond what it already claims stays out of scope.

### R10 — Classes built at render time reach the stylesheet

*feature · advances G6, G5*

Components that assemble a class name from an attribute at render time produce classes the stylesheet build never sees, so the markup is correct and the styling is absent. One reported case has four of five responsive variants missing, with the fifth working only because that exact string happens to appear in an unrelated docstring. An earlier instance of the same fault was fixed in isolation and this one appeared anyway. It is silent by construction: nothing fails, the page just renders wrong, which makes it the sharpest threat to the no-build-tooling promise.

**Deliverables:**

- Every class the library can build at render time made reachable by the stylesheet build.
- A check that fails when a component can produce a class the build would not generate.
- The check proven against the reported case before it becomes a gate.

Serves G6 and G5. Classes a consuming project builds in its own templates stay out of scope, since those are covered by the generated build entry point.

### R11 — A shipped theme that meets contrast requirements

*feature · advances G5*

The package ships no theme of its own, so a stock theme applies, and on it the error colour fails WCAG AA against the page background. That lands on form validation: both the message text and the input border a user is meant to notice are the pairings that fail. A survey of the stock themes found no replacement that fixes it, so the fix is a theme the package owns. G5 promises a polished look out of the box, and an inaccessible error state is not one.

**Deliverables:**

- A theme shipped and applied by default, meeting WCAG AA contrast for text and for the interface colours the components rely on.
- Light and dark variants, both meeting the same bar.
- A check that fails when a colour pairing the components use drops below the bar.
- A project's own theme still overriding the shipped one without touching templates.

Serves G5. The wider theming and branding story is R18.

### R12 — Optional dependencies behave the way they are documented

*feature · advances G3, G7, G10*

The package is deliberate about optional dependencies, and ~~three~~ **two** places do not follow it. ~~Form and list pages load a third-party template library unconditionally, so a project that installs the package as documented and renders a form gets a template error rather than the promised working page.~~

**Settled by this feature, 2026-08-05**: django-crispy-forms and crispy-tailwind are now declared runtime dependencies rather than an implicit requirement of the packaged form rendering. The list page loads the same distribution as the form page, so declaring it settles both at once — a project that installs the package as documented no longer hits this on either one.

One view module imports an optional package at module level with none of the guarding the others have, so the failure is a bare import error instead of a message saying what to install. And a documented setting for choosing how forms render does not exist in the code at all. Each one turns a configuration question into a crash.

**Deliverables:**

- Every optional dependency either declared, or guarded so its absence produces a message naming the package to install.
- ~~Form and list pages rendering without any undeclared dependency, at a reduced but working level of polish.~~

  **Settled by this feature, 2026-08-05**: both pages load django-crispy-forms and crispy-tailwind as declared dependencies now, not conditionally, so there is no undeclared dependency left to guard against and no reduced-polish fallback left to build toward — installing the two apps gets the full packaged look on both pages.
- The documented form-rendering choice either built or removed from the documentation, whichever is right.
- A check covering every optional dependency, not the two it covers today.

Serves G3, G7 and G10.

### R13 — The component library covers what a data-centric application needs

*multi-feature · advances G2*

Thirty of the design system's sixty-one components have a wrapper here. The absent ones include most of the pieces a data-centric page is built from:

- statistic tiles, list rows and timelines, for presenting records
- tabs and step indicators, for splitting a page or a process
- progress, loading and skeleton states, for anything that takes time
- keyboard keys and inline links, the latter separately requested

Three more are used inside other components but have no reusable wrapper of their own, so a developer cannot reach them. Comparable libraries in this space ship seventy or more components and treat this set as the baseline. G2 asks for coverage of what a data-centric web application needs, and the gap is concentrated exactly there.

**Deliverables:**

- Wrappers for the data-presentation components a dashboard or record page needs, chosen against G2 rather than against the design system's full list.
- Standalone wrappers for the pieces currently reachable only from inside another component.
- The form control set completed, so a form does not fall out of the library for a common input type.
- Each new component holding to the existing house style: a small attribute API, deliberately limited variation.
- A recorded decision on which of the design system's components stay out, so the gap is a choice rather than a backlog.

Serves G2. Presentation and marketing components stay out, including carousels, chat bubbles, animation effects and image galleries. They do not serve a data-centric application, and skipping them keeps the library small.

### R14 — Component attribute APIs are verified, not just rendered

*multi-feature · advances G2, G11*

Every component is covered by a test that renders it and checks it does not raise. That test says so itself: it is a floor, not a specification. Four components of seventy-eight have a test that verifies what their attributes actually do. The widest APIs in the library are among the unverified, including the button with eleven attributes, the avatar with ten, and the alert and grid with eight each. The 1.0.0 gate is a claim that the component library is delivered and its surface is safe to depend on, and that claim cannot rest on proof that the templates do not crash.

**Deliverables:**

- A verified attribute contract for each component: what each attribute changes in the rendered markup, and what the defaults are.
- The components with the widest attribute APIs covered first.
- The one component with no coverage at all brought up to the same bar as the rest.
- Component tests organised so a missing contract is visible rather than implied.

Serves G2 and G11. Browser-driven testing stays out. These are markup contracts.

### R15 — Accessible markup in the shipped components

*feature · advances G5, G2*

Nineteen of the seventy-eight component templates carry any accessibility attribute. The contributing guide asks for them and nothing checks, so the practice depends on whoever wrote the component. Interactive components are where this costs most. Dropdowns, modals, the sidebar toggle and the pagination controls all need their state and relationships expressed for assistive technology, not just for sighted users. Comparable libraries in this space lead with accessibility as a property of every component, so it is expected of the category rather than a finishing touch, and it belongs with G5's promise of a finished look.

**Deliverables:**

- Interactive components carrying the roles, states and relationships their behaviour requires.
- Navigation, pagination and dialog components announcing themselves and their current position.
- Icon-only controls carrying accessible names.
- A check that holds new components to the same bar, so the guide's instruction is enforced rather than requested.

Serves G5 and G2. A full audit against the accessibility guidelines across composed pages stays out. This covers the components the package ships.

## Expected goals: v1.x

What a complete, dependable version is expected to have.

### R16 — Integrations with the packages projects already use

*Delivered · needs verification · advances G10*

Views that put the packaged look around django-tables2, django-filter and htmx, kept in guarded modules so none of them becomes a required dependency.

Serves G10.

### R17 — Brand logo and icon configuration

*Delivered · needs verification · advances G8*

A project's logo, icon and avatar presentation are resolved from configuration and rendered by the shell, without overriding templates to change them.

Serves G8.

### R18 — Theming and branding without forking templates

*feature · advances G8*

Once a theme ships with the package (R11), the question becomes how a project departs from it. G8 asks for that to happen without copying templates: colour, typography and density adjusted through the design system's own theming surface, with the packaged components picking the changes up. This is the step between the default look and a project bringing its own CSS.

**Deliverables:**

- A documented set of theming values a project can override, with the effect of each one shown.
- Multiple themes selectable at runtime, including a user-facing switch, without template overrides.
- Guidance on how far theming reaches and where component overrides take over.

Serves G8.

### R19 — A recorded public surface and a deprecation policy

*feature · advances G11*

The changelog has version headings for 0.1.0 and for unreleased work, and for nothing in between, though twenty or more releases have shipped. Roughly two hundred lines of release notes sit under no heading at all, and several published releases read "no changes". Nothing in the package marks anything as deprecated, and only one module states what it exports. G11 asks for a surface that becomes safe to depend on across releases, and today a consumer cannot find out what changed in a release, let alone what is going away.

**Deliverables:**

- The changelog reconstructed so every shipped release has its entry.
- A stated boundary between the public surface and the internals, for both the Python API and the components.
- A deprecation policy: how a change is announced, how long it stays, and when it may be removed.
- The policy applied to anything already due to change.

Serves G11. This is the item that makes the 1.0.0 promise checkable.

### R20 — Documentation that matches the code

*feature · advances G9, G11*

The documentation describes several things the package does not do and omits several it does. A setting for choosing how forms render is documented and absent. The rule for where a form sends the user after submitting is documented with two steps the code does not have. Components appear in the reference that have no template behind them. In the other direction, the testing fixtures the package ships to every consumer are documented nowhere, ten of its fourteen template tags are undocumented, and one shipped tag cannot work outside this repository because the template it renders lives only in the demo. Documentation that is wrong in both directions is worse than thin documentation, because it is trusted.

**Deliverables:**

- Every documented capability either present in the code or removed from the documentation.
- The shipped testing fixtures and template tags documented, or withdrawn from the public surface if they are not meant to be part of it.
- The tag that cannot work outside this repository either fixed or removed.
- A check that catches a documented component with no template behind it.

Serves G9 and G11.

### R21 — A demo that shows every component in use

*feature · advances G9*

The demo application has a component gallery, and it covers thirteen of roughly seventy-eight components. G9 asks for a demo that shows every component in use, and the value of a gallery is that a developer can find what exists without reading the source. As R13 adds components, a gallery covering a sixth of them falls further behind.

**Deliverables:**

- A gallery page for every shipped component, with its attributes exercised rather than only its default rendering.
- The markup for each example visible next to it, so it can be copied.
- The gallery kept honest by a check that fails when a component has no page.

Serves G9.

### R22 — A documented way to add an integration

*feature · advances G10*

The package integrates with third-party packages by convention, and the convention is not written down. Both existing integrations follow the same shape, so the shape exists. What is missing is a statement of it that a contributor or a downstream project can follow. G10 asks for a consistent look around the packages projects already rely on, and that stays achievable only if adding the next one does not mean reverse-engineering the last one.

**Deliverables:**

- The integration contract written down: where an integration lives, how its dependency is guarded, and what it may and may not assume.
- The existing integrations checked against the stated contract.
- A check that holds new integrations to it.

Serves G10, and prepares G13.

### R23 — Retire the pre-rewrite backlog

*resolve · advances G11*

Thirteen of the twenty-six open issues describe work against markup the package no longer has: they name classes and toggles from the Bootstrap-era look that the design-system move replaced. One of them describes work the changelog says shipped. The stored feature records have two folders sharing a number, one with no number at all, and one still titled after the framework that was replaced. An issue tracker that mostly describes a package that no longer exists cannot be read as declared intent, which is what G11's predictability rests on.

**Deliverables:**

- Every open issue either restated against the current package or closed as superseded, with the reason recorded.
- The stored feature records given consistent identifiers and titles.
- The remaining backlog labelled, so what is accepted work is distinguishable from what is untriaged.

Serves G11.

## Aspirational goals: v2.0

Genuine wants whose absence never makes the package incomplete.

### R24 — A hosted component gallery

*feature · advances G12, G9*

The gallery from R21, published, so the components can be browsed and copied without installing anything. Comparable libraries in this space lead with exactly this, and it is how most developers decide whether a library covers what they need. The docs deploy is scaffolded and switched off, so the distance from R21 to here is short.

Serves G12, and G9 by giving the documentation somewhere to live.

### R25 — Integrations beyond the packages currently relied on

*multi-feature · advances G13*

Further third-party packages given the same consistent look, chosen as projects and adopters ask for them rather than in advance. R22 is the precondition: the contract has to be written before the set can grow without each addition becoming its own design question.

Serves G13.
