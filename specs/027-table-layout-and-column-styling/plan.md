# Implementation Plan: Full-screen tables and column styling helpers

**Branch**: `027-table-layout-and-column-styling` | **Date**: 2026-08-17 | **Spec**: [`spec.md`](./spec.md)

**Input**: Feature specification from `specs/027-table-layout-and-column-styling/spec.md`

## Summary

Turn the django-tables2 integration's page template into a filled page whose table owns its own
scrolling, ship a documented set of column behaviour classes applied through django-tables2's own
column attributes, and add one template tag that infers a column's alignment from the model field
behind it.

The technical approach is mostly subtraction. The shell's full-height mechanism shipped in #251 and
needs no extension. daisyUI's `table-pin-rows` already emits exactly the sticky heading and footer
rules FR-003 and FR-004 describe, so the sticky behaviour is two class names rather than bespoke
CSS. What has to be written is small: a scroll container with the right flex and overflow
properties, five or six behaviour classes, one config default, one template tag, and the markup
that wires them together.

The one genuinely new piece of machinery is the alignment tag, and its shape is forced by the
library: `BoundColumn._table` is private and Django's template engine will not resolve it, so
nothing can read a column's model field from a template without being handed the table as well.
A tag taking both is the only version of this that does not require the author to subclass
something.

## Technical Context

**Language/Version**: Python 3.12+, Django 5.2 and 6.0

**Primary Dependencies**: django-tables2 3.0.0 (optional, behind the existing `mvp.integrations`
guard — not promoted to a runtime dependency), django-cotton, Tailwind v4 + daisyUI (build-time)

**Storage**: N/A

**Testing**: pytest, pytest-django, rendered-template assertions; pytest-playwright for the geometry
that needs a browser

**Target Platform**: Server-rendered Django, modern browsers; verified at 1440x900 and 390x844

**Project Type**: Installable Django package with a demo application

**Performance Goals**: None stated. Rendering cost per row must not grow — the alignment tag runs
once per column, not once per cell.

**Constraints**: No new runtime dependency. No front-end build tooling required of a consumer. The
committed stylesheet is a build artifact and its build is not byte-reproducible.

**Scale/Scope**: Three stories, roughly a dozen files. Two templates rewritten, one component
rewritten, one template tag added, one config section added, one CSS block added, docs and demo
updated.

## Constitution Check

*Checked against `memory/constitution.md` v4.1.0 before Phase 0 and re-checked after Phase 1.*

| Article | Bearing on this feature | Verdict |
|---|---|---|
| I — Test-First | Every behaviour here is assertable before it exists: emitted classes, config resolution, inferred alignment, the ordering error, and the browser geometry. Tasks are ordered red-green throughout. | Pass |
| II — Simplicity | The sticky rows come from daisyUI utilities already in the stylesheet, and the height chain from the mechanism shipped in #251. Nothing new is built where something exists. | Pass |
| III — Anti-Abstraction | No base table class, no column subclass, no registry. One template tag and a set of classes. The rejected alternative — registering column classes so they win the dispatch — is recorded in `decisions.md` D6. | Pass |
| IV — Integration-First | The acceptance scenarios drive the work through the surfaces a consumer touches: a table view, a column's attributes, a project setting. | Pass |
| V — Security | No author-supplied value is interpolated into markup. This is the reason maximum width is a fixed class set, and the reason the component's existing `min_height` inline style is removed rather than reproduced (`decisions.md` D2). | Pass |
| VI — Documentation | `docs/components.md`, `docs/integrations.md` and `docs/styling.md` change in this pull request, along with the changelog. FR-016 makes the documented set and the shipped set checkable in both directions. | Pass |
| VII — Dependency discipline | django-tables2 stays a dev-group dependency behind its guard. Nothing is added. | Pass |
| VIII — Internationalization | The bars carry a result count and an accessible name for the scroll region. Both are translatable strings. | Pass |
| XI — Components are the public API | The component is named for its role and configured by attributes. The behaviour classes are the one tension: they are utility classes an author writes by hand. See Complexity Tracking. | Pass with a recorded justification |
| XII — Configuration-driven layout | The wrap default resolves column class, then `MVP_CONFIG`, then package default — FR-015 states the same order the article does. | Pass |
| XIII — Rendered markup is a contract | FR-025 puts the scroll region behind a tab stop with a region role and an accessible name. Every markup change gets a rendered assertion. | Pass |
| XIV — Browser tests are the exception | Only the geometry claims go to Playwright: window does not scroll, heading stays visible, at both viewports. Everything else is a template assertion. | Pass |
| XV — Shipped assets are build artifacts | New classes go in `mvp/tailwind/base.css`, the stylesheet is rebuilt with `invoke build-stylesheet` and committed on this branch. The daisyUI pinned-row utilities are added to the `@source inline(...)` safelist so a consumer generating their own stylesheet gets them. | Pass |
| XVI — Compatibility | Removing the component's `min_height` attribute and changing the default appearance of the table view are both recorded in the changelog as behaviour changes. | Pass |
| XVII — Cohesion | The alignment work is one tag plus a small helper it delegates to; if it grows past that it becomes a class in `mvp/tables.py`. Flagged as a watch item rather than pre-built. | Pass |

