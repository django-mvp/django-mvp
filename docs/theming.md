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

Both are DaisyUI's, not palettes this package drew. That is on purpose: a theme is the entire
visible surface of your application, and the identity on it should be one you chose rather than
one your dependency picked. The package's job is the mechanism and the components; the palette is
yours.

Which means **the applied theme carries no contrast guarantee, including the default**. The
prebuilt themes are DaisyUI's files, and most of them put at least one brand colour below the WCAG
AA text floor against their own page background — `light` renders `text-error` at 2.87:1, which is
what a form validation message is drawn in. That matters because `text-*` and `border-*` render
the raw fill value rather than a pairing someone checked.

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

## The full variable table

Every theme may set the following properties. A theme does not have to set all of them.
A property left unset simply has no value for `var()` to resolve, so a theme that omits one
loses whatever visual effect that property controls, not the whole theme.

`color-scheme` is a standard CSS property, not a custom one, but it lives in the same block
and every shipped theme sets it.

| Property | Controls |
| --- | --- |
| `color-scheme` | Whether the browser renders its own UI (scrollbars, form controls, the built-in date picker) as `light` or `dark`, so native chrome doesn't clash with the theme. |
| `--color-base-100` | The page's primary background surface. |
| `--color-base-200` | A background surface one step more contrasted than `base-100`, used for subtle separation (a card on the page, a table row). |
| `--color-base-300` | A background surface two steps more contrasted than `base-100`, for stronger separation (a well, a disabled state). |
| `--color-base-content` | The default text and icon color on top of the base surfaces. |
| `--color-primary` | The theme's brand color, used for primary buttons, links and focus states. |
| `--color-primary-content` | Text and icon color for content placed on top of `primary`. |
| `--color-secondary` | A second brand color for elements that shouldn't compete with `primary`. |
| `--color-secondary-content` | Text and icon color for content placed on top of `secondary`. |
| `--color-accent` | A third, distinct color for drawing attention (badges, highlights). |
| `--color-accent-content` | Text and icon color for content placed on top of `accent`. |
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

This list was checked against a shipped theme definition rather than written from memory, and
a test keeps it in step with the installed DaisyUI version: it extracts every custom property
name from a shipped theme file and fails if one is missing from this table.

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
`choices`, it's now an entry in `<c-actions.theme-controller />`.

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

A theme controls color, corner radius, border width, base sizing, and the depth/noise
surface effects listed in the [variable table](#the-full-variable-table) above. That's the
full extent of what it can change. It never adds, removes or rearranges markup, which is why
switching a theme never requires a template change (see the *Theme* entry in
[CONTEXT.md](../CONTEXT.md)).

Spacing, typography, which components appear where, and a one-off visual change to a single
component are none of a theme's business. Those go through a component attribute or a
template override instead. See [Styling & Extending the CSS](styling.md) for the
attribute-and-override model, and [Components](components.md) for what each component
exposes.
