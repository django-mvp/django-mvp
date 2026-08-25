# Styling and theming — reference

What you can put in a `class=` attribute without installing Node, what forces your project
to build its own stylesheet, how themes are applied and written, and what the bundled
JavaScript provides. Read this before writing a CSS class or choosing a theme.

## The two tiers

| You | Tier |
| --- | --- |
| Compose packaged components, configure them through attributes and `MVP_CONFIG`, and lay pages out with classes from the shipped set | Tier 1 — no build step |
| Reach for a Tailwind class outside the shipped set, or an arbitrary value | Tier 2 — your own build |

Tier 1 is not "components only". The packaged stylesheet is loaded for you by
`mvp/base.html` and already contains four things:

- **The complete daisyUI 5 component set** — every component, not only the ones the
  package's own templates render. `carousel`, `kbd`, `chat`, `timeline` and the rest work
  out of the box.
- **Every prebuilt daisyUI theme.** All of `light`, `dark`, `dracula`, `synthwave`,
  `cupcake`, `nord`, `retro`, `abyss`, `silk` and the others are in the shipped file. The
  package adds none of its own: a theme is branding, and that is the project's.
- **The Tailwind typography plugin.** `prose` works, and so does `not-prose` — it is not a
  generated utility but part of every `.prose` selector, so it is always there. The size and
  colour modifiers (`prose-lg`, `prose-invert`) do not ship.
- **A curated pack of plain Tailwind utilities** — layout, spacing, sizing, position,
  typography, colour and interaction states — safelisted so they exist regardless of what
  the package's templates happen to use. `class="grid grid-cols-3 gap-4"` is Tier 1.

The package's own layout CSS is there too: the drawer-state variants
(`is-drawer-open:`, `is-drawer-close:`), the icon-rail rules, the sidebar breakpoint
classes and the `mvp-col-*` table classes.

## The boundary

| Free in Tier 1 | Forces Tier 2 |
| --- | --- |
| Any daisyUI component or modifier class | A utility outside the curated pack (`shadow-md`, `rotate-45`, `blur-sm`, `space-y-4`) |
| Any utility in the four tiers below | Any arbitrary value: `w-[37px]`, `bg-[#abc]`, `top-[3.5rem]` |
| Any theme name that has a `[data-theme]` block | A pack utility at a variant it does not ship (`sm:flex`, `2xl:gap-4`, `md:shadow-lg`) |
| Custom themes, custom properties, hand-written CSS in your own file | A scale step outside the shipped one (`gap-7`, `p-16`, `max-w-8xl`) |

### The curated pack

| Tier | Contents | Variants |
| --- | --- | --- |
| R | display, flexbox, flex/grid alignment, `grid-cols-1..12`, `col-span-*`, gap, padding, margin, width/height, max/min width/height, text alignment, text size, position, inset, overflow | base, `md:`, `lg:`, `xl:` |
| B | z-index, border width, border radius, opacity, font family, font weight, leading, tracking, text treatment (`truncate`, `italic`, `uppercase`, `underline`, …), cursor, `transition`, `duration-*`, `select-none`, `pointer-events-none`, `object-*`, `list-*` | base only |
| C | daisyUI's semantic palette as `bg-`/`text-`/`border-`: `primary`, `secondary`, `accent`, `neutral`, `info`, `success`, `warning`, `error`, each `-content` partner, `base-100/200/300`, `base-content` | base only |
| S | Tier C's colours under `hover:` and `focus-visible:`, plus `hover:opacity-75`, `hover:opacity-100`, `hover:underline` and the `focus-visible:` equivalents | those two prefixes only |

Scale steps for spacing and gap are `0 1 2 3 4 5 6 8 10 12`. Nothing between or beyond.

`sm:` and `2xl:` are **not** in the pack. A handful of classes ship at those prefixes
because a component builds them from its own attributes (`sm:grid-cols-3`,
`2xl:hidden`, `sm:flex-row`, `md:max-w-2xl`, `lg:drawer-open`), but treat that as
component internals, not a responsive scale you can use. Write `md:`, `lg:` or `xl:`.

The package's `docs/utility-classes.md` enumerates every class in the pack. Its closing
paragraph about named themes is out of date — every prebuilt theme ships.

## Traps

**Shadow utilities are deliberately left out, and a missing one is silent.** `shadow-md`
matches nothing and the element renders flat with no error. Nor does any prefixed form
(`md:shadow-lg`, `hover:shadow-xl`). A few unprefixed names exist as a by-product of how
daisyUI's own source is scanned, so `shadow-sm` may appear to work while `shadow-md` does
not — do not build on that. The omission is easy to miss because the components carry
their own shadows internally: your `<c-card>` looks raised whether or not your
`shadow-lg` did anything. If a project wants loose shadow utilities, that is a Tier 2
decision.

