# Feature Specification: Swipe and menu actions on list rows

**Feature Branch**: `048-row-actions`

**Created**: 2026-11-22

**Status**: Draft

**Serves**: G2 (a component library covering what a data-centric web application needs, with
small attribute APIs and deliberately limited variation), G5 (a polished, modern look and feel out
of the box). Bound by G14: the gesture script ships with the package.

**Roadmap**: none. No roadmap item covers actions on list rows. This may be a gap in the roadmap.

**Issue**: https://github.com/django-mvp/django-mvp/issues/688

**Input**: On a phone, the quickest way to act on a row in a list is to swipe it, as mail and
music apps do. With a mouse, the same actions belong in a ⋯ menu on the row. django-mvp's list
rows offer neither, so each project builds its own and usually leaves keyboard users out.

After this feature, a developer gives a list row its actions once and they are offered both ways.
On a touch screen, swiping the row to the left reveals the actions under it, a long swipe runs
the row's main action, and only one row is open at a time. Every action is also in the row's ⋯
menu, which is a dropdown with a mouse and a sheet on a touch screen. A keyboard user reaches
every action through that menu, and an action that fails on the server puts the row back as it
was.

The row is a list row, the package's existing `c-list.row`, with actions added. The look is
agreed and already exists: it is carried across at build time, not drawn afresh
(`planning-notes.md`).

## Clarifications

### Session 2026-11-22

All answered from the issue, its sibling feature requests and the agreed design. The reasoning
for each is in `decisions.md`.

- Q: Which pointers swipe a row? → A: A finger on a touch screen and a two-finger swipe on a
  trackpad. A mouse does not drag rows: with a mouse, the ⋯ menu is the way to the actions (D1).
- Q: Which way does a row swipe? → A: Towards the start of the line, which is to the left on a
  left-to-right page and to the right on a right-to-left one. One direction only. A swipe the other way gives a little
  and settles back (D2).
- Q: How does a keyboard user reach an action? → A: Through the row's ⋯ menu, which holds every
  action. The actions under a closed row are out of the tab order, so a keyboard user does not
  meet each action twice (D3).
- Q: On a device with both a touch screen and a mouse, is the menu a dropdown or a sheet? → A:
  It follows the device's primary pointer (D4).
- Q: Must a row have a main action for a long swipe? → A: No. A row without one opens on a long
  swipe and goes no further. A row has at most one main action (D5).
- Q: What happens to a row whose action takes it out of the list? → A: The row folds away as the
  action is sent, and comes back as it was if the request fails (D6).
- Q: Can a list be told not to swipe? → A: Yes. A developer switches swiping off for one list
  and back on, and can shut an open row from script. The menu keeps working while swiping is off
  (D7).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A developer gives a list row its actions (Priority: P1)

A developer building a list adds actions to a list row: each action with its icon, its name and
what it does (a link, a button, a form or an htmx request). They give each action once, and the
row offers it both under the swipe and in the row's ⋯ menu. They can mark one action as the
row's main action, run by a long swipe, and mark an action as one that takes the row out of the
list. They can switch swiping off for a whole list, for instance while it is being reordered,
and shut a row that is open, from one documented script interface.

**Why this priority**: Without the developer's declaration there is nothing for a user to swipe
or open. It is the whole public surface of the feature.

**Independent Test**: Render a list whose rows each declare two actions, one of them main, and
confirm each action is offered once under the row and once in its menu, the main action is the
one a long swipe runs, and nothing the developer gave an id appears twice on the page.

**Acceptance Scenarios**:

1. **Given** a list row with two actions, **When** the page renders, **Then** the row offers both
   actions under the swipe and both in its ⋯ menu, from the one declaration.
2. **Given** a list row with no actions, **When** the page renders, **Then** it is a plain list
   row: it does not swipe and has no ⋯ menu.
