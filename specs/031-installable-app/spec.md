# Feature Specification: Installable app

**Feature Branch**: `031-installable-app`

**Created**: 2026-09-24

**Status**: Draft

**Goals**: G1 (a complete, responsive application shell that a project configures rather than builds), G8 (theming and branding without forking templates)

**Roadmap**: — No roadmap item covers this. Recorded here as a possible roadmap gap.

**Issues**: #186

**Input**: A project built on django-mvp can be installed from the browser as an app, on the
desktop or on a phone's home screen, and opens in its own window with the project's name, icon
and colours. The package provides the app manifest, a service worker, and the tags in the
document head that register both, built from settings and the brand mark the project already
has. It is off by default, and one switch turns it on. The service worker does nothing yet: it
exists to make the app installable, caches nothing, and is where offline support is added later.
A project can point at its own worker instead. A management command renders the fixed-size
images install prompts need from the project's brand mark, and can run in CI.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A project becomes installable by turning on one setting (Priority: P1)

A project built on django-mvp is used every day by the same people: a lab's data portal, an
internal tool, a back office. They keep it in a browser tab among twenty others. Making it
something they can install, with its own window, its own icon on the dock or home screen and
its own name in the app switcher, takes a manifest file, a service worker served from the right
address, and a handful of tags in the page head. Each piece is small. Getting all of them right,
and keeping them in step with the project's name and branding, is the kind of work nobody gets
round to.

The shell already knows the project's name, its brand mark and its theme. This story has it use
them. The developer turns the feature on, adds one URL include at the root of the site, and the
browser offers to install the application.

**Why this priority**: It is the capability the feature exists for. The other two stories make
it easier to reach and easier to adjust, and neither delivers anything without it.

**Independent Test**: In a project that has the application images in place, turn the feature
on and mount the root include. Request a page and confirm the head carries the manifest and the
registration. Request the manifest and confirm it names the site, points at the images and
carries the default theme's colours. Request the service worker and confirm it is served from
the root with a script content type. Then turn the feature off and confirm none of those tags
appear.

**Acceptance Scenarios**:

1. **Given** a project that has not turned the feature on, **When** any page of the shell
   renders, **Then** the page carries no manifest link, no service worker registration and no
   other install-related tag, exactly as before this feature.
2. **Given** a project that has turned the feature on and mounted the root include, **When** a
   page of the shell renders, **Then** the document head links the manifest and the page
   registers the service worker.
3. **Given** that project, **When** the manifest is requested, **Then** it is served with the web
   app manifest content type and names the application after the site's name, opens at the
   site's root in its own window, and lists the application images at the sizes install prompts
   require.
4. **Given** that project with a default theme the package ships, **When** the manifest is
   requested, **Then** its theme and background colours match that theme without further
   configuration.
5. **Given** that project, **When** the service worker is requested, **Then** it is served from
   the root of the site as JavaScript, so that it controls every page of the site.
6. **Given** the packaged service worker is active, **When** any page, form submission or
   request is made, **Then** the response is exactly what the network returns. The worker
   stores nothing and serves nothing from storage.
7. **Given** that project, **When** a page renders, **Then** the head also carries the tags a
   phone's home screen reads for the application's name, icon and status-bar colour.

---

### User Story 2 - The developer generates the app images from the brand mark (Priority: P2)

The brand mark a project gives django-mvp is a vector image, and that is all the shell needs
for everything else it draws. An install prompt needs something different: square raster images
at fixed sizes, one of them padded so that a phone can crop it to a circle or a rounded square
without cutting into the mark, and a separate one for Apple home screens. Producing these by
hand means an image editor and a list of sizes looked up somewhere, and redoing it every time
the mark changes. Doing it once and committing the output means the images drift from the mark
the first time someone updates it.

This story makes it one command. It reads the brand mark from where the project already keeps
it and writes the full set into the project's static files. It asks nothing and can be scripted,
so a project can run it in its build pipeline and never commit the output at all.

**Why this priority**: US-1 works without it for a project willing to produce the images itself,
so it is not P1. It is what removes the step the issue names as the hardest part of the feature.

**Independent Test**: In a project with its own brand mark, run the command, and confirm the
full set of images exists at the sizes the manifest points at, rendered from that mark. Remove
the optional image library and run it again, and confirm it fails with a message naming what to
install and a non-zero exit status.

**Acceptance Scenarios**:

1. **Given** a project with a brand mark in the place the shell reads it from, **When** the
   command runs, **Then** it writes a 192-pixel and a 512-pixel square image, a padded 512-pixel
   image for masked display, and an Apple home-screen image, all rendered from that mark, to the
   location the manifest and the page head point at.
