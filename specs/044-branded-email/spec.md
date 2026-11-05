# Feature Specification: Branded HTML email layout

**Feature Branch**: `044-branded-email`

**Created**: 2026-11-04

**Status**: Draft

**Serves**: G8 (theming and branding without forking templates), G5 (a polished, modern look and
feel out of the box), G10 (a consistent UI around the third-party packages projects already rely
on, without extending or replacing them)

**Roadmap**: none. No roadmap item covers email. This may be a gap in the roadmap.

**Issue**: https://github.com/django-mvp/django-mvp/issues/642

**Input**: Packages built on django-mvp, and the third-party packages they wrap, send email:
sign-in codes, account notices, receipts, policy updates. Today each sends plain text or draws its
own HTML, so a project's mail looks nothing like the project. django-mvp ships a base email
template that carries the project's logo, colours and name. Whoever owns an email template,
whether a django-mvp package or a project overriding a third-party package's template, extends
it and writes only the message, so every email looks like it came from the same site. How an
email is sent stays with whatever sends it today: django-mvp adds no way of sending email. A
developer can see an email rendered in the browser while writing it. The person receiving it gets
a readable message in the common mail clients.

How each of these is achieved (how the colours and logo reach the email, which packages are used)
is left to research and planning. Sam's notes for that are in `planning-notes.md`.

## Clarifications

### Session 2026-11-04 (intake)

- **Q: Is the plain-text version generated, or does each email carry its own?**
  A: Each email carries its own, as it does today. django-mvp does not send the email, so it
  cannot build its plain-text part. Revised 2026-11-05 with Sam's ruling below.

- **Q: How is dark mode handled?**
  A: The email is designed light. Clients that honour a dark colour scheme get the dark logo and
  dark colours. Clients that invert colours on their own stay readable. Recorded as FR-008 and
  FR-009.

- **Q: Where do the email's colours and logo come from?**
  A: From the project's own theme and brand logo, so the email matches the site. A project
  configures nothing for its email beyond what it has already set for the site. Recorded as
  FR-005 and FR-006.

- **Q: Do the packages that send mail today move over in this feature?**
  A: No. Each moves over in its own repository once this is released. Recorded under
  Out of scope.

### Session 2026-11-05 (plan review)

- **Q: Does django-mvp give packages a way to send email?**
  A: No (Sam, 2026-11-05). Sending is usually built into the third-party package being wrapped,
  and a django-mvp package cannot change it: django-mvp-accounts can only override allauth's
  email templates. So django-mvp provides a base email template to extend, email pieces, and
  template tags where a template needs them, and nothing that renders or sends an email. This
  replaces the earlier sending helper, its subject templates and its language handling, which all
  belonged to the sender. Recorded as FR-001, FR-003 and FR-016.

### Session 2026-11-04 (coverage scan)

- **Q: Does an email rendered with no request, by a background worker, still have a working logo
  and working links in the layout?**
  A: Yes. The layout's logo and links are absolute addresses on the project's site whether or not
  a request is in the template's context. A template tag gives a body the same absolute address
  for any path. If the site's address cannot be found at all, rendering fails with an error saying
  so, rather than an email going out with a broken logo. Recorded as FR-004.

- **Q: Who can open the email preview page?**
  A: Only while `DEBUG` is on, and only a signed-in staff member. With `DEBUG` off the page does
  not exist. Recorded as FR-013.

- **Q: Where does a preview get the data its email is rendered with?**
  A: From example data the developer declares with the preview. A preview never reads real
  people's records. Recorded as FR-012.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A developer gives an email the project's look (Priority: P1)

A developer who owns an email template, in a django-mvp package or in a project overriding a
third-party package's email template, makes it extend the base email template and writes only the
message. The email then arrives with the project's logo, colours, name and footer around the
message, however it is sent, without the developer writing any layout or styling and without
changing the code that sends it.

**Why this priority**: it is the feature. Every other story serves this one.

**Independent Test**: override a third-party package's HTML email template with one that extends
the base template, trigger that package's email, and inspect the message in Django's outbox.

**Acceptance Scenarios**:

1. **Given** a third-party package that sends an HTML email from a template, **When** a project
   overrides that template with one extending the base template, **Then** the package's email
   arrives with the project's logo, name and footer around the message, with the package's
   sending code unchanged.
