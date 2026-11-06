# Research

The full investigation happens when the feature is planned. This file holds, for now, what the
specification assumes already works, and what running it here showed.

## Assumptions checked

- **The Account Center takes a page, a menu entry and a landing-page card from an installed app.**
  Holds. The tests covering contributed pages and cards pass on main (28 tests selected by
  `account_center`, and the 55 in the package's tests that use `tests/testapp_account`).
- **The shell has a language switcher that posts to Django's `set_language`.** Holds. The demo
  routes `set_language` at `/i18n/setlang/` and installs `LocaleMiddleware`, and the switcher's 9
  tests pass on main. FR-008 builds on it.
- **django-object-preferences can store a group of preferences on the user model and show a page
  for the signed-in person.** Holds as documented: `register(model, name=...)` takes any model
  carrying a `PreferencesField`, and `PreferencesView` is a `DetailView` whose `get_object()` can
  return `request.user` (its ADR 0003).
- **A user model without a preferences field is caught at startup.** Holds already for any app
  that declares a group for it: django-object-preferences raises `ImproperlyConfigured` at
  registration when the model has no `PreferencesField`. FR-004 asks for a message that names the
  mixin, which the plain error does not.
- **The preferences field can have any name.** Holds. `registry.get_field(model)` finds the field
  by its type, not its name. Reading a record's preferences, though, goes through the attribute,
  so code outside the model has to look the field up itself to stay independent of the name.
  FR-011 depends on https://github.com/django-mvp/django-object-preferences/issues/27 for a public
  way to do that.
- **The demo can show the feature.** Not yet. The demo project runs on Django's own user model
  (`auth.User`), so it needs a user model of its own with the mixin before the page can be seen
  there.
- **The standard timezones are available without another package.** Holds. Python's `zoneinfo`
  lists 599 on this machine.
