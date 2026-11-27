# Research: Arrange the application shell with a layout code

The full investigation belongs to the build. This file holds only what was run before the
specification was put up for approval.

## Assumptions checked

- **django-mvp-layout 0.3.0 is released.** Tagged and published 2026-11-27, with
  https://github.com/django-mvp/django-mvp-layout/pull/24 (the slide timing and the drawer width)
  merged into it.
- **The sidebar takes `behavior`, `width`, `breakpoint`, `collapse`, `persist` and `label`.** Read
  in 0.3.0's `cotton/layout/sidebar.html` and `Sidebar.settle`. `behavior` accepts `auto`,
  `docked` and `overlay`, `collapse` accepts `offcanvas`, `icons` and `none`, and `breakpoint`
  accepts `sm` to `2xl`, defaulting to `lg` on the left and `xl` on the right. Any other value
  raises `LayoutOptionError` when the sidebar is drawn, which is why the system check reads them.
- **A sidebar with no content draws nothing.** 0.3.0's `cotton/layout/sidebar.html` renders the
  `aside` only when its slot is not empty. A page that leaves `app.secondary_sidebar` empty has no
  right sidebar.
- **The remembered state is read on the server.** `Sidebar.settle` reads the cookie
  `mvpl-<persist>`, accepts `open` or `closed` and ignores anything else, and forces `open` under
  `collapse: "none"`. On the prototype, http://devserver:8002/products/ drawn with
  `mvpl-mvp-sidebar=closed` returns the left sidebar with `data-mvpl-state="closed"`, and with
  `open` returns `open`.
- **The parser is public.** `mvp_layout.view.LayoutView.parse` reads a code and raises
  `LayoutViewError` on anything else, so the system check can call it.
- **The rail classes and the state attributes are documented.** `.mvpl-rail-hide` and
  `.mvpl-rail-only` are in 0.3.0's `layout.css`. `data-mvpl-state`, `data-mvpl-mode` and
  `data-mvpl-when` are listed in its `docs/developer/styling.md`, and the `mvpl:change` event in
  `docs/developer/scripting.md`.
- **The prototype's shell screens are served.** http://devserver:8002/products/ and
  http://devserver:8002/layout/full-page/ return 200.
- **`<c-mvp.page fill>` exists on `main`.** `cotton/mvp/page/index.html` takes `fill` and marks the
  page `mvp-page-fill`.
- **The dock's toggle on `main` names the drawer's checkbox.** `cotton/mvp/dock/item.html` passes
  `toggle` to daisy-cotton's dock item as a checkbox id, and `docs/navigation.md` and the demo's
  `cotton/app/dock.html` use `mvp-app-toggle`. The new shell has no checkbox, so FR-023 is needed.
- **The language control is harmless on a project without translations.**
  `cotton/mvp/actions/language_switcher_modal.html` draws nothing without `request.LANGUAGE_CODE`
  or a `set_language` URL.