**Quality bar**: coverage floors project 90% / patch 85%; `ruff check`, `ruff format --check`, `mypy`
and `deptry` green; docs and changelog in the same pull request.

## Project Structure

### Documentation (this feature)

```text
specs/027-table-layout-and-column-styling/
├── spec.md
├── decisions.md
├── research.md          # Phase 0
├── plan.md              # this file
├── progress.md
└── tasks.md             # Phase 2
```

### Source Code (repository root)

```text
mvp/
├── config.py                                    # + the table section (wrap default)
├── tables.py                                    # NEW — column-kind resolution, if it outgrows the tag
├── templatetags/mvp.py                          # + the alignment tag
├── tailwind/base.css                            # + behaviour classes, + pinned-row safelist
├── static/css/django-mvp.css                    # rebuilt artifact (+ .br sibling)
├── integrations/django_tables/views.py          # ordering refused; default action set
└── templates/
    ├── table_view.html                          # rewritten: overrides the outer content block —
    │                                            #   filled page, bars, no card; page_view.html's
    │                                            #   container and toolbars are bypassed, and
    │                                            #   page_view/list_view/container.html are unchanged
    ├── cotton/addons/django_table.html          # rewritten: the scroll container itself
    └── django_tables2/bootstrap5-mvp.html       # + pinned rows, + alignment tag on th/td

demo/
├── tables.py                                    # columns demonstrating each behaviour class
├── views.py                                     # the full-screen table demo
└── templates/demo/                              # a page showing the classes side by side

docs/
├── components.md                                # component attrs, minus min_height
├── integrations.md                              # the table view's new shape
└── styling.md                                   # the column behaviour classes, with examples

tests/
├── test_config.py                               # the wrap default and its override
├── test_templatetags.py                         # the alignment tag, every column kind
├── test_integrations.py                         # the ordering refusal, the action set
├── test_components/test_render_all.py           # the component renders
├── test_table_layout.py                         # rendered-markup contract for the layout
└── test_table_layout_e2e.py                     # geometry, both viewports
```

**Structure Decision**: the package's existing layout, unchanged. Template tags stay in the single
`mvp` library per Article XVII's framework-dictated exception; a new `mvp/tables.py` appears only if
the kind-resolution logic outgrows one tag function, and the tag stays the thin wrapper over it.

## Phase plan

**Foundational (sequential, before any story).** The behaviour classes and the safelist entries land
first, because both US-1's markup and US-2's documentation reference them and neither can be
asserted until the stylesheet carries them. This is the only cross-story dependency.

**US-1 (P1) — the layout.** Component becomes the scroll container; page template becomes a filled
page with the two bars; the table template gains the pinned-row classes; the view refuses a declared
ordering and drops sort from its action set. Independently shippable: it delivers the whole
acceptance set on its own.

**US-2 (P2) — column behaviour.** The config section, the resolution order, and the documentation
that FR-016 makes checkable. Depends on the foundational classes existing, nothing else.

**US-3 (P3) — inferred alignment.** The tag, its wiring into the table template, and the demo.
Depends on US-1 only for where the markup lives. Droppable without touching the other two.

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
|---|---|---|
| Article XI — the column behaviour classes are utility classes an author writes by hand, and the article says a component's attributes are the only supported way to customise it | A django-tables2 column is not a Cotton component and has no attribute surface this package controls. The library's own mechanism for saying anything about a column is `attrs`, and the intake explicitly required using it rather than inventing a surface on top. The classes are named for behaviour (grow, shrink, wrap) rather than for their implementation, which is the part of the article that carries the intent. | A component wrapper around a column would mean the author declaring columns twice, once for django-tables2 and once for us. A table base class with a declarative API would mean importing and subclassing, which the intake ruled out. |
