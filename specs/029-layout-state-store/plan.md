# Implementation Plan: Layout state store and static responsive visibility

**Branch**: `029-layout-state-store` | **Date**: 2026-09-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/029-layout-state-store/spec.md`

## Summary

One resolver on the server produces the shell's layout facts once. Two consumers read it: the
shell's markup, which renders them as attributes the stylesheet selects on, and a JSON payload the
client store hydrates from. The drawer's checkbox stays the single truth for whether the sidebar
is open, and the store reads it rather than recomputing it. Three template tags that assembled
responsive visibility classes at render time are deleted, and their rules become static CSS in the
packaged preset.

The through-line is that every layout fact is computed once, on the server, and everything else
reads it.

## Technical Context

**Language/Version**: Python 3.12+, Django 5.2+ · JavaScript (ES modules, bundled by esbuild)

**Primary Dependencies**: django-cotton, Alpine 3 with `@alpinejs/persist`, htmx, Tailwind CSS v4,
DaisyUI 5. No new dependency of any kind.

**Storage**: N/A. The sidebar's remembered open state uses `localStorage` through Alpine's persist
plugin, exactly as today.

**Testing**: pytest, pytest-django, pytest-playwright. Rendered-template assertions for everything
expressible that way (Article XIV); browser tests only for first-paint ordering, viewport response
and the boosted-navigation case, none of which a rendered template can show.

**Target Platform**: Evergreen browsers. The shell must render correctly with JavaScript disabled.

**Project Type**: Installable Django package with a demo application.

**Performance Goals**: No measurable change. The work removes per-request string building and adds
one JSON payload per page.

**Constraints**: First paint must not wait on the bundle (FR-005). The stylesheet and JavaScript
artifacts are committed and must be rebuilt on this branch (Article XV). No new configuration key.

**Scale/Scope**: Four regions of the shell, three template tags, two committed build artifacts,
one new Python module, one new JavaScript module.

## Constitution Check

| Article | Status | Note |
|---|---|---|
| I — Test-First | Applies | Every behaviour change starts red. The visibility substitution is the sharp case: its tests must be written against the *current* package, pass against it, and still pass after the change. A test written after the tags are gone proves only that the new code does what it does. |
| II — Simplicity | Pass | Nothing is introduced that is not required by a requirement. The store is one object; the resolver is one class. |
| III — Anti-Abstraction | Pass | One resolver class with a present second use (attributes and the JSON payload), not a layer built for a future one. |
| IV — Integration-First | Pass | The store is a consumer-facing contract and is specified and tested as one before its internals matter. |
| V — Security | Applies | Configuration reaches the client through `json_script`, never hand-built interpolation (FR-012). No user data is involved. |
| VI — Documentation | Applies | `docs/layout.md` gains the store, `CONTEXT.md` gains the term, `CHANGELOG.md` records the removal as breaking. All in this pull request. |
| VII — Dependency discipline | Pass | No dependency added or changed. |
| VIII — Internationalization | Not engaged | No new user-facing string. |
| IX — Data-model conventions | Not engaged | No model, no migration. |
| X — Test structure | Applies | New tests mirror their subject: `mvp/layout.py` is exercised by `tests/test_layout.py`. Template-subject tests belong under the already-declared `tests/test_components/`. |
| XI — Components are the public API | Applies | The attributes are rendered by components, not written into a project's own templates. No new component attribute is invented where an existing one already carries the value. |
| XII — Configuration-driven layout | Pass | Resolution order unchanged: component attribute, then settings, then package default. The resolver is where that order is applied, once. |
| XIII — Rendered markup is a contract | Applies | Every markup change carries a test asserting the rendered result. |
| XIV — Browser tests are the exception | Applies | See Testing above. Anything provable from rendered HTML is proved there. |
| XV — Build artifacts | Applies | Both artifacts rebuilt and committed. The JavaScript bundle is byte-reproducible and must match a fresh build. |
| XVI — Compatibility | Applies | Pre-1.0 removal, recorded in the changelog as breaking. |
| XVII — Cohesion | Applies | The layout facts and their resolution live on one class, not as a scatter of module-level functions. This is the article that decides the shape of `mvp/layout.py`. |
| XVIII — The skill is part of the product | Applies | `skills/django-mvp/references/layout.md` documents the store and loses the tags, in this pull request. |
| XIX — Views forward attributes as a dict | Not engaged | No view changes. |

No violations. Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/029-layout-state-store/
├── spec.md
├── decisions.md
├── plan.md            # this file
├── research.md        # the three load-bearing unknowns and how they were settled
├── progress.md
├── tasks.md
└── feature-state.json
```

### Source code