2. **Given** the images already exist, **When** the command runs again after the mark changed,
   **Then** they are replaced with images rendered from the current mark.
3. **Given** the library the command needs to render vector images is not installed, **When**
   the command runs, **Then** it fails with a message naming the package to install, and exits
   with a non-zero status.
4. **Given** a project that has not supplied a brand mark of its own, **When** the command runs,
   **Then** it renders the images from the mark the package ships and says so in its output.
5. **Given** the command runs in a non-interactive environment, **When** it succeeds, **Then**
   it asks no questions and exits with a zero status.

---

### User Story 3 - A project adjusts what it installs as (Priority: P3)

The defaults suit a project whose site name is what people call the application and whose theme
is one the package ships. Plenty of projects are not that project. The site name is long and
needs a shorter label under an icon. The theme is the project's own, so there is no colour the
package can read from it. The team already has a service worker of its own, or wants to start
one now, and needs the page to register that one instead.

This story lets each of those be set in the configuration the project already uses for the
shell, without overriding a template.

**Why this priority**: The feature is complete for a project that fits the defaults. This widens
who it fits.

**Independent Test**: Set a short name, a start address, both colours and a service worker of
the project's own in the configuration. Request the manifest and confirm each value appears.
Render a page and confirm the head registers the project's worker instead of the packaged one.

**Acceptance Scenarios**:

1. **Given** a project that configures a name, a short name, a start address or a display mode,
   **When** the manifest is requested, **Then** each configured value replaces the packaged
   default and every value left unset keeps its default.
2. **Given** a project that configures theme and background colours, **When** the manifest is
   requested and a page renders, **Then** both carry the configured colours.
3. **Given** a project whose default theme is its own rather than one the package ships, and
   which configures no colours, **When** the manifest is requested, **Then** it carries no
   colour entries rather than a guess, and the browser falls back to its own defaults.
4. **Given** a project that configures a service worker of its own, **When** a page renders,
   **Then** the page registers that worker rather than the packaged one.
5. **Given** a project that wants to change the head tags themselves, **When** it overrides the
   template that renders them, **Then** its template decides what the head carries, the same way
   every other packaged template is overridden.

### Edge Cases

- The feature is on but the root include is not mounted. The manifest link and the worker
  registration would point at addresses that do not exist. The developer needs to find out at
  startup, not from a browser console.
- The feature is on but the application images do not exist in the project's static files. The
  application would install with a missing icon or not be offered for install at all. This also
  needs to show at startup, naming the command that produces them.
- The project has a dark variant of its brand mark. The images are rendered from the light mark
  only, because an installed app has one icon regardless of theme.
- The site is served under a path prefix rather than at the root of its domain. The worker has
  to be served at the root of what the site controls, and the start address has to include the
  prefix.
- The project does not use Django's sites framework, so there is no site name to read. The
  application still needs a name.
- The configured name contains characters that are special in JSON or HTML.
- The brand mark is not square. The images must keep its proportions rather than stretch it.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The feature MUST be off unless a project turns it on with a single setting in the
  shell's configuration. With it off, pages MUST NOT carry any tag, link or script the
  feature adds.
- **FR-002**: With the feature on, every page of the shell MUST link the web app manifest from
  the document head and register the service worker.
- **FR-003**: The package MUST provide the manifest and the service worker through a URL
  configuration that a project mounts at the root of its site, so that the worker controls every
  page. Mounting that configuration MUST be the only URL setup the feature requires.
- **FR-004**: The manifest MUST be served with the web app manifest content type and the service
  worker as JavaScript.
- **FR-005**: By default the manifest MUST name the application after the site's name, start at
  the site's root and open in a standalone window. Where the site has no name to read, a
  non-empty name MUST still be provided.
- **FR-006**: When the configured default theme is one the package ships, the manifest's theme
  and background colours MUST match that theme by default. When it is not, and no colours are
  configured, the manifest MUST omit them.
- **FR-007**: The manifest MUST list application images at 192 and 512 pixels and a padded image
  for masked display, and the page head MUST carry an Apple home-screen image, all read from a
  fixed location in the project's static files.
- **FR-008**: The page head MUST carry the tags phone home screens read for the application's
  name and status-bar colour, alongside the manifest link.
- **FR-009**: The packaged service worker MUST pass every request straight to the network and
  MUST NOT store or serve any response. It MUST be written so that caching can be added to it
  later without replacing it.
- **FR-010**: A project MUST be able to set the name, short name, start address, display mode
  and both colours in the shell's configuration, each independently, with every unset value
  keeping its default.
- **FR-011**: A project MUST be able to configure a service worker of its own, which the page
  registers in place of the packaged one.
