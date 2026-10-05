# Feature Specification: The sidebar and user menus are built from daisy-cotton's menu

**Feature Branch**: `038-menus-from-daisy-cotton`

**Created**: 2026-10-05

**Status**: Draft

**Serves**: G1 (a complete, responsive application shell that a project configures rather than builds), G5 (a polished, modern look and feel out of the box)

**Roadmap**: R29 (the basic daisyUI components come from daisy-cotton)

**Issue**: #438

**Depends on**: #435, and [django-mvp/daisy-cotton#120](https://github.com/django-mvp/daisy-cotton/issues/120)

**Input**: The sidebar, the collapsed icon rail and the user menu should be drawn with
daisy-cotton's menu, submenu and drawer. The sign-out entry, share links and rail tooltips keep
working.

## Summary

This package draws every menu with its own menu components: an entry, a group, a collapse wrapper
and a divider. daisy-cotton ships the same pieces for any Django project, as a menu, an entry, a
heading row and a collapsible submenu, plus the drawer a sidebar sits in. After this feature the
shell uses daisy-cotton's. That covers the sidebar menu a project declares in Python, the link back
to the host on a mounted app's pages, the user menu in the sidebar footer, the share menu, the
theme chooser's list and the drawer shell around the page. The package's own entry, group,
collapse and divider components are removed.

Nothing a person does in the shell changes. The sidebar opens, closes and remembers its state. The
icon rail hides labels and names each entry in a tooltip. A collapsible group flies out beside the
rail. Sign-out still posts a form, share links still open in a new tab, and a project still
declares its menus in Python exactly as it does today. What changes is the vocabulary a project
uses when it writes a menu entry by hand, and that change is breaking.

Three things in the shell need an attribute on the link or button of a menu entry: the sign-out
entry, the share links and the rail tooltips. daisy-cotton's entry puts every extra attribute on
the list item around the link, so none of them can be built on it yet. That gap is
django-mvp/daisy-cotton#120, and this feature waits for the daisy-cotton release that closes it.

Component names in this document are the ones #434 gives them: a component this package keeps is
written `<c-mvp.…>`, and a bare name such as `<c-menu.item>` means daisy-cotton's component.

## Clarifications

### Session 2026-10-05

The coverage scan found five ambiguities. Each was resolved from #438, its sibling issues under
R29, the roadmap item and the package's constitution. Longer rationale is in `decisions.md`.

- **Q: #438 and #440 both name the drawer. Which one moves the drawer shell onto daisy-cotton's
  drawer?**
  A: This one. #438 names the drawer in its own request, the rail's tooltips depend on the drawer
  not clipping them, and #440 already depends on #438. #440 keeps the button in the navbar that
  opens the drawer, along with the rest of its list. Recorded as FR-012 to FR-017.

- **Q: daisy-cotton#120 is still open, and its discussion names two ways to close it. Does this
  feature depend on which one is chosen?**
  A: No. The requirement is that a caller can put attributes on an entry's link or button. Whether
  daisy-cotton sends extra attributes there, or gives the entry a form whose content fills the
  list item, the requirements here read the same. The feature does not start until a daisy-cotton
  release carries one of them, and it does not work around the gap in this package. Recorded as
  FR-021 and in Assumptions.

- **Q: In the collapsed rail an entry's label is hidden. Does the entry still need a name a screen
  reader can announce?**
  A: Yes. A hidden label names nothing, and a tooltip drawn by the stylesheet is not a name. The
  link back to the host already carries one, and every rail entry gets the same treatment while
  the entries are being redrawn. Recorded as FR-009.

- **Q: What happens to a project template that still calls the removed components or passes the
  old attribute names?**
  A: It is not kept working. R29 lands as one breaking release with no compatibility aliases. A
  call to a removed component fails with an error naming it. A call to `<c-menu.item>` with the
  old attribute names reaches daisy-cotton's entry and renders without its label, so the
  changelog carries a table from every old tag and attribute to its replacement. Recorded as
  FR-022 and FR-024.