```text
mvp/
├── layout.py                              NEW — the resolver (Article XVII: one class)
├── templatetags/mvp.py                    three tags removed, one tag added
├── tailwind/base.css                      static visibility rules in, safelist entries out
├── templates/
│   ├── mvp/base.html                      passes the collapse mode to <c-app>
│   ├── mvp/account/base.html              two call sites become semantic classes
│   └── cotton/
│       ├── app/index.html                 forwards the collapse mode to the drawer
│       ├── layout/sidebar/index.html      attributes, payload, store binding, seed script
│       ├── app/header/index.html          stuck state moves to the store
│       └── app/header/navbar.html         three call sites become semantic classes
└── static/js/django-mvp.js                rebuilt artifact
assets/js/
├── index.js                               registers the store
└── layout.js                              NEW — the store definition
demo/                                      one page showing a project reacting to the shell
tests/
├── test_layout.py                         NEW — mirrors mvp/layout.py
└── test_components/
    ├── test_layout_config.py              tag tests replaced by rendered-markup tests
    ├── test_layout_store.py               NEW — the store, in a browser
    ├── test_responsive_visibility.py      NEW — the substitution, at every setting
    ├── test_responsive_safelist.py        the removed tags' case deleted
    └── test_sidebar_persisted_state.py    extended to cover the store's agreement
tests/test_views/test_account.py           two assertions restated against the new classes
```

**Structure Decision**: The package's existing layout is kept. One new Python module, one new
JavaScript module, three new test modules. Nothing is reorganised.

## Design

### The resolver — `mvp/layout.py`

One class, `LayoutConfig`, built from the values a page has already resolved (the component
attribute where the page set one, otherwise `MVP_CONFIG`). It is the single place where a
breakpoint name becomes anything else:

| Property | Value |
|---|---|
| `breakpoint` | the normalised name: one of `sm`, `md`, `lg`, `xl`, `2xl`, or `never` |
| `persistent` | whether the sidebar ever becomes persistent |
| `breakpoint_px` | the width in pixels, or nothing when it is never persistent |
| `collapse` | `offcanvas` or `icons` |
| `sticky`, `boost` | as configured |

Normalisation is the behaviour the three removed tags each re-implemented: `never` or `none` in
any case means not persistent, and an unrecognised name falls back to `lg`. It happens once, here.
`as_dict()` returns the payload the client receives.

The surviving tags (`sidebar_breakpoint_class`, `breakpoint_px`, `sidebar_has_breakpoint`) become
thin readers of this class rather than three independent implementations of the same rules, which
is what Article XVII asks for and what makes "the fallback is defined once" checkable.

### What reaches the client, and how

The drawer component emits `LayoutConfig.as_dict()` through Django's `json_script` filter, into a
script element of type `application/json`. That is the whole transport. It satisfies FR-011
(server-emitted, not re-derived) and FR-012 (escaped by the template layer) at once, and it is the
idiom Django already ships for this, so there is nothing to invent and nothing to review.

It is emitted by the drawer component rather than by `mvp/base.html` for the reason D4 gives about
the attributes: a project overriding the base template writes its own, and a payload that lives
there is silently lost, leaving the store with no configuration and a viewport flag stuck false.
One element carries the attributes and the payload, so a project either keeps both or keeps
neither. A script element of this type is valid anywhere in the body.

### The store — `assets/js/layout.js`

`Alpine.store("layout", …)`, registered from `assets/js/index.js` **after `Alpine.plugin(persist)`
and before `Alpine.start()`**. The ordering is not stylistic: the persist plugin is what defines
`Alpine.$persist`, so a store registered earlier — beside the dropdown and theme wiring, for
instance — cannot hold a persisted property at all. It carries:

- **Configuration**, hydrated in `init()` by parsing the payload above.
- **`sidebarOpen`**, read from the drawer checkbox at `init()` and kept in agreement with it.
- **`desktopOpen`**, the remembered state of a persistent sidebar: a persisted property whose
  storage key and initial value are read from the drawer's own attributes when the store object is
  constructed. This is what makes FR-006 true. Today the default and the key are written twice —
  once in the blocking script and once in the persisted expression beside it — and merely moving
  the second copy onto the store would carry the duplication with it. Instead the blocking script
  becomes the single definition: it resolves the value before first paint, as it does now, and
  renders both the key and the value it resolved into the markup for the store to read.
- **`isWide`**, from a `matchMedia` query built on the pixel width, with a `change` listener.
  Permanently false when the sidebar is never persistent.
- **`headerStuck`**, written by the header's existing scroll handler.

A page that does not render the shell — the entrance page, the error pages — carries no payload and
no drawer. The store still registers, reports the package defaults, and reports the sidebar closed.
It does not throw, and it does not require every page to be a shell page.

**The ordering that matters.** Alpine calls a store's `init()` during start, before it walks the
DOM. The store therefore reads the checkbox's state — which the blocking script set during parse —
*before* any binding on that checkbox is evaluated. The binding then writes back the value the
checkbox already has, and nothing moves. This is what keeps FR-005 true and what stops the feature
reintroducing #178. It is also why the store reads the checkbox rather than re-deriving from
storage: one computation, done before first paint, two readers.

### Rebinding after a boosted navigation

A boosted navigation replaces the body, so the drawer and its checkbox are new elements and the
server rendered them closed. Today the fresh local state re-derives the resting position, which is
why a mobile overlay closes on navigation and a desktop sidebar does not. A global store survives
the swap and would keep a mobile overlay open, which is a behaviour change.

