# Feature Specification: Preferences for each signed-in person

**Feature Branch**: `045-user-preferences`

**Created**: 2026-11-06

**Status**: Draft

**Serves**: G1 (a complete application shell that a project configures rather than builds), G7
(customization that never dead-ends, for the way an installed app contributes its own
preferences), G10 (a consistent UI around the third-party packages projects already rely on,
without extending or replacing them)

**Roadmap**: none. R27 delivered the Account Center this feature adds a page to, but no roadmap
item covers per-person preferences. This may be a gap in the roadmap.

**Issue**: https://github.com/django-mvp/django-mvp/issues/652

**Input**: A signed-in person cannot tell a django-mvp site which timezone they live in or which
language they read, so every page shows times in the server's timezone and text in whatever
language the browser asked for. Each person chooses both once, on a preferences page in the
Account Center, and from then on sees every page in their own timezone and language, on every
device they sign in from. The same page takes preferences from other installed apps, so a package
built on django-mvp can let people choose how it behaves for them without a model of its own.
Preferences are stored by django-object-preferences, which django-mvp integrates as it is and does
not reimplement. Every project on django-mvp gives its user model the preferences field, by adding
the mixin django-mvp provides or a preferences field of its own under any name, as one of the
steps of installing django-mvp.

**Depends on**: https://github.com/django-mvp/django-object-preferences/issues/27, so that an app
can read a person's preferences without knowing what the project named the field (FR-011).

How each of these is achieved is left to research and planning. Sam's notes for that are in
`planning-notes.md`.

## Clarifications

### Session 2026-11-06 (intake)

- **Q: Where does this live: django-mvp-accounts, django-mvp or django-object-preferences?**
  A: django-mvp (Sam, 2026-11-06). Preferences are a part of the shell any installed app
  contributes to, the way the Account Center already is. django-mvp-accounts only links to the
  page from its account management, which is a change to that package once this is released.

- **Q: Does every project have to give its user model the preferences field?**
  A: Yes (Sam, 2026-11-06: "The mixin (or at least the preferences field) becomes required").
  Django itself recommends a custom user model for every new project, and every project on
  django-mvp today has one. Requiring the field means every app can declare and read preferences
  for people without checking whether the project has them. A project without it is stopped at
  startup with a message saying what to add. This replaces an earlier reading in which the mixin
  was optional. Recorded as FR-003 and FR-004.

- **Q: What if a project's user model already has a `preferences` attribute for something else?**
  A: The project gives its own preferences field another name instead of using the mixin.
  django-object-preferences already finds the field by its type, whatever it is named (Sam,
  2026-11-06). Apps reading a person's preferences therefore never assume the name. Recorded as
  FR-003 and FR-011.

- **Q: Is django-object-preferences rewritten inside django-mvp?**
  A: No. It is integrated as it is (Sam, 2026-11-06). django-mvp gives its page the shell's look
  and places it in the Account Center. How it stores, validates and reads preferences is
  unchanged. Recorded as FR-012.

### Session 2026-11-06 (coverage scan)

- **Q: What does a person see before they have chosen anything?**
  A: The project's own defaults: its configured timezone, and the language Django would pick for
  them today. Nothing about their pages changes until they choose. Recorded as FR-007.

- **Q: A signed-in person changes language with the shell's existing language switcher. Does that
  change their preference?**
  A: Yes. Otherwise the next page they load in another browser, or after signing in again, would
  go back to the old language, and the switcher would appear not to work. Recorded as FR-008.

- **Q: Which languages and timezones can a person choose from?**
  A: The languages the project offers, and the standard timezones. A person cannot choose a
  language the project has not offered. Recorded as FR-005 and FR-006.

- **Q: What happens to a stored choice the project later stops offering, such as a language it
  removes?**
  A: The person sees the project's default, and the page shows the choice as unset until they
  pick again. Nothing fails. Recorded as FR-009.

- **Q: Does turning preferences on need any new setting?**
  A: Two installation lines, the app and its middleware, found in research (Sam approved at the
  plan gate, 2026-11-07). Recorded as SC-002.

