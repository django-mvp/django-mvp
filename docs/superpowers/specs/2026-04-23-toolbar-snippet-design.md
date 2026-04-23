# Toolbar Snippet Design

**Date:** 2026-04-23
**Status:** Approved
**Format:** Raw HTML snippet using Bootstrap 5 utility classes

---

## Overview

A fully responsive toolbar HTML snippet with two named sections — `start` and `end`. Suitable for use as a page heading, content toolbar, or card header. Spans the full width of its container. No custom CSS; relies entirely on Bootstrap 5 utility classes.

---

## Structure

The toolbar is a single `<div>` containing two child `<div>`s.

### Root container

```
d-flex  flex-column  flex-{sm}-row  flex-wrap  align-items-stretch  align-items-{sm}-center  gap-2
```

- `d-flex` — flex container
- `flex-column` / `flex-column-reverse` — controls mobile stack order (see below)
- `flex-sm-row` — switches to horizontal layout on desktop (≥576px)
- `flex-wrap` — allows end to fall to a new line when start is too wide
- `align-items-stretch` — on mobile, sections span full width
- `align-items-sm-center` — on desktop, sections are vertically centered
- `gap-2` — consistent spacing between sections and, when wrapped, between rows

### Start section

```
flex-grow-1  [min-width:0 inline style]
```

- `flex-grow-1` — absorbs available space, pushing end as far right as possible
- `min-width: 0` — prevents long content from overflowing (required for flex children with text truncation)
- Content: title text, breadcrumbs, subtitles, or any inline start content

### End section

Two modes, selected by swapping classes on the end `<div>`:

| Mode | Classes on end `<div>` | Children |
|---|---|---|
| `wrap` | `d-flex align-items-center gap-2 flex-wrap` | No extra classes needed |
| `scroll` | `d-flex align-items-center gap-2 flex-nowrap overflow-x-auto` + `min-width:0` | Each child gets `flex-shrink-0` |

---

## Responsive Behavior

### Desktop (≥576px, `sm` breakpoint)

1. Start and end sit on the same row, vertically centered.
2. Start grows to fill available space; end uses only the space its content requires.
3. If start's content is wide enough that combined minimum widths exceed the container, end wraps to the row below — start and end are then full-width and stacked.

### Mobile (<576px)

- Sections stack vertically.
- **Default order:** start (title) on top, end (actions) below — `flex-column` on root.
- **Reversed order:** end (actions) on top, start (title) below — `flex-column-reverse` on root.
- Stack order is a configuration choice at the point of use; both forms are valid.

---

## Configurations

| Configuration | How to apply |
|---|---|
| End wraps when overflow | `flex-wrap` on end `<div>` (default) |
| End scrolls horizontally | `flex-nowrap overflow-x-auto` on end `<div>`; `flex-shrink-0` on each child |
| Mobile: title first | `flex-column` on root `<div>` |
| Mobile: actions first | `flex-column-reverse` on root `<div>` |

---

## Reference Snippet

```html
<!-- Toolbar: wrap mode, title-first mobile -->
<div class="d-flex flex-column flex-sm-row flex-wrap align-items-stretch align-items-sm-center gap-2">

  <!-- Start: title / breadcrumb area -->
  <div class="flex-grow-1" style="min-width:0">
    <span class="fw-semibold fs-5">Page Title</span>
  </div>

  <!-- End: action buttons, inputs, icons — wrap mode -->
  <div class="d-flex align-items-center gap-2 flex-wrap">
    <button class="btn btn-sm btn-outline-secondary">Filter</button>
    <input class="form-control form-control-sm" style="width:160px" placeholder="Search…">
    <button class="btn btn-sm btn-primary">+ New</button>
  </div>

</div>

<!-- Toolbar: scroll mode -->
<div class="d-flex flex-column flex-sm-row flex-wrap align-items-stretch align-items-sm-center gap-2">
  <div class="flex-grow-1" style="min-width:0">
    <span class="fw-semibold fs-5">Page Title</span>
  </div>
  <div class="d-flex align-items-center gap-2 flex-nowrap overflow-x-auto" style="min-width:0">
    <button class="btn btn-sm btn-outline-secondary flex-shrink-0">Filter</button>
    <button class="btn btn-sm btn-outline-secondary flex-shrink-0">Sort</button>
    <input class="form-control form-control-sm flex-shrink-0" style="width:160px" placeholder="Search…">
    <button class="btn btn-sm btn-primary flex-shrink-0">+ New</button>
  </div>
</div>

<!-- Toolbar: actions-first on mobile (flex-column-reverse) -->
<div class="d-flex flex-column-reverse flex-sm-row flex-wrap align-items-stretch align-items-sm-center gap-2">
  <div class="flex-grow-1" style="min-width:0">
    <span class="fw-semibold fs-5">Page Title</span>
  </div>
  <div class="d-flex align-items-center gap-2 flex-wrap">
    <button class="btn btn-sm btn-outline-secondary">Filter</button>
    <button class="btn btn-sm btn-primary">+ New</button>
  </div>
</div>
```

---

## Design Rationale

- **No custom CSS** — all behavior is driven by Bootstrap 5 flex utilities. Nothing to override or maintain.
- **Natural wrap point** — flexbox computes break based on content minimum widths, so the wrap happens exactly when needed without any hardcoded breakpoint values.
- **`min-width: 0` on start** — without this, flex children containing long text can force the container to overflow. This inline style is required on the start section in all modes, and also on the end section in scroll mode (to allow the `overflow-x-auto` to take effect inside a flex child). These are the only non-utility declarations required.
- **`flex-shrink-0` in scroll mode** — prevents action items from compressing to zero in the nowrap scroll container.
- **Breakpoint choice (`sm`, 576px)** — aligns with Bootstrap's smallest named breakpoint, ensuring mobile phones stack and desktop/tablet layouts use the inline form.

---

## Out of Scope

- Padding, border, background — entirely determined by the surrounding context (page header, card header, etc.)
- Typography size for start content — consumer's responsibility
- Icon sizing in end section — consumer's responsibility