**Inline-axis utilities ship in their logical form only.** `ps-` `pe-` `ms-` `me-`
`text-start` `text-end` `border-s` `border-e` `start-0` `end-0` are in the stylesheet.
The physical `pl-` `pr-` `ml-` `mr-` `text-left` `text-right` `border-l` `border-r` are
not, and produce nothing. Block-axis utilities are unaffected: `pt-` `pb-` `mt-` `mb-`
`border-t` `border-b` all ship. Translate as you write — `mr-2` becomes `me-2`.

**Arbitrary values never ship.** `w-[37px]`, `text-[13px]`, `bg-[#f0f0f0]` are generated
by Tailwind from your source at build time and there is no build. Use a scale step, or a
`style=""` attribute, or move to Tier 2.

**A class assembled at render time is not in the stylesheet.** `class="text-{{ level }}"`,
a class name built in a view, and a utility named in a django-tables2 column's `attrs`
are all invisible to a scanner that never saw the finished string. It works only if the
finished string happens to be in the shipped set. Prefer whole class names in templates.

## Moving to your own build

Three commands, run from your project root:

```bash
npm install -D tailwindcss @tailwindcss/cli daisyui   # once
python manage.py mvp_tailwind > assets/tailwind.css   # generate the entry file
npx @tailwindcss/cli -i assets/tailwind.css -o static/css/app.css --minify
```

`mvp_tailwind` writes an entry that imports Tailwind and daisyUI with `themes: all`,
imports the package's preset (`mvp/tailwind/base.css`: drawer variants, icon-rail CSS,
`mvp-col-*`, and the safelist for classes the components build from their attributes),
adds a `@source` for the packaged templates, and leaves `@source "./templates"` for you to
extend — one line per directory containing Tailwind classes.

`python manage.py mvp_tailwind --paths` prints just the two resolved package paths (preset
CSS, templates directory) if you would rather wire your own entry file.

Two things to know before you switch:

**The generated paths are absolute and machine-specific.** They point into the installed
package inside your environment. Re-run the command after upgrading django-mvp, after
rebuilding a virtualenv, and in any new environment. A stale path silently stops the
packaged templates being scanned, and components lose their classes.

**The generated entry is not a superset of the shipped build.** It omits the typography
plugin, the blanket scan of daisyUI's source and the utility safelist. Your own templates
are now scanned, so anything you write yourself is emitted — including physical `pl-4` and
arbitrary values. But classes that worked in Tier 1 without appearing in any scanned file
stop working. Moving to Tier 2 to add classes can take away ones you already had.

To keep them, add these to the generated entry, after the `@plugin "daisyui"` block. Every
`@source` path is resolved relative to the entry file, not to the project root, so the `../`
below is what steps back out of `assets/` — the package's own entry sits at the same depth and
is written the same way:

```css
/* assets/tailwind.css — restore what Tier 1 gave you */
@plugin "@tailwindcss/typography";                          /* prose */
@source "../node_modules/daisyui/components/**/*.js";       /* every component */
@source "../node_modules/daisyui/utilities/**/*.js";
@source "../yourapp/tables.py";                             /* classes named in Python */
```

A path at the wrong depth matches nothing and reports nothing — `./node_modules/…` from
`assets/tailwind.css` looks for `assets/node_modules` and quietly finds no files.

The two daisyUI `@source` lines force every component class into the build rather than
only the ones your templates and the packaged templates mention. For the utility pack,
either copy the `@source inline(...)` block from the package repository's
`assets/tailwind.css`, or do nothing — Tailwind now emits whatever your templates use.

## Theming

A theme is a block of CSS custom properties scoped to `[data-theme="<name>"]`. Switching
one changes which block matches. There is no build step in either tier.

| `MVP_CONFIG["theme"]` key | Default | What it does |
| --- | --- | --- |
| `default` | `"light"` | Applied when the visitor has expressed no preference |
| `dark` | `"dark"` | The other half of the two-state toggle |
| `choices` | `[]` | Themes the packaged switcher offers, in order |

The three interact: **`dark` is consulted only while `choices` is empty.** With `choices`
empty, `<c-actions.theme-controller />` renders a two-state toggle between `default` and
`dark`, so replace both or neither. Set `choices` to a non-empty list and the same
component becomes a dropdown of exactly those names — `dark` is then unused, and a name
missing from the list can no longer be reached.

### How the theme is applied

