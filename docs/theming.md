# Theming

django-mvp ships every prebuilt DaisyUI theme and the mechanism to write your own. It ships no
theme of its own, deliberately. This page explains how theming actually works, lists every
variable a theme can set, and walks through writing a theme from an empty file to a rendered
page.

## The theme the package applies

With nothing configured, pages render in `light`. Its partner is `dark`, and the packaged
switcher moves between the two:

```python
MVP_CONFIG = {
    "theme": {
        "default": "light",     # applied when the visitor has expressed no preference
        "dark": "dark",         # the other half of the toggle
        "choices": [],          # a menu instead of a toggle, when non-empty
    },
}
```

Setting `choices` to a non-empty list changes what `<c-mvp.actions.theme-controller />` renders:
a dropdown of exactly those names instead of a toggle between `default` and `dark`. `dark`
goes unused once `choices` is set, and a theme left out of `choices` can no longer be reached
through the switcher, whatever `dark` says.

`<c-mvp.actions.theme-cycle />` is a second switcher: one button that steps from `default` to
`dark`, then to automatic, then back to `default`. Automatic follows the device's light or dark
setting, and keeps following it while the page is open. The button moves between `default` and
`dark` whether or not `choices` is set, so it can sit beside the menu. List
`"mvp.actions.theme-cycle"` in `layout.navbar.end` to put it in the navbar. The sidebar footer
keeps the toggle unless you override `cotton/app/sidebar/footer.html`.

A visitor who has never chosen still gets `default`, not automatic, so adding the button
changes nothing for anyone until they use it.

Both are DaisyUI's, not palettes this package drew. That is on purpose: a theme is the entire
visible surface of your application, and the identity on it should be one you chose rather than
one your dependency picked. The package's job is the mechanism and the components; the palette is
yours.

