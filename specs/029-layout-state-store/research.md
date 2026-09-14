# Research — 029 Layout state store and static responsive visibility

Three questions had to be answered before the plan could commit to an approach. Each is recorded
with what was checked, not what was assumed.

## R1 — When does a store's `init()` run, relative to the DOM walk?

**Why it matters.** The whole first-paint argument rests on the store reading the drawer checkbox
*before* any binding on that checkbox is evaluated. If the order were the other way round, the
binding would push the store's uninitialised value onto a checkbox the pre-paint script had
already set correctly, and the sidebar would animate on every load — issue #178, reintroduced.

**Checked**: `node_modules/alpinejs/dist/module.esm.js`, the version the bundle is built from
(3.16.1).

**Finding**: `Alpine.store(name, value)` calls `value.init()` synchronously at registration, the
moment the store is defined. `Alpine.start()` is a separate, later call, and the DOM walk that
evaluates directives happens inside it, after the `alpine:init` dispatch.

Registering the store in the bundle's entry module, before the existing `Alpine.start()` call,
therefore guarantees the ordering the plan needs. The bundle is deferred, so the document is fully
parsed by the time any of this runs and the checkbox is present to be read.

**Consequence for the plan**: the store reads the checkbox. It does not re-derive the state from
storage, and there is no third copy of the rule.

## R2 — Does the persist plugin work on a store?

**Why it matters.** The sidebar's remembered desktop state is currently held by the persist plugin
in local component state. Moving it to the store must not mean hand-rolling `localStorage` access,
which would be a second implementation of something already bundled.

**Checked**: the same file. `Alpine.store()` has two branches for interceptors — one for a value
that is itself an interceptor, and a call to `initInterceptors` for a plain object, which walks it
and initialises any interceptor found on a property.

**Finding**: both the whole-store and the single-property forms are supported. A store may hold a
persisted property alongside ordinary ones. Two details decide where the code goes:

- The property's key and initial value are needed when the store object is constructed, before
  `init()` runs. The bundle is deferred, so the document is parsed and the markup can be read at
  that point — the key and the resolved value can come from the drawer's own attributes rather
  than being written down a second time in script.
- `Alpine.$persist` is defined by the persist plugin, on the plugin call. The store must therefore
  be registered after `Alpine.plugin(persist)`, not merely before `Alpine.start()`.

**Consequence for the plan**: the remembered desktop state stays a persisted property, now on the
store, keyed and seeded from markup. The storage key does not change, so an upgrading project
keeps whatever its users had.

## R3 — Where can the stylesheet's rules find the configured breakpoint?

**Why it matters.** The rules have to be static, so the value they select on must be in the markup.
FR-017 adds that a project overriding the base template must not silently lose them.

**Checked**: the template chain from `mvp/base.html` down, and every call site of the three tags
being removed.

**Finding**: all four governed regions are descendants of the element the drawer component renders.
The header, the page content and the Account Center's layout all sit inside the drawer's content
pane, and the navbar's toggle and site icon sit inside the header. That element is rendered by a
component, and it already receives the resolved breakpoint, with per-page overrides applied.

It is also the element the existing drawer-state selectors key on, which is what lets one rule
express "hidden at this width only while the drawer is open" without a second attribute host.

**But the collapse mode does not reach it today.** `mvp/templates/mvp/base.html` resolves both
values and passes only the breakpoint to `<c-app>`; the collapse mode goes to the sidebar and the
header instead. `mvp/templates/cotton/app/index.html` declares no `collapse` variable and cannot
forward what it never received. The stylesheet rule for the sidebar's duplicated controls needs
both values on one element, so the value has to be threaded through two components that do not
currently carry it.

**Consequence for the plan**: the attributes go on the drawer element, and threading the collapse
mode through `<c-app>` is part of the work rather than something already in place. A project that
replaces `base.html` still renders `<c-app>`, and therefore still gets both attributes.

## What was not researched, and why

The visibility substitution's correctness is not a research question — it is a test question. The
current behaviour is fully determined by three small functions and their four call sites, all read
in full. Rather than reason about equivalence, the plan writes the tests against the current
package first and requires them to pass before anything is removed.