- **FR-012**: The head tags MUST be rendered by a template a project can override at the same
  path, the same way every other packaged template is.
- **FR-013**: The package MUST provide a management command that renders the full image set of
  FR-007 from the project's brand mark, writing to the location FR-007 reads from, replacing any
  existing images, keeping the mark's proportions, and asking no questions.
- **FR-014**: The command MUST NOT make any new package a runtime dependency. The library it
  needs to render vector images MUST be optional, and its absence MUST produce a message naming
  what to install and a non-zero exit status.
- **FR-015**: When the project has no brand mark of its own, the command MUST render from the
  mark the package ships and say so in its output.
- **FR-016**: With the feature on, the project MUST be warned at startup when the root URL
  configuration is not mounted or when any image FR-007 names is missing, and the image warning
  MUST name the command that produces them.
- **FR-017**: Every value written into the manifest or the head MUST be escaped for the format
  it is written into.
- **FR-018**: Anything the feature serves MUST NOT be fetched from a third party.
- **FR-019**: The package MUST document how to turn the feature on, the root include, the image
  command, every configuration key it adds, and how to supply a service worker of the project's
  own. The domain glossary MUST define *installable app* and *service worker*.
- **FR-020**: The demo application MUST turn the feature on, mount the root include and
  generate its images with the package's own command rather than committing them, so that what
  ships is what the package is shown to do.

### Key Entities

Not applicable. This feature stores nothing and introduces no model.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A project that turns the feature on, mounts one URL include and runs one command
  is offered for installation by a browser that supports installing web apps, with no
  template, view or static file written by hand.
- **SC-002**: A project that does not turn the feature on renders byte-identical page heads
  before and after upgrading.
- **SC-003**: The packaged service worker changes no response the application returns. Every
  page and form behaves the same with it active as without it.
- **SC-004**: Changing the brand mark and re-running the command updates every installed image
  with no other step.
- **SC-005**: Every manifest value the package derives can be changed from the shell's
  configuration without overriding a template.
- **SC-006**: A misconfiguration that would leave the application uninstallable, either an
  unmounted root include or missing images, is reported when the project starts.

## Clarifications

Resolved during specification from the agreed feature statement and the discussion that
preceded it. Each answer is integrated into the requirements and scenarios above. This section
records what was ambiguous and what was chosen.

**Q1 — Where do the manifest colours come from, when a theme is a stylesheet rather than a
setting?**
From the theme's own colour values, for the themes the package ships. A project's own theme is
a CSS file that nothing on the server reads, so the package has no colour to offer for it. It
omits the entry rather than guess, and the project sets the colours in configuration if it wants
them. Keeping them in step with a visitor's theme choice is the project's concern and out of
scope. Integrated as FR-006 and US-3 scenario 3.

**Q2 — Where do the application images live, and does the manifest point at the brand mark
itself?**
At one fixed location under the project's static files, next to the brand mark the shell
already reads. The manifest points at the rendered images, not at the vector mark, because Apple
home screens and several install prompts do not accept a vector icon. A fixed location is what
lets the command, the manifest and the startup check agree without a setting. Integrated as
FR-007 and FR-013.

**Q3 — What is the application called when the project does not use Django's sites
framework?**
The shell's page title already reads the site's name. Where there is no site to read, the
application falls back to a non-empty packaged default, and the project sets its own name in
configuration. The specific fallback is a planning decision. Integrated as FR-005 and an edge
case.

**Q4 — How does a developer learn that the feature is on but cannot work?**
Through a warning when the project starts, following Django's own practice of reporting
configuration mistakes through its system checks rather than at request time. The two failures
that leave an application silently uninstallable are the unmounted root include and the missing
images, and both are reported. Integrated as FR-016 and SC-006.

**Q5 — Which brand mark is rendered when a project has both a light and a dark one?**
The light one. An installed application has a single icon on the home screen or dock,
whatever theme the page is showing, and the light mark is the one the shell treats as the
default everywhere else. Recorded as an edge case.

## Assumptions

- The feature is off by default. A project that upgrades sees no change, which Article XVI
  requires of default behaviour.
- The service worker does nothing yet. Offline support, response caching, push notifications
  and an in-page install button are separate features.
- Removing the feature from a site where browsers have already installed it is out of scope.
- Splash screens are out of scope. Android draws its own from the manifest, and Apple's need a
  set of device-specific images that is a feature of its own.
- The image command's rendering library is an optional dependency, installed by whoever runs
  the command. The published package gains no runtime dependency, in keeping with Article VII.
- Nothing is fetched from a third party, in keeping with G14 and Article XV.
