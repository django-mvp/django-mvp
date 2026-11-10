# Research

What the plan needs settled, read against main on 2026-11-07.

## Planning notes

### Integrate django-object-preferences, don't rewrite it

**Adopted.** django-object-preferences 0.2.0 becomes a runtime dependency (`>=0.2,<0.3`), and
`object_preferences` joins the apps a project installs. django-mvp uses, unchanged:

- `PreferencesField`, through the mixin.
- The registry and its `register` decorator, for the timezone and language group.
- `registry.get_preferences(record)`, added in 0.2.0, to read a person's preferences whatever the
  field is named (FR-011).
- `PreferencesView`, subclassed only to choose the record (the signed-in person), add the sign-in
  requirement and point at a template drawn in the shell. Its saving, validation and all-or-nothing
  handling are its own.

Its plain page template is replaced by a django-mvp template of its own name, the same way the
package's other integrations restyle a third-party page.

### A user model mixin, required

**Adopted.** The mixin is an abstract model carrying one `PreferencesField`. A project whose user
model has no preferences field is stopped at startup. The check runs when the timezone and language
group is registered, before django-object-preferences raises its own, less specific error, so the
message names the mixin and the alternative of a field under another name.

### The field may have another name

**Adopted, through django-object-preferences 0.2.0.** No class constant or class method is needed:
the registry finds the field by its type, and `registry.get_preferences(record)` reads it without
the name. Everything django-mvp writes goes through that call. The documentation tells an app's
developer to do the same.

## Approach

1. **Install.** `django-object-preferences` in `dependencies`, `object_preferences` in the
   installation guide's `INSTALLED_APPS`, and a system check that names it when it is missing,
   because without it no group is ever registered and the page would be empty.
2. **The mixin.** `mvp.models.PreferencesMixin`, abstract, one field. The package itself stays
   without a concrete model and without migrations.
3. **The timezone and language group.** `mvp/preferences.py`, picked up by django-object-preferences'
   own autodiscovery. Registered for `get_user_model()` under the name `locale`.
   - **Timezone:** a choice over `zoneinfo.available_timezones()`, grouped by region so the select
     is navigable without a script, with the project's `TIME_ZONE` as its default. A person who
     never chooses follows the project's setting if it later changes.
   - **Language:** a choice over the project's `LANGUAGES`, plus an empty "automatic" choice as the
     default, which leaves the language to Django's own negotiation (FR-007, scenario 5). The field
     is removed when the project offers one language (FR-006).
   - A stored value the project no longer offers already reads as the default in
     django-object-preferences (FR-009), so nothing is added for it.
4. **Applying them to each request.** A middleware, listed after `AuthenticationMiddleware`. For a
   signed-in person it activates their timezone for the request and deactivates it afterwards, and
   activates their language and sets `request.LANGUAGE_CODE` when they chose one. Django's
   `LocaleMiddleware` runs before authentication, so it cannot read the person's choice itself. Its
   response handling runs after ours, so the `Content-Language` header follows the activated
   language. Without the middleware nothing fails, the choices just have no effect, so a system
   warning names it when it is missing.
5. **The language switcher writes the preference (FR-008).** A small view in `mvp.urls`, at
   `account/preferences/language/`, that saves a valid language to a signed-in person's preferences
   and then hands the request to Django's own `set_language` view, which does the cookie, the
   `next` redirect and the validation it already does. The switcher posts there for a signed-in
   person and to `set_language` for a visitor.
6. **The page.** `account/preferences/` in the Account Center's URLconf, an entry in
   `AccountCenterMenu`, and a card in the landing page's own `account.cards` block. Each group is a
   fieldset drawn through the shell's form rendering, with the group's name as its heading.
7. **The demo and the tests.** A new demo app, `demo.users`, with `User(PreferencesMixin,
   AbstractUser)` as `AUTH_USER_MODEL`. It has to be an app of its own: the user model must exist in
   its app's first migration, because `django.contrib.admin`'s first migration depends on it, and
   `demo`'s first migration is already taken. The tests inherit it through `tests/settings.py`.
   Every test already creates users through `get_user_model()`, so none changes for the swap. The
   development database is rebuilt from `seed_demo`.

## Spec deltas found in research

- **SC-002 says "no new setting".** Applying the choices to each request needs one middleware line,
  and the package needs `object_preferences` in `INSTALLED_APPS`. Both are installation steps of the
  kind the guide already lists, but the criterion as written is false. To be put to Sam at the plan
  gate: SC-002 reads "with one change to its user model, one migration, and two installation lines".
- **A breaking change for every existing project.** Upgrading stops a project whose user model has
  no preferences field. The release is a minor version and its changelog entry says what to add.

## What already exists

```
user model field for preferences       · 3, package · object_preferences.fields.PreferencesField
mixin carrying the field               · 7, new     · searched mvp/, object_preferences: no abstract model ships
timezone field and its choices         · 6, package · timezone_field.TimeZoneFormField (django-timezone-field)
grouped, searchable timezone control   · 3, package · mvp_forms.widgets.TimeZoneSelect (django-mvp-forms 0.10.0)
language list                          · 4, Django  · settings.LANGUAGES
storing, validating and saving groups  · 3, package · object_preferences RecordPreferences.get_form / apply / save
reading without the field's name       · 3, package · object_preferences.registry.registry.get_preferences
preferences page                       · 3, package · object_preferences.views.PreferencesView, subclassed for get_object and the template
sign-in requirement on the page        · 4, Django  · django.contrib.auth.mixins.LoginRequiredMixin
page in the shell                      · 2, repo    · mvp/account/base.html, MVPTemplateView's PageMixin breadcrumbs
form rendering                         · 3, package · crispy_forms with mvp_forms' template pack
menu entry                             · 2, repo    · mvp.menus.AccountCenterMenu.append
landing card                           · 2, repo    · mvp/account/overview.html account.cards block
activating timezone per request        · 7, new     · searched Django (documents a sample middleware only), django-timezone-field (a field, no activation), django-tz-detect (browser detection, no stored choice)
activating language per request        · 4, Django  · django.utils.translation.activate, inside the same middleware
language switch and its cookie         · 4, Django  · django.views.i18n.set_language, called by the wrapper
saving the switcher's choice           · 7, new     · searched Django, object_preferences: nothing writes a stored preference on set_language
startup check                          · 2, repo    · mvp/checks.py, the existing mvp.E/W check pattern
```

## Assumptions checked

- **The Account Center takes a page, a menu entry and a landing-page card.** Holds. 28 tests
  selected by `account_center` and the 55 in `tests/testapp_account` pass on main.
- **The shell's language switcher posts to Django's `set_language`.** Holds. The demo routes it at
  `/i18n/setlang/` and installs `LocaleMiddleware`. The switcher's 9 tests pass on main.
- **django-object-preferences 0.2.0 is on PyPI with `registry.get_preferences`.** Holds. Released
  2026-11-06. `PreferencesView.get_preferences` already uses it.
- **A user model without a preferences field is caught at startup.** Holds in
  django-object-preferences, with a message that does not name the mixin. The plan raises its own
  first.
- **The preferences field can have any name.** Holds. `registry.get_field(model)` finds it by type.
- **Swapping the demo's user model breaks no test.** Every test creates users through
  `get_user_model()`. 18 references to `auth.models` are all `AnonymousUser`, which does not change.
- **The standard timezones are available without another package.** Holds. `zoneinfo` lists 599.