- **Q: The user menu, the share menu and the theme chooser each sit inside a dropdown. Does this
  feature change the dropdown or its trigger?**
  A: No. The dropdown and its triggers belong to #437. This feature changes the menu and the
  entries inside each panel and leaves the panel alone. Recorded in Assumptions.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The sidebar menu is drawn with daisy-cotton's menu components (Priority: P1)

A developer declares their project's menu in Python, as they do today: entries with a label, an
icon, an address and sometimes a badge, some of them gathered under a parent. They upgrade the
package and change nothing. The sidebar draws the same menu. An entry is a link, the current page's
entry is marked as current, a parent that can collapse opens and closes and is open when the
current page is inside it, and a parent that cannot collapse is a heading over its entries. On a
mounted app's pages the link back to the host sits above the app's menu. Underneath, every one of
those rows is now daisy-cotton's entry, heading or submenu, so a fix made there reaches the sidebar
without being made again here.

**Why this priority**: The sidebar menu is on every page of every project. It is the reason the
package has menu components at all, and the other stories build on it.

**Independent Test**: In a test project, declare a menu with a plain entry, an entry with a badge,
a collapsible parent and a parent that cannot collapse. Render a page and confirm each entry's
link, the current-page marking, the open state of the parent holding the current page, the heading
row and the single navigation landmark. Confirm the package's own entry and group components took
no part in the render.

**Acceptance Scenarios**:

1. **Given** a menu declared in Python with entries that carry a label, an icon and an address,
   **When** a page renders, **Then** the sidebar draws one link per visible entry, each going to
   its entry's address and carrying its label and icon.
2. **Given** the page being rendered is the target of one entry, **When** the sidebar renders,
   **Then** that entry alone is marked as current, in a way assistive technology can read.
3. **Given** an entry that declares a badge, **When** the sidebar renders, **Then** the badge's
   value is drawn with the entry. **Given** an entry with no badge, **Then** no badge is drawn.
4. **Given** a parent entry that can collapse, **When** the sidebar renders on a page outside it,
   **Then** its children are inside a closed disclosure the person can open. **When** it renders
   on a page that is one of its children, **Then** the disclosure is open.
5. **Given** a parent entry that cannot collapse, **When** the sidebar renders, **Then** its label
   is a heading row that is not a link or a button, and its children follow it as ordinary
   entries.
6. **Given** any page, **When** the sidebar renders, **Then** it contains exactly one navigation
   landmark for the menu, named from the menu's own declaration.
7. **Given** a page inside a mounted app, **When** the sidebar renders, **Then** the link back to
   the host is drawn above the app's menu, goes to the host's home page, and does not add a second
   navigation landmark.
8. **Given** a page whose context holds a variable with the same name as one of the menu
   components' attributes, such as `text`, `icon`, `class` or `open`, **When** the sidebar
   renders, **Then** every entry renders as it does without that variable.
9. **Given** a project whose menus were declared before this feature, **When** it upgrades,
   **Then** its menu declarations work without change.

---

### User Story 2 - The collapsed icon rail keeps working (Priority: P1)

A project sets the sidebar to collapse to an icon rail. Someone using it collapses the sidebar. The
labels, badges and headings go, and each entry is left as its icon. Hovering or focusing an entry
shows its label as a tooltip beside the rail. Hovering a collapsible group opens its entries beside
the rail, with their labels. Someone using a screen reader hears each entry's name whether the rail
is collapsed or not. Content a project marked to hide in the rail, or to show only in the rail,
still does.

**Why this priority**: The rail is the part of the sidebar most tied to the exact markup of an
entry. A swap that leaves the open sidebar right can still break it, and nothing short of a browser
shows that.

**Independent Test**: In a browser test with the sidebar set to collapse to icons, collapse it and
confirm that an entry's label is not displayed, that hovering the entry displays its label as a
tooltip that is not cut off at the rail's edge, that the entry has an accessible name, and that
hovering a collapsible group displays its children with their labels.