2. **Given** an email template extending the base template, **When** it is rendered, **Then** its
   styling works in clients that ignore a style element, without the template's author writing
   any styling.
3. **Given** the email pieces (a button, a muted note, a divider, a code), **When** a body uses
   them, **Then** they render in the project's colours in every client User Story 2 covers.
4. **Given** a body that fills the footer (for example with a postal address or the reason the
   person is receiving the email), **When** it is rendered, **Then** that text replaces the
   default footer content.
5. **Given** a body that needs a link to a path on the site, **When** it uses the template tag for
   it, with or without a request in the context, **Then** the link is an absolute address on the
   project's site.
6. **Given** an email whose sender also renders its own plain-text template, **When** it is sent,
   **Then** the plain-text part is that template, unchanged by the base template.

---

### User Story 2 - A person reads a project's email in their mail client (Priority: P1)

A person who receives an email from a project reads it in Gmail, Outlook or Apple Mail. In every
one the message is readable and recognisably the project's. Where the client shows a dark colour
scheme, the email follows it. Where images are blocked, the email still reads correctly.

**Why this priority**: an email that breaks in a common client is worse than plain text, which
is what the packages send today.

**Independent Test**: send one email and open it in each client named above, in light and dark
mode, with images on and off.

**Acceptance Scenarios**:

1. **Given** Gmail, Outlook or Apple Mail, **When** the person opens the email, **Then** it shows
   the project's logo and colours.
2. **Given** a client that blocks images, **When** the person opens the email, **Then** the
   project's name stands where the logo would be, and nothing in the layout depends on an image
   to be understood.
3. **Given** a client that honours a dark colour scheme, **When** the person opens the email in
   dark mode, **Then** it shows the dark logo, when the project has one, and the project's dark
   colours.
4. **Given** a client that inverts an email's colours on its own, **When** the person opens it,
   **Then** the text stays readable.
5. **Given** a narrow phone screen, **When** the person opens the email, **Then** it fits the
   width without sideways scrolling.

---

### User Story 3 - A project developer's email takes on the project's theme and logo (Priority: P1)

A developer running a project on django-mvp gets every email built on the base template in the
project's own colours and logo, the ones the site already uses, without configuring anything for
email.

**Why this priority**: without it every project's mail looks the same, which defeats the feature.

**Independent Test**: give a project a theme and brand logo of its own, render an email, and
check that it carries them.

**Acceptance Scenarios**:

1. **Given** a project using one of the package's shipped themes, **When** an email is rendered,
   **Then** the email uses that theme's colours.
2. **Given** a project using a theme it wrote itself, **When** an email is rendered, **Then** the
   email uses the colours of the project's theme.
3. **Given** a project that changes its light or dark theme, **When** an email is next rendered,
   **Then** it uses the new theme's colours, with nothing else changed.
4. **Given** a project with its own brand logo, **When** an email is rendered, **Then** the email
   shows that logo, and its dark variant in dark mode when there is one.
5. **Given** a theme colour or a logo the email cannot use, **When** the project starts, **Then**
   it is told which one and why, and emails still render with the package's fallback in its place.
6. **Given** a project that overrides the base email template, **When** any email built on it is
   rendered, **Then** the project's version is used.

---

### User Story 4 - A developer previews an email in the browser (Priority: P2)

A developer writing or restyling an email opens a page on their dev server that lists every email
with a declared preview, and opens any one of them rendered as it will be sent, with its subject
and plain text where the email has them.

**Why this priority**: emails are slow to check by sending them. The feature works without the
preview, so it comes after the three that make the look work.

**Independent Test**: declare a preview for one email template with example data, turn on
`DEBUG`, sign in as staff and open the preview page.

**Acceptance Scenarios**:

1. **Given** a package that declares a preview for one of its email templates with example data,
   **When** the developer opens the preview page, **Then** that email is listed.
2. **Given** a listed email, **When** the developer opens it, **Then** they see its HTML exactly as
   it renders, and its subject and plain-text templates rendered when they exist.
3. **Given** a preview, **When** it is opened in another of the project's languages, **Then** the
   email renders in that language.
