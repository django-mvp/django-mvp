# Feature Specification: An Account Center in the shell that any app can add a page to

**Feature Branch**: `028-move-account-center`

**Created**: 2026-09-14

**Status**: Draft

**Serves**: G1 (a complete, responsive application shell that a project configures rather than builds), G7 (customization that never dead-ends, from view configuration through component override to a project's own CSS)

**Roadmap**: — (no item covers the account area; R16 and R22 are about third-party integrations and this is shell surface. Possible roadmap gap.)

**Issue**: #338

**Input**: A project that wants to give people somewhere to manage their own account has to adopt django-accounts-center to get one, because the sub-navigation, the page layout, the landing page and the address they live at all belong to that package. The Account Center should be part of the shell instead, so that any installed app can add a page to it, and django-accounts-center becomes one consumer of that surface rather than its owner.

## Clarifications

### Session 2026-09-14

Five ambiguities were found by the coverage scan and resolved from the intake discussion, the
package's constitution and its README. Longer rationale is in `decisions.md`.

- **Q: django-accounts-center already declares a menu under the name this feature wants. What
  happens in a project that installs both?**
  A: The name is kept here, and the overlap is resolved by django-accounts-center's own next
  release rather than by a second name. Menus register against one global tree and are looked up
  by name, so two menus sharing a name means one of them silently wins and the other's entries
  never render — a name chosen to dodge that would then be the wrong name forever, for the sake of
  a transitional period in one downstream package. Article XVI allows the change pre-1.0 with a
  changelog entry, which is where the version relationship is stated. Recorded as FR-023.

- **Q: How does the area reach a project's URLs — a URLconf the project includes, or a view the
  project wires up itself?**
  A: An includable URLconf, mounted at a prefix the project chooses, with the landing page's URL
  name left un-namespaced. This is the package's first URLconf, so the choice sets a precedent:
  un-namespaced keeps the name the shell's own user menu already reverses, and keeps every page
  already written against that name working. Recorded as FR-001 and FR-002.

- **Q: What does a project see if it installs the package and never includes the URLconf?**
  A: Exactly what it sees today. Every reverse of the area's name in shipped markup is already
  conditional, so the entry disappears from the user menu and nothing raises. The area is opted
  into by mounting it, and there is no setting that disables it separately. Recorded as FR-003 and
  in Assumptions.

- **Q: Does the area require a signed-in user for pages other apps add to it?**
  A: It requires one for its own landing page, and a contributed page answers that question for
  itself. The area does not sit in front of another app's view and cannot gate it, and a menu
  entry can already be hidden per request by the check it carries. Recorded as FR-004 and FR-009.

- **Q: When no installed app has contributed anything, does the landing page fall back to listing
  the menu?**
  A: No. It renders its own heading and introduction with an empty card region. The menu is
  already the navigation and is on the page beside it, so a fallback would draw the same links
  twice. Recorded as FR-019.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - An account area that comes with the shell (Priority: P1)

A developer builds a project on this package alone, with no account-management package installed.
They include the area's URLs in their project and sign in. There is an Account Center: a landing
page rendered inside the usual application shell, with its own navigation panel beside the
content, reachable from the user menu in the sidebar where the link has always been drawn. The
page tells them what the area is for and shows nothing else, because nothing has been added to it
yet. Nothing about the sidebar, navbar or mobile dock changes on this page.

**Why this priority**: It is the surface every other part of the feature attaches to, and on its
own it closes a gap the shell already has — the user menu draws a link to this area and names an
icon for it today, and in a project without django-accounts-center that link goes nowhere and the
icon is not registered.

**Independent Test**: Install the package into a project with no other account package, include
the URLconf, sign in, and open the area. The page renders in the shell with its navigation panel,
and the link in the user menu resolves to it.

**Acceptance Scenarios**:

1. **Given** a project with only this package installed and the URLconf mounted, **When** a
   signed-in person opens the area's address, **Then** the landing page renders inside the
   application shell with its navigation panel and no cards.
2. **Given** the same project, **When** a signed-in person opens any page carrying the shell's
   user menu, **Then** that menu offers a link to the area and the link resolves.
3. **Given** the same project, **When** an anonymous visitor opens the area's address, **Then**
   they are sent to the project's configured sign-in location.
4. **Given** a project that installs the package but never mounts the URLconf, **When** any page
   renders, **Then** no reverse fails and the user menu omits the link.
5. **Given** a viewport below the shell's navigation breakpoint, **When** the area renders,
   **Then** the navigation panel is presented as a collapsed control rather than a persistent
   panel, and the entries in it are the same entries.

---

### User Story 2 - An app adds its own page to the area (Priority: P2)

A developer has an app that needs one account-related page: notification preferences, API keys, a
billing summary. They add an entry to the Account Center menu from their app and write their page
against the area's layout. The page comes back looking like part of the area, with the same
navigation panel, their entry marked as the one being viewed, and a trail above the content naming
the area and the page within it. They install nothing else, import from no other account package
and extend none of its templates. Where their entry only applies to some people, they attach a
check to it and the entry appears only for those it applies to.

**Why this priority**: This is the point of the feature. Story 1 gives the area somewhere to live,
and this is the part that lets anything be put into it.

**Independent Test**: In a project with a test app that declares one menu entry and one page
extending the area's layout, open that page and confirm it renders with the area's navigation, its
own entry marked as current, and the trail above the content, with no other account package
installed.

**Acceptance Scenarios**:

1. **Given** an installed app that appends an entry to the area's menu, **When** any page in the
   area renders, **Then** the navigation panel shows that entry alongside the landing-page entry.
2. **Given** an installed app whose page extends the area's layout, **When** that page renders,
   **Then** it carries the area's navigation panel and the shell around it, with only the app's
   own content inside.
3. **Given** that app's page is the one being viewed, **When** it renders, **Then** its menu entry
   is marked as current and the trail above the content names the area and that page.
4. **Given** a page below one of those entries rather than at the entry's own address, **When** it
   renders, **Then** the trail names the section the page belongs to and links back to it.
5. **Given** a menu entry carrying a check that answers no for the person making the request,
   **When** the area renders for them, **Then** the entry is absent; **Given** a request the check
   answers yes for, **Then** the entry is present.
6. **Given** an entry whose address cannot be resolved, **When** the area renders, **Then** the
   entry is omitted and the rest of the menu renders.
7. **Given** a page in the area that no menu entry points at, **When** it renders, **Then** it
   still gets the layout, with no entry marked as current and a trail naming the area alone.

---

### User Story 3 - An app contributes a card to the landing page (Priority: P3)

The same developer wants their app's page to be discoverable from the area's landing page rather
than only from the navigation. They declare a card on their app's configuration and it appears in
the landing page's card region, showing whatever their card needs to show. A project that installs
two such apps gets both cards, and a project that installs neither gets the landing page with no
cards, as in Story 1.

**Why this priority**: It makes the landing page worth visiting, but an area whose pages are
reachable from its navigation is usable without it.

**Independent Test**: In a project with two test apps that each declare a card, open the landing
page and confirm both cards render with their own content. Remove one app and confirm only the
other's card renders.

**Acceptance Scenarios**:

1. **Given** an installed app declaring a card for the area, **When** a signed-in person opens the
   landing page, **Then** the card renders in the page's card region.
2. **Given** that app also supplies extra information for its card, **When** the landing page
   renders, **Then** the card can show that information.
3. **Given** two installed apps each declaring a card, **When** the landing page renders, **Then**
   both cards render.
4. **Given** an app that declares no card, **When** the landing page renders, **Then** nothing is
   contributed on its behalf and no error occurs.

---

### Edge Cases

- A project that mounts the URLconf at a prefix of its own choosing: every link the area draws
  still resolves, because none of them assume a prefix.
- A project running an account-management package that declares its own menu under the same name:
  one of the two menus wins the name lookup. Covered by FR-023, which puts the version
  relationship in the changelog; the overlap ends when that package adopts this surface.
- An app contributing an entry whose address does not exist in the project's URLs: the entry is
  dropped, as any menu entry with an unresolvable address already is.
- A contributed page that is not itself restricted to signed-in people: it is reachable as its
  author wrote it. The area gates its own landing page and does not sit in front of another app's
  view.
- A contributed card whose template raises: the landing page fails as any page with a broken
  template does. Cards are trusted code from installed apps, not user input.

## Requirements *(mandatory)*

### Functional Requirements

**The area and its address**

- **FR-001**: The package MUST ship a URLconf a project includes at a prefix of its own choosing,
  carrying the area's landing page.
- **FR-002**: The landing page's URL name MUST be `account-center`, un-namespaced, so that markup
  already written against that name keeps resolving.
- **FR-003**: A project that installs the package without including that URLconf MUST see no
  failure: every reverse of the name in shipped markup stays conditional, and the entry is omitted
  from the shell's user menu.
- **FR-004**: The landing page MUST require an authenticated user and send an anonymous visitor to
  the project's configured sign-in location.
- **FR-005**: Pages in the area MUST render inside the application shell, leaving sidebar, navbar,
  footer and mobile dock as any other page has them.

**The menu**

- **FR-006**: The package MUST declare the area's menu in its own menus module, importable by any
  app that wants to add to it, in the same way the shell's sidebar and dock menus are declared.
- **FR-007**: The menu MUST ship carrying only the entry for the area's own landing page, leaving
  every other entry to whoever installs a page into the area.
- **FR-008**: An installed app MUST be able to add entries to the menu, including a labelled group
  of entries, and to reorder or remove what is there.
- **FR-009**: A menu entry MUST be able to carry a per-request check so that it is shown only to
  the people it applies to, and an entry carrying no check MUST always be shown.
- **FR-010**: An entry whose address cannot be resolved MUST be omitted from the rendered menu
  without affecting the rest of it.
- **FR-011**: The icon the shell's user menu names for this area MUST be registered in the
  package's own icon pack, so the link renders with its icon in a project with no other package
  installed.

**The page layout**

- **FR-012**: The package MUST provide a layout that any installed app's page extends to become a
  page of the area, without referencing a template belonging to another package.
- **FR-013**: The layout MUST render the area's menu beside the page content: a persistent panel
  at wide viewports and a collapsed control below the shell's navigation breakpoint, from one
  declaration of the menu rather than two.
- **FR-014**: The layout MUST mark the entry matching the current page as the one being viewed.
- **FR-015**: The layout MUST render a trail above the content naming the area and, where the
  current page is one of the area's sections, that section.
- **FR-016**: A page below a section's own address MUST resolve to that section in the trail, with
  the section named and linked, through a declaration the section's own entry carries.
- **FR-017**: The layout MUST be built from the package's existing components, with no raw utility
  classes standing in for a component (Article XI).

**The landing page**

- **FR-018**: The landing page MUST render cards contributed by installed apps, through two
  optional attributes an app declares on its application configuration: one naming a template to
  render, one supplying additional information for it.
- **FR-019**: With no app contributing a card, the landing page MUST render its own heading and
  introduction with an empty card region, and MUST NOT fall back to listing the menu.
- **FR-020**: Any installed app MUST be able to contribute a card, not only an app that also adds
  a menu entry.

**Shipping it**

- **FR-021**: The documentation MUST cover mounting the area, adding a menu entry, writing a page
  against the layout and contributing a card, with a worked example of each (Article VI).
- **FR-022**: The shipped stylesheet MUST be rebuilt so that every class the new templates use is
  present in it, and the rebuilt artifact committed on this branch (Article XV).
- **FR-023**: The changelog MUST record the new surface and state its relationship to the versions
  of django-accounts-center that declare a menu of the same name (Article XVI).
- **FR-024**: Every string the area renders to a person MUST be translatable (Article VIII).
- **FR-025**: The shipped skill MUST describe the area alongside the rest of the shell, since it
  is the first thing a coding agent reads before writing against this package (Article XVIII).
- **FR-026**: The README's statement of what the package deliberately is not MUST be restated: the
  package provides the area, and account management itself still lives in django-accounts-center.

### Requirement coverage

| Story | Requirements |
|---|---|
| US-1 — An account area that comes with the shell | FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-011, FR-012, FR-013, FR-017, FR-019, FR-021, FR-022, FR-023, FR-024, FR-025, FR-026 |
| US-2 — An app adds its own page to the area | FR-008, FR-009, FR-010, FR-014, FR-015, FR-016, FR-021, FR-022, FR-024, FR-025 |
| US-3 — An app contributes a card to the landing page | FR-018, FR-020, FR-021, FR-022, FR-024, FR-025 |

The requirements under *Shipping it* are carried by every story that changes what they describe:
each story documents its own surface, rebuilds the stylesheet if it added classes, and keeps the
skill current. FR-023 and FR-026 are release-level statements and land with the first story.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A project with this package as its only account-related dependency has a working
  Account Center after one edit to its URLs, and no other installation step.
- **SC-002**: An app adds a page to the area with two declarations: one menu entry and one page
  extending the area's layout. It imports nothing from, and extends no template of, any other
  account package.
- **SC-003**: Every link the shell already draws to this area resolves in a project with no other
  account package installed, where today none of them do.
- **SC-004**: The landing page renders for a signed-in person when no app has contributed anything
  to it.
- **SC-005**: A developer can add a page, a menu entry and a card by following the documentation
  alone, without reading the package's source.
- **SC-006**: Every acceptance scenario above is proved by a test that fails if the behaviour is
  removed, and the area's pages carry the same rendered-markup assertions every other packaged
  page has (Articles I, X, XIII).

## Assumptions

- django-accounts-center is not modified by this work and nothing here is coordinated with a
  change in it. It keeps its own copies of what is built here until its own next release, and the
  scope it is left with afterwards is decided separately.
- The anonymous-facing entrance layout, the branded card that sign-in, sign-up and recovery pages
  render into, is not part of the account area and stays where it is.
- The two-column arrangement this feature ships is built for the account area alone. Generalising
  it, and finding a general way to attach a menu to a view class or a group of addresses, is later
  work that this feature neither attempts nor designs for.
- The area is opted into by mounting its URLconf. No setting turns it on or off, and none
  relocates it.
- The area carries no models and stores nothing. It is navigation, a layout and a landing page.
- The names in use today are kept: the area is the Account Center, singular, in US spelling, and
  its address is named `account-center`.