**Acceptance Scenarios**:

1. **Given** the sidebar is set to collapse to icons and is collapsed, **When** it renders,
   **Then** each entry's icon is displayed and its label, badge and any heading row are not.
2. **Given** the collapsed rail, **When** someone hovers or focuses an entry, **Then** the entry's
   label is displayed as a tooltip, and the tooltip is not cut off by the edge of the rail.
3. **Given** the collapsed rail, **When** assistive technology reads an entry, **Then** the entry
   has an accessible name equal to its label.
4. **Given** the collapsed rail and a collapsible group, **When** someone hovers or focuses the
   group, **Then** its children are displayed beside the rail with their labels.
5. **Given** the sidebar is open, **When** someone hovers an entry, **Then** no tooltip is
   displayed.
6. **Given** the collapsed rail on a mounted app's page, **When** it renders, **Then** the link
   back to the host follows the same rules as any other entry: icon only, labelled by tooltip, and
   named for assistive technology.
7. **Given** sidebar content a project marked to hide in the rail or to show only in the rail,
   **When** the sidebar collapses and opens, **Then** that content hides and shows as it did before
   this feature.
8. **Given** the sidebar is set to slide away instead of collapsing to icons, **When** it is
   closed, **Then** nothing of the menu is displayed and no tooltip behaviour applies.

---

### User Story 3 - The drawer around the page is daisy-cotton's drawer (Priority: P2)

Someone opens a page on a laptop. The sidebar is in the state they left it in, with no flicker as
the page loads. They close it with the toggle and it stays closed on the next page. On a phone the
same sidebar is an overlay: the toggle opens it over the page and touching the page behind it
closes it again, without changing what the laptop remembers. A developer who reads the sidebar's
state from the layout store, or who sets the breakpoint and collapse mode for one page, sees no
difference. The shell that does all this is now drawn with daisy-cotton's drawer.

**Why this priority**: The drawer holds the sidebar and carries its open and closed state, so it
is part of what #438 asks for. It comes after the menu itself because the menu can move first and
the drawer cannot move without care for the state it carries.

**Independent Test**: Render a shell page and confirm the drawer's toggle, side region and content
region come from daisy-cotton's drawer, with the layout payload and the script hooks present. In a
browser test, toggle the sidebar at desktop width, reload and confirm the state held from first
paint. Repeat the toggle at phone width and confirm the remembered desktop state is unchanged.

**Acceptance Scenarios**:

1. **Given** a shell page, **When** someone uses the sidebar toggle, **Then** the sidebar opens if
   it was closed and closes if it was open.
2. **Given** a viewport at or above the configured breakpoint, **When** the page renders, **Then**
   the sidebar sits beside the page content. **Given** a viewport below it, **Then** an open
   sidebar overlays the content, and activating the area outside it closes it.
3. **Given** someone closed the sidebar at desktop width, **When** they load another page, **Then**
   the sidebar is closed from the first paint, with no visible change of state while the page
   loads. The same holds for a sidebar left open.
4. **Given** someone opens and closes the overlay below the breakpoint, **When** they later load a
   page at desktop width, **Then** the sidebar is in the state last chosen at desktop width.
5. **Given** a shell page, **When** the sidebar opens or closes, **Then** the layout store reports
   the new state, and the page still publishes the resolved breakpoint and collapse mode for
   scripts to read.
6. **Given** a page that sets its own breakpoint or collapse mode through the shell's attributes,
   **When** it renders, **Then** the drawer follows the page's values over the project's
   configuration.
7. **Given** a project template that uses the drawer shell directly with its own sidebar content,
   **When** it renders, **Then** that content is drawn in the side region and the page content in
   the main region, as before.
8. **Given** a shell page, **When** assistive technology reads the control that toggles the
   sidebar and the area that closes the overlay, **Then** each has an accessible name.
9. **Given** the sidebar is configured to navigate with htmx, **When** someone follows a sidebar
   link from the open overlay, **Then** the new page arrives with the overlay closed.

---

