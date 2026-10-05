# Planning notes: The basic components come from daisy-cotton

Notes for whoever plans the build. They come from reading both packages' templates on 2026-10-05.
They say how, which `spec.md` does not, and the plan answers each one by name.

**Dock class.** This package's dock read its default class from `mvp_config.layout.dock.class`
inside the component. daisy-cotton's dock has no such default. `mvp/templates/menus/dock/index.html`
is the one caller and can pass the configured value itself.

**Dock toggle.** This package's dock item gave the drawer-toggle label `role="button"` and
`tabindex="0"`. daisy-cotton's does not, and it forwards extra attributes to the element, so
`mvp/templates/menus/dock/item.html` can pass them. Worth raising on daisy-cotton's tracker too,
since a label that toggles a checkbox is not keyboard-reachable on its own.

**Breadcrumb truncation.** The rule in `mvp/tailwind/base.css` (search for
`mvp-breadcrumb-text`) targets a span this package's crumb wrapped its text in. daisy-cotton's
crumb puts the text straight inside the link, or inside a span for the current page. The selector
has to follow. The trail's smaller text size was written into the component and now comes from the
caller in `app/header/navbar.html`.

**Breadcrumb attributes.** `tests/test_components/test_breadcrumbs_href_attribute.py` guards
against `href` being written twice (#127). daisy-cotton declares `href` on the item, so the fault
cannot recur the same way, but the trail a page declares is still worth one test.

**Sidebar menu.** `mvp/templates/menus/sidebar/container.html` passes `label` and `grow`. With
daisy-cotton's container the accessible name needs a wrapping navigation landmark, and the classes
`w-full` and `grow` come from the caller. This package's container also set `role="navigation"` on
the list itself, which is not a role a list should carry. `tests/test_components/test_menu.py`,
`test_sidebar_footer.py` and `test_sidebar_user_menu.py` assert the current markup.

**Other menu callers.** `actions/theme_controller.html`, `addons/share_dropdown.html` and
`user/sidebar_menu.html` call `<c-menu>`, two of them with `label`. Their entries are still this
package's.

**Button callers.** `variant="ghost"` appears in `mvp/templates/500.html`,
`mvp/templates/mvp/error_base.html` and several demo pages. `full` and `reverse` appear only in the
demo. `condition` is documented in `docs/components.md`. Grep the Python side as well: views that
forward attribute dictionaries (Article XVIII) may carry button attributes.

**Divider direction.** This package's `vertical` emitted `divider-horizontal`. daisy-cotton's
`horizontal` emits the same class. A caller that passed `vertical` now passes `horizontal`.

**Alert under `only`.** daisy-cotton's alert draws its dismiss control with `<c-button>` and its
icon with `<c-icon>`. Check both still render when the alert is called with `only`, and that the
icon goes through this package's lookup.

**Mockups.** This package's window and phone mockups wrapped the slot in centring and fixed-height
classes that daisy-cotton's do not have. The demo page is the only caller.

**Tests that glob the component directory.** `tests/test_components/test_render_all.py` and
`test_declared_attributes.py` walk `mvp/templates/cotton`, so they shrink by themselves. Check that
neither keeps a hard-coded list naming a removed component.

**Classes the callers now write.** Any class a caller passes that the old component wrote itself
has to be in the prebuilt stylesheet after the rebuild. The breakpoint-prefixed safelist in
`mvp/tailwind/base.css` may hold entries for the removed divider and menu that can go.