Which means **the applied theme carries no contrast guarantee, including the default**. The
prebuilt themes are DaisyUI's files, and most of them put at least one brand colour below the WCAG
AA text floor against their own page background — `light` renders `text-error` at 2.87:1, which is
what a form validation message is drawn in. That matters because `text-*` and `border-*` render
the raw fill value rather than a pairing someone checked. A theme of your own can
[separate the two](#a-text-value-for-a-brand-colour) for `primary`, `secondary` and `accent`.

If your project has a contrast obligation to meet, write a theme to it. That is what the mechanism
below is for, and it is the only way to be sure, whatever theme you start from. It costs one CSS
file and one setting, and [the worked example](#a-worked-example) is the whole of it.

The demo site does exactly this, and its two themes are a working example you can copy:
[`demo/static/css/themes.css`](https://github.com/django-mvp/django-mvp/blob/main/demo/static/css/themes.css)
holds the palette, [`demo/settings.py`](https://github.com/django-mvp/django-mvp/blob/main/demo/settings.py)
names the pair, and the demo's `base.html` links the file. Those two themes, `mvp` and `mvp-dark`,
were part of the package once and were the applied default — see
[ADR 0016](adr/0016-branded-themes-belong-to-the-demo-site.md) for why they no longer are. If your
project was rendering in them, copying that file across restores the appearance exactly.

The demo's *Theme Preview* page, at `/theme/preview/`, draws every component a theme paints on one
page. Run the demo, add your theme to `demo/static/css/themes.css` and to `choices`, and reload
the page to see the whole theme at once. The stylesheet is plain CSS, so nothing needs building.

Set `default` and `dark` together. The toggle switches between exactly those two names, so
changing one alone leaves it moving between a theme you chose and one you did not.

A visitor who has already used your site has their choice stored in `localStorage`, and that
is read before `default`. Upgrading the package does not move them, by design, because a stored
value is a choice someone made. They reach the new pair by using the switcher.

## What a theme is

A theme is a block of CSS custom properties, scoped to `[data-theme="<name>"]`, that the
packaged components read through `var()` at the moment the browser paints the page:

```css
[data-theme="dracula"] {
  color-scheme: dark;
  --color-base-100: oklch(28.822% 0.022 277.508);
  --color-primary: oklch(75.461% 0.183 346.812);
  /* ... about thirty properties in total */
}
```

There is no build step involved in applying one. Setting `data-theme` on the document
changes which block matches, the browser recalculates `var()` lookups, and the page
re-renders with the new values. This is why you can switch a theme with plain JavaScript
(`document.documentElement.setAttribute('data-theme', 'dracula')`) and why writing a theme
of your own is just writing CSS.

## How the theme is applied

`mvp/base.html` opens `<head>` with a small inline script, before the `head` block and
before any stylesheet. It reads `localStorage.theme`, checks it against `choices` if
`choices` is set, and falls back to `default` if there's no stored value or the stored one
isn't offered. A stored value that is empty is the automatic choice, and the script picks
`dark` or `default` from the device's `prefers-color-scheme` instead. It then sets
`data-theme` on `<html>`, and `data-theme-mode` to `dark` or `auto` when the visitor is on
that step of the theme-cycle button, so the button shows the right icon from the first frame.

The script is deliberately blocking and inline: an external or deferred script runs after
first paint, so the page would render in `default` and visibly flip to the visitor's stored
theme on every navigation. A stored theme the project no longer offers is rewritten back to
`default` in `localStorage` at the same time, rather than just for that one render.

The bundled theme-change library binds the `data-set-theme` / `data-toggle-theme` controls
afterwards, once the deferred JavaScript bundle runs — it only wires the controls; the inline
script above is what applies the theme before the page paints.

A second inline script, the last thing in the `<head>`, reads the applied theme's
`color-scheme` and sets `data-color-scheme` on `<html>` to `dark` or `light`. It runs again
whenever `data-theme` changes. The attribute comes from the theme's stylesheet rather than from
its name, so it's right for any theme, inside the configured pair or not. A brand image with a
dark variant follows it, see [the `brand.*` resolvers](configuration.md#brand-resolvers). A theme that sets
no `color-scheme` counts as light.

## The full variable table

Every theme may set the following properties. A theme does not have to set all of them.
A property left unset simply has no value for `var()` to resolve, so a theme that omits one
loses whatever visual effect that property controls, not the whole theme. The text values and
the fonts are the exception: each has a default, so leaving one out changes nothing.

`color-scheme` is a standard CSS property, not a custom one, but it lives in the same block
and every shipped theme sets it.

| Property | Controls |
| --- | --- |
| `color-scheme` | Whether the browser renders its own UI (scrollbars, form controls, the built-in date picker) as `light` or `dark`, so native chrome doesn't clash with the theme. |
| `--root-bg` | The page's own background, `base-200` unless a theme says otherwise. The header and the mobile dock paint from it. See [Keeping the page on another surface](#keeping-the-page-on-another-surface). |
| `--color-base-100` | Raised: what sits above the page. Cards, inputs, modals, dropdowns and tables. |
| `--color-base-200` | The page: the page background, the header and the mobile dock. |
| `--color-base-300` | Sunk: what sits below the page. The sidebar, wells, stripes and placeholders. |
| `--color-line` | Optional. A colour that shows on all three surfaces, for edges, rules and the default button. See [A line colour](#a-line-colour). |
| `--color-base-content` | The default text and icon color on top of the base surfaces. |
| `--color-primary` | The theme's brand color, used for primary buttons, links and focus states. |
| `--color-primary-content` | Text and icon color for content placed on top of `primary`. |
| `--color-secondary` | A second brand color for elements that shouldn't compete with `primary`. |
| `--color-secondary-content` | Text and icon color for content placed on top of `secondary`. |
| `--color-accent` | A third, distinct color for drawing attention (badges, highlights). |
| `--color-accent-content` | Text and icon color for content placed on top of `accent`. |
| `--color-primary-text` | Optional. `primary` where it is drawn as text on the page, in place of the fill. See [A text value for a brand colour](#a-text-value-for-a-brand-colour). |
| `--color-secondary-text` | Optional. The same for `secondary`. |
| `--color-accent-text` | Optional. The same for `accent`. |
| `--color-neutral` | A low-saturation color for elements that should recede, such as footers. |
| `--color-neutral-content` | Text and icon color for content placed on top of `neutral`. |
| `--color-info` | The color for informational messages and badges. |
| `--color-info-content` | Text and icon color for content placed on top of `info`. |
| `--color-success` | The color for success messages and badges. |
| `--color-success-content` | Text and icon color for content placed on top of `success`. |
| `--color-warning` | The color for warning messages and badges. |
| `--color-warning-content` | Text and icon color for content placed on top of `warning`. |
| `--color-error` | The color for error messages and badges. |
| `--color-error-content` | Text and icon color for content placed on top of `error`. |
| `--radius-selector` | Corner radius on selection-style controls: checkbox, radio, toggle, badge, range. |
| `--radius-field` | Corner radius on field-style controls: button, input, select, tab. |
| `--radius-box` | Corner radius on container elements: card, modal, alert, table. |
| `--size-selector` | Base size unit for selection-style controls, scaled per size variant (`sm`, `lg`, ...). |
| `--size-field` | Base size unit for field-style controls, scaled per size variant. |
| `--border` | Default border width used across components. |
| `--depth` | `0` or `1`. At `1`, flat elements get a subtle inset highlight and shadow that reads as raised. At `0`, they render flat. |
| `--noise` | `0` or `1`. At `1`, components that support it render a faint grain texture over their background. At `0`, the background is a plain fill. |
| `--font-sans` | Optional. The body font, which is everything without a font of its own. See [Fonts](#fonts). |
| `--font-serif` | Optional. The font of the `font-serif` utility. |
| `--font-mono` | Optional. The font of `code`, `kbd`, `samp`, `pre` and the `font-mono` utility. |
| `--font-heading` | Optional. The font of headings and component titles. Follows the body font when unset. |

This list was checked against a shipped theme definition rather than written from memory, and
a test keeps it in step with the installed DaisyUI version: it extracts every custom property
name from a shipped theme file and fails if one is missing from this table. The text values and
the fonts appear in no theme file, because a theme adds them.

## The theme plugin is a pass-through

`@plugin "daisyui/theme"` is the syntax DaisyUI itself uses to register a theme, both for
the prebuilt ones and in a Tailwind build. It's worth being precise about what it does,
because it's the single most common thing to get wrong here: **it computes nothing.** It
takes the properties you give it and emits exactly those properties, in a block scoped to
`[data-theme="<name>"]`. No color is derived, no contrast is calculated, no missing value is
filled in.

That means a hand-written CSS file containing a `[data-theme="<name>"] { ... }` block and a
build that runs the same properties through `@plugin "daisyui/theme" { ... }` produce
identical output. There is no advantage to running a theme through the plugin, which is why
this page never asks you to. Write the CSS directly.

## Why your theme wins, whatever order it loads in

`mvp/static/css/django-mvp.css` places its theme blocks inside `@layer base`. Cascade layers
are resolved before specificity: any rule in an unlayered stylesheet beats any rule in a
layer, regardless of which one loads first in the page. A plain CSS file you write yourself
has no `@layer` wrapper, so it is unlayered.

The practical result: if your project defines `[data-theme="dracula"]` with different values
than the packaged one, yours applies, whether your stylesheet is linked before or after
`django-mvp.css` in `<head>`. Don't write ordering assumptions into your base template, such
as "load my theme file last so it wins." They aren't needed. If a future change reorders
your `<head>`, code that depends on load order breaks silently while code that doesn't keeps
working.

This also means you can override one of the shipped themes by name. Writing your own
`[data-theme="dracula"]` block replaces the packaged Dracula theme everywhere in your
project, without touching the package.

## Coloring the header, the dock and the sidebar

The header, the mobile dock and the sidebar paint themselves from the same properties as
everything else, and set their text color from them:

| Region | Class | Its background | Its text |
| --- | --- | --- | --- |
| Header | `.mvp-header` | `--root-bg`, the page's own background | `--color-base-content` |
| Mobile dock | `.mvp-dock` | `--root-bg` | `--color-base-content` |
| Sidebar, with its header and footer strips | `.mvp-sidebar` | `--color-base-300` | `--color-base-content` |

A theme that says nothing about them keeps the header and dock on the page's background and
the sidebar sunk below it. Every prebuilt theme renders that way.

A theme recolors a region by giving those properties other values inside it. The selector is
the theme's own, followed by the region's class:

```css
/* The header and dock raised above the page. */
[data-theme="sunrise"] .mvp-header,
[data-theme="sunrise"] .mvp-dock {
  --root-bg: var(--color-base-100);
}

/* The sidebar in a colour of its own. */
[data-theme="sunrise"] .mvp-sidebar {
  --color-base-300: oklch(84% 0.05 80);
}
```

The same block can set any other property from [the table above](#the-full-variable-table),
and it applies to everything drawn inside the region. That matters because DaisyUI's
components read the theme properties themselves and do not inherit a text color from the
element around them. A ghost button reads `--color-base-content`, the current item in a
menu reads `--color-neutral`, and a primary button reads `--color-primary`. Setting those
properties on the region is what reaches them:

```css
/* A dark header on a light page. */
[data-theme="sunrise"] .mvp-header,
[data-theme="sunrise"] .mvp-dock {
  --root-bg: oklch(35% 0.06 250);
  --color-base-100: oklch(35% 0.06 250);
  --color-base-200: oklch(30% 0.06 250);
  --color-base-300: oklch(48% 0.05 250);
  --color-base-content: oklch(98% 0.01 250);
}

/* A dark sidebar, with its current item drawn in a light color. */
[data-theme="sunrise"] .mvp-sidebar {
  --color-base-100: oklch(38% 0.02 80);
  --color-base-200: oklch(30% 0.02 80);
  --color-base-300: oklch(25% 0.02 80);
  --color-base-content: oklch(95% 0.01 80);
  --color-neutral: oklch(95% 0.01 80);
  --color-neutral-content: oklch(25% 0.02 80);
}
```

Three things to know when writing one of these blocks:

- **Change `--color-base-content` and `--color-base-100` together.** A dropdown or a modal
  that opens out of a region is drawn on `base-100` in `base-content`, read from where it
  sits. A block that sets only the text color leaves light text on the theme's light panel.
- **Write a value out when the same block changes the property you would read it from.**
  `--color-base-300: var(--color-neutral)` beside a new `--color-neutral` takes the new
  one, because both are resolved on the same element.
- **A region can hold a whole theme.** Any theme written for `[data-theme="<name>"]`, from
  DaisyUI's theme generator or from a prebuilt theme's file, works with the region's class
  added to the selector. Add `--root-bg` for the header and dock, since a theme file does
  not usually set it.

A prebuilt theme can be added to by name in the same way, without redefining its palette:

```css
[data-theme="nord"] .mvp-sidebar {
  --color-base-300: var(--color-base-200);
}
```

The classes are part of the package's interface, as are `.mvp-sidebar-header` and
`.mvp-sidebar-footer` for the sidebar's two strips. They stay on the regions when a project
passes [a background class of its own](layout.md#header-and-dock-background), which
replaces the packaged one and so stops that region following the theme.

## A line colour

Most of a theme's surfaces are told apart by which base colour they use, so a few things need a
colour that shows on all of them: the default button, the default alert, a border that identifies
something, and a rule. That colour is `--color-line`. The default button and alert fill from it
and `border-line` and `bg-line` draw it, so a theme can set it once:

```css
[data-theme="sunrise"] {
  --color-line: oklch(78% 0.04 80);
}
```

A theme that leaves it unset gets 85% of `base-300` mixed with 15% of `base-content`, worked
out where the colour is read. A block that gives a region its own surfaces therefore gets a line
that belongs to them, and only needs `--color-line` for a particular colour. A part of the page
in another theme starts without the page's value.

Coloured buttons and alerts set their own fill and never read it, so only the default ones change.

## Keeping the page on another surface

`--root-bg` moves the page. The header, the mobile dock and the filter panel's column follow
it, and everything else keeps its meaning. To put a theme's page back on `base-100`, as it was
before the colours had fixed meanings, and the sidebar on `base-200`:

```css
[data-theme="sunrise"] {
  --root-bg: var(--color-base-100);
}

[data-theme="sunrise"] .mvp-sidebar {
  --color-base-300: var(--color-base-200);
}
```

Cards are then drawn on the same colour as the page, and stand off it by their shadow only.

## A text value for a brand colour

A theme has one value per colour, and DaisyUI uses that value both as a fill and as text. Many
brand colours are good fills and poor text: a mid amber with dark text on it looks right as a
button and is unreadable as a link on a pale page.

Each of `primary`, `secondary` and `accent` takes an optional second value for the places it is
drawn as text:

```css
[data-theme="sunrise"] {
  --color-primary: #d9922f;       /* 2.5:1 on a pale page, 6.1:1 under its dark content */
  --color-primary-content: #2b2118;
  --color-primary-text: #8a4b0c;  /* 6.5:1 on the same page */
}
```

| Reads the text value | Keeps the fill |
| --- | --- |
| `text-primary`, including `hover:text-primary` and `text-primary/50` | `bg-primary`, `border-primary` |
| `link-primary`, darkened on hover as before | `btn-primary`, `badge-primary` |
| The text of an outline, dash, soft or ghost `btn-primary`, and of a `btn-link` | The border and the tint of those buttons, and the fill they take on hover |
| The text of an outline, dash or soft `badge-primary`, and an outline badge's border, which follows its text | The tint of a soft badge |

`--color-secondary-text` and `--color-accent-text` do the same for their colours. A theme that
sets none of them renders as it did before they existed, since each falls back to the fill.

The package checks nothing about the value. Work out its contrast against every surface you draw
it on, as with any other colour in a theme.

A text value belongs to the theme that set it. A region can set one of its own, in the block that
[recolors the region](#coloring-the-header-the-dock-and-the-sidebar). Set the text value in any
block that changes the fill, because a text value already in force keeps applying there. Part of a
page drawn with a `data-theme` of its own starts without one, so it doesn't pick up the page's
value.

## Fonts

A theme can set its type families. `--font-sans` is the page's body font, `--font-serif` and
`--font-mono` are the fonts [the variable table](#the-full-variable-table) names them for, and
`--font-heading` is the font of headings:

```css
[data-theme="sunrise"] {
  --font-sans: "Inter", ui-sans-serif, system-ui, sans-serif;
  --font-heading: "Source Serif", ui-serif, Georgia, serif;
}
```

`--font-heading` applies to `h1` to `h6`, and to the elements that act as headings without being
one: `card-title`, `collapse-title`, `fieldset-legend`, `footer-title`, `menu-title`, `stat-title`
and the site name at the top of the sidebar. That covers the page title and every other heading
the shell draws. Left unset, each of them inherits the font around it, so a theme that sets only
`--font-sans` changes its headings too, and a theme that sets neither renders as before. A
`font-*` utility on an element still wins.

Set `--font-sans` and its siblings on the theme's own `[data-theme="<name>"]` block. The body
font is resolved once on `<html>`, so setting `--font-sans` in a region's block doesn't change that
region's text. `--font-heading` is read at each heading, so a region can set its own.

**Serve the font files yourself.** A theme's `@font-face` rules go in the same stylesheet, with the
files in your project's static directory, so that the browser fetches them from your own site and
visitors' addresses go to no third party:

```css
@font-face {
  font-family: "Source Serif";
  src: url("../fonts/source-serif-4.woff2") format("woff2");
  font-weight: 200 900;
  font-display: swap;
}
```

The address is relative to the stylesheet, so `static/css/theme-sunrise.css` finds
`static/fonts/source-serif-4.woff2`, and Django's static file storage rewrites it if it hashes file
names. WOFF2 is all a current browser needs. The file is only downloaded by a page that uses the
font, so a font in a theme nobody has selected costs nothing. Avoid a stylesheet link to a font
service, which sends every visitor's address to that service.

Fonts are separate from the icons: the base template loads the Bootstrap Icons webfont from a CDN
until you [point it elsewhere](icons.md#where-the-icons-come-from).

## A worked example

Starting from a project with nothing custom, here's every step to a rendering custom theme
called `sunrise`.

**1. Write the CSS file.** Create `static/css/theme-sunrise.css` in your project:

```css
[data-theme="sunrise"] {
  color-scheme: light;
  --color-base-100: oklch(98% 0.01 80);
  --color-base-200: oklch(94% 0.02 80);
  --color-base-300: oklch(89% 0.03 80);
  --color-base-content: oklch(25% 0.02 80);
  --color-primary: oklch(68% 0.19 40);
  --color-primary-content: oklch(98% 0.01 40);
  --color-secondary: oklch(70% 0.15 350);
  --color-secondary-content: oklch(98% 0.01 350);
  --color-accent: oklch(75% 0.17 200);
  --color-accent-content: oklch(20% 0.02 200);
  --color-neutral: oklch(30% 0.02 80);
  --color-neutral-content: oklch(95% 0.01 80);
  --color-info: oklch(74% 0.16 232);
  --color-info-content: oklch(29% 0.07 232);
  --color-success: oklch(76% 0.18 163);
  --color-success-content: oklch(37% 0.08 163);
  --color-warning: oklch(82% 0.19 84);
  --color-warning-content: oklch(41% 0.11 84);
  --color-error: oklch(71% 0.19 13);
  --color-error-content: oklch(27% 0.11 13);
  --radius-selector: 1rem;
  --radius-field: 0.5rem;
  --radius-box: 1rem;
  --size-selector: 0.25rem;
  --size-field: 0.25rem;
  --border: 1px;
  --depth: 1;
  --noise: 0;
}
```

There's nothing DaisyUI-specific about this file beyond the property names. It's plain CSS.
A good way to start one is to copy the values from a shipped theme you like and adjust them.
Every file under `node_modules/daisyui/theme/` (if you have the front-end toolchain
installed) or [daisyui.com's theme list](https://daisyui.com/docs/themes/) is a working
example in the same shape.

**2. Load the stylesheet.** Override the `styles` block in your project's own `base.html`,
which already extends `mvp/base.html` (see [Getting Started](getting-started.md)):

```django
{% extends "mvp/base.html" %}
{% load static %}
{% block styles %}
  {{ block.super }}
  <link rel="stylesheet" href="{% static 'css/theme-sunrise.css' %}" />
{% endblock styles %}
```

`{{ block.super }}` keeps the packaged stylesheet loading. Because your theme file is
unlayered, its position in `<head>` relative to `django-mvp.css` doesn't matter (see
[why your theme wins](#why-your-theme-wins-whatever-order-it-loads-in) above).

**3. Name it in configuration.** Set it as the applied theme, offer it in the switcher, or
both:

```python
MVP_CONFIG = {
    "theme": {
        "default": "sunrise",
        "choices": ["light", "dark", "sunrise"],
    },
}
```

**4. Reload the page.** The application renders in `sunrise`, and if you added it to
`choices`, it's now an entry in `<c-mvp.actions.theme-controller />`.

No template was overridden, no build tool was installed, and nothing was fetched from
outside your project.

## When your theme does not appear

A theme name that matches no `[data-theme="<name>"]` block anywhere on the page is not an
error. django-mvp does not validate theme names against anything, so a typo or an unloaded
stylesheet doesn't raise. It can't: your own theme lives in a CSS file the package never
reads, so there is no list to check a name against that wouldn't also reject every custom
theme. Instead the document falls back to the default theme through a zero-specificity
`:where(:root)` rule and renders normally, just not in the theme you expected.

If your theme isn't showing up, check, in order:

1. **The name matches exactly.** `MVP_CONFIG["theme"]["default"]` (or the entry in
   `choices`) must be character-for-character the same as the `data-theme` value in your
   CSS file.
2. **The stylesheet is actually loading.** Check your browser's network tab for the file, or
   view source for the `<link>` tag. A missing `{{ block.super }}` in a `styles` block
   override silently drops the packaged stylesheet too, so check for that while you're
   there.
3. **The selector is right.** It must be `[data-theme="sunrise"]`, not `.sunrise` or
   `#sunrise`.

Because nothing errors, the CSS itself is rarely the actual fault. Check the name and that
the file is loading before you start debugging the properties inside it.

## Where theming stops

A theme controls color, type families, corner radius, border width, base sizing, and the
depth/noise surface effects listed in the [variable table](#the-full-variable-table) above.
That's the full extent of what it can change. It never adds, removes or rearranges markup, which is why
switching a theme never requires a template change (see the *Theme* entry in
[CONTEXT.md](../CONTEXT.md)).

Spacing, the type scale, which components appear where, and a one-off visual change to a single
component are none of a theme's business. Those go through a component attribute or a
template override instead. See [Styling & Extending the CSS](styling.md) for the
attribute-and-override model, and [Components](components.md) for what each component
exposes.
