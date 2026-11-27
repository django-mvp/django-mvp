# Decisions: Arrange the application shell with a layout code

The reading of https://github.com/django-mvp/django-mvp/issues/751 was settled without a round of
questions, from the issue, `PROTOTYPE.md` on `prototype-layout` and the code on `main`. Each
assumption made in that reading is recorded here as a decision, with what was chosen and why it is
defensible.

## The reading

A developer arranges the whole application shell with one layout code from django-mvp-layout, and
draws one page with another. Both sidebars are configured from settings, a page gets a right
sidebar by filling one block, the header's toolbar is set in settings, and a view gives its record
local navigation under the breadcrumbs. A user's sidebars are drawn as they left them, and on a
phone the dock's Menu item opens the sidebar. The card, dialog and bottom sheet (issue 750) and the
demo pages (issue 752) are outside it. It serves G1 and G7.

## Self-resolved

1. **Three stories.** What a developer configures for the whole project, what a developer does on
   one page, and what a visitor does. The region blocks, the breadcrumbs block, local navigation
   and the right sidebar are all one thing a developer sets out to do (shape one page's shell), so
   they are scenarios of one story. The developer's stories and the visitor's are kept apart.

2. **A system check also reads the sidebars' options.** The hand-over names a check on
   `layout.view`. django-mvp-layout raises `LayoutOptionError` when a sidebar is drawn with a value
   it refuses (read in `Sidebar.choose`, 0.3.0), so a project that kept `breakpoint: "never"` would
   fail on every page at render. The same check reads both sidebars' options against the package's
   own choices, never a copy of them. Cheap, and it turns the one break every upgrading project
   with `never` will meet into a message at startup.

3. **No warnings for removed settings.** `main` warns about some removed keys
   (`_warn_on_removed_sidebar_footer_setting`). Sam ruled out aliases and deprecation shims for
   this change, so `layout.navbar.sticky` and `layout.navbar.mobile.site_name` are dropped silently
   and the changelog lists them. A refused value (`never`) is still reported by the check in
   decision 2, because it would otherwise break every page.

4. **`layout.navbar.mobile.site_name` goes.** `main` added it in
   https://github.com/django-mvp/django-mvp/pull/725 after the prototype branched, off by default.
   Sam decided on 2026-11-27 that the name always shows beside the icon, and that a full logo comes
   from overriding the brand mark. The setting would switch off what he settled, so it is removed.

5. **`layout.navbar.mobile.sidebar_toggle` stays.** The prototype keeps it and reads it, and a
   project with no dock still needs a way to open the sidebar on a phone.

6. **The default `layout.navbar.actions` holds the theme and the language controls.** The prototype's
   package default has the theme control only, its demo adds the language. On `main` the sidebar's
   footer carries the language control, and Sam decided that footer holds only the account button
   and that theme and language are set from the header. With the theme control alone, a project
   with translations would lose its language control on upgrade. The language control draws
   nothing on a project without `LocaleMiddleware` or `set_language` (checked in
   `cotton/mvp/actions/language_switcher_modal.html`), so the default costs other projects nothing.

7. **The right sidebar and the page's side panel both stay.** The prototype left this for the
   rebuild. The side panel (specs/042) belongs to the page and sits inside it, with its own panel
   button and title. The right sidebar is a region of the shell beside the page. Replacing one with
   the other would rewrite a delivered feature that nobody asked to change.

8. **The layout store is replaced by django-mvp-layout's published state.** The prototype removes
   `assets/js/layout.js` and the `/layout/store/` page. What a project could do with the store
   (follow the sidebar's open state, whether it is a drawer) it now does with the state attributes
   and the `mvpl:change` event the layout package documents (`docs/developer/styling.md` and
   `docs/developer/scripting.md` in django-mvp-layout 0.3.0). A second store in django-mvp would
   mirror the package's own state, which is the duplication this rebuild removes.

9. **Without script, sidebars stay as the server drew them.** `specs/029-layout-state-store`
   FR-008 asked that the sidebar could be opened and closed with no JavaScript, which the drawer's
   checkbox allowed. django-mvp-layout's toggles are buttons driven by its script, and the package
   documents no fallback. The shell draws each sidebar from the remembered state on the server, so
   the page is readable and every link works. The loss is accepted with the rest of the break, and
   a fallback, if wanted, belongs in the layout package.

10. **Edge cases about existing behaviour were checked against the code.** The cookie handling and
    `collapse: "none"` in django-mvp-layout 0.3.0's `Sidebar.settle`, the breakpoint defaults in
    `Sidebar.DEFAULT_BREAKPOINTS`, the dock's `toggle` in `cotton/mvp/dock/item.html` and
    `docs/navigation.md` on `main`, the header height in `assets/js/header_height.js`, and the
    language control in `language_switcher_modal.html`. Where the prototype and `main` differ, the
    note is in `planning-notes.md`.

11. **The success criteria's screens are this feature's own.** The products list, the full-height
    page, the landing page, the account page and the install page are drawn by the shell and not
    rebuilt by issue 752. The App layout, Page layout and Theme pages and the card and modal
    examples are left to issue 752's own check.

## What moved from the old specifications

12. **`specs/001-app-components` is removed.** What still holds on `main` moved here:
    - User Story 4 (replace one region of the shell) → US-2 scenarios 4 to 7 and FR-021.
    - User Story 5 (breadcrumbs from a template) → US-2 scenario 8.
    - User Stories 6 and 7 (a trail that fits its box, a step's icon) → US-2 scenario 11, US-3
      scenarios 9 to 11 and 13, FR-026.
    - User Stories 1 to 3 (attribute-driven configuration on Bootstrap breakpoints) describe the
      AdminLTE shell, which no longer exists. They are replaced by the layout code and the sidebar
      settings, and nothing of them moves.

13. **`specs/00x-layout-configuration` is removed.** Its fixed sidebar, fixed header and fixed
    footer are what an upper-case letter in the layout code does now (US-1 scenarios 2 and 3). Its
    `fill` on `<c-app>` is `<c-mvp.page fill>` on `main` (US-2 scenario 10, FR-025). Its demo page
    requirements describe a `/layout/` page that issue 752 rewrites, so they do not move.

14. **`specs/029-layout-state-store` keeps only its User Story 3.** Moved here and removed from it:
    - User Stories 1 and 2 (the layout store and the configuration on it) → replaced by
      django-mvp-layout's published state, US-2 scenario 12 and FR-022 (decision 8).
    - User Story 4 (a sidebar that does not collapse) → US-1 scenarios 7 and 8 and FR-008, now
      django-mvp-layout's `collapse: "none"`.
    - FR-008 (open and close without script) → replaced by FR-024 (decision 9).
    User Story 3 (responsive visibility from the stylesheet, keyed to the shell's breakpoint
    attribute, with the template tags removed) still holds and stays in 029, edited so it reads as
    the shell now is: `never` becomes the `overlay` behaviour, and its scenario about the icon rail
    hiding the navbar's toggle moved here as US-3 scenario 1.
