# Implementation Plan: An Account Center in the shell that any app can add a page to

**Branch**: `028-move-account-center` | **Date**: 2026-09-14 | **Spec**: [`spec.md`](./spec.md)

**Input**: Feature specification from `specs/028-move-account-center/spec.md`

## Summary

Add an account area to the package: a menu declared beside the two the shell already declares, a
URLconf a project includes, a landing page that collects cards from installed apps, and a layout
that puts the menu beside the content. Nothing here is novel machinery. The menu is a
django-flex-menus `Menu` like `AppMenu` and `MobileFooterMenu`; the layout is a template extending
the project base and overriding one block; the landing page is a `MVPTemplateView` with an app
walk in `get_context_data`; the cards are two optional attributes on an app's `AppConfig`.

Three findings from reading the code shape the plan, and they are recorded in
[`research.md`](./research.md):

1. **The trail belongs in the header, not above the content.** django-accounts-center draws its
   own breadcrumb bar inside the page, because when it was written the shell had none. The shell
   draws one now, in the navbar, from `page.breadcrumbs` that `PageMixin` puts in the context. The
   area therefore supplies breadcrumbs rather than drawing a second bar in a second style.
2. **Menus are looked up by name on one global tree**, and the lookup returns the first match, so
   the collision with django-accounts-center is real and is handled by documentation rather than
   code (D1 in [`decisions.md`](./decisions.md)).
3. **The shell already reverses `account-center` and already names an `account_center` icon**, and
   neither exists in this package. Both are closed by US-1.

The work is roughly: two new Python modules, one new module-level addition to `mvp/menus.py`, four
templates, two icon keys, one documentation page, and the tests for all of it.

## Technical Context

**Language/Version**: Python 3.12+, Django 5.2 and 6.0

**Primary Dependencies**: django-flex-menus (already required), django-cotton, django-easy-icons,
Tailwind v4 and daisyUI at build time. No new runtime dependency, and no optional one.

**Storage**: N/A — the area has no models and stores nothing.

**Testing**: pytest, pytest-django, rendered-template assertions through the Django test client.
Nothing here needs a browser: the responsive behaviour is class-based and asserted in the markup,
per Article XIV.

**Target Platform**: Server-rendered Django, modern browsers.

**Project Type**: Installable Django package with a demo application.

**Performance Goals**: None stated. The app walk that collects cards runs once per landing-page
render and touches installed app configs only.

**Constraints**: No new dependency. The committed stylesheet is a build artifact whose build is not
byte-reproducible, so classes the new templates introduce require a rebuild on this branch. The
package's public surface is pre-1.0 and every addition here is additive.

**Scale/Scope**: Three stories. Roughly fifteen files, of which four are templates and five are
tests.

## Constitution Check

*Checked before Phase 0 and re-checked after the design below.*

| Article | Bearing on this feature | Verdict |
|---|---|---|
| I — Test-First | Every story is behaviour a rendered page either has or does not. Tests come first for each. | Pass |
| II — Simplicity | The area is a menu, a view, a layout and a walk over app configs. The generic version of the layout is explicitly deferred (D6). | Pass |
| III — Anti-Abstraction | No registry, no plugin API, no base class an app must inherit to contribute. An app appends to a menu and sets two attributes. | Pass |
| VI — Documentation | A page in `docs/` covering mounting, menu entries, pages and cards, with a worked example of each, plus the skill reference. | Planned, FR-021 |
| VIII — Internationalization | Every string the area renders is wrapped in `gettext_lazy` or `{% trans %}`. | Planned, FR-024 |
| X — Test structure | Tests mirror the source: `tests/test_views/test_account.py`, `tests/test_components/test_account_nav.py`, additions to `tests/test_menus.py`. | Planned |
| XI — Components are the public API | The navigation panel is a Cotton component, not an `{% include %}`. No raw utility class stands in for a component. | Planned, FR-017 |
| XII — Configuration-driven layout | No new `MVP_CONFIG` key. The area is opted into by mounting its URLconf (D3), and the layout reads the shell's existing breakpoint config rather than declaring one. | Pass |
| XIII — Rendered markup is a contract | The panel is a `nav` landmark with an accessible name; the collapsed control is keyboard-reachable because it is the packaged dropdown component. Rendered-markup assertions for each. | Planned |
| XIV — Browser tests are the exception | None added. | Pass |
| XV — Shipped assets are build artifacts | `invoke build-stylesheet` runs on this branch and the rebuilt CSS is committed with the templates that need it. | Planned, FR-022 |
| XVI — Compatibility | Additive; the changelog records the surface and the django-accounts-center version relationship. | Planned, FR-023 |
| XVIII — The skill is part of the product | `skills/django-mvp/` gains the area in its menus and layout references. | Planned, FR-025 |
| XIX — Views forward component attributes as a dict | The landing view renders no component that needs per-instance attributes, so no `<thing>_attrs` surface is added. | Not applicable |