3. **Given** a list row whose actions carry an id or a form hook, **When** the page renders,
   **Then** each id appears exactly once on the page.
4. **Given** a list row with one action marked main, **When** the page renders, **Then** that
   action is the one a long swipe runs.
5. **Given** a row declaring two actions marked main, **When** the page renders, **Then** the
   developer is told the row may have only one.
6. **Given** an action marked as taking the row out of the list, **When** a user runs it, **Then**
   the row folds away.
7. **Given** a list the developer has switched swiping off for, **When** a user swipes a row in
   it, **Then** the row does not move, and its ⋯ menu still offers every action.
8. **Given** a list with swiping switched off, **When** the developer switches it back on,
   **Then** its rows swipe again.
9. **Given** a row that is open, **When** the developer's script shuts it through the documented
   interface, **Then** it closes.
10. **Given** a list that announces on its own element that reordering has started, **When**
    the announcement arrives, **Then** any open row in that list shuts and the list stops
    swiping, and **When** the list announces that reordering has ended, **Then** its rows swipe
    again, with no work by the developer.
11. **Given** a list replaced by an htmx request, **When** the new rows arrive, **Then** they swipe
    and their menus open with no further work by the developer.
12. **Given** a project that loads the package's shipped assets, **When** a page with actionable
    rows loads, **Then** nothing the rows need is fetched from a third party.

---

### User Story 2 - A user acts on a list row by swiping it or from its ⋯ menu (Priority: P1)

A person using a site built on django-mvp acts on one row of a list. On a phone they swipe the
row to the left to reveal its actions and tap one, or swipe all the way to run the main action
in one movement. With a mouse they open the row's ⋯ menu, which drops down beside it. On a touch
screen the same ⋯ menu opens as a sheet from the bottom of the screen. With a keyboard they tab
to the ⋯ menu and choose from it.

**Why this priority**: This is what the feature is for. It is equal in priority to the
developer's story, because neither is of use without the other.

**Independent Test**: On a touch screen, swipe a row partway and confirm it stays open on its
actions, swipe another and confirm the first closes, and swipe a row past most of its width and
confirm its main action runs. With a mouse and then a keyboard alone, run every action from the
⋯ menu.

**Acceptance Scenarios**:

1. **Given** a row with actions on a touch screen, **When** the user swipes it partway to the
   left and lets go, **Then** it stays open with its actions revealed.
2. **Given** a row that is open, **When** the user taps one of its actions, **Then** that action
   runs and the row closes.
3. **Given** a row with a main action, **When** the user swipes it past more than 60% of the
   row's width and lets go, **Then** the main action runs.
4. **Given** a row being swiped past that point, **When** the device can vibrate, **Then** it
   gives a short cue as the point is passed, once.
5. **Given** a row with no main action, **When** the user swipes it past its actions, **Then** it
   resists and settles back open on them when released.
6. **Given** a row the user swipes quickly and briefly, **When** they let go, **Then** a flick
   towards the actions opens it and a flick back closes it, however far it moved.
7. **Given** a row that is open, **When** the user swipes another row, taps anywhere else, scrolls
   the page or presses Escape, **Then** the open row closes. At most one row is open at a time.
8. **Given** a row that is open, **When** the user taps the row itself, **Then** it closes and
   nothing else happens: its link is not followed.
9. **Given** a swipe that ends, **When** the finger lifts over the row's content, **Then** the
   content's link or button is not triggered.
10. **Given** a finger that starts within the system's back-gesture area at either edge of the
    screen, **When** it moves sideways, **Then** the row does not move and the system's gesture
    is left alone.
11. **Given** a finger that moves mostly up or down, **When** it starts on a row, **Then** the
    page scrolls and the row does not move.
12. **Given** a trackpad, **When** the user swipes two fingers sideways over a row, **Then** the
    row opens, runs its main action or closes as a finger swipe would.
