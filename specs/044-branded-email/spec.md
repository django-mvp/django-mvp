# Feature Specification: Branded HTML email layout

**Feature Branch**: `044-branded-email`

**Created**: 2026-11-04

**Status**: Draft

**Serves**: G8 (theming and branding without forking templates), G5 (a polished, modern look and
feel out of the box), G10 (a consistent UI around the third-party packages projects already rely
on)

**Roadmap**: none. No roadmap item covers email. This may be a gap in the roadmap.

**Issue**: https://github.com/django-mvp/django-mvp/issues/642

**Input**: Packages built on django-mvp send email: sign-in codes, account notices, receipts,
policy updates. Today each sends plain text or draws its own HTML, so a project's mail looks
nothing like the project. django-mvp ships a base email layout that carries the project's logo,
colours and name. A package writes only the message, and every email from every package looks
like it came from the same site. A developer can see an email rendered in the browser while
writing it. The person receiving it gets a readable message in the common mail clients, with a
plain-text version where HTML is not shown. Mail goes out through Django's configured email
backend, so a project that swaps in a queuing backend gets its mail queued and logged with no
change to the packages sending it.

## Clarifications

### Session 2026-11-04 (intake)

Sam confirmed the stated reading and took the recommended option at every open point:

- **Q: How does the brand logo reach the email, given that many mail clients do not show SVG?**
  A: The email shows a raster logo, linked by absolute URL. The project supplies the file or
  generates it from its brand logo with a management command. Recorded as FR-008 and FR-009.

- **Q: Is the plain-text version generated, or does each email carry its own?**
  A: Generated from the HTML by default. An email that has its own plain-text template uses that
  instead. Recorded as FR-004 and FR-005.

- **Q: What does a package call to send one?**
  A: Both a base template to extend and a helper that renders and sends. Recorded as FR-001 and
  FR-002.

- **Q: How is dark mode handled?**
  A: The email is designed light. Clients that honour a dark colour scheme get the dark logo and
  dark colours. Clients that invert colours on their own stay readable without being styled for.
  Recorded as FR-013 and FR-014.

- **Q: Where do the email's colours come from?**
  A: A small set of email colours in `MVP_CONFIG`. A project that sets none gets the installable
  app's `theme_color` as its brand colour and neutral defaults for the rest. Recorded as FR-010
  and FR-011.

- **Q: Do the packages that send mail today move over in this feature?**
  A: No. Each moves over in its own repository once this is released. Recorded under
  Out of scope.

### Session 2026-11-04 (coverage scan)

- **Q: What base address do the logo and links use when an email is sent with no request, from a
  background worker?**
  A: A site address the project sets once in `MVP_CONFIG`. When it is unset and a request is
  available, the request's address is used. With neither, sending fails with an error naming the
  setting, rather than sending an email whose logo and links are broken. Recorded as FR-007.

- **Q: In which language is an email rendered?**
  A: The language the sender passes to the helper. With none passed, the active language. The
  subject is rendered in the same language. Recorded as FR-006.

- **Q: Who can open the email preview page?**
  A: Only while `DEBUG` is on, and only a signed-in staff member. With `DEBUG` off the page does not
  exist. Recorded as FR-017. Rationale in `decisions.md`.

- **Q: Where does a preview get the data its email is rendered with?**
  A: From example data the developer declares with the preview. A preview never reads real
  people's records. Recorded as FR-016.

- **Q: Does the subject come from a template too?**
  A: Yes. Each email has a one-line subject template beside its body, so the subject is translated
  and overridden the same way the body is. Recorded as FR-003.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A package developer sends an email in the project's look (Priority: P1)

A developer writing a package on django-mvp writes the body of one email as a template that
extends the base email layout, then sends it with one call naming the template, the data and the
recipients. The email arrives with the project's logo, colours, name and footer around the
message, as HTML with a plain-text alternative, without the developer writing any layout or
styling.

**Why this priority**: it is the feature. Every other story serves this one.

**Independent Test**: write an email template that extends the base layout, send it with the
helper under Django's in-memory email backend, and inspect the message in the outbox.

**Acceptance Scenarios**:

1. **Given** an email template extending the base layout, **When** the developer sends it with
   the helper, **Then** one message goes out through Django's configured email backend, carrying
   an HTML part and a plain-text part, addressed to the given recipients.
2. **Given** the sent message, **When** its HTML is read, **Then** the styling is inline on the
   elements, with no dependency on a stylesheet the mail client would have to load.
3. **Given** the sent message, **When** its HTML is read, **Then** it carries the project's logo,
   its name and the layout's footer around the body the developer wrote.
4. **Given** an email with no plain-text template, **When** it is sent, **Then** the plain-text
   part is generated from the HTML and holds the body's text and every link's address.
5. **Given** an email with its own plain-text template, **When** it is sent, **Then** that
   template is the plain-text part.