The store therefore re-derives its sidebar state on `htmx:afterSettle` when the swap target was
the body, in the same handler that already rebinds the theme controls and the dropdowns: open only
when the viewport is wide and the remembered desktop state says so. That reproduces today's
behaviour exactly, in an existing handler rather than a new one.

### Responsive visibility in the stylesheet

Every one of the four governed regions is a descendant of the shell's drawer element — the header
and the page content both live inside the drawer's content pane. It renders `data-mvp-breakpoint`
and `data-mvp-collapse`, and it is a component rather than the base template, which is what FR-017
requires: a project that overrides `base.html` keeps `<c-app>` and therefore keeps the attributes.

The drawer resolves the breakpoint today but **not** the collapse mode, which `base.html` sends to
the sidebar and the header instead. Threading it through `<c-app>` to the drawer is part of this
work, not something already in place.

Regions take semantic classes instead of assembled utilities:

| Class | Replaces | Rule |
|---|---|---|
| `mvp-desktop-only` | `navbar_wide_only_class` | hidden below the breakpoint |
| `mvp-mobile-only` | `navbar_narrow_only_class` | hidden at and above the breakpoint |
| `mvp-sidebar-hidden-only` | `sidebar_navbar_toggle_class` | hidden where the sidebar header shows its own copy |

`mvp/tailwind/base.css` gains one media block per supported breakpoint, each selecting on the
matching attribute value. The third rule needs the collapse mode as well: under `icons` the region
is hidden throughout, under `offcanvas` only while the drawer is open — which the attribute host
can express directly, because it is the same element the drawer-state selector already keys on.

Because `never` renders as its own attribute value, no media block matches it and the regions fall
back to their unconditional state. For two of the three classes that is exactly what the tags did.
The third is asymmetric and needs saying out loud: `navbar_narrow_only_class` returns `hidden`
under `never`, so that a project reads one set of header actions rather than two stacked copies.
Falling back to shown would put the mobile copy on screen at every width — a visible regression in
the one setting nobody tests by accident. The preset therefore carries one explicit rule hiding the
narrow-only region under that attribute value.

An unrecognised value never reaches the stylesheet at all: the resolver normalised it to `lg`
before rendering.

Three safelist entries and the safelist test's case for the removed tags go with them.

### What is deliberately not done

- The drawer-open class stays assembled at render time. It is DaisyUI's own API.
- The drawer-state variants stay. They cost nothing, and they are how the sidebar, the icon rail
  and the drawer side panel already react to the checkbox.
- `c-layout.sidebar` is not generalised. Nothing but `c-app` renders it, in the package or in the
  documentation.

### How the substitution is proved

The correctness condition is that no rendered page changes, and the natural way to test that in
this repository — asserting class strings in rendered HTML — cannot do it. The class strings *are*
the mechanism being substituted, so an assertion on them either pins the old mechanism and has to
be rewritten (at which point it has stopped being a regression test) or pins the new one and never
had anything to say about the old.

So the characterisation tests assert **computed visibility in a real browser**: the resolved
`display` of each governed region, at a width below and a width at or above each setting. That form
is indifferent to how visibility is achieved, which is the entire point, and it is what lets the
tests be written against the current package, pass against it, and stand unchanged afterwards.

This is a deliberate exception under Article XIV, and it is the exception the article is for:
equivalence across six breakpoint settings and two collapse modes is not expressible from rendered
HTML once the mechanism moves into the stylesheet. Everything else in the feature that *is* so
expressible — which class each region carries, which attributes the shell renders, what the payload
contains — stays a rendered-template assertion.

### Story order

The three stories are dispatched **sequentially**, not in parallel worktrees. They share too much
to converge cleanly:

- one committed bundle artifact, rebuilt by both US-1 and US-2 — a single minified line, so two
  worktrees rebuilding it collide by construction;
- one store module, one browser-test module, one rendered-markup test module;
- the drawer template, which US-1 rebinds and US-3 adds attributes to;
- two documentation files.

Order: **Phase 0 → US-1 → US-2 → US-3**. Phase 0 carries the resolver and the payload, because
both the store and the attributes read them, and because the plan's own through-line puts every
layout fact on the server side of one resolution.

## Risks

| Risk | Mitigation |
|---|---|
| The substitution changes rendering somewhere unnoticed. Six breakpoint settings by two collapse modes by four regions is a wide surface for a change with no visible payoff. | Computed-visibility tests, written first against the current package, green before anything is removed, and unchanged afterwards. See *How the substitution is proved*. |
| The `never` setting is the one nobody exercises by accident, and one of the three regions behaves asymmetrically under it. | An explicit stylesheet rule for that region, and the `never` setting included in the characterisation matrix for all four regions. |
| A binding against the store fights the pre-paint script and reintroduces #178. | The store reads the checkbox rather than a second source, and the existing regression test for #178 is extended to assert the store agrees with the DOM rather than replaced. |
| The boosted-navigation path is easy to get right at desktop width and wrong at mobile width. | An explicit acceptance scenario and an end-to-end test at a narrow viewport, not only a wide one. |
| The committed bundle drifts from its source. | It is byte-reproducible. Convergence rebuilds and compares. |

## Complexity Tracking

No constitution violations. Table intentionally empty.
