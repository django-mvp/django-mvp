# Utility Class Reference

The packaged stylesheet (`mvp/static/css/django-mvp.css`) ships daisyUI's component set
alongside a set of plain Tailwind utility classes, built in explicitly rather than
discovered by scanning your templates. This page lists what's available.

Utilities that act on the inline axis ship in their logical form only — `ps-4` rather than
`pl-4`, `me-2` rather than `mr-2`, `text-start` rather than `text-left`. A logical utility
follows the writing direction, so a layout built from them reads correctly in an RTL locale
without a second set of rules. The physical forms are not in the packaged stylesheet. If you
build your own with `python manage.py mvp_tailwind`, Tailwind scans your templates and emits
whatever you actually use, physical forms included.

## Responsive utilities (base, `md:`, `lg:`, `xl:`)

These ship at four breakpoint variants each: unprefixed, `md:`, `lg:`, `xl:`.

| Group | Classes |
| --- | --- |
| Display | `block`, `inline-block`, `inline`, `flex`, `inline-flex`, `grid`, `hidden` |
| Flexbox | `flex-row`, `flex-col`, `flex-wrap`, `flex-nowrap`, `flex-1`, `flex-auto`, `flex-none`, `grow`, `grow-0`, `shrink`, `shrink-0` |
| Flex/grid alignment | `items-{start,center,end,baseline,stretch}`, `justify-{start,center,end,between,around,evenly}`, `content-{start,center,end,between,around,evenly}`, `self-{auto,start,center,end,stretch}` |
| Grid | `grid-cols-{1..12}`, `col-span-{1..12,full}` |
| Gap | `gap-{0,1,2,3,4,5,6,8,10,12}`, `gap-x-*`, `gap-y-*` (same scale) |
| Padding | `p-`, `px-`, `py-`, `pt-`, `pb-`, `ps-`, `pe-` at `{0,1,2,3,4,5,6,8,10,12}` |
| Margin | `m-`, `mx-`, `my-`, `mt-`, `mb-`, `ms-`, `me-` at `{0,1,2,3,4,5,6,8,10,12}`, plus `m-auto`, `mx-auto`, `my-auto` |
| Width / height | `w-{auto,full,screen,min,max,fit,1/2,1/3,2/3,1/4,3/4}`, `h-{auto,full,screen,min,max,fit}` |
| Max/min width / height | `max-w-{xs,sm,md,lg,xl,2xl,3xl,4xl,5xl,6xl,7xl,full,none,prose}`, `min-w-{0,full}`, `max-h-{full,screen}`, `min-h-{0,full,screen}` |
| Text alignment | `text-{start,center,end,justify}` |
| Text size | `text-{xs,sm,base,lg,xl,2xl,3xl,4xl,5xl,6xl}` |
| Position | `static`, `relative`, `absolute`, `fixed`, `sticky` |
| Inset | `inset-0`, `inset-x-0`, `inset-y-0`, `top-{0,auto}`, `bottom-{0,auto}`, `start-{0,auto}`, `end-{0,auto}` |
| Overflow | `overflow-{auto,hidden,visible,scroll}`, `overflow-x-auto`, `overflow-y-auto` |

## Base-only utilities

These ship unprefixed only.

| Group | Classes |
| --- | --- |
| Z-index | `z-{0,10,20,30,40,50,auto}` |
| Border width | `border`, `border-0`, `border-2`, `border-4`, `border-8`, `border-t`, `border-b`, `border-s`, `border-e` |
| Border radius | `rounded-{none,sm,md,lg,xl,2xl,3xl,full}`, `rounded-{t,b,s,e}-{sm,md,lg,xl,full}` |
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

`hover:` and `focus-visible:` variants of the full colour palette above
(`hover:bg-primary`, `focus-visible:border-error`, ...), plus `opacity-75`, `opacity-100`
and `underline` under both prefixes.

## The daisyUI component set

The packaged stylesheet ships daisyUI 5's **complete component set** — every component,
not just the ones django-mvp's own templates use — so classes like `carousel`, `kbd`,
`chat`, `timeline`, and the rest of the [daisyUI component
list](https://daisyui.com/components/) work out of the box. Every prebuilt daisyUI theme
ships too — `light`, `dark`, `dracula`, `synthwave` and the rest — so switching between
them is a `data-theme` value rather than another build. See
[ADR 0010](adr/0010-every-prebuilt-theme-ships-in-the-package.md). A theme of your own
needs no build either, just a CSS file — see [Theming](theming.md).