4. **Given** `DEBUG` off, **When** anyone requests the preview page, **Then** it does not exist.
5. **Given** `DEBUG` on and a visitor who is not a signed-in staff member, **When** they request
   the preview page, **Then** they are refused.
6. **Given** a preview whose email fails to render, **When** the developer opens it, **Then** the
   error is shown for that email and the list still loads.

---

### Edge Cases

- A template that does not extend the base template: it renders as written, without the brand.
- A body that links to an address on another site: the link is left as written.
- A project with no brand logo of its own: the email shows the package's default logo, the same as
  the site does.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The package MUST ship a base email template that an email's HTML template extends,
  with blocks for the body, the preheader text and the footer. (US-1)
- **FR-002**: An email built on the base template MUST render as intended in Gmail, Outlook and
  Apple Mail, including clients that ignore a style element or do not display some image formats,
  and MUST fit a phone's width, without its author writing any styling. (US-1, US-2)
- **FR-003**: The base template MUST work whatever renders and sends the email, needing nothing in
  its context beyond what Django's template rendering already provides. (US-1)
- **FR-004**: The layout's logo and links MUST be absolute addresses on the project's site, with
  or without a request in the context, and a template tag MUST give a body the same absolute
  address for any path. When the site's address cannot be found, rendering MUST fail with an error
  saying so. (US-1)
- **FR-005**: The email's light and dark colours MUST be the project's own light and dark theme
  colours, including for a theme the project wrote itself. (US-3)
- **FR-006**: The email MUST show the project's brand logo, with its dark variant in dark mode when
  there is one, and the project's name in its place when images are not shown. (US-2, US-3)
- **FR-007**: A theme colour or logo the email cannot use MUST be reported when the project
  starts, and MUST NOT stop email rendering. (US-3)
- **FR-008**: The email MUST follow a dark colour scheme in clients that honour one. (US-2)
- **FR-009**: Text in the email MUST stay readable in light, in dark, and when a client inverts the
  colours, meeting a contrast ratio of at least 4.5:1 with the package's shipped default themes.
  (US-2, US-3)
- **FR-010**: The package MUST provide reusable email pieces (a button, a muted note, a divider, a
  code) that render in the project's colours. (US-1)
- **FR-011**: A project MUST be able to replace the base template and each email piece by
  overriding its template at the same path. (US-3)
- **FR-012**: A developer MUST be able to declare a preview for an email template with example
  data, and the preview page MUST list every declared preview and render each one's HTML, and its
  subject and plain text where they exist, in any of the project's languages. (US-4)
- **FR-013**: The preview page MUST exist only while `DEBUG` is on, and MUST refuse anyone who is
  not a signed-in staff member. (US-4)
- **FR-014**: The feature MUST add no runtime dependency under a GPL or AGPL licence, and MUST NOT
  require a front-end build step. (US-1)
- **FR-015**: An email's plain-text part MUST be left to whatever sends it. The base template MUST
  NOT change it. (US-1)
- **FR-016**: The feature MUST add no way of rendering or sending email. (US-1)

### Key Entities

- **Base email template**: the template an email's HTML template extends. It draws the logo, the
  project's colours, the project's name and the footer around the body.
- **Email piece**: a reusable part of an email body, such as a button.
- **Email preview**: an email template paired with the example data it is previewed with.

### Out of scope

- Moving the email that packages send today onto the layout. Each package moves over in its own
  repository, once this is released: django-mvp-accounts by overriding allauth's email templates.
- Any way of sending email, and anything the sender owns: the subject, the plain-text part, the
  language, the recipients, queuing and delivery logs.
- Email templates stored in the database, unsubscribe links and digests.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An email takes on the project's look when its HTML template extends the base
  template, with no layout or styling of its own and no change to the code that sends it.
- **SC-002**: A project's email takes on its theme and logo with nothing configured for email and
  no template override beyond the email's own.
- **SC-003**: A third-party package's email, sent by that package's own code, carries the brand
  once the project overrides its HTML template.
- **SC-004**: Text in an email in the package's default themes meets 4.5:1 contrast in light, dark
  and inverted rendering.
- **SC-005**: The feature adds no GPL or AGPL runtime dependency and keeps Django 5.2 supported.
- **SC-006**: A developer opens any declared email rendered in the browser in one click from the
  preview list.
