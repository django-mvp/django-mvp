# ADR 0030 — The package's components carry a prefix, and the icon does not

**Status:** accepted

## Decision

Every component this package owns lives under `mvp/templates/cotton/mvp/` and is reached as
`<c-mvp.…>`: `<c-mvp.card>`, `<c-mvp.page.list>`, `<c-mvp.app.sidebar>`. A bare name is for the
basic daisyUI components, which [daisy-cotton](https://github.com/django-mvp/daisy-cotton)
provides. The package's own copies of those (the alert, badge, button and the like) were not
renamed first. They kept their bare names until they were removed in favour of daisy-cotton's.

The icon is the one permanent exception. It stays at `cotton/icon.html` and is written
`<c-icon>`.

A component name written anywhere other than a tag is the full name, prefix included. That
covers the navbar's widget lists in `MVP_CONFIG`, a view's `htmx_form_component` and the name
passed to the testing fixtures. The package adds no prefix on a project's behalf.

There are no aliases at the old names.

## Why

Cotton resolves `<c-card>` to `cotton/card.html` in the first installed app that has one. Two
packages that both use plain names leave `INSTALLED_APPS` order to decide which component a tag
reaches, and nothing in the template says which was meant. This package's card, modal, avatar,
dropdown and menu entry shared a name with a daisy-cotton component and took different
attributes. daisy-cotton's own templates call its menu entry and button, so a narrower component
of the same name placed above it would have been drawn inside daisy-cotton's components too.

A prefix takes app order out of the question for everything the package owns, and a reader can
tell from the tag which package a component comes from.

The icon is the case where sitting at the same name is the point. daisy-cotton ships a plain
icon and expects a project that wants icons looked up by name to place its own component at
that path, above daisy-cotton in `INSTALLED_APPS`, so that every caller picks it up, daisy-cotton's
own components included. This package's icon is that replacement. Under the prefix it would stop
reaching them. It is the only component that is meant to depend on app order.

Names in settings are not prefixed for the project because the same list can hold a project's own
component or one of daisy-cotton's, and the package cannot tell which names are its own without
guessing.

An alias at an old name would put a component of this package back at a daisy-cotton name, which
is the collision the prefix removes.

## Consequences

- A project's override of a packaged component sits at the prefixed path,
  `templates/cotton/mvp/…`. A file left at an old path is not used, and for the five shared
  names it overrides daisy-cotton's component once daisy-cotton is installed.
- A new component added to the package goes under `mvp/`. A test fails when a component template
  sits outside it and is not on a short list of exceptions. That list holds the icon and, until
  they are removed in favour of daisy-cotton's, the package's remaining basic components.
- The rule is stated in Article XI of the constitution and in the glossary's naming rules.