- **Q: Does the shell's theme choice become a stored preference?**
  A: Not in this feature. The theme stays a choice kept in the browser, as it is today. Recorded
  under Out of scope.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A person chooses their timezone and language (Priority: P1)

A signed-in person opens the preferences page in the Account Center, chooses their timezone and
their language, and saves. From then on every page they load shows dates and times in their
timezone and the interface in their language, in every browser and on every device they sign in
from.

**Why this priority**: it is the feature. Every other story serves this one.

**Independent Test**: sign in, choose a timezone and a language other than the project's
defaults, then load a page that shows a time and translated text, in this browser and in a second
one signed in as the same person.

**Acceptance Scenarios**:

1. **Given** a signed-in person, **When** they open the
   Account Center, **Then** it offers a preferences page, in its menu and on its landing page.
2. **Given** the preferences page, **When** the person chooses a timezone and saves, **Then**
   every page they load afterwards shows dates and times in that timezone.
3. **Given** a project that offers more than one language, **When** the person chooses one and
   saves, **Then** every page they load afterwards is in that language.
4. **Given** a person who has chosen a language, **When** they sign in from another browser,
   **Then** the pages there are in their chosen language without choosing it again.
5. **Given** a person who has chosen nothing, **When** they load a page, **Then** it shows the
   project's default timezone and the language Django would pick for them today.
6. **Given** a signed-in person, **When** they pick a language with the shell's language
   switcher, **Then** their preference changes to it, and the preferences page shows it.
7. **Given** a project that offers only one language, **When** the person opens the preferences
   page, **Then** it offers no language choice.
8. **Given** a submitted value the page does not offer, **When** the person saves, **Then**
   nothing is saved and the page says which choice was not accepted.
9. **Given** a person signed out, **When** they visit any page, **Then** it behaves as it does
   today, whatever they chose while signed in.

---

### User Story 2 - A developer gives their user model preferences when installing django-mvp (Priority: P1)

As one of the steps of installing django-mvp, a developer adds the preferences mixin to their
project's user model and runs the migration, or adds a preferences field of their own under
another name when the model already uses the name `preferences`. The preferences page then
appears in the Account Center with nothing further to configure. A project whose user model has
no preferences field is stopped at startup, with a message saying what to add.

**Why this priority**: no person can choose anything until the project's user model carries
preferences, and every app relies on it doing so.

**Independent Test**: add the mixin to a project's user model and check the page appears, then
remove it and check the project refuses to start with a message naming the mixin.

**Acceptance Scenarios**:

1. **Given** a project whose user model uses the mixin, **When** it starts, **Then** the
   preferences page, its Account Center menu entry and its landing-page card are present.
2. **Given** a project whose user model carries a preferences field of its own under another
   name, **When** it starts, **Then** it behaves as in scenario 1, and the attribute already
   called `preferences` is left as it was.
3. **Given** a project whose user model has no preferences field, including a project on
   Django's own user model, **When** it starts, **Then** startup stops with a message naming the
   mixin and how to add it.
4. **Given** a project that adds the mixin, **When** the developer runs `makemigrations`,
   **Then** it produces one migration for the user model, and no other model or table is added
   for preferences.
5. **Given** the installation guide, **When** a developer follows it, **Then** it includes giving
   the user model preferences, shows the mixin, and shows the field under another name.

---

### User Story 3 - An app's developer adds their own preferences to the page (Priority: P2)

A developer of an installed app built on django-mvp declares a group of preferences for people,
for example how many rows their lists show. Without the project wiring anything, that group
appears on the same preferences page, saved with the rest, and the app reads each person's
values back in its own code, the same way in every project, whatever the project named the
field.

**Why this priority**: it makes the page the one place for a person's preferences across every
app, but the page is already useful with timezone and language alone.

**Independent Test**: install an app that declares a preference group for people, check it
appears on the page and saves, then run the same app in a project whose field has another name.

**Acceptance Scenarios**:

1. **Given** an installed app that declares a preference group for people, **When** a person
   opens the preferences page, **Then** the group appears there as a group of its own, alongside
   timezone and language.
2. **Given** a page with several groups, **When** the person changes values in two of them and
   saves, **Then** both are saved together.