### User Story 4 - Menu entries that need an attribute on the link keep working (Priority: P2)

Someone signed in opens the user menu at the foot of the sidebar and chooses to sign out. The entry
is a button that submits the sign-out form, so they are signed out by a POST with its CSRF token,
never by following a link. On a list page they open the share menu and pick a social network. It
opens in a new tab that cannot reach back into the page they came from. They pick the entry that
copies the link, and the address is copied without the page going anywhere. In a project that
offers several themes, each theme in the chooser is a button they can reach and press from the
keyboard. Each of these depends on an attribute sitting on the link or button itself.

**Why this priority**: These are the entries the upstream gap blocks. They are fewer than the
sidebar's and appear on fewer pages, but sign-out is one of them, and getting it wrong either
breaks signing out or turns it into a link.

**Independent Test**: Render the user menu for a signed-in person and confirm the sign-out entry
is a submit button tied to a form that posts to the sign-out address with a CSRF token. Submit it
and confirm the session ends. Render the share menu and confirm each external link carries its
new-tab and no-opener attributes on the link. Render the theme chooser with several themes and
confirm each choice is a button carrying its theme on the button.

**Acceptance Scenarios**:

1. **Given** a signed-in person, **When** the user menu renders, **Then** the sign-out entry is a
   button that submits a form posting to the project's sign-out address with a CSRF token.
2. **Given** that menu, **When** the person activates the sign-out entry, **Then** they are signed
   out, and the menu offers no link that signs a person out.
3. **Given** a signed-in person and a project where the account area's address resolves, **When**
   the user menu renders, **Then** it carries a link to the account area. **Given** a person who
   is staff, **Then** it also carries a link to the admin site, and a person who is not staff gets
   none.
4. **Given** a project that adds its own rows to the user menu, **When** it renders, **Then**
   those rows sit between the built-in links and the sign-out entry, and the sign-out entry is
   separated from the rows above it only when there are rows above it.
5. **Given** an anonymous visitor, **When** the sidebar footer renders, **Then** no user menu is
   drawn.
6. **Given** the collapsed icon rail, **When** someone opens the user menu, **Then** its rows are
   displayed with their labels.
7. **Given** the share menu, **When** it renders, **Then** every link to an external site opens in
   a new browsing context and denies that context access to the opener, with both attributes on
   the link itself. The address being shared and the page title are encoded into each link.
8. **Given** the share menu, **When** someone activates the copy entry, **Then** the page's
   address is copied and the page does not navigate.
9. **Given** a project that configures several themes, **When** the theme chooser renders,
   **Then** each theme is a button that can be focused and activated from the keyboard, carrying
   the theme it selects on the button itself, and activating it applies that theme.

---

### User Story 5 - The package's own menu entry, group, collapse and divider are gone (Priority: P3)

A developer maintaining a project on this package reads the changelog before upgrading. It tells
them the four menu components this package used to ship are removed, and gives a table from each
old tag and attribute to what replaces it. They search their templates, change the few menu entries
they wrote by hand, and upgrade. A developer new to the package reads the components page and the
navigation page and finds one way to write a menu, the one daisy-cotton documents, with this
package's pages covering only what it adds: the Python declaration, the renderers and the rail.

**Why this priority**: The sidebar works as soon as the first four stories land. This story is
what makes the change safe to release: a second copy of the menu components left in the package,
or documentation that still teaches the old names, is the drift R29 exists to remove.

**Independent Test**: Confirm no template in the package or its demo calls the removed components,
that rendering one of them raises an error naming it, that every documentation example of a menu
renders against the branch, and that the changelog's table covers every removed tag and renamed
attribute.

**Acceptance Scenarios**:

1. **Given** the package after this feature, **When** its component templates are listed, **Then**
   it ships no menu entry, menu group, menu collapse or menu divider component of its own, under
   any name.
2. **Given** a template that calls one of the removed components, **When** it renders, **Then**
   rendering fails with an error that names the missing component.
