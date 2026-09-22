# Feature Specification: Sign-in and sign-out pages in the package

**Feature Branch**: `030-development-sign-in`

**Created**: 2026-09-22

**Status**: Draft

**Goals**: G1 (a complete, responsive application shell that a project configures rather than builds), G4 (a usable front end for the Django features that ship backend machinery without one)

**Roadmap**: — No roadmap item covers this. R27 delivered the Account Center as an area of the shell, and this fills a gap that area left: the shell draws sign-in and sign-out controls that a project has to wire itself before they point anywhere. Recorded here as a possible roadmap gap.

**Issues**: #381

**Input**: Sign-in and sign-out views exist only in this repository's demo application. A developer building a third-party package against django-mvp cannot reach a page that requires a signed-in user without writing their own views, and the shell's own sign-in button and sign-out row stay hidden because the URL names they look for do not resolve.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A developer signs in and out of a project built on django-mvp (Priority: P1)

Someone is building a package that adds pages to a django-mvp project — a billing area, a
notifications page, anything behind a login. To see their own work they need to be a signed-in
user, and today there is nothing to sign in with. Django ships `LoginView` and `LogoutView` and
no page worth rendering, so the developer either stops at the anonymous half of their feature or
writes a view, a template and two URL entries before they can look at the thing they are actually
building.

The shell already has the controls for this. The sidebar footer draws a sign-in button for a
visitor and a user menu with a sign-out row for a signed-in person, and both are written so that
a control whose destination does not resolve is left out rather than rendered broken. In a
project that has not wired up authentication, that means neither one ever appears.

This story ships the two pages in the package, at the same address the Account Center is mounted
at, so that including one URLconf is the whole of the setup.

**Why this priority**: It is the capability the feature exists for. The other two stories protect
it, and neither delivers anything on its own.

**Independent Test**: Mount the Account Center URLconf in a project with no authentication
configuration of its own, visit the sign-in page, sign in as an existing user, confirm the shell
now draws the user menu, use its sign-out row, and confirm the shell goes back to drawing the
sign-in button.

**Acceptance Scenarios**:

1. **Given** a project that mounts the Account Center URLconf and configures nothing else,
   **When** an anonymous visitor opens the sign-in address, **Then** a sign-in page renders inside
   the application shell with fields for the credentials the project's user model expects.
2. **Given** that page, **When** valid credentials are submitted, **Then** the person is signed in
   and sent onward to the Account Center.
3. **Given** that page, **When** invalid credentials are submitted, **Then** the page re-renders
   with the error shown against the form and the person stays anonymous.
4. **Given** a signed-in person, **When** the sign-out control in the shell's user menu is used,
   **Then** the session ends and the next page renders as anonymous.
5. **Given** a project that mounts the Account Center URLconf, **When** any page of the shell
   renders, **Then** the sidebar footer draws the sign-in button for a visitor and the user menu
   for a signed-in person, with no further configuration.
6. **Given** a visitor sent to the sign-in page from a page that required a signed-in user,
   **When** they sign in, **Then** they arrive at the page they originally asked for rather than
   the default destination.
7. **Given** a signed-in person, **When** they open the sign-in address directly, **Then** they
   are sent to the Account Center rather than shown a sign-in form.
8. **Given** the sign-out address, **When** it is requested by following a link rather than by
   submitting, **Then** the session is not ended.

---

### User Story 2 - Installing the account-management package takes over (Priority: P2)

The same project reaches the point of needing real account management and installs
django-accounts-center, which brings allauth with it. From that moment the sign-in page a person
sees must be allauth's: the one that offers sign-up, password reset, email verification and
whatever social or multi-factor methods the project has configured.

Nothing the developer already wrote should have to change for that to happen, and it must not
depend on the order in which the two URLconfs are mounted. Both packages are mounted at the same
prefix, and mounting the packaged pages first — which is the order this project's own
documentation and django-accounts-center's own example both use — would otherwise leave requests
resolving to the packaged pages while links point at allauth's.

That failure is silent and it is the dangerous one: the page renders, the form works, a session
is created, and the project's email verification, sign-up path and second factor are all quietly
absent.

**Why this priority**: Without it, adding account management to a project makes its sign-in worse
in a way nothing reports. The capability in US-1 is still worth having on its own, which is why
this is not P1.