No violations, so **Complexity Tracking is empty**.

## Design

### The menu — `mvp/menus.py`

`AccountCenterMenu = Menu("AccountCenterMenu", children=[MenuItem(name="overview", …)])`, declared
beside `AppMenu` and `MobileFooterMenu`, documented in the same module docstring, and carrying the
one entry the package can know: its own landing page, via `view_name="account-center"`.

The module also gains `get_active_section(request)`, which processes the menu for the request and
returns the entry the request is on, or the section the request sits below. Section membership is
declared by the entry itself as a tuple of URL-name prefixes in its `extra_context`, which is how
a page two levels down still names its section. This is the one piece of logic that has to move
rather than be re-derived, and django-accounts-center's version of it is the reference.

Everything else an app needs — appending, grouping, per-request checks, dropping an entry whose
URL will not resolve — is django-flex-menus behaviour the package already relies on, and the
stories assert it rather than implement it.

### The address — `mvp/urls.py`

A new module, the package's first, holding one route: the landing page at `""`, named
`account-center`, un-namespaced (D2). A project includes it wherever it wants the area to live.

### The views — `mvp/views/account.py`

- `AccountCenterView` — `LoginRequiredMixin` + `MVPTemplateView`. Its `get_context_data` walks
  `django.apps.apps.get_app_configs()` collecting `account_center_card_template` from each, calling
  `account_center_card_context(request)` where it exists and merging what it returns. The template
  names are handed to the page as a list.
- `AccountPageMixin` — supplies `page.breadcrumbs` for a page in the area: the area itself, then
  the active section resolved from the menu, the last crumb carrying no link. A page that is the
  area's own landing page gets the single crumb. Composed with `LoginRequiredMixin` by the
  contributing app, not by the mixin, because the area does not decide another app's access rules
  (FR-004).

`AccountCenterView` is exported from `mvp.views`; the mixin is imported from its module, following
the package's existing convention that mixins are not re-exported.

### The templates

- `mvp/templates/mvp/account/base.html` — the layout. Extends `base.html`, the unqualified name a
  project owns, so a project's own base still applies. Overrides the content block with a
  two-column arrangement: the navigation panel, then the page's own content block.
- `mvp/templates/mvp/account/overview.html` — the landing page: heading, introduction, and the
  card region that iterates the collected templates.
- `mvp/templates/cotton/account/nav.html` — `<c-account.nav>`, the navigation panel: the menu
  rendered through the packaged sidebar renderer, as a persistent card at and above the shell's
  configured breakpoint and as the packaged dropdown below it. Two render sites, one menu, exactly
  as django-accounts-center resolved it — CSS-only single markup would mean overriding the
  dropdown's hidden-state internals per breakpoint.
- `mvp/templates/cotton/account/card.html` — `<c-account.card>`, the wrapper a contributed card
  renders inside, so cards from different apps agree on their outer shape without each app
  reproducing it.