3. **Given** the package's own templates and its demo application, **When** they are searched,
   **Then** none calls a removed component or passes a removed attribute to a menu entry.
4. **Given** the documentation, **When** each example that draws a menu is rendered against this
   branch, **Then** it renders, and it uses daisy-cotton's menu components.
5. **Given** the changelog entry for this change, **When** a developer looks up any removed tag or
   renamed attribute, **Then** they find what to write in its place.
6. **Given** a project that overrides the sidebar's renderer templates with its own, **When** it
   follows the changelog's table, **Then** its override draws the same menu as before.

---

### Edge Cases

- A menu has no entry the current person can see. The sidebar draws an empty menu, and on a mounted
  app's page the link back to the host alone, as it does today.
- A menu entry has no icon. In the collapsed rail it has nothing to show, which is how it behaves
  today. It still has its accessible name and its tooltip.
- A menu entry's label, badge or address comes from a model or from a person. Each is escaped once
  when drawn, in the entry, in its tooltip and in its accessible name.
- A collapsible parent sits inside another collapsible parent. Each level opens when the current
  page is beneath it.
- A parent entry has no children the current person can see. It is drawn as it is today.
- A project gives an entry no address. It is drawn as a button, not as a link with an empty
  address.
- A project still passes the old attribute names to `<c-menu.item>` after upgrading. The tag now
  reaches daisy-cotton's entry, which does not know them, so the entry renders without its label
  and no error is raised. The changelog names this case first.
- Browser storage is unavailable or holds a value that cannot be read. The sidebar falls back to
  its default state at desktop width and the page still works.
- The page is narrower than the breakpoint when it loads. The remembered desktop state is not
  applied, and the overlay starts closed.
- A project draws a second menu through the sidebar renderer. It gets its own navigation landmark,
  named from its own declaration.
- The installed daisy-cotton is older than the release this feature needs. The package's
  dependency range does not allow that install.

## Requirements *(mandatory)*

### Functional Requirements

**The sidebar menu**

- **FR-001**: The sidebar renderer MUST draw the menu, each entry, each heading row and each
  collapsible parent with daisy-cotton's menu, entry, heading and submenu components. The package
  MUST NOT draw any of them with a menu component of its own.
- **FR-002**: Each visible entry MUST be drawn as a link to its address carrying its label and its
  icon, and an entry with no address MUST be drawn as a button.
- **FR-003**: The entry for the current page MUST be marked as current, in a way assistive
  technology can read, and no other entry may be.
- **FR-004**: An entry's badge MUST be drawn with the entry when one is declared and absent when
  none is.
- **FR-005**: A parent that can collapse MUST be drawn as a disclosure a person can open and
  close, open when the current page is beneath it. A parent that cannot collapse MUST be drawn as
  a heading row that is not interactive, followed by its children.
- **FR-006**: The sidebar MUST contain exactly one navigation landmark per menu it draws, named
  from that menu's declaration. The link back to the host on a mounted app's page MUST NOT add
  one.
- **FR-007**: How a project declares a menu in Python, registers a renderer and names the menu the
  sidebar draws MUST NOT change.
- **FR-008**: Every call this feature writes to a daisy-cotton menu or drawer component MUST be
  isolated from the page's context, so that a page variable sharing a name with one of the
  component's attributes never changes what is drawn.

**The icon rail**

- **FR-009**: In the collapsed rail every entry, including the link back to the host, MUST keep an
  accessible name equal to its label.
- **FR-010**: In the collapsed rail an entry's label, its badge and every heading row MUST NOT be
  displayed, and hovering or focusing an entry MUST display its label as a tooltip that the rail
  does not cut off. With the sidebar open, no tooltip is displayed.
- **FR-011**: In the collapsed rail, hovering or focusing a collapsible parent MUST display its
  children beside the rail with their labels. A menu inside a dropdown panel opened from the rail,
  such as the user menu, MUST display its rows with their labels. The two documented classes that
  hide content in the rail and show content only in the rail MUST keep working.

**The drawer**

