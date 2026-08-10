# Utility Class Reference

The packaged stylesheet (`mvp/static/css/django-mvp.css`) ships more than daisyUI's
component set. It also includes a curated set of plain Tailwind utility classes, generated
into the build explicitly rather than discovered by scanning your templates. This page
lists every one of them, so you know what's available without running your own Tailwind
build. See [Styling](styling.md) for the two-tier build model this fits into.

## Why a curated list, not "everything"

Tailwind only generates the classes it finds referenced somewhere in scanned source. The
packaged stylesheet is scanned against django-mvp's own templates and daisyUI's component
set, not yours, so a raw `class="grid grid-cols-3"` in your own project's template
wouldn't normally produce anything. This pack closes that gap for a chosen set of common
layout, spacing, sizing, typography, colour and state utilities, force-included in the
build regardless of what django-mvp's own source uses.

**This does not remove the need for your own Tailwind pipeline — it reduces it.** Anything
outside the list below, and in particular any arbitrary value (`w-[37px]`,
`bg-[#123456]`, `grid-cols-[2fr_1fr]`), can never work from a pre-built stylesheet: those
classes don't exist until a Tailwind build sees them in your source and generates them.
If your project needs values outside this list, follow [Tier 2 in the styling
guide](styling.md#tier-2-build-your-own-stylesheet).

## Responsive utilities (base, `md:`, `lg:`, `xl:`)

These ship at four breakpoint variants each: unprefixed, `md:`, `lg:`, `xl:`. There is no
`sm:` and no `2xl:` variant of anything in this pack.

| Group | Classes |
| --- | --- |
| Display | `block`, `inline-block`, `inline`, `flex`, `inline-flex`, `grid`, `hidden` |
| Flexbox | `flex-row`, `flex-col`, `flex-wrap`, `flex-nowrap`, `flex-1`, `flex-auto`, `flex-none`, `grow`, `grow-0`, `shrink`, `shrink-0` |
| Flex/grid alignment | `items-{start,center,end,baseline,stretch}`, `justify-{start,center,end,between,around,evenly}`, `content-{start,center,end,between,around,evenly}`, `self-{auto,start,center,end,stretch}` |
| Grid | `grid-cols-{1..12}`, `col-span-{1..12,full}` |
| Gap | `gap-{0,1,2,3,4,5,6,8,10,12}`, `gap-x-*`, `gap-y-*` (same scale) |
| Padding | `p-`, `px-`, `py-`, `pt-`, `pr-`, `pb-`, `pl-` at `{0,1,2,3,4,5,6,8,10,12}` |
| Margin | `m-`, `mx-`, `my-`, `mt-`, `mr-`, `mb-`, `ml-` at `{0,1,2,3,4,5,6,8,10,12}`, plus `m-auto`, `mx-auto`, `my-auto` |
| Width / height | `w-{auto,full,screen,min,max,fit,1/2,1/3,2/3,1/4,3/4}`, `h-{auto,full,screen,min,max,fit}` |
| Max/min width / height | `max-w-{xs,sm,md,lg,xl,2xl,3xl,4xl,5xl,6xl,7xl,full,none,prose}`, `min-w-{0,full}`, `max-h-{full,screen}`, `min-h-{0,full,screen}` |
| Text alignment | `text-{left,center,right,justify}` |
| Text size | `text-{xs,sm,base,lg,xl,2xl,3xl,4xl,5xl,6xl}` — stops at `text-6xl`. `text-7xl`, `text-8xl`, `text-9xl` are not shipped |
| Position | `static`, `relative`, `absolute`, `fixed`, `sticky` |
| Inset | `inset-0`, `inset-x-0`, `inset-y-0`, `top-{0,auto}`, `right-{0,auto}`, `bottom-{0,auto}`, `left-{0,auto}` |
| Overflow | `overflow-{auto,hidden,visible,scroll}`, `overflow-x-auto`, `overflow-y-auto` |

## Base-only utilities

These ship unprefixed only — no `md:`/`lg:`/`xl:` variant, because a breakpoint variant of
a z-index, border, or typography utility isn't something a project has ever needed here.

| Group | Classes |
| --- | --- |
| Z-index | `z-{0,10,20,30,40,50,auto}` |
| Border width | `border`, `border-0`, `border-2`, `border-4`, `border-8`, `border-t`, `border-r`, `border-b`, `border-l` |
| Border radius | `rounded-{none,sm,md,lg,xl,2xl,3xl,full}`, `rounded-{t,r,b,l}-{sm,md,lg,xl,full}` |
| Opacity | `opacity-{0,25,50,75,100}` |
| Font family | `font-{sans,serif,mono}` |
| Font weight | `font-{light,normal,medium,semibold,bold,extrabold}` |
| Line height | `leading-{none,tight,snug,normal,relaxed,loose}` |
| Letter spacing | `tracking-{tight,normal,wide}` |
| Text treatment | `truncate`, `whitespace-nowrap`, `break-words`, `italic`, `uppercase`, `lowercase`, `capitalize`, `underline`, `no-underline` |
| Cursor | `cursor-{pointer,not-allowed,default}` |
| Interaction | `transition`, `select-none`, `pointer-events-none`, `align-middle`, `duration-{150,200,300}` |
| Object fit | `object-{cover,contain,fill}` |
| List style | `list-{none,disc,decimal}` |

## Colour utilities (base only)

daisyUI's semantic colour palette as plain Tailwind `bg-`/`text-`/`border-` utilities:

```
primary, secondary, accent, neutral, info, success, warning, error,
primary-content, secondary-content, accent-content, neutral-content,
info-content, success-content, warning-content, error-content,
base-100, base-200, base-300, base-content
```

So `bg-primary`, `text-error`, `border-base-300`, and so on for every name above, are all
available on any element, not just inside a daisyUI component.

## State utilities

`hover:` and `focus-visible:` variants of the full colour palette above (`hover:bg-primary`,
`focus-visible:border-error`, ...), plus a small state-only set: `hover:opacity-75`,
`hover:opacity-100`, `hover:underline` (and the same three under `focus-visible:`).

## What's deliberately not shipped

**Shadow utilities are not part of this pack.** None of these are included:

- `shadow-none`, `shadow-sm`, `shadow-md`, `shadow-lg`, `shadow-xl`, `shadow-2xl`, `shadow-inner`
- `hover:shadow-*`, `focus-visible:shadow-*`

This isn't an oversight. A loose `shadow-*` class on an arbitrary element is one of the
most reliable ways to make a page look inconsistent, and it works against django-mvp's
goal of a page that looks assembled from one system rather than bolted together. The
components that need a shadow carry it themselves:

- Cards
- Dropdown panels
- The modal box
- Toast messages

You don't add the shadow to those. You shouldn't add one anywhere else either. If you
inspect the compiled CSS and find a `shadow-sm` or `shadow-lg` rule anyway, that's this
internal usage, not a supported utility. Don't build on it in your own templates: it can
disappear without notice if those components change.

Beyond shadows, anything not listed on this page is out of scope for the same reason
every pre-built stylesheet has a ceiling: Tailwind only ships a class it was told to
generate, and arbitrary values (`w-[37px]`, `bg-[#123456]`, `grid-cols-[2fr_1fr]`) are
never on that list because they can't be predicted ahead of time.

## The daisyUI component set

Alongside these utilities, the packaged stylesheet ships daisyUI 5's **complete component
set** — every component, not just the ones django-mvp's own templates use — so classes
like `carousel`, `kbd`, `chat`, `timeline`, and the rest of the [daisyUI component
list](https://daisyui.com/components/) work out of the box. The only exception is themes:
only the default light/dark themes are included, not the ~30 additional named themes
(`dracula`, `synthwave`, ...), which are one CSS file you can add yourself — see
[Theming](styling.md#theming).

For django-mvp's own components (`c-card`, `c-button`, `c-dropdown`, ...) built on top of
this CSS, see the [Component Reference](components.md).
