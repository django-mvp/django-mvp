# Planning notes: Arrange the application shell with a layout code

Notes for research and planning to answer by name. None of them is settled by this file.

## The prototype

1. This feature is specified from a prototype. Branch `prototype-layout`, prototype issue
   https://github.com/django-mvp/django-mvp/issues/719, served on http://devserver:8002. Read
   `PROTOTYPE.md` at the branch's root in full. This feature is its section 1, "The shell on a
   layout code", together with every entry under "Decisions" and "Decided on my own" that
   concerns the shell, the sidebars, the header and its toolbar, the brand, local navigation and
   the dock.
2. The build starts once https://github.com/django-mvp/django-mvp/issues/750 has merged. That
   change adds the django-mvp-layout 0.3.0 dependency, the shared heading and footer rows in
   `cotton/mvp/box/`, the box styles, and the card, the dialog and the bottom sheet built from
   parts. This feature builds on top of it and does not redo any of it.

## The look is ported, never redrawn

3. These files from the prototype land at the same paths on `main`. The plan names each one, and
   the design review fails a plan that redraws a screen the prototype already has:

   | File on `prototype-layout` | Lands in |
   |---|---|
   | `mvp/templates/mvp/base.html`, the `app` block | Same path |
   | `mvp/templates/cotton/app/header.html` | Same path |
   | `mvp/templates/cotton/app/navbar.html` | Same path |
   | `mvp/templates/cotton/app/sidebar/header.html` | Same path |
   | `mvp/templates/cotton/app/sidebar/index.html` | Same path |
   | `mvp/templates/cotton/app/sidebar/footer.html` | Same path |
   | `mvp/templates/menus/dock/item.html` | Same path |
   | `mvp/config.py` (`layout.view`, `sidebar`, `secondary_sidebar`, `navbar.actions`) | Same path |
   | `mvp/tailwind/base.css`, the shell's part: the rail-aware variants, the rail, the full-page rules | Same path |

   The prototype also adds `cotton/mvp/brand/mark.html`, `menus/local/container.html`,
   `menus/local/item.html`, `mvp.renderers.LocalNavigationRenderer`, the account button in
   `cotton/mvp/user/sidebar_menu.html` and the `size` on `cotton/mvp/actions/login.html`. They are
   ported the same way.

4. `main` has moved since the prototype branched (2026-11-24). The port keeps `main`'s changes:
   - **The dock.** https://github.com/django-mvp/django-mvp/pull/725 added `c-mvp.dock.item`, a
     dock declared in a template, whose `toggle` names the drawer's checkbox `mvp-app-toggle`, and
     deprecated the menu-driven dock. The prototype only changed the menu-driven dock's item. Both
     must open the shell's left sidebar (FR-023), and `docs/navigation.md` and the demo's own
     `cotton/app/dock.html` must stop naming the checkbox.
   - **The header's site name.** The same pull request added `layout.navbar.mobile.site_name`. The
     prototype shows the name always, through the brand mark (Sam, 2026-11-27), so that setting is
     removed (FR-009).
   - **The sheet.** https://github.com/django-mvp/django-mvp/pull/732 changed the sheet's menu.
     That is issue 750's to keep, not this feature's.
   - **The head portal.** https://github.com/django-mvp/django-mvp/pull/748 added
     `<c-portal name="head" />` to `mvp/base.html`, outside the `app` block. Keep it.

## Shared pieces

5. **The rail-aware variants `is-drawer-open` / `is-drawer-close`.** In `mvp/tailwind/base.css`
   as `@custom-variant`. Kept, keyed to `.mvpl-sidebar[data-mvpl-rail]`. Built by this feature.
6. **Rail labels.** Today the `mvp-sidebar--icons` rules in `mvp/tailwind/base.css` and the
   package's `.mvpl-rail-hide` / `.mvpl-rail-only` both hide labels in the rail. One mechanism
   remains: the package's classes, used by django-mvp's menu. Built by this feature (FR-012).
7. **Parsing the code.** The package's `LayoutView.parse`. A django-mvp system check on
   `layout.view` calls the package's own parser, never a copy of it. Built by this feature
   (FR-004). The specification widens the check to both sidebars' options, read against the
   package's own choices (`Sidebar.choose` and its tuples in `mvp_layout.templatetags.mvp_layout`),
   for the reason in `decisions.md`.

## Duplication to remove

8. This feature removes:
   - the `.drawer[data-mvp-breakpoint…]` rules in `mvp/tailwind/base.css` for
     `mvp-sidebar-hidden-only` and `mvp-sidebar-toggle`, which match nothing once the drawer is
     gone
   - `mvp/layout.py` (`LayoutConfig`), which resolves breakpoint, collapse and sticky for a shell
     that no longer exists
   - `cotton/app/index.html`, `cotton/mvp/layout/sidebar/index.html`, the layout store
     (`assets/js/layout.js`) and the demo page `/layout/store/`, listed under "Faked or skipped" in
     `PROTOTYPE.md`
   - `layout.navbar.sticky`, which the prototype no longer reads

## Questions for research

9. **Where `data-mvp-breakpoint` sits.** The prototype puts it on a `<div class="contents">` in
   `mvp/base.html`'s `app` block. `specs/029-layout-state-store` FR-017 asks for the attribute on an
   element a component renders, so a project that overrides the base template keeps it. Decide
   which holds and say why.
10. **The header's height.** `assets/js/header_height.js` publishes the height only while the
    header's computed position is `sticky`. Check that this still holds for the layout's header
    under an upper-case `H`, or change what it reads (FR-005).
11. **The right sidebar's button without script.** The prototype always draws the header's right
    toggle and the layout package's script hides it when there is no right sidebar. FR-013 asks
    for no control on a page without one. Decide whether the server leaves it out.
12. **The drawer's width.** Sam settled the main sidebar at 20rem as a drawer and 16.25rem beside
    the page, through django-mvp-layout's `--mvpl-drawer-w` (its default) and `layout.sidebar.width`.
    `--mvp-sidebar-width` and its touch sizing are no longer read and go.
13. **The default toolbar.** The prototype's package default for `layout.navbar.actions` holds the
    theme control only, and its demo adds the language control. This specification makes both the
    package default (FR-018), since the sidebar footer no longer carries the language control.
    Pick the language component the header uses.
14. **Tests that name the old shell.** The tests and test templates that render `<c-app>`,
    `breakpoint="never"` or the store (`demo/templates/tests/app_breakpoint_*.html` and the rest)
    are moved to the new shell or removed with what they test.
15. **The right sidebar on a demo page.** After issue 752, no demo page in the shell has a right
    sidebar (App layout shows the layout in its diagrams, Sam, 2026-11-27). Its tests use a test
    template.