13. **Given** a user who has never seen a swipeable list on this site on a touch screen, **When**
    the first such list appears with its first row in view, **Then** that row is nudged open and
    back once, so the actions under it are seen to be there, and never again in that browser.
14. **Given** an action that takes its row out of the list, **When** the request it sends fails,
    **Then** the row comes back as it was.
15. **Given** a user who has asked for reduced motion, **When** a row opens, closes, folds or is
    nudged, **Then** it changes without animated movement.
16. **Given** a mouse as the primary pointer, **When** the user opens a row's ⋯ menu, **Then** it
    opens as a dropdown beside the row, offering every action.
17. **Given** a touch screen as the primary pointer, **When** the user opens a row's ⋯ menu,
    **Then** it opens as a sheet offering every action, and the sheet closes once one is chosen.
18. **Given** a keyboard user, **When** they tab through the list, **Then** they reach each row's ⋯
    menu, can open it and run every action from it, and do not tab through the actions under
    closed rows.
19. **Given** a row that is open, **When** the user presses Escape with focus inside it, **Then**
    the row closes and focus returns to the row's content.
20. **Given** a screen reader, **When** it reads an action, **Then** the action's name says which
    row it acts on where the action's own word does not.

---

### Edge Cases

- A row whose content is itself a link: a tap still follows the link, a swipe never does.
- A list that grows by htmx after the page loads: its new rows behave like the first ones, and an
  open row elsewhere is not disturbed until the user acts.
- The script fails to load: each row still shows its content and its ⋯ menu still opens and runs
  every action. Swiping is the only thing lost.
- An action that sends no htmx request (a plain link or a full-page form): the row closes, or
  folds when the action takes it out of the list, and the browser carries on as usual.
- A row inside a menu, sheet or dropdown that is itself open: closing the row does not close
  what contains it.
- Right-to-left pages swipe the mirror way.
- A list with swiping switched off while a row is open: the open row closes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A list row MUST accept a set of actions, each given once with an icon, a name and
  what it does (a link, a button, a form submission or an htmx request).
- **FR-002**: A list row with actions MUST offer every one of them both under the swipe and in the
  row's ⋯ menu, from the one declaration.
- **FR-003**: A list row without actions MUST render as a plain list row, with no swipe and no ⋯
  menu.
- **FR-004**: The row MUST build on the package's existing list row (`c-list.row`), not on a row
  of its own.
- **FR-005**: An id or form hook a developer gives an action MUST appear exactly once on the page.
  The ⋯ menu's items MUST be drawn once per row.
- **FR-006**: A developer MUST be able to mark at most one action as the row's main action, and a
  row marking more than one MUST be reported to the developer as an error.
- **FR-007**: A developer MUST be able to mark an action as taking the row out of the list.
- **FR-008**: On a touch screen, a row with actions MUST swipe in one direction, to the left in a
  left-to-right page and to the right in a right-to-left one, revealing its actions. A swipe the
  other way MUST give a little and settle back.
- **FR-009**: A swipe released partway MUST leave the row open on its actions when it passed half
  their width and close it otherwise. A quick flick MUST open or close it whatever its offset.
- **FR-010**: A swipe released past more than 60% of the row's width MUST run the main action. A
  row without a main action MUST resist past its actions and settle back open.
- **FR-011**: Where the device can vibrate, passing the 60% point MUST give one short cue.
- **FR-012**: At most one row on the page MUST be open at a time. An open row MUST close when
  another is swiped, on a tap elsewhere, on a tap on the row itself, on a page scroll and on
  Escape.
- **FR-013**: A swipe MUST never trigger the link or button in the row's content.
- **FR-014**: A touch that starts within 20 CSS pixels of either edge of the screen MUST NOT move
  a row, so the system's back gesture keeps working. A movement that is mostly vertical MUST
  scroll the page and never move the row.
- **FR-015**: A two-finger sideways swipe on a trackpad MUST move a row as a finger does. A mouse
  MUST NOT drag a row.