### The icons — `mvp/utils.py`

`BS5_ICONS` gains `account_center` and `overview`. The first is named by the shell's user menu
today and resolves to nothing in a project without django-accounts-center, which is the bug US-1
closes.

### Documentation

- `docs/account-center.md` — what the area is, mounting it, adding an entry, writing a page,
  contributing a card, and per-request visibility. Added to the documentation index.
- `docs/navigation.md` — the third menu named alongside the two it documents.
- `skills/django-mvp/references/menus.md` and `references/layout.md` — the same surface for the
  agent-facing skill.
- `README.md` — the "deliberately not" bullet restated (FR-026).
- `CHANGELOG.md` — the new surface and the django-accounts-center version relationship (FR-023).

## Project Structure

### Documentation (this feature)

```text
specs/028-move-account-center/
├── plan.md              # This file
├── research.md          # What reading the code settled
├── spec.md              # The approved specification
├── decisions.md         # Decisions and their rationale
├── progress.md          # Stage and gate record
├── tasks.md             # Task graph
└── feature-state.json   # Ledger
```

### Source code

```text
mvp/
├── menus.py                             # + AccountCenterMenu, get_active_section()
├── urls.py                              # new — the area's route
├── utils.py                             # + two icon keys
├── views/
│   ├── __init__.py                      # + AccountCenterView export
│   └── account.py                       # new — landing view, page mixin
└── templates/
    ├── mvp/account/base.html            # new — the layout
    ├── mvp/account/overview.html        # new — the landing page
    └── cotton/account/
        ├── nav.html                     # new — <c-account.nav>
        └── card.html                    # new — <c-account.card>

tests/
├── test_menus.py                        # + menu shape, contribution, checks, section resolution
├── test_views/test_account.py           # new — landing page, gating, card collection
├── test_components/test_account_nav.py  # new — panel and collapsed control markup
└── testapp_account/                     # new — an installed app that contributes, for US-2/US-3

docs/
├── account-center.md                    # new
├── index.md                             # + toctree entry
└── navigation.md                        # + the third menu

demo/                                    # the area mounted, so the demo shows it
skills/django-mvp/references/            # menus.md, layout.md
```

**Structure Decision**: the package's existing layout is kept exactly. The area is not a sub-app
and not an entry under `mvp/integrations/`: integrations are guarded modules for optional
third-party dependencies (`docs/integrations.md`), and this has no dependency to guard. It is shell
surface, so it sits beside the rest of the shell.

### Test support

US-2 and US-3 need an installed app that contributes an entry and a card. A minimal app under
`tests/` is the honest way to prove it, because the point of both stories is that an app outside
this package can do it. The demo application then mounts the area and contributes one card, which
is what makes the feature visible to a human and keeps the demo honest under G9.

## Story sequence

| Order | Story | Depends on | Rationale |
|---|---|---|---|
| 1 | US-1 — the area exists | — | Everything attaches to it. Delivers the menu, the address, the view, the layout, the icons and the documentation skeleton. |
| 2 | US-2 — an app adds a page | US-1 | Needs the menu and the layout to exist. Adds section resolution, the trail, and the test app. |
| 3 | US-3 — an app contributes a card | US-1 | Needs the landing page. Independent of US-2 and could run beside it, but the run is sequential by default. |

## Risks

- **The menu-name collision is documented, not prevented.** A project on the current
  django-accounts-center gets one of the two menus. Nothing in this package can detect the other
  reliably, and a check that guessed would be wrong in both directions.
- **A card's template is rendered with the landing page's context plus whatever the contributing
  app merges in.** Two apps whose card context uses the same key collide. This is the same
  namespace risk Django template context has always had, and the documentation says to prefix.
- **The stylesheet rebuild is the one step a machine cannot verify**, because the build is not
  byte-reproducible (Article XV). The reviewer checks that classes the new templates use appear in
  the committed artifact.
