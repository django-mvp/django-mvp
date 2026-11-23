# ADR 0042 — Every user model carries preferences, stored by django-object-preferences

**Status:** accepted

## Decision

A project on django-mvp gives its user model a `PreferencesField` from django-object-preferences, through `mvp.models.PreferencesMixin` or as a field of its own under any name. A user model without one stops the project at startup, with a message naming the mixin. django-mvp declares its own preferences as a django-object-preferences group, reads every preference through `registry.get_preferences(record)` and never through the attribute name, and uses that package's page, storage and validation as they are.

## Why

Preferences are part of the shell that any installed app contributes to, as the Account Center already is. If the field were optional, every app declaring preferences for people would have to check for it, and a project without it would quietly lose a page. Django recommends a custom user model for every new project, and every project on django-mvp already has one, so requiring one more field costs a line and a migration. Reading through the registry rather than the attribute lets a project keep an existing attribute called `preferences`.

## Revisit if

A project needs to adopt django-mvp while still on Django's built-in user model, or preferences need to live somewhere other than on the user record.