`mvp/base.html` opens `<head>` with a small inline script, before the `head` block and
before any stylesheet. It reads `localStorage.theme`, checks it against `choices` if
`choices` is set, falls back to `default`, and sets `data-theme` on `<html>`. It is
deliberately blocking and inline: an external or deferred script runs after first paint,
so the page would render in the default theme and visibly flip to the visitor's on every
navigation. A stored theme the project no longer offers is rewritten to `default`.

The bundled `theme-change` library binds the `data-set-theme` / `data-toggle-theme`
controls afterwards. A stored choice survives a package upgrade by design — a visitor
moves to a new pair by using the switcher.

### Writing your own theme

Plain CSS, no build step, no plugin. Copy the properties from a shipped theme and change
values.

```css
/* static/css/theme-sunrise.css */
[data-theme="sunrise"] {
  color-scheme: light;
  --color-base-100: oklch(98% 0.01 80);
  --color-base-content: oklch(25% 0.02 80);
  --color-primary: oklch(68% 0.19 40);
  --color-primary-content: oklch(98% 0.01 40);
  /* ...about thirty properties in total */
}
```

Load it by extending the `styles` block in your own base template, then name it in
`MVP_CONFIG["theme"]["default"]` or add it to `choices`:

```django
{# templates/base.html #}
{% extends "mvp/base.html" %}
{% load static %}
{% block styles %}
  {{ block.super }}
  <link rel="stylesheet" href="{% static 'css/theme-sunrise.css' %}" />
{% endblock styles %}
```

Load order does not matter. The packaged theme blocks sit inside `@layer base`, and cascade
layers are resolved before specificity, so any rule in your unlayered file beats them
wherever the `<link>` sits. That also means you can redefine a shipped theme by name —
your own `[data-theme="dracula"]` replaces the packaged one project-wide.

**Theme names are not validated.** A typo raises nothing and logs nothing: the document
falls through to the default theme and renders normally, just not in the theme you asked
for. When a theme "does not work", check the spelling and that the stylesheet is loading
before you debug the properties inside it.

The package's `docs/theming.md` carries the full table of every custom property a theme
can set and what each one controls.

## The bundled JavaScript

`mvp/static/js/django-mvp.js` is a committed bundle of four libraries: Alpine.js, the
`@alpinejs/persist` plugin, htmx and theme-change. They are served from your own static
files. Nothing is fetched from a third party at page load.

Two globals are exposed: `window.Alpine` and `window.htmx`.

Packaged behaviour that depends on them:

| Feature | Needs |
| --- | --- |
| Sidebar collapse state, remembered across page loads | Alpine + `persist` |
| Dismissible alerts and messages, with optional auto-dismiss | Alpine |
| Sticky header picking up a shadow once the page scrolls | Alpine |
| Formset add/remove rows | Alpine (`mvp/static/js/formset.js` reaches for the global) |
| Theme toggle and theme dropdown | theme-change |
| `hx-boost` sidebar navigation, when enabled | htmx |

Three rules:

- **The bundle is not configurable.** The components are written against these versions.
  A project cannot swap or drop one without breaking packaged markup.
- **Add your own plugins from your own base template**, by extending `{% block head %}`
  with `{{ block.super }}` — an Alpine plugin, an htmx extension. Do not replace the
  bundle.
- **htmx is already loaded. Do not add a CDN script tag for it.** A second copy
  double-binds every `hx-*` attribute and fires each request twice. The same applies to
  Alpine.

## Adding your own stylesheet

Override `{% block styles %}` and call `{{ block.super }}`, as in the theme example above.
That block contains only the packaged stylesheet link, so it is the safe one to extend.

Overriding `{% block head %}` without `{{ block.super }}` takes the whole head with it. The
`styles` block is nested inside `head`, so `django-mvp.css` goes too, along with the icon
webfont link, both favicon links, the JavaScript bundle's `<script>` tag, and the charset,
viewport and title tags. The page renders unstyled, with no icons and no interactivity. Extend
`styles` unless you need to replace the whole head, and if you do, copy the packaged block's
contents forward.

The Bootstrap Icons webfont is the one thing the shell does fetch from a CDN, so an
offline or air-gapped deployment must self-host it — see the icons reference.

## Table column classes

`mvp-col-grow`, `mvp-col-shrink`, `mvp-col-wrap`, `mvp-col-nowrap` and
`mvp-col-max-{xs,sm,md,lg,xl}` are shipped CSS rules in the package's preset, not Tailwind
utilities, so they survive both tiers and are applied the ordinary django-tables2 way
through a column's `attrs`. Grow and shrink contradict each other — name only one. Put the
width classes on the `th` as well as the `td` when a column's heading is the long part.

---

Back to [SKILL.md](../SKILL.md).