- **FR-012**: The drawer shell MUST draw its toggle, its side region, its overlay and its content
  region with daisy-cotton's drawer.
- **FR-013**: The sidebar MUST sit beside the content at and above the configured breakpoint and
  overlay it below, and activating the overlay MUST close it. The toggle and the overlay MUST each
  have an accessible name.
- **FR-014**: The sidebar's open or closed state at desktop width MUST be remembered between page
  loads and applied before the first paint. Toggling the overlay below the breakpoint MUST NOT
  change the remembered state. When storage cannot be read, the sidebar MUST fall back to its
  default state.
- **FR-015**: The layout store MUST keep reporting the sidebar's state in step with the drawer,
  and the page MUST keep publishing the resolved layout values for scripts to read.
- **FR-016**: The breakpoint, the collapse mode, the pinned header and htmx navigation MUST keep
  resolving from the component attribute first, then the project's configuration, then the
  package default.
- **FR-017**: A project that uses the drawer shell directly with its own sidebar content MUST keep
  working. Any id or `data-` attribute on the drawer that a project's script or stylesheet could
  depend on MUST either be kept or be listed in the changelog with its replacement.

**Entries that need an attribute on the link or button**

- **FR-018**: The sign-out entry MUST be a button that submits a form posting to the project's
  sign-out address with a CSRF token. Nothing in the user menu may sign a person out with a GET
  request.
- **FR-019**: The user menu MUST keep its contents and their conditions: a link to the account
  area when its address resolves, a link to the admin site for staff only, a project's own rows
  between those and sign-out, a separator before sign-out only when there are rows above it, and
  nothing at all for an anonymous visitor.
- **FR-020**: Every share link to an external site MUST open in a new browsing context and deny it
  access to the opener, with both attributes on the link itself. The copy entry MUST copy the
  page's address without navigating. Each theme in the theme chooser MUST be a keyboard-operable
  button carrying its theme on the button itself.
- **FR-021**: The package's dependency on daisy-cotton MUST require the first release in which a
  caller can put attributes on a menu entry's link or button. The entries in FR-010, FR-018 and
  FR-020 MUST be built on that, and MUST NOT be built on a workaround in this package.

**Removing the package's own components**

- **FR-022**: The package's own menu entry, menu group, menu collapse and menu divider components
  MUST be removed, with no alias left under the old or any new name. Every template in the
  package and in its demo application that called them MUST call daisy-cotton's components.
- **FR-023**: The dropdown that holds the user menu, the share menu and the theme chooser, and the
  trigger of each, MUST NOT be changed by this feature.

**Shipping it**

- **FR-024**: The changelog MUST record the change as breaking, with a table from every removed
  tag and every renamed or removed attribute to its replacement, and MUST call out that a
  `<c-menu.item>` still given the old attribute names renders without its label (Article XVI).
- **FR-025**: The documentation MUST describe menus as they are after this feature: the components
  page, the navigation page, the layout page's account of the rail and the drawer, and every
  example that writes a menu entry. `CONTEXT.md`'s component list MUST drop the removed
  components. The shipped skill's routing table MUST still point at the right pages (Articles VI
  and XVII).
- **FR-026**: If the changed templates use a class the shipped stylesheet does not already carry,
  the stylesheet MUST be rebuilt and committed on this branch (Article XV).
- **FR-027**: Every changed component MUST keep a test of its rendered markup, and the rail and
  the remembered drawer state MUST keep their browser tests (Articles XIII and XIV). Tests that
  only assert the removed components' markup are removed with them.
- **FR-028**: Every string this feature renders to a person MUST stay translatable (Article VIII).
- **FR-029**: This feature MUST NOT cut a release. It lands on the main branch with the rest of
  R29, which ships as one breaking minor release.

### Requirement coverage