6. **Given** a language passed to the helper, **When** the email is sent, **Then** its subject and
   body are rendered in that language, and the language active before the call is active again
   afterwards.
7. **Given** a project whose email backend is a queuing backend, **When** a package sends with the
   helper, **Then** the message reaches that backend unchanged, with no change to the package.
8. **Given** the base layout's email pieces (a button, a muted note, a divider), **When** a body
   uses them, **Then** they render in the project's colours and work in clients that ignore
   stylesheets.
9. **Given** a body that fills the footer's slot (for example with a postal address or the reason
   the person is receiving the email), **When** it is sent, **Then** that text replaces the
   default footer content.
10. **Given** a link written in the body as a URL path, **When** it is sent, **Then** it is an
    absolute address on the project's site.

---

### User Story 2 - A person reads a project's email in their mail client (Priority: P1)

A person who receives an email from a project reads it in Gmail, Outlook, Apple Mail or a
plain-text client. In every one the message is readable and recognisably the project's. Where the
client shows a dark colour scheme, the email follows it. Where images are blocked, the email
still reads correctly.

**Why this priority**: an email that breaks in a common client is worse than plain text, which
is what the packages send today.

**Independent Test**: render one email and check the sent HTML for the properties each client
depends on: inline styles, a table-based layout, a raster logo with a text alternative, and the
dark-scheme rules.

**Acceptance Scenarios**:

1. **Given** a client that shows only plain text, **When** the person opens the email, **Then**
   they read the full message and every link's address.
2. **Given** a client that blocks images, **When** the person opens the email, **Then** the
   project's name stands where the logo would be, and nothing in the message depends on an image
   to be understood.
3. **Given** a client that honours a dark colour scheme, **When** the person opens the email in
   dark mode, **Then** it shows the dark logo, when the project has one, and its dark colours.
4. **Given** a client that inverts an email's colours on its own, **When** the person opens it,
   **Then** the text keeps a contrast ratio of at least 4.5:1 against its background.
5. **Given** a narrow phone screen, **When** the person opens the email, **Then** it fits the
   width without sideways scrolling.

---

### User Story 3 - A project developer gives its email the project's logo and colours (Priority: P1)

A developer running a project on django-mvp makes every email from every installed package carry
the project's brand by setting it once in the settings, with no template overridden.

**Why this priority**: without it every project's mail looks the same, which defeats the feature.

**Independent Test**: set the email colours, the site address and the logo in `MVP_CONFIG`, send
an email, and check that the HTML carries them.

**Acceptance Scenarios**:

1. **Given** email colours set in `MVP_CONFIG`, **When** any package sends an email, **Then** the
   email uses those colours.
2. **Given** no email colours set and an installable-app `theme_color` set, **When** an email is
   sent, **Then** the `theme_color` is the email's brand colour and the rest are the package's
   defaults.
3. **Given** neither set, **When** an email is sent, **Then** it uses the package's default
   colours and still meets the contrast in User Story 2.
4. **Given** the developer runs the logo command, **When** it finishes, **Then** a light and,
   where the brand has one, a dark raster logo exist in the project's static files, rendered
   from the brand logo the shell already uses.
5. **Given** the renderer the logo command needs is not installed, **When** the command runs,
   **Then** it stops and names the package to install.
6. **Given** a raster logo the project supplied itself at the documented path, **When** an email
   is sent, **Then** the email uses that file.
7. **Given** no raster logo at all, **When** an email is sent, **Then** the project's name is
   shown in its place and the email still sends.
8. **Given** a project that overrides the base layout template, **When** any package sends an
   email, **Then** the project's layout is used.

---

### User Story 4 - A developer previews an email in the browser (Priority: P2)

A developer writing or restyling an email opens a page on their dev server that lists every email
with a declared preview, and opens any one of them rendered as it will be sent, with its subject,
its HTML and its plain text.

**Why this priority**: emails are slow to check by sending them. The feature works without the
preview, so it comes after the three that make sending work.

**Independent Test**: declare a preview for one email with example data, turn on `DEBUG`, sign in
as staff and open the preview page.

**Acceptance Scenarios**:

1. **Given** a package that declares a preview for one of its emails with example data, **When**
   the developer opens the preview page, **Then** that email is listed.
2. **Given** a listed email, **When** the developer opens it, **Then** they see its subject, its
   HTML exactly as it would be sent, and its plain-text part.
3. **Given** a preview, **When** it is opened in another of the project's languages, **Then** the
   email renders in that language.
4. **Given** `DEBUG` off, **When** anyone requests the preview page, **Then** it does not exist.
5. **Given** `DEBUG` on and a visitor who is not a signed-in staff member, **When** they request
   the preview page, **Then** they are refused.
6. **Given** a preview whose email fails to render, **When** the developer opens it, **Then** the
   error is shown for that email and the list still loads.

---

### Edge Cases

- A recipient list that is empty: the helper sends nothing and says so, rather than sending an
  email to nobody.