- **FR-016**: Running an action under an open row MUST close the row, or fold it away when the
  action takes the row out of the list.
- **FR-017**: When an htmx request sent by an action that took its row out of the list fails, the
  row MUST come back as it was.
- **FR-018**: The first time a browser shows a swipeable list on a touch screen with its first
  row in view, that row MUST be nudged open and back once. It MUST NOT be nudged again in that
  browser.
- **FR-019**: When the user has asked for reduced motion, rows MUST open, close, fold and nudge
  without animated movement.
- **FR-020**: The ⋯ menu MUST open as a dropdown (`c-mvp.dropdown`) when the primary pointer is a
  mouse, and in the package's sheet when the primary pointer is a finger. The sheet MUST close
  once an action in it is chosen.
- **FR-021**: The actions under a closed row MUST be out of the tab order and hidden from
  assistive technology. Every action MUST be reachable by keyboard through the ⋯ menu.
- **FR-022**: Escape on an open row holding focus MUST close it and return focus to the row's
  content.
- **FR-023**: An action MUST be able to carry an accessible name that says which row it acts on.
- **FR-024**: A developer MUST be able to switch swiping off for one list and back on, and to shut
  an open row from script, through one documented, named script interface. Switching swiping off
  MUST close any open row in that list and leave the ⋯ menus working.
- **FR-025**: When a list announces on its own element that reordering has started, the row
  MUST shut any open row in that list and switch swiping off for it, and when the list announces
  that reordering has ended, switch swiping back on. The announcements are the documented events
  of the reorder feature; this feature does not depend on that feature being delivered.
- **FR-026**: Rows that arrive by htmx MUST swipe and open their menus with no work by the
  developer.
- **FR-027**: When the gesture script does not run, every action MUST still be reachable from the
  ⋯ menu.
- **FR-028**: The gesture script MUST be the package's own, shipped and versioned with the package
  (G14). Nothing the rows need may be fetched from a third party at page load.
- **FR-029**: The package's icon set MUST name an icon for the ⋯ trigger.
- **FR-030**: The documentation MUST describe how to give a row its actions, how to mark the main
  action and an action that takes the row out of the list, and the script interface, and the
  demo MUST show a list with actionable rows.

### Key Entities

- **Row action**: one thing a person can do to the record a list row shows. It has an icon, a
  name, an optional accessible name, and what it does. It is offered under the swipe and in the
  row's menu.
- **Main action**: the one row action a long swipe runs. A row has none or one.
- **Row menu**: the ⋯ on a list row that opens every row action, as a dropdown with a mouse and a
  sheet with a finger.

The word *row* alone already means a related row of a formset in this repository's vocabulary.
This feature's row is always a *list row*.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer gives a list row its actions in one place, and every action is offered
  under the swipe and in the row menu without being written twice.
- **SC-002**: Every row action is reachable by keyboard alone, through the row menu.
- **SC-003**: No more than one row on a page is open at any moment.
- **SC-004**: An action that fails on the server leaves its row on the page as it was before the
  action.
- **SC-005**: A page with actionable rows fetches nothing from a third party for them.
- **SC-006**: A list can be stopped from swiping, and an open row shut, by the developer's
  script, so a list can be reordered without a row opening under the user.

## Assumptions

- The sheet a row menu opens in on a touch screen is the package's sheet component, delivered by
  https://github.com/django-mvp/django-mvp/issues/687 before this feature is built.
- Reordering a list is delivered separately
  (https://github.com/django-mvp/django-mvp/issues/689) and announces on the list's element when
  reordering starts and ends. This feature listens for those announcements and owns what happens
  to the swipe. It does not wait on that feature: without it, the announcements simply never
  arrive.
- htmx is part of the package's shipped front end, so an action sending an htmx request needs
  nothing more from the project.
- The look of the row, its actions and its menu is agreed and carried across at build time.