| Story | Requirements |
|---|---|
| US-1 — The sidebar menu is drawn with daisy-cotton's menu components | FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-026, FR-027, FR-028 |
| US-2 — The collapsed icon rail keeps working | FR-008, FR-009, FR-010, FR-011, FR-021, FR-026, FR-027 |
| US-3 — The drawer around the page is daisy-cotton's drawer | FR-008, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017, FR-026, FR-027, FR-028 |
| US-4 — Menu entries that need an attribute on the link keep working | FR-008, FR-018, FR-019, FR-020, FR-021, FR-023, FR-027, FR-028 |
| US-5 — The package's own menu entry, group, collapse and divider are gone | FR-022, FR-024, FR-025, FR-029 |

Every story that changes something the *Shipping it* requirements describe carries them: it
updates the pages describing what it changed and adds its rows to the changelog table. FR-024's
entry is opened by the first story and completed by the last.

### Key Entities

- **Menu entry**: one row of a menu, drawn as a link when it has an address and as a button when
  it does not. It may carry an icon, a badge and a current-page marking.
- **Collapsible parent**: a menu entry with children, drawn as a disclosure. In the collapsed rail
  its children open beside the rail.
- **Icon rail**: the sidebar's collapsed state when a project sets the collapse mode to icons.
  Entries show their icon alone and name themselves by tooltip.
- **Drawer shell**: the component that wraps the page in a drawer, with the sidebar in its side
  region. It owns the toggle and is the source of truth for whether the sidebar is open.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The package ships none of its own menu entry, group, collapse or divider components,
  and no template in the package or its demo calls one.
- **SC-002**: A project that declares its menus in Python and writes no menu entry by hand
  upgrades without changing a line, and its sidebar offers the same entries, links, current-page
  marking and groups as before.
- **SC-003**: In the collapsed icon rail, every entry has an accessible name, and every entry
  shows its label in a tooltip that is not cut off.
- **SC-004**: The sidebar's open state at desktop width survives a page load with no visible
  change of state while the page loads, and toggling the overlay on a narrow screen leaves it
  untouched.
- **SC-005**: Signing out from the user menu ends the session through a POST carrying a CSRF
  token, and every external share link opens in a new browsing context without opener access.
- **SC-006**: A developer who wrote menu entries by hand can bring them up to date from the
  changelog's table alone, without reading either package's source.
- **SC-007**: A page variable named like a menu or drawer attribute changes nothing the sidebar,
  the user menu or the drawer draws.
- **SC-008**: Every acceptance scenario above is proved by a test that fails if the behaviour is
  removed, and every changed component carries rendered-markup assertions (Articles I and XIII).

## Assumptions

- #435 has landed before this feature starts. A bare `<c-menu>` already means daisy-cotton's menu,
  and the sidebar's menu container already uses it inside a named navigation landmark. This
  feature keeps that landmark and does not introduce it.
- #434 has landed before this feature starts, so the components this package keeps carry the
  `mvp.` prefix. If the four menu components this feature removes were renamed by #434, they are
  removed under the names they then carry.
- django-mvp/daisy-cotton#120 is closed and released before this feature starts. If daisy-cotton
  declines the change in every form, this feature stops and goes back to its maintainer. It does
  not ship its own menu entry to get around the gap, because that is the second copy R29 removes.
- Wherever daisy-cotton's drawer cannot carry something the drawer shell needs, the gap is raised
  on daisy-cotton and this feature waits for it, as R29 says. Whether there is such a gap is
  established when the work is planned.
- The dropdown that holds the user menu, the share menu and the theme chooser, and the trigger of
  each, belong to #437. The navbar's button that opens the drawer and the rest of the shell's
  hand-written markup belong to #440. The buttons, badges and the mobile dock belong to #435.
- The sidebar's header and its fixed footer keep their composition. Only the user menu inside the
  footer changes, and only in how its rows are drawn.
- The pages are meant to look as they do now. A difference a person can see that comes from
  daisy-cotton's markup, and that no requirement above covers, is judged when the pull request is
  reviewed and is not a requirement of this specification.
- Packages built on this one that write menu entries by hand move in their own repositories,
  around the release that carries R29. This feature changes none of them.
- No workflow under `.github/` changes.