- A body that links to an address on another site: the link is left as written.
- A body template that does not extend the base layout: it is sent as written, without the brand.
- A subject template that renders more than one line: the subject is joined to one line, because
  Django refuses a line break in a subject header.
- A project that sets only some of the email colours: the rest take their defaults.
- A colour value that is not a valid colour: the project is told at start-up, rather than an email
  going out with a broken colour.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The package MUST ship a base email layout template that an email body extends, with
  blocks for the body, the preheader text and the footer. (US-1)
- **FR-002**: The package MUST provide a helper that takes a template name, the data, the
  recipients, and optionally a language, the sender, reply-to, attachments and extra headers, and
  sends one message through Django's configured email backend. (US-1)
- **FR-003**: Each email MUST take its subject from a subject template beside its body, rendered
  with the same data and joined to one line. (US-1)
- **FR-004**: The plain-text part MUST be generated from the HTML when the email has no plain-text
  template, keeping the text and every link's address. (US-1, US-2)
- **FR-005**: An email that has a plain-text template MUST use it as the plain-text part. (US-1)
- **FR-006**: The helper MUST render the subject and body in the language it is given, otherwise
  the active language, and MUST restore the previously active language afterwards. (US-1)
- **FR-007**: Links written as URL paths, and the logo, MUST be absolute addresses, built from the
  site address set in `MVP_CONFIG`, otherwise the request's address. With neither, sending MUST
  fail with an error naming the setting. (US-1)
- **FR-008**: The email MUST show a raster logo from a documented static path, with a dark variant
  when one exists, and the project's name as its text alternative. With no logo file, the
  project's name MUST stand in its place. (US-2, US-3)
- **FR-009**: The package MUST provide a management command that renders the light and dark
  raster logos from the brand logo the shell uses, and stops naming the missing package when its
  optional renderer is absent. (US-3)
- **FR-010**: The email's colours MUST be configurable in `MVP_CONFIG` and MUST be validated when
  the project starts. (US-3)
- **FR-011**: With no email colours configured, the email's brand colour MUST be the installable
  app's `theme_color` when set, and the package's default otherwise. Any colour not set MUST take
  its default. (US-3)
- **FR-012**: The sent HTML MUST carry its styling inline on the elements, so it does not depend on
  a client loading a stylesheet. (US-1, US-2)
- **FR-013**: The email MUST follow a dark colour scheme in clients that honour one, with the dark
  logo and dark colours. (US-2)
- **FR-014**: Text in the email MUST meet a contrast ratio of at least 4.5:1 against its
  background with the package's default colours, in light, in dark, and when a client inverts
  them. (US-2, US-3)
- **FR-015**: The base layout MUST provide reusable email pieces (a button, a muted note, a
  divider) that render in the project's colours in clients that ignore stylesheets. (US-1)
- **FR-016**: A developer MUST be able to declare a preview for an email with example data, and
  the preview page MUST list every declared preview and render each one's subject, HTML and plain
  text, in any of the project's languages. (US-4)
- **FR-017**: The preview page MUST exist only while `DEBUG` is on, and MUST refuse anyone who is
  not a signed-in staff member. (US-4)
- **FR-018**: A project MUST be able to replace the base layout and each email piece by overriding
  its template at the same path. (US-3)
- **FR-019**: The feature MUST add no runtime dependency under a GPL or AGPL licence, and MUST NOT
  require a front-end build step. (US-1)

### Key Entities

- **Email**: a subject template, an HTML body template extending the base layout, and optionally
  a plain-text template, all under one name.
- **Base email layout**: the template every branded email extends. It draws the logo, the brand
  colours, the project's name and the footer around the body.
- **Email piece**: a reusable part of an email body, such as a button, that renders safely in mail
  clients.
- **Email brand**: the colours, the site address and the raster logo the layout draws with, set
  in `MVP_CONFIG`.
- **Email preview**: an email's name paired with the example data it is previewed with.

### Out of scope

- Moving the email that packages built on django-mvp send today onto the layout. Each package
  moves over in its own repository, once this is released.
- Queuing, delivery logs, email templates stored in the database, unsubscribe links and digests.
  These belong to a separate package. This feature promises only that mail goes through Django's
  configured email backend.
- Reading the email's colours out of the project's theme stylesheet.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A package sends a branded email by writing a body template and one helper call, with
  no layout or styling of its own.
- **SC-002**: A project brands every installed package's email by changing settings only, with no
  template override.
- **SC-003**: Every sent email carries an HTML part with inline styling and a plain-text part.
- **SC-004**: Text in an email with the default colours meets 4.5:1 contrast in light, dark and
  inverted rendering.
- **SC-005**: The feature adds no GPL or AGPL runtime dependency and keeps Django 5.2 supported.
- **SC-006**: A developer opens any declared email rendered in the browser in one click from the
  preview list.
