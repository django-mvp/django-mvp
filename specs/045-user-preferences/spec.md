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
not reimplement. A project turns preferences on by adding a mixin to its user model. The mixin is
optional, and the documentation recommends it.

How each of these is achieved is left to research and planning. Sam's notes for that are in
`planning-notes.md`.

## Clarifications

### Session 2026-11-06 (intake)

- **Q: Where does this live: django-mvp-accounts, django-mvp or django-object-preferences?**
  A: django-mvp (Sam, 2026-11-06). Preferences are a part of the shell any installed app
  contributes to, the way the Account Center already is. django-mvp-accounts only links to the
  page from its account management, which is a change to that package once this is released.

- **Q: Does every project have to add the mixin to its user model?**
  A: No. The mixin is optional, and the documentation strongly recommends it (Sam, 2026-11-06).
  A project on Django's own user model, or one that has not added the mixin, keeps working and
  simply has no preferences page. Recorded as FR-003 and FR-004.

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

- **Q: An installed app declares preferences for people, and the project has not added the mixin.
  Does the project still start?**
  A: Yes. The app's preferences are left out, as the preferences page is. Today
  django-object-preferences stops startup in that case, so django-mvp has to account for it.
  Recorded as FR-011.

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

1. **Given** a signed-in person in a project with preferences turned on, **When** they open the
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

### User Story 2 - A developer turns preferences on for their project (Priority: P1)

A developer adds the preferences mixin to their project's user model and runs the migration. The
preferences page then appears in the Account Center with nothing further to configure. A developer
who does not add it, or whose project uses Django's own user model, sees no preferences page and
nothing breaks.

**Why this priority**: no person can choose anything until a project has turned preferences on.

**Independent Test**: add the mixin to a project's user model and check the page appears, then
remove it and check the project starts and the page and its menu entry are absent.

**Acceptance Scenarios**:

1. **Given** a project whose user model uses the mixin, **When** it starts, **Then** the
   preferences page, its Account Center menu entry and its landing-page card are present.
2. **Given** a project whose user model does not use the mixin, **When** it starts and a person
   opens the Account Center, **Then** it has no preferences page, menu entry or card, and no
   error.
3. **Given** a project on Django's own user model, **When** it starts, **Then** it behaves as in
   scenario 2.
4. **Given** a project that adds the mixin, **When** the developer runs `makemigrations`,
   **Then** it produces one migration for the user model, and no other model or table is added
   for preferences.
5. **Given** the documentation for setting up a project, **When** a developer reads how to define
   their user model, **Then** it recommends the mixin and shows how to add it.

---

### User Story 3 - An app's developer adds their own preferences to the page (Priority: P2)

A developer of an installed app built on django-mvp declares a group of preferences for people,
for example how many rows their lists show. Without the project wiring anything, that group
appears on the same preferences page, saved with the rest, and the app reads each person's
values back in its own code. In a project that has not turned preferences on, the app still
works and its group is left out.

**Why this priority**: it makes the page the one place for a person's preferences across every
app, but the page is already useful with timezone and language alone.

**Independent Test**: install an app that declares a preference group for people, check it
appears on the page and saves, then run the same app in a project without the mixin.

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
5. **Given** a project without the mixin, **When** it starts with that app installed, **Then** it
   starts without error and the app's group is left out.

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
- **FR-003**: The package MUST provide a mixin a project adds to its user model to turn
  preferences on. Adding it MUST need one migration for the user model and nothing else. (US-2)
- **FR-004**: In a project whose user model does not use the mixin, the preferences page, its
  menu entry and its card MUST be absent, and the project MUST start and run without error. (US-2)
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
- **FR-011**: A project without the mixin MUST start without error when an installed app declares
  a group of preferences for people, and that group MUST be left out. (US-3)
- **FR-012**: Preferences MUST be stored, validated and read by django-object-preferences as it
  is. django-mvp MUST NOT reimplement its storage, its forms handling or its page. (US-1, US-3)
- **FR-013**: The preferences page MUST carry the shell's look, the same as every other Account
  Center page. (US-1, US-3)
- **FR-014**: The documentation MUST recommend the mixin where it describes setting up a project's
  user model, show how to add it, and show an app's developer how to declare a group of
  preferences for people. (US-2, US-3)

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
- **SC-002**: A project turns preferences on with one change to its user model and one migration,
  and no new setting.
- **SC-003**: An installed app adds its own group to the page with one declaration in its own
  code, and no change to the project.
- **SC-004**: Every project that worked before this feature still starts and runs unchanged, with
  or without the mixin.
