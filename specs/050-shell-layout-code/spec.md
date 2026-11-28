# Feature Specification: Arrange the application shell with a layout code

**Feature Branch**: `050-shell-layout-code`

**Created**: 2026-11-27

**Status**: Draft

**Serves**: G1 (a complete, responsive application shell that a project configures rather than
builds), G7 (customization that never dead-ends, from view configuration through component
override to a project's own CSS). It keeps to G5, G6 and G14: the shell keeps its finished look,
needs no build tooling in a project, and every script and style it needs ships with the package
or with django-mvp-layout.

**Roadmap**: R1 — A configurable application shell.

**Issue**: https://github.com/django-mvp/django-mvp/issues/751

**Input**: The application shell is built on a daisyUI drawer. Its arrangement is fixed: a project
can choose the sidebar's breakpoint and how it collapses, and whether the header sticks, but not
where the sidebar runs or what stays in place while the page scrolls. It has one sidebar, and a
page that wants a second column on the right has to build its own. Whether the sidebar is open is
kept in the browser's local storage, so the server cannot draw it as the visitor left it.

After this feature, the whole shell is one layout from django-mvp-layout, arranged by one layout
code in `MVP_CONFIG["layout"]["view"]`. A developer changes the arrangement of every page by
changing that code, and draws one page with another code from its view or template. Both
sidebars are configured from settings: how they behave at each width, their width, their
breakpoint and how they close. A page gets a right sidebar by filling one template block. The
header's toolbar is set in settings, and a view gives its record a row of local navigation under
the breadcrumbs. A user's sidebars are drawn as they left them, from the first paint, and on a
phone the dock's Menu item opens the sidebar.

The shell's look is agreed on the `prototype-layout` branch
(https://github.com/django-mvp/django-mvp/issues/719), section 1 of its `PROTOTYPE.md`. Its
templates and styles are carried into the package, not redrawn. How it is built is left to
research and planning, with the notes in `planning-notes.md`.

This specification replaces `specs/001-app-components` and `specs/00x-layout-configuration`,
which are removed with it. What `specs/029-layout-state-store` said about the layout store and the
sidebar that never collapses is described here now. `decisions.md` records what moved and why.

## Clarifications

### Session 2026-11-27

- **Q**: What happens to a layout setting the shell no longer reads, such as
  `layout.navbar.sticky` or a breakpoint of `never`?
  **A**: The layout code replaces `sticky` (an upper-case `H` keeps the header in place), and the
  sidebar's `behavior: "overlay"` replaces a breakpoint of `never`. Nothing translates the old
  values. A key the shell no longer reads is ignored, and a value the layout package refuses is
  reported by the system check. Breaking existing projects is accepted for this change. (FR-004,
  FR-009)
- **Q**: Is a wrong layout code reported at startup or when a page is drawn?
  **A**: At startup, by a system check that reads `layout.view` with django-mvp-layout's own
  parser, so a project cannot be served with a shell that fails on every page. The same check
  reads both sidebars' options against the choices the layout package accepts. A code a view sets
  for one page is read when that page is drawn. (FR-003, FR-004)
- **Q**: Does the right sidebar replace the page's side panel?
  **A**: No. The side panel belongs to the page and sits inside it. The right sidebar is a region
  of the shell, beside the page. Both stay, and a page may use either. (FR-013)
- **Q**: Where do the theme and language controls go now that the sidebar's footer holds only the
  account button?
  **A**: Into the header's toolbar, as `layout.navbar.actions`, which the package fills with the
  theme control and the language control by default. A project lists its own. (FR-010)
- **Q**: What replaces the layout store a project's markup could read?
  **A**: The state django-mvp-layout publishes on the layout and on each sidebar, and the change
  event it sends, which its documentation lists. The shell adds no second store of its own.
  (FR-021)
- **Q**: What does the shell do where scripts do not run?
  **A**: Every page is drawn and readable, its links work, and each sidebar is drawn as the server
  resolved it from the visitor's remembered state. Opening and closing a sidebar needs the layout
  package's script. (FR-024)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A developer arranges and configures the application shell from settings (Priority: P1)

A developer sets up the shell for a whole project. They choose where the sidebar runs and what
stays in place while the page scrolls by writing one layout code, and they configure both
sidebars and the header's toolbar in the same settings, without overriding a template.

**Why this priority**: This is the feature. A project arranges its shell by configuration, which
is what G1 asks for, and every other story draws inside the arrangement this one sets.

**Independent Test**: In a project with no layout settings, load a page and check the shell's
regions and which of them stay in place while the page scrolls. Change `layout.view`, a sidebar
option and the toolbar lists, load the page again and check each change took effect. Set a
wrong code and a refused sidebar option and run the system check.

**Acceptance Scenarios**:

1. **Given** a project that sets nothing under `layout`, **When** a page is drawn, **Then** the
   shell is the default layout code's arrangement: a left sidebar running the full height of the
   window, the header and the page beside it, and a footer, with the header and the sidebar kept in
   place while the page scrolls.
2. **Given** a project that sets `layout.view` to another layout code, **When** any page is drawn,
   **Then** the shell is arranged by that code: which region reaches each corner, and which regions
   stay in place while the page scrolls, follow the code.
3. **Given** a code whose header letter is lower-case, **When** the page is scrolled, **Then** the
   header scrolls away with it, and the header's height the shell publishes for other elements to
   clear is zero.
4. **Given** a `layout.view` that is not a layout code, **When** the project's system checks run,
   **Then** an error names the setting and gives the layout package's reason, and the project is
   not served until it is fixed.
5. **Given** a sidebar whose `behavior` is `auto`, **When** the window is narrower than its
   `breakpoint`, **Then** the sidebar is a drawer over the page, and at or above it the sidebar
   sits beside the page.
6. **Given** a sidebar whose `behavior` is `docked`, **When** a page is drawn at any width,
   **Then** the sidebar sits beside the page. **Given** `overlay`, **Then** it is a drawer over the
   page at every width.
7. **Given** a sidebar beside the page whose `collapse` is `offcanvas`, **When** it is closed,
   **Then** it slides fully away and the page takes its room. **Given** `icons`, **Then** it
   closes to an icon rail in which the menu shows icons only, each item keeping its name for a
   screen reader and as a tooltip. **Given** `none`, **Then** it is always open beside the page,
   no control to close it is drawn, and a closed state the visitor's browser remembers is neither
   used nor overwritten.
8. **Given** a sidebar with `collapse: "none"`, **When** the window is below its breakpoint,
   **Then** it is a drawer like any other, opened and closed by the same controls.
9. **Given** a `width` on either sidebar, **When** that sidebar sits beside the page, **Then** it
   takes that width.
10. **Given** a sidebar option that the layout package refuses, such as a breakpoint of `never`,
    **When** the project's system checks run, **Then** an error names the setting and lists the
    values it accepts.
11. **Given** `layout.sidebar.title`, **When** a page is drawn, **Then** that name is shown beside
    the site's icon in the sidebar's brand row, and in the header while the sidebar is closed.
    **Given** no title, **Then** the application's name is shown instead.
12. **Given** a project that overrides the brand mark's template, **When** a page is drawn,
    **Then** its mark is drawn in both places the name and icon were.
13. **Given** `layout.sidebar.boost` on, **When** a visitor follows a link in the sidebar,
    **Then** the page is loaded with htmx in place of a full page load. **Given** it off, **Then**
    the sidebar says so on its own element and links load normally.
14. **Given** components listed in `layout.navbar.end`, **When** a page is drawn at any width,
    **Then** each is drawn in the header in the listed order, and the log-in button stays the
    header's last item wherever the list names it.
15. **Given** components listed in `layout.navbar.actions`, **When** the left sidebar sits beside
    the page, **Then** they are drawn in the header before the `end` components. **When** the left
    sidebar is a drawer, **Then** they are drawn in a row under the sidebar's brand row instead,
    and never in both places at once.
16. **Given** `layout.secondary_sidebar` settings, **When** a page that has a right sidebar is
    drawn, **Then** the right sidebar follows its own `behavior`, `breakpoint`, `collapse` and
    `width`, and its `label` names the sidebar and the header button that opens it.
17. **Given** `layout.navbar.mobile.sidebar_toggle` on, **When** the window is below the left
    sidebar's breakpoint, **Then** the header draws its own button to open the sidebar, for a
    project with no dock. **Given** it off, **Then** below the breakpoint the header draws none
    and the dock's Menu item opens the sidebar.

---

### User Story 2 - A developer shapes one page's part of the shell from its view or template (Priority: P1)

A developer building one page changes the shell around it: a different arrangement for a full
screen map, a right sidebar with the record's details, a row of tabs for the record's own pages,
breadcrumbs from a template whose view they do not own, or one region replaced outright.

**Why this priority**: A shell that can only be configured for the whole project dead-ends on the
first page that needs something else, which is what G7 rules out. The right sidebar is the
capability the old shell lacked altogether.

**Independent Test**: Render templates that extend `mvp/base.html` and each fill one block or set
one context variable, and check the shell draws the change on that page and leaves every other
page as configured.

**Acceptance Scenarios**:

1. **Given** a view or template that sets `layout_view` in the context to a layout code, **When**
   that page is drawn, **Then** it is arranged by that code, and pages without it keep the
   project's code.
2. **Given** a template that fills `{% block app.secondary_sidebar %}`, **When** the page is drawn,
   **Then** the shell has a right sidebar holding that content, and the header has a button that
   opens and closes it.
3. **Given** a template that leaves `app.secondary_sidebar` empty, **When** the page is drawn,
   **Then** the shell has no right sidebar and offers no control to open one.
4. **Given** a template that fills none of the region blocks, **When** the page is drawn, **Then**
   the sidebar and the header draw their packaged regions.
5. **Given** a template that fills `app.sidebar.header`, `app.sidebar.body` or
   `app.sidebar.footer`, **When** the page is drawn, **Then** that content replaces the region and
   the sidebar's other two regions are unchanged. **Given** `app.sidebar`, **Then** its content
   replaces the whole left sidebar.
6. **Given** a template that fills `app.navbar.start`, **When** the page is drawn, **Then** that
   content replaces the header's menu button, brand and breadcrumb trail. **Given**
   `app.navbar.center`, **Then** the content sits between the header's start and end. **Given**
   `app.navbar.end`, **Then** the content is drawn before the configured components, which are
   still drawn. **Given** `app.navbar`, **Then** the content replaces the header's row and the
   tray below it is unchanged.
7. **Given** a template that fills `app.messages`, **When** the page is drawn, **Then** that
   content replaces the message toasts.
8. **Given** a template that leaves `app.breadcrumbs` empty and a view that declares no trail,
   **When** the page is drawn, **Then** the header draws no breadcrumb navigation. **Given** a view
   that declares a trail, **Then** the header draws it. **Given** a template that fills
   `app.breadcrumbs`, **Then** its steps are drawn in place of any trail the view declared, and
   the header's menu button and brand are unchanged.
9. **Given** a view whose context names a menu as `local_menu`, **When** the page is drawn,
   **Then** that menu is drawn as a row of local navigation under the breadcrumbs, with the
   current page marked. **Given** no `local_menu`, **Then** no row is drawn. **Given** a template
   that fills `app.header.tray`, **Then** its content takes the row's place.
10. **Given** a page drawn with `<c-mvp.page fill>`, **When** it is shown, **Then** the page fills
    the room the layout leaves it, from the header to the footer, and the window itself does not
    scroll.
11. **Given** a breadcrumb trail placed in a card, a sidebar or a panel, **When** the box is
    narrower than the trail, **Then** the trail folds to fit that box, as the header's does.
12. **Given** a project's own element styled or scripted against the state django-mvp-layout
    publishes for a sidebar, **When** the sidebar is opened, closed, or changes between a drawer
    and a docked sidebar, **Then** the element follows each change, with no package internals
    read and no breakpoint written down twice.

---

### User Story 3 - A user moves around the site in the shell, on any screen (Priority: P1)

A visitor reads pages and moves between them. On a wide screen they close the sidebar to give the
page more room and find it still closed on the next page. On a phone they open the sidebar from
the dock, reach the theme and language controls inside it, and close it again. They always see
where the page sits.

**Why this priority**: Every page a site draws is drawn in this shell, so how it opens, closes,
remembers and folds is what every visitor meets first.

**Independent Test**: In a real browser, at a phone width and a desktop width, signed out and
signed in: open and close each sidebar by each of its controls, load another page, and check the
sidebars come back as left. Narrow the window and check the breadcrumbs and local navigation fit.

**Acceptance Scenarios**:

1. **Given** a wide screen and the left sidebar open beside the page, **When** the visitor closes
   it with the button in its brand row, **Then** it closes as its `collapse` setting says, and the
   header shows a button to open it again with the site's brand beside it. **When** they open it
   again, **Then** the header's button and brand give way to the sidebar's own brand row.
2. **Given** a visitor who closed a sidebar, **When** they load another page or come back later,
   **Then** that sidebar is drawn closed from the first paint, with no slide, and the same holds
   for open. The left and the right sidebar are remembered apart.
3. **Given** a phone, **When** the visitor taps the dock's Menu item or the header's button,
   **Then** the sidebar opens as a drawer over the page with a backdrop, and focus moves into it.
   **When** they tap the backdrop, press Escape or press its close button, **Then** it closes and
   focus returns to the control that opened it.
4. **Given** a sidebar drawn as a drawer, **When** it is opened, **Then** the header's actions are
   in a row under its brand row, at a size meant for a finger.
5. **Given** a sidebar's menu longer than the window, **When** the visitor scrolls it, **Then** the
   brand row and the footer stay in place and only the menu moves, with no sideways scrolling.
6. **Given** a signed-in visitor, **When** they press the account button in the sidebar's footer,
   **Then** a menu opens with their account, the admin site where they may use it, and log out.
   **Given** a visitor who is not signed in, **Then** the footer offers Log in in its place.
7. **Given** the sidebar closed to an icon rail, **When** the visitor points at an item, **Then**
   its name is shown, and the account button shows the avatar alone.
8. **Given** a page with a right sidebar, **When** the visitor presses the header's button for it,
   **Then** it opens or closes, beside the page from its breakpoint up and as a drawer below it.
9. **Given** a breadcrumb trail too wide for the header, **When** the page is drawn, **Then** the
   steps between the first and the parent fold into a "…" menu from the middle outwards, and the
   first step, the parent and the current page stay. Narrower still, the first step shrinks to its
   icon where it has one, then folds, then the parent is cut short. The current page never folds.
10. **Given** a folded trail, **When** the visitor presses the "…" button, **Then** a menu lists
    the folded steps in order as links, takes focus and closes on Escape, and the button's name
    says how many steps it holds.
11. **Given** a trail in a right-to-left language, **When** the page is drawn, **Then** the
    separators point the other way. **Given** any trail, **Then** each step carries its position
    for schema.org breadcrumb markup and the last is marked as the current page.
12. **Given** local navigation wider than the header, **When** the page is drawn, **Then** the row
    stays on one line and scrolls sideways, and the current page's tab is marked for a screen
    reader as well as on screen.
13. **Given** a browser that runs no script, **When** any page is drawn, **Then** the page, the
    header and its links work, each sidebar is drawn as remembered, and every step of the trail is
    drawn, each shrinking with an ellipsis.

### Edge Cases

- **A remembered state the layout package does not recognise.** A cookie holding anything but
  `open` or `closed` is ignored, and the sidebar is drawn open. (Checked in django-mvp-layout
  0.3.0's `Sidebar.settle`.)
- **A remembered closed state under `collapse: "none"`.** The sidebar is drawn open and the cookie
  is left as it was. (Checked in the same function: `none` forces the state to open.)
- **A secondary sidebar setting given with no page that has a right sidebar.** Nothing is drawn,
  and the settings still go through the system check.
- **The breakpoint left out of a sidebar's settings.** The layout package's own default applies:
  `lg` for the left sidebar and `xl` for the right. (Checked in `Sidebar.DEFAULT_BREAKPOINTS`.)
- **A `layout_view` a view sets that is not a layout code.** The page fails to draw with the
  layout package's error, naming the code. The system check cannot see a value set at render
  time.
- **A navigation that replaces the page body with htmx.** The new body's sidebars are drawn by the
  server in the remembered state and the layout package's script picks them up, so the shell
  agrees with what is on screen after a boosted link as after a full load.
- **A dock declared in a project's own template.** A dock item that toggles the sidebar opens the
  shell's left sidebar, whether the dock comes from the menu or from `c-mvp.dock.item` in a
  template. On `main` today such an item names the drawer's checkbox, `mvp-app-toggle`, which the
  shell no longer has.
- **The header's height for elements that clear it.** The side panel and anchor scrolling read the
  header's height. It is the header's real height while the code keeps the header in place, and
  zero when the header scrolls away or the page has none, as on `main` today.
- **A project with no dock and `mobile.sidebar_toggle` off.** Below the breakpoint nothing opens
  the sidebar. This is the case on `main` today and the setting's description says so.
- **The default toolbar on a project without translations.** The language control draws nothing
  where `LocaleMiddleware` is not installed or `set_language` does not reverse, as on `main` today,
  so the default `actions` list costs such a project nothing.
- **Old shell markup a project wrote against.** The drawer checkbox `mvp-app-toggle`, the layout
  store and its localStorage key are gone. A project's markup that used them stops working, and
  the documentation says what replaces each.

## Requirements *(mandatory)*

### Functional Requirements

**The layout code**

- **FR-001**: The shell MUST be one django-mvp-layout layout, arranged by the layout code in
  `MVP_CONFIG["layout"]["view"]`.
- **FR-002**: The default code MUST keep the arrangement of the shell on `main`: a left sidebar
  running the full height, and the header and both sidebars kept in place while the page scrolls.
- **FR-003**: A `layout_view` in a page's context MUST arrange that page by its code in place of
  the project's.
- **FR-004**: A system check MUST read `layout.view` with django-mvp-layout's own parser, and the
  options of both sidebars against the values the layout package accepts, and report each value
  it refuses as an error naming the setting.
- **FR-005**: The shell MUST publish the header's height while the code keeps the header in place,
  and zero otherwise, for the elements that clear the header.

**The sidebars**

- **FR-006**: `layout.sidebar` MUST accept `behavior` (`auto`, `docked`, `overlay`) and `width`,
  beside `collapse`, `breakpoint`, `title` and `boost`, and the left sidebar MUST follow each.
- **FR-007**: `layout.secondary_sidebar` MUST accept `behavior`, `breakpoint`, `collapse`, `width`
  and `label`, and the right sidebar MUST follow each.
- **FR-008**: Under `collapse: "none"` a sidebar MUST be open whenever it sits beside the page,
  with no control to close it there, and the remembered state MUST be neither used nor
  overwritten. Below its breakpoint it MUST behave as under any other collapse.
- **FR-009**: The settings the layout code replaces MUST be removed: `layout.navbar.sticky`, the
  breakpoint value `never`, and `layout.navbar.mobile.site_name`. No alias or translation is kept.
- **FR-010**: Each sidebar's open or closed state MUST be remembered for the visitor, the left and
  the right apart, and drawn by the server from the first paint.
- **FR-011**: The left sidebar's brand row and footer MUST stay in place while its menu scrolls,
  and the sidebar MUST NOT scroll sideways.
- **FR-012**: In an icon rail, the menu's labels and the account button's name MUST be hidden by
  one mechanism, django-mvp-layout's rail classes, and each item MUST keep its name for a screen
  reader and as a tooltip.
- **FR-013**: A page MUST get a right sidebar by filling `{% block app.secondary_sidebar %}`, and a
  page that leaves it empty MUST have no right sidebar and no control for one. The page's side
  panel is unchanged.
- **FR-014**: The sidebar's footer MUST hold the account button for a signed-in visitor and the
  log-in button for a visitor, and nothing else.

**The header**

- **FR-015**: The header's button to open the left sidebar, and the brand beside it, MUST be shown
  only while the left sidebar is closed or a closed drawer. The sidebar's own brand row MUST carry
  the button that closes it.
- **FR-016**: The brand MUST show the site's icon with a name beside it: `layout.sidebar.title`,
  else `site_name`, else the current site's name. A project MUST be able to replace the mark with
  one template override.
- **FR-017**: `layout.navbar.end` MUST list the components drawn in the header at every width, the
  log-in button kept last.
- **FR-018**: `layout.navbar.actions` MUST list the components drawn in the header while the left
  sidebar sits beside the page, and in a row under the sidebar's brand row while it is a drawer,
  never both. Its default MUST be the theme control and the language control.
- **FR-019**: The header MUST draw a button for the right sidebar on a page that has one.
- **FR-020**: A view MUST be able to name a menu as `local_menu` in its context, and the shell MUST
  draw it under the breadcrumbs as local navigation, on one line that scrolls sideways when it
  does not fit, with the current page marked. The package MUST provide the renderer it is drawn
  with.

**Templates and markup**

- **FR-021**: The region blocks of `mvp/base.html` (`app.header`, `app.navbar`, `app.navbar.start`,
  `app.navbar.center`, `app.navbar.end`, `app.breadcrumbs`, `app.header.tray`, `app.sidebar`,
  `app.sidebar.header`, `app.sidebar.body`, `app.sidebar.footer`, `app.main`, `app.messages`,
  `app.footer`, `app.dock`) MUST keep their meaning, each replacing its region outright when filled.
- **FR-022**: The shell MUST use django-mvp-layout's `HbF` stacking class for the left sidebar's
  content and the package's state attributes and event as the way a project's markup follows the
  shell. It MUST NOT carry stacking rules or a layout store of its own.
- **FR-023**: Every dock item that toggles the sidebar, from the menu or from `c-mvp.dock.item`,
  MUST open and close the shell's left sidebar.
- **FR-024**: Without script, every page MUST be drawn and usable through its links, with each
  sidebar in the state the server resolved.
- **FR-025**: `<c-mvp.page fill>` MUST fill the room the layout leaves the page.
- **FR-026**: The breadcrumb trail MUST fit the box it sits in, in the header or anywhere a
  developer places it, folding as User Story 3 describes, and MUST draw every step where no script
  runs.

**What it replaces**

- **FR-027**: The drawer shell (`c-app`, `c-mvp.layout.sidebar`, the `mvp-app-toggle` checkbox),
  `mvp/layout.py` and its `LayoutConfig`, the layout store and its localStorage key, the stylesheet
  rules for the drawer's sidebar toggles, and the demo page that shows the store MUST be removed.
- **FR-028**: The documentation MUST describe the layout code, both sidebars' settings, the
  toolbar settings, the right sidebar, local navigation and the brand mark, and the changelog MUST
  list every removed setting, component and template with what replaces it.

### Requirement coverage

| Story | Requirements |
|---|---|
| US-1 — the shell from settings | FR-001, FR-002, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-016, FR-017, FR-018, FR-027, FR-028 |
| US-2 — one page's part of the shell | FR-003, FR-013, FR-019, FR-020, FR-021, FR-022, FR-025, FR-026 |
| US-3 — a user in the shell | FR-010, FR-011, FR-012, FR-014, FR-015, FR-023, FR-024 |

### Key Entities

- **Layout code**: three groups of three letters naming the region at each place of the top,
  middle and bottom rows, defined and parsed by django-mvp-layout. An upper-case letter keeps its
  region in place while the page scrolls.
- **Sidebar settings**: one set for the left sidebar (`layout.sidebar`) and one for the right
  (`layout.secondary_sidebar`), read by django-mvp-layout's sidebar.
- **Remembered sidebar state**: one cookie per sidebar holding `open` or `closed`, the only state
  the shell keeps.
- **Header toolbar**: two lists of component names, `layout.navbar.end` and
  `layout.navbar.actions`.
- **Local navigation**: a menu a view names, drawn as a row of tabs under the breadcrumbs.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer changes the arrangement of every page, including which regions stay in
  place while the page scrolls, by changing one setting, with no template overridden.
- **SC-002**: Every wrong layout code and every refused sidebar option in settings is reported by
  `manage.py check` before a page is served, naming the setting.
- **SC-003**: A page gets a right sidebar with one template block and no other change, and a page
  without it draws no right sidebar and no control for one.
- **SC-004**: A sidebar a visitor closed is drawn closed on their next page from the first paint,
  with no slide, at phone and desktop width.
- **SC-005**: Every shell screen this feature draws matches the agreed design side by side at 390
  and 1440 pixels wide, signed out and signed in: the products list (no right sidebar), the
  full-height page, the landing page, the account page and the install page, each with the left
  sidebar open and closed.
- **SC-006**: The package carries no stacking rules, no layout store and no sidebar resolver of its
  own: the shell's stacking, sidebar state and code parsing all come from django-mvp-layout.
- **SC-007**: A project upgrading finds every removed setting, component and template, and what
  replaces it, in the changelog and the documentation.

## Assumptions

- django-mvp-layout 0.3.0 is a dependency of the package before this feature is built. The card,
  dialog and bottom sheet rebuild (https://github.com/django-mvp/django-mvp/issues/750) adds it,
  with the shared heading and footer rows and the box styles, and this feature builds on that.
- django-mvp-layout's tests cover how its stacking classes stack, how its sidebars slide and how
  its toggles work. This feature tests that the shell's markup uses them, never how they behave.
- Breaking existing projects is accepted. Removed settings, components and templates go with no
  alias and no deprecation warning.
- The Look & Feel demo pages (https://github.com/django-mvp/django-mvp/issues/752) come after this
  feature. It leaves the demo's layout pages working, and their rewrite is not part of it.
- Nothing is stored on the server. The sidebar cookies are the only state, so nothing migrates.

## Out of Scope

- The card, the dialog and the bottom sheet built from parts, and the box styles: issue 750.
- The demo's Look & Feel pages and the card and dialog examples: issue 752.
- A toggle taking its sidebar's label as its name, which is django-mvp-layout's to provide.
- Changes to django-mvp-accounts, compliance, community and payments, which follow on their own.