**Independent Test**: In a project that has allauth's account app installed, request the sign-in
address and confirm allauth's view answers it, and confirm the packaged views are absent from the
URL configuration entirely.

**Acceptance Scenarios**:

1. **Given** a project with allauth's account application installed, **When** the Account Center
   URLconf is mounted, **Then** it contributes no sign-in or sign-out page.
2. **Given** that project mounts the Account Center URLconf **before** the account-management
   package's URLconf, **When** the sign-in address is requested, **Then** allauth's sign-in page
   answers it.
3. **Given** that project, **When** shipped markup resolves the sign-in and sign-out destinations,
   **Then** it resolves them to allauth's addresses, and those addresses serve allauth's views.
4. **Given** a project with allauth installed, **When** the URL configuration is checked for
   duplicate registrations of the sign-in and sign-out names, **Then** each name is registered
   once.
5. **Given** a project without allauth, **When** the Account Center URLconf is mounted, **Then**
   the packaged pages are present and answer those addresses.

---

### User Story 3 - The developer is told not to ship this (Priority: P3)

The packaged pages are deliberately thin. They authenticate against the project's user model and
do nothing else: no sign-up, no password reset, no rate limiting beyond what Django itself does,
no email verification. A developer who meets them for the first time has no way to tell whether
they are the package's answer to authentication or a stopgap, and the cost of guessing wrong is a
production site whose users cannot recover an account.

This story puts that on the page itself, where the person deciding will actually be standing,
rather than only in the documentation they may never open.

**Why this priority**: It changes no behaviour, and the pages are correct without it. It is the
last slice because it is the cheapest to add once the pages exist, not because the warning is
optional.

**Independent Test**: Render each packaged page and confirm the notice is present, names what is
missing and points at django-accounts-center. Render allauth's equivalent pages in a project that
has it installed and confirm no such notice appears.

**Acceptance Scenarios**:

1. **Given** the packaged sign-in page, **When** it renders, **Then** it shows a notice stating
   that these pages are for development and naming django-accounts-center as what to install for
   a production site.
2. **Given** the packaged sign-out page, **When** it renders, **Then** it shows the same notice.
3. **Given** a project that has replaced the packaged pages by installing account management,
   **When** its sign-in page renders, **Then** the notice is absent.
4. **Given** a project that overrides the packaged page templates with its own, **When** its pages
   render, **Then** the project's templates decide what is shown, including whether the notice
   appears.

### Edge Cases

- A project mounts `django.contrib.auth.urls` in addition to the Account Center URLconf. Those
  entries register the names the shell's controls fall back to, so the same duplicate-registration
  question arises one level down and has to resolve to something predictable.
- A project has allauth installed but not django-accounts-center. The packaged pages must still
  stand down, because allauth is what owns the addresses, not the package that pulls it in.
- A project uses a custom user model whose identifying field is not `username`. The packaged page
  must ask for whatever that model actually uses rather than assuming.
- A project has no Account Center mounted at all. Nothing should change for it, and the shell's
  controls stay absent as they are today.
- The sign-out address is requested by an anonymous visitor.
- A project sets its own `LOGIN_REDIRECT_URL` or `LOGIN_URL`. The packaged behaviour must give way
  to the project's setting rather than overriding it.
- A `next` destination supplied on the sign-in URL points at another host.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The package MUST provide a sign-in page and a sign-out endpoint as part of the
  Account Center's includable URL configuration, so that mounting that one URLconf is the entire
  setup.
- **FR-002**: The sign-in and sign-out destinations MUST be registered under the names the shell's
  existing controls already look for, so that those controls begin rendering with no further
  configuration.
- **FR-003**: The packaged pages MUST NOT be registered when allauth's account application is
  installed, so that which view answers an address never depends on the order two URLconfs were
  mounted in.
- **FR-004**: Signing out MUST require a submission and MUST NOT act on a plain request for the
  address.
- **FR-005**: The sign-in page MUST authenticate against the project's configured user model and
  authentication backends, and MUST ask for the identifying field that model declares.
- **FR-006**: A failed sign-in MUST re-render the page with the failure shown against the form,
  and MUST NOT reveal whether the account exists.
