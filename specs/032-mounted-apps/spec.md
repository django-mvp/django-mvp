# Feature Specification: Mount one django-mvp app inside another

**Feature Branch**: `032-mounted-apps`

**Created**: 2026-09-25

**Status**: Draft

**Serves**: G1 (a complete, responsive application shell that a project configures rather than builds), G7 (customization that never dead-ends, from view configuration through component override to a project's own CSS)

**Roadmap**: — No roadmap item covers this. Recorded here as a possible roadmap gap.

**Issue**: #402

**Input**: A package built on django-mvp should be able to run as a site in its own right and
also be mounted inside another django-mvp project, without changing its code. django-literature
and FairDM are the motivating pair. Each is deployable on its own and fills the sidebar with its
own navigation, and FairDM also wants to include django-literature as one part of itself. Today
the only option is for the host to fold the other package's menu into its own, which means a large
menu drawn on every page and a long integration guide. A package declares itself a mounted app,
with a name, an icon, its own menu, its URLs and an optional check on who may see it. On its own
pages the sidebar swaps to the app's menu, headed by a link back to the host, and every other page
keeps the host's menu. The built-in Account Center becomes the first mounted app.

## Clarifications

### Session 2026-09-25

The coverage scan found five ambiguities. Each was resolved from the intake discussion on #402,
the package's constitution and the Account Center's specification (FS-028). Longer rationale is
in `decisions.md`.

- **Q: What does the browser title read on a mounted app's pages?**
  A: The title today reads `<page title> | <site name>`. Inside a mounted app, the app's name goes
  before the site name: `<page title> | <app name> | <site name>`. A page with no title of its own,
  such as the app's landing page, reads `<app name> | <site name>`. Recorded as FR-008.

- **Q: Which name does the link back to the host carry, and where does it go?**
  A: The host's site name, the same name the page title already ends with. It goes to the host's
  home page, the address the sidebar brand links to. The sidebar title was the other candidate and
  was rejected because it is empty by default. Recorded as FR-007.

- **Q: What happens when someone the app's visibility check excludes requests one of its pages?**
  A: An anonymous visitor is sent to the project's sign-in page and a signed-in person is refused
  as forbidden, which is how Django already answers a failed permission check. The app's entry in
  the host's menus is absent for them. Recorded as FR-012 and FR-013.

- **Q: What happens if a project mounts the same app twice, or mounts an app inside another
  mounted app?**
  A: Neither is supported. Both are refused when the project starts, with an error that names the
  app. Silently picking one of two mounts would make the sidebar depend on URL order. Recorded as
  FR-014 and FR-015.

- **Q: How does a package that is also a site in its own right show its menu as the main sidebar?**
  A: The project names one mounted app as its main app. That app's menu becomes the sidebar on
  every page that belongs to no other mounted app, with no back link, because there is nothing to
  go back to. The package itself never writes into the host's menu, so the same code serves both
  deployments. Recorded as FR-016 to FR-018.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A host project mounts an app and its pages carry the app's menu (Priority: P1)

A developer builds FairDM on django-mvp and wants to include django-literature, which is also
built on django-mvp and declares itself a mounted app. They install the package and add one line
to their project's URLs, choosing the address the app lives under. They add one entry for the app
to their own sidebar menu, taking its label, icon and address from the app's declaration rather
than restating them. Someone using FairDM clicks that entry and lands in the literature pages. The
sidebar now shows the literature menu under a "Back to FairDM" link, and the browser tab names the
literature app as well as FairDM. The back link returns them to FairDM's home page, where FairDM's
own menu is back. The header, brand, footer, theme, user menu and mobile dock stay FairDM's
throughout. No literature entry ever appears in FairDM's menu beyond the one FairDM added.

**Why this priority**: This is the feature. The other stories apply it to the package's own area
or refine who can reach a mounted app.

**Independent Test**: In a test project with one test app declared as a mounted app, mount it
under a prefix and add its entry to the host menu. Request a page inside the app and confirm the
sidebar carries the app's menu and the back link and not the host's menu, and that the title
carries both names. Request a page outside the app and confirm the host's menu is drawn and the
app's is not.

**Acceptance Scenarios**:

1. **Given** a host project that mounts an app under a prefix of its choosing, **When** a page
   served by the app is requested, **Then** the sidebar renders the app's menu and does not render
   the host's menu.
2. **Given** the same project, **When** a page served by the app is requested, **Then** the top of
   the sidebar carries a link labelled "Back to <site name>" that goes to the host's home page.
3. **Given** the same project, **When** a page that does not belong to the app is requested,
   **Then** the sidebar renders the host's menu and the app's menu is not rendered.
4. **Given** a page in the app that declares its own title, **When** it renders, **Then** the
   browser title reads `<page title> | <app name> | <site name>`. **Given** a page in the app with
   no title of its own, **Then** it reads `<app name> | <site name>`.
5. **Given** a host that adds an entry for the app to one of its menus from the app's declaration,
   **When** that menu renders, **Then** the entry carries the app's name, icon and landing address
   without the host restating them.
6. **Given** a host that draws an entry for the app in a menu still visible inside the app, such as
   the mobile dock, **When** a page in the app renders, **Then** that entry is marked as current.
7. **Given** the app is mounted under a different prefix, **When** any of its pages render,
   **Then** every link the app's menu draws still resolves.
8. **Given** a project that mounts no app, **When** any page renders, **Then** the sidebar, title
   and menus are exactly what they were before this feature.

---

### User Story 2 - The Account Center is a mounted app (Priority: P2)

A person using a project built on django-mvp opens the Account Center from the user menu. Today
its pages draw a second navigation panel next to the content, a card on wide screens and a
drop-down on narrow ones, while the sidebar still shows the whole application menu. After this
change the Account Center behaves like any other mounted app. On its pages the sidebar carries the
Account Center menu under "Back to <site name>", the panel next to the content is gone, and the
content has the full width of the page. An app that already adds a page or a card to the Account
Center keeps working without being changed.

**Why this priority**: It replaces the one place the package already solved this problem with a
one-off layout, and it proves the mechanism on a real area of the package. The mechanism in
Story 1 stands without it.

**Independent Test**: In a project with only this package installed and its URLs mounted, sign in
and open the Account Center. Confirm the sidebar carries the Account Center menu and the back link,
and the page has no second navigation panel. In a project with a test app that adds an entry and a
page to the Account Center, confirm that page renders with its entry in the sidebar marked as
current, with the test app unchanged.

**Acceptance Scenarios**:

1. **Given** a project with the package's URLs mounted, **When** a signed-in person opens the
   Account Center, **Then** the sidebar carries the Account Center menu under "Back to
   <site name>", and the host's menu is not rendered.
2. **Given** the same page, **When** it renders at any viewport width, **Then** no second
   navigation panel or drop-down is drawn next to or above the content.
3. **Given** an installed app that appends an entry to the Account Center menu and ships a page
   written against the Account Center layout, **When** that page renders, **Then** it renders
   inside the Account Center with its entry in the sidebar marked as current, and the app needs no
   change.
4. **Given** an installed app that contributes a card to the Account Center's landing page,
   **When** the landing page renders, **Then** the card renders as before.
5. **Given** the Account Center's landing page, **When** it renders, **Then** the browser title
   names the Account Center and the site.
6. **Given** an anonymous visitor, **When** they open the Account Center's landing page, **Then**
   they are sent to the project's sign-in page, as before.

---

### User Story 3 - A package runs as a site in its own right (Priority: P2)

The developers of django-literature deploy it as a site of its own as well as offering it to
FairDM. In their own project they mount the app and name it as the main app. Its menu is the
sidebar on every page that belongs to no other mounted app. No back link is drawn, because there
is nothing to go back to, and the title reads as on any other site. The same package, unchanged,
is what FairDM mounts in Story 1.

**Why this priority**: It is half of the motivating case, since both packages want to be
deployable on their own. It comes after Story 1 because a package can be mounted before it is ever
deployed alone, and a standalone project can build its own menu by hand in the meantime.

**Independent Test**: In a test project that mounts one test app and names it as the main app,
request a page of the app and a page belonging to neither the app nor the Account Center. Confirm
both render the app's menu as the sidebar with no back link. Open the Account Center and confirm
it still swaps to its own menu, with a back link.

**Acceptance Scenarios**:

1. **Given** a project that names a mounted app as its main app, **When** any page that belongs to
   no other mounted app renders, **Then** the sidebar renders the main app's menu.
2. **Given** the same project, **When** such a page renders, **Then** no back link is drawn and the
   browser title carries no app name beyond what it would carry without this feature.
3. **Given** the same project, **When** a page of another mounted app, such as the Account Center,
   renders, **Then** the sidebar swaps to that app's menu with a back link, as in Story 1.
4. **Given** the same package mounted in a different host project that does not name it as its
   main app, **When** its pages render, **Then** they behave as in Story 1, with no change to the
   package.
5. **Given** a project that names more than one main app, or names an app it has not mounted,
   **When** the project starts, **Then** it is refused with an error that names the problem.

---

### User Story 4 - A mounted app is visible only to the people it applies to (Priority: P3)

The developer of a mounted app, or the host mounting it, wants the app reachable only by some
people, for example staff. They attach a check to the app. For someone the check excludes, the
host's entry for the app is absent from every menu and the app's pages refuse them. Everyone else
sees the app as in Story 1.

**Why this priority**: It completes the mechanism for administrative apps, but an app with no
check, or one that protects its own views, is fully usable without it.

**Independent Test**: Mount a test app carrying a check that admits staff only, and add its entry
to the host menu. Render the host's home page as a staff member and as a regular user, and confirm
the entry is present only for the staff member. Request a page of the app anonymously, as a
regular user and as staff, and confirm the three responses.

**Acceptance Scenarios**:

1. **Given** a mounted app carrying a check the current request fails, **When** any host menu
   holding an entry for the app renders, **Then** the entry is absent.
2. **Given** the same app, **When** an anonymous visitor requests one of its pages, **Then** they
   are sent to the project's sign-in page.
3. **Given** the same app, **When** a signed-in person the check excludes requests one of its
   pages, **Then** the request is refused as forbidden.
4. **Given** the same app, **When** a person the check admits requests one of its pages, **Then**
   the page renders as in Story 1.
5. **Given** a mounted app that carries no check, **When** any request is made, **Then** its entry
   and its pages are available as in Story 1.

---

### Edge Cases

- A host mounts an app but never adds an entry for it to any menu. The app's pages still work and
  still swap the sidebar, and people reach it from whatever links the host draws.
- A mounted app's menu has no entry the current person can see. The sidebar renders the back link
  alone, so the person always has a way out.
- A mounted app's menu has an entry whose address cannot be resolved. The entry is omitted, as any
  menu entry with an unresolvable address already is.
- A page inside a mounted app raises an error and the project's error page renders. The error page
  renders the way it would anywhere else in the project.
- The site has no name configured. The back link and the title fall back the same way the page
  title does today, and neither renders an empty name.
- The Account Center carries no visibility check. Its landing page keeps requiring a signed-in
  person, and a page another app contributes keeps deciding its own access, as FS-028 specified.
- An app is mounted at the site root without being named the main app. Its pages are identified by
  the URLs they were served through, not by address prefix, so the host's other pages keep the
  host's menu.
- A project writes a page that uses the sidebar component with a menu of its own choosing. That
  page keeps the menu it asked for.

## Requirements *(mandatory)*

### Functional Requirements

**Declaring and mounting an app**

- **FR-001**: A package MUST be able to declare itself a mounted app, carrying a name, an icon, its
  own menu, its URLs and its landing page.
- **FR-002**: A host project MUST be able to mount a declared app with one line in its own URLs, at
  an address of its own choosing.
- **FR-003**: A mounted app's menu MUST be its own. Declaring or mounting an app MUST NOT add
  anything to the host's menus.
- **FR-004**: A host MUST be able to add an entry for a mounted app to any of its menus from the
  app's declaration, with the entry carrying the app's name, icon and landing address.

**Pages inside a mounted app**

- **FR-005**: On a page served by a mounted app, the sidebar MUST render the app's menu in place of
  the host's, and the host's menu MUST NOT be rendered on that page.
- **FR-006**: Which app a page belongs to MUST be decided from the URLs the page was served
  through, not by comparing the page's address with a prefix.
- **FR-007**: On a page served by a mounted app, the sidebar MUST carry a link at its top labelled
  "Back to <site name>" that goes to the host's home page. The site name MUST be the one the page
  title already uses.
- **FR-008**: On a page served by a mounted app, the browser title MUST read
  `<page title> | <app name> | <site name>`, or `<app name> | <site name>` for a page with no
  title of its own.
- **FR-009**: Any host menu entry for a mounted app that is drawn on the app's own pages, such as
  one in the mobile dock, MUST be marked as current there.
- **FR-010**: On every page that belongs to no mounted app, the sidebar, title and menus MUST
  render exactly as they did before this feature.
- **FR-011**: The header, brand, footer, theme, user menu and mobile dock MUST remain the host's on
  every page, inside a mounted app or not.

**Who can reach a mounted app**

- **FR-012**: A mounted app MUST be able to carry a per-request check. A request the check fails
  MUST NOT see the app's entry in any host menu.
- **FR-013**: A request the check fails MUST be refused on every page of the app. An anonymous
  visitor is sent to the project's sign-in page, and a signed-in person is refused as forbidden. An
  app with no check MUST be open to every request its own views allow.

**What is refused**

- **FR-014**: Mounting the same app more than once in one project MUST be refused when the project
  starts, with an error that names the app.
- **FR-015**: Mounting an app inside the URLs of another mounted app MUST be refused when the
  project starts, with an error that names both apps.

**An app as a site in its own right**

- **FR-016**: A project MUST be able to name one mounted app as its main app.
- **FR-017**: A main app's menu MUST be the sidebar on every page that belongs to no other mounted
  app, with no back link, and the browser title MUST read as it does without this feature.
- **FR-018**: Naming more than one main app, or naming an app the project has not mounted, MUST be
  refused when the project starts, with an error that names the problem.

**The Account Center**

- **FR-019**: The Account Center MUST be a mounted app, declared by this package and mounted
  wherever the package's URLs are included, with the Account Center menu as its menu.
- **FR-020**: The Account Center's pages MUST NOT draw a second navigation panel or drop-down next
  to or above their content, and the content MUST take the full width of the page.
- **FR-021**: An app that adds an entry to the Account Center menu, writes a page against the
  Account Center layout, or contributes a card to its landing page MUST keep working without
  change.
- **FR-022**: The Account Center MUST keep its existing access rules. Its landing page requires a
  signed-in person, and a page another app contributes decides its own access.

**Shipping it**

- **FR-023**: The documentation MUST cover declaring a mounted app, mounting one, adding its entry
  to a host menu, naming a main app and attaching a visibility check, with a worked example of
  each (Articles VI and XVIII).
- **FR-024**: `CONTEXT.md` MUST define **Mounted app** and **Host project**.
- **FR-025**: The changelog MUST record the new surface and the change to the Account Center's
  layout (Article XVI).
- **FR-026**: Every string this feature renders to a person MUST be translatable (Article VIII).
- **FR-027**: If the new templates use a class the shipped stylesheet does not already carry, the
  stylesheet MUST be rebuilt and committed on this branch (Article XV).
- **FR-028**: The shipped skill's routing table MUST point at the page documenting mounted apps
  (Article XVIII).

### Requirement coverage

| Story | Requirements |
|---|---|
| US-1 — A host project mounts an app and its pages carry the app's menu | FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-014, FR-015, FR-023, FR-024, FR-025, FR-026, FR-027, FR-028 |
| US-2 — The Account Center is a mounted app | FR-019, FR-020, FR-021, FR-022, FR-023, FR-025, FR-027 |
| US-3 — A package runs as a site in its own right | FR-016, FR-017, FR-018, FR-023, FR-025 |
| US-4 — A mounted app is visible only to the people it applies to | FR-012, FR-013, FR-023, FR-025 |

Every story that changes what the *Shipping it* requirements describe carries them: it documents
its own surface and records its change in the changelog. FR-024 lands with the first story.

### Key Entities

- **Mounted app**: a package built on django-mvp that declares a name, an icon, its own menu, its
  URLs, its landing page and optionally a visibility check, so that a host project can place it
  under an address of its choosing.
- **Host project**: the Django project that mounts one or more mounted apps. It owns everything
  outside them: its own menu, header, brand, footer, theme, user menu and mobile dock.
- **Main app**: the one mounted app, if any, whose menu a project uses as its sidebar everywhere
  outside other mounted apps.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A host project includes a mounted app with two edits, one line in its URLs and one
  entry in its menu. It writes no template and restates none of the app's navigation.
- **SC-002**: Exactly one navigation menu is rendered in the sidebar on every page, inside a
  mounted app or not.
- **SC-003**: The same package, with no change to its code, runs as a site in its own right and
  mounted inside a host project.
- **SC-004**: A project that mounts no app and names no main app renders every page identically to
  the release before this feature.
- **SC-005**: Every existing app that adds to the Account Center passes its own tests unchanged
  against the release carrying this feature.
- **SC-006**: A developer can mount an app, add its entry, name a main app and attach a check by
  following the documentation alone, without reading the package's source.
- **SC-007**: Every acceptance scenario above is proved by a test that fails if the behaviour is
  removed, and the changed pages carry rendered-markup assertions (Articles I, X and XIII).

## Assumptions

- Mounting is one level deep. An app mounted inside another mounted app is refused rather than
  supported, and so is mounting one app twice. Both wait until a project needs them.
- Installing a mounted app's package works as it does today, including its entry in
  `INSTALLED_APPS` and any settings it needs. This feature covers how the app's pages are placed
  and navigated, not how the package is installed.
- Only the sidebar menu changes inside a mounted app. The mobile dock stays the host's, and a
  mounted app does not bring a dock of its own.
- The host's home page is the address the sidebar brand already links to.
- No existing package declares itself a mounted app yet. django-literature and FairDM adopt this in
  their own work once it is released.
- FS-028 recorded a general way to attach a menu to a group of addresses as later work, outside
  its scope. This feature is that work, and it replaces the two-column layout FS-028 built for the
  Account Center alone.
