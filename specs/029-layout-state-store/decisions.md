# Decisions — 029 Layout state store and static responsive visibility

Rationale too long to carry inline in `spec.md`, plus every ambiguity resolved without
escalation. Each entry records what was unclear, what was chosen, and why the choice is
defensible on evidence already in this repository.

## D1 — Responsive visibility stays in the stylesheet

**Ambiguous because** issue #345 proposes the opposite: that regions be shown and hidden by
client-side expressions keyed off layout state, rather than by classes injected from template
tags.

**Chosen**: the tags go, but their rules become stylesheet rules. No region's visibility depends
on the client-side runtime.

**Why this is defensible on this repository's own evidence.** The shipped bundle is loaded with
`defer`, so nothing it registers exists until after the document has parsed. Expression-driven
visibility therefore applies after first paint, and both the wide and narrow copies of a region
are on screen until it does. This package has already paid for exactly that, in a different
place: `mvp/templates/cotton/layout/sidebar/index.html` carries a blocking inline script whose
whole purpose is to set the drawer's state before first paint, because resolving it after paint
turned a correction into a visible width animation (#178). Its comment says so. Reintroducing the
same ordering problem in the header, on every load and again on every boosted navigation, to
retire a template tag would be trading a maintenance cost for a user-visible one.

Three further properties the current approach has and an expression-driven one would not:
visibility survives JavaScript being unavailable, it costs no work on resize, and it is what every
other responsive decision in the library is expressed with, so the header would stop being special.

**What this does not settle.** The complaint underneath #345 is real and is acted on: the classes
are assembled at render time, which the stylesheet build cannot see, and the package compensates
with safelist entries and a test guarding them. That is the actual cost, and moving the rules into
the preset removes it without moving them into script.

## D2 — The third tag joins the two named in the issue

**Ambiguous because** neither issue names `sidebar_navbar_toggle_class`, and the standing rule is
that scope comes from the issue rather than from what looks adjacent.

**Chosen**: it is in scope, on Sam's explicit ruling.

**Why**: it is the same mechanism — a class assembled at render time from the configured
breakpoint, covered by entries in the same safelist block, carrying the same "keep in sync"
comment. Removing two of three would leave the safelist, the comments and the render-time
construction standing, so the cost the feature exists to remove would survive it.

## D3 — Removal without a deprecation period

**Ambiguous because** the three tags are reachable from any project template through
`{% load mvp %}`, which makes them public by access even though nothing advertises them.

**Chosen**: removed outright in this release, recorded as a breaking change.

**Why**: Article XVI states the package is pre-1.0 and that component and import APIs may change
between minor versions with a changelog entry. A search of `docs/`, `README.md` and the shipped
skill finds no mention of any of the three, so a deprecation cycle would be announcing the
withdrawal of something never announced in the first place. Sam ruled on this directly.

## D4 — The attributes the stylesheet selects on go on a component-rendered element

**Ambiguous because** the obvious host for a document-wide attribute is `<body>`, which
`mvp/templates/mvp/base.html` renders.

**Chosen**: an element rendered by a component, containing all four governed regions. The spec
states the constraint rather than naming the element, because which one satisfies it is a
planning decision.

**Why `<body>` is the wrong host**: overriding the base template is a documented and expected
extension, and a project that does so writes its own `<body>`. The rules would then find no
attribute to select on and the header's trailing regions would never hide — a silent, width-
dependent failure of exactly the kind this feature is trying to reduce. Every one of the four
regions is already a descendant of the element the shell's drawer component renders, and that
component resolves the breakpoint and collapse mode itself.

## D5 — The store mirrors the drawer's control rather than owning it

**Ambiguous because** "one store holding layout state" reads as though the store should be the
single source of truth, and a mirror is a weaker claim.

**Chosen**: the drawer's existing checkbox stays authoritative for whether the sidebar is open.
The store tracks it in both directions, and the stylesheet keeps reacting to the checkbox
directly through the drawer-state variants.

**Why**: the same first-paint argument as D1, applied to the sidebar. The checkbox's state is
established during parse by a blocking script; a store's state is established when the deferred
bundle runs. Making the store authoritative would move the sidebar's resting position behind the
bundle and reinstate #178. It would also break the `is-drawer-open` / `is-drawer-close` variants,
which the sidebar, the drawer side panel and the icon rail all depend on and which cost nothing.

SC-002 still holds, because what it forbids is the same *fact* being written down twice, not a
reactive mirror of a fact with one owner. The duplication the feature removes is real and
separate: the sidebar's persisted default is currently spelled out once in the blocking script and
again in the persisted expression beside it.

## D6 — The store carries the layout settings only

**Ambiguous because** #346 says "app configuration", which could mean the whole merged
configuration dictionary.

**Chosen**: the `layout` subtree.

**Why**: the theme already reaches the client by its own mechanism, through the document attribute
the pre-paint script sets and the controls the bundle binds. The remaining top-level keys —
view names and table defaults — are read on the server to decide what to render, and nothing on
the page reacts to them. Publishing them would add public surface the package must then keep
stable, in exchange for no capability. If a later feature needs one, adding a key to a store that
already exists is cheap.