- **FR-007**: After a successful sign-in the person MUST arrive at the destination they were
  originally sent from, when there was one, and otherwise at the Account Center. A project's own
  configured destination MUST take precedence over the packaged default.
- **FR-008**: A sign-in destination supplied on the request MUST be honoured only when it points
  within the project's own site.
- **FR-009**: A person who is already signed in MUST NOT be shown the sign-in form.
- **FR-010**: Both packaged pages MUST render inside the application shell and MUST be overridable
  by a project shipping its own template at the same path, the same way every other packaged
  template is.
- **FR-011**: Both packaged pages MUST carry a notice that names them as unsuitable for a
  production site and names django-accounts-center as what to install instead.
- **FR-012**: All text the pages present MUST be translatable.
- **FR-013**: The package MUST document how the pages are mounted, what they deliberately do not
  do, and what installing account management changes.
- **FR-014**: The demo application MUST use the packaged pages rather than wiring up its own, so
  that what ships is what the package is shown to do.

### Key Entities

Not applicable. This feature stores nothing and introduces no model.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A project that mounts the Account Center URLconf and writes no view, template or URL
  entry of its own can sign a person in and out.
- **SC-002**: Reaching a signed-in state in a new project built on the package takes one line of
  URL configuration, down from a view, a template and two URL entries.
- **SC-003**: In a project with account management installed, every request for a sign-in or
  sign-out address is answered by allauth, for both mount orders of the two URLconfs.
- **SC-004**: Each of the sign-in and sign-out names resolves to exactly one registration in every
  supported combination of installed packages.
- **SC-005**: Both packaged pages state, on the page, that they are not for production use and
  name what to install instead.
- **SC-006**: The demo application carries no sign-in or sign-out wiring of its own.

## Clarifications

Resolved during specification from the agreed feature statement and the grilling that preceded
it. Each answer is integrated into the requirements and scenarios above. This section records
what was ambiguous and what was chosen.

**Q1 — Does the stand-down key on allauth, or on django-accounts-center?**
On allauth's account application. django-accounts-center is one way allauth arrives in a project
and a project may install allauth directly. Keying on the package that actually registers the
competing addresses is the narrower and more accurate test. Integrated as FR-003 and the second
edge case.

**Q2 — Are the pages gated on a debug setting?**
No. The agreed statement describes a notice telling the developer to install account management
before production, which presumes the pages work outside development — a deployed staging build
still has to be signed in to. A debug gate would also make a project's behaviour differ between
environments in a way that only shows up after deployment. The notice is the guard. Recorded in
Assumptions.

**Q3 — Where does a person land after signing in?**
The Account Center, when the project has expressed no preference. Django's default,
`/accounts/profile/`, is an address most projects do not have, so leaving it would send people to
a 404 on a successful sign-in. A project's own `LOGIN_REDIRECT_URL` takes precedence. Integrated
as FR-007.

**Q4 — What happens to the names `django.contrib.auth.urls` registers, which the shell's sign-in
control falls back to?**
Out of scope to change. The packaged pages register the account-management names the shell
prefers. A project that also mounts Django's own auth URLconf has made that choice itself, and
the shell's fallback continues to behave as it does today. Recorded as an edge case so planning
reads it rather than discovering it.

**Q5 — Is the notice part of the page template or a separate opt-out?**
Part of the template, with no setting to suppress it. A setting to hide a warning is a setting
whose only use is to hide a warning. A project that genuinely wants these pages without the
notice already has the override point every packaged template has, which is the answer the
package gives everywhere else. Integrated as FR-011 and US-3 scenario 4.

## Assumptions

- The pages are not gated on `DEBUG`, and work wherever they are mounted. The on-page notice is
  what stops them being shipped by accident.
- They belong to the Account Center's existing URL configuration rather than a second include the
  developer has to discover. "Available everywhere" means mounting one thing.
- The demo application drops its own sign-in and sign-out wiring in the same change, so the
  package demonstrates the feature rather than describing it.
- The notice is a visible element of the page, aimed at a developer looking at it, not a warning
  raised in a console log.
- The README's scope statement, which says the package is not an authentication system, needs a
  sentence acknowledging these pages. The statement stays true — this is a development
  convenience, not account management — but a reader comparing the two will otherwise think it is
  contradicted.
- No new dependency is added. Django already ships the authentication machinery these pages need.