3. **Given** a page with several groups, **When** one value is invalid and the person saves,
   **Then** nothing is saved and the invalid value is marked in its own group.
4. **Given** an app that has declared a group, **When** its code reads a person's value, **Then**
   it gets their choice, or the group's default when they have not chosen.
5. **Given** a project whose preferences field has another name, **When** the app reads a
   person's value, **Then** it gets the same result as in scenario 4, with no change to the
   app's code.

---

### Edge Cases

- A person whose stored timezone or language the project no longer offers sees the project's
  default, and the preferences page shows that choice as unset.
- A person whose preferences change in another browser sees the new choices on their next page
  load here.
- A page rendered for no signed-in person, such as an entrance page or an error page, uses the
  project's defaults.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The package MUST provide a preferences page in the Account Center, with an entry in
  its menu and a card on its landing page, that a signed-in person uses to change their own
  preferences. (US-1)
- **FR-002**: The preferences page MUST be reachable only by a signed-in person, and MUST only
  ever show and change that person's own preferences. (US-1)
- **FR-003**: The package MUST provide a mixin that gives a project's user model its preferences
  field. Adding it MUST need one migration for the user model and nothing else. A project MAY
  instead give its user model a preferences field of its own under any name. (US-2)
- **FR-004**: A project whose user model has no preferences field MUST be stopped at startup,
  with a message naming the mixin and how to add it. (US-2)
- **FR-005**: The preferences page MUST let a person choose their timezone from the standard
  timezones. (US-1)
- **FR-006**: The preferences page MUST let a person choose their language from the languages the
  project offers, and MUST offer no language choice in a project that offers one language. (US-1)
- **FR-007**: On every request from a signed-in person, the site MUST show dates and times in that
  person's chosen timezone and the interface in their chosen language, and MUST use the project's
  defaults for whatever they have not chosen. (US-1)
- **FR-008**: When a signed-in person picks a language with the shell's language switcher, their
  language preference MUST change to it. (US-1)
- **FR-009**: A stored timezone or language the project no longer offers MUST be treated as not
  chosen, without an error. (US-1)
- **FR-010**: An installed app MUST be able to declare a group of preferences for people that
  appears on the preferences page and is saved with the others, without the project configuring
  anything. (US-3)
- **FR-011**: An installed app, and django-mvp itself, MUST read a person's preferences without
  depending on the name the project gave the preferences field. (US-2, US-3)
- **FR-012**: Preferences MUST be stored, validated and read by django-object-preferences as it
  is. django-mvp MUST NOT reimplement its storage, its forms handling or its page. (US-1, US-3)
- **FR-013**: The preferences page MUST carry the shell's look, the same as every other Account
  Center page. (US-1, US-3)
- **FR-014**: The installation guide MUST include giving the user model preferences, with the mixin
  and with a field under another name, and the documentation MUST show an app's developer how to
  declare and read a group of preferences for people. (US-2, US-3)

### Key Entities

- **Preferences**: a person's choices about how the site is shown to them and how its apps behave
  for them. They belong to that person's account and to no other record.
- **Preference group**: a named set of preferences one installed app declares. django-mvp
  declares one for timezone and language.

### Out of scope

- The theme choice, which stays a choice kept in the browser.
- A reader's choice of text size, which https://github.com/django-mvp/django-mvp/issues/544
  defers until per-person preferences exist. This feature makes it possible, and it stays that
  issue's work.
- Preferences for anyone who is not signed in.
- Preferences on records other than a person's account.
- The link from django-mvp-accounts' account management, which is that package's change once this
  is released.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A person who chooses a timezone and a language sees both on the next page they load,
  and in a second browser signed in as them, with nothing else to do.
- **SC-002**: A project gives its user model preferences with one change to the user model, one
  migration, and two installation lines: the app in `INSTALLED_APPS` and the middleware in
  `MIDDLEWARE`.
- **SC-003**: An installed app adds its own group to the page with one declaration in its own
  code, and no change to the project.
- **SC-004**: A project that has not given its user model preferences learns what to add from the
  first startup after upgrading, without reading anything else.
