# Implementation Plan: Preferences for each signed-in person

**Branch**: `045-user-preferences` · **Spec**: [spec.md](spec.md) · **Research**:
[research.md](research.md)

## Summary

django-mvp depends on django-object-preferences and uses it as it is. A project gives its user
model the preferences field with `mvp.models.PreferencesMixin`, or with a `PreferencesField` of its
own under another name, and a project with neither is stopped at startup. django-mvp registers one
group for people, `locale`, holding their timezone and language. A middleware applies both to each
request from a signed-in person. A preferences page in the Account Center, a subclass of
django-object-preferences' own page, shows every group registered for the user model, so any
installed app's group appears there without wiring. The shell's language switcher saves a
signed-in person's choice as their preference.

## Technical context

Python 3.12+, Django 5.2–6.1. One new runtime dependency, django-object-preferences `>=0.2,<0.3`
(Article VII, justified in research.md). Tests are pytest, with rendered-HTML assertions and the
Django test client. No browser test (Article XIV): nothing here depends on script.

## Constitution check

| Article | How the plan meets it |
|---|---|
| I Testing | Every task writes its tests first |
| II Simplicity, III Anti-abstraction | One abstract model, one form, one middleware, one small view, one subclass of the upstream page. No setting, no registry of our own |
| IV Integration-first | Storage, validation, saving and the page's behaviour are django-object-preferences'. Language switching is Django's `set_language`, called from the wrapper |
| V Security | The page only ever shows and saves `request.user`, behind `LoginRequiredMixin`. The language view writes only a language the project offers, and only for the signed-in person. CSRF on both, which Django's view and the upstream page already enforce |
| VI, XVII Documentation | Installation steps in `docs/getting-started.md`, the page in `docs/account-center.md`, and a new `docs/preferences.md` for app developers, each in the task that introduces its names |
| VII Dependencies | One addition, justified. `deptry` stays green |
| VIII Internationalization | Every new string in the package is translatable. The demo's are not |
| IX Data model | The package stays model-free: the mixin is abstract. The demo's new user model carries `verbose_name` and `help_text` |
| XI Components | The page uses existing components and the form rendering. No new component |
| XIII Rendered markup | The page, the card and the menu entry have rendered-markup tests |
| XVI Compatibility | A breaking change for projects without the field. Minor version, and the changelog says what to add |

## Design

### Install and startup

- `pyproject.toml`: `django-object-preferences>=0.2,<0.3`.
- `docs/getting-started.md`: `object_preferences` in `INSTALLED_APPS`,
  `mvp.middleware.PreferencesMiddleware` after `AuthenticationMiddleware`, and a section "Your user
  model" showing the mixin and a field of another name.
- `mvp/checks.py`:
  - `mvp.E004`, an error, when `object_preferences` is not installed. Without it nothing imports
    `mvp/preferences.py` and the page would show no group. Its hint also names
    `mvp.models.PreferencesMixin`, so a project upgrading learns both steps from its first startup
    (SC-004).
  - `mvp.W006`, a warning, when `mvp.middleware.PreferencesMiddleware` is not in `MIDDLEWARE` or
    comes before `django.contrib.auth.middleware.AuthenticationMiddleware`. Without it nothing
    fails, the choices just have no effect.
- `mvp/preferences.py`, imported by django-object-preferences' autodiscovery while apps load,
  first calls `registry.get_field(get_user_model())`. When that raises, it raises
  `ImproperlyConfigured` naming the user model, `mvp.models.PreferencesMixin`, and the alternative
  of a `PreferencesField` under another name. It runs while apps load, so it stops `runserver`,
  `migrate` and the test run alike (FR-004). Adding the mixin to the model's code is what makes the
  error go away, so `makemigrations` then runs and writes the migration.

### The mixin: `mvp/models.py`

```python
class PreferencesMixin(models.Model):
    preferences = PreferencesField()

    class Meta:
        abstract = True
```

### The group: `mvp/preferences.py`

```python
@register(get_user_model(), name="locale")
class LocalePreferences(forms.Form):
    timezone = forms.ChoiceField(...)   # zoneinfo names grouped by region, initial settings.TIME_ZONE
    language = forms.ChoiceField(...)   # ("", "Automatic") + settings.LANGUAGES, initial ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if len(settings.LANGUAGES) < 2:
            del self.fields["language"]
```

- Choices are computed when the form is built, not at import, so a project's `LANGUAGES` and
  `override_settings` in tests both take effect.
- A person who never chooses has nothing stored, so they follow the project's `TIME_ZONE`, and
  Django's own language negotiation, even after either changes.
- Group order on the page is registration order, which follows `INSTALLED_APPS`. The spec asks
  for nothing more.
- The timezone choices are built once per process and cached: building them from `zoneinfo`
  costs about 2 ms, and the form is built on every signed-in request.
- `language` is `required=False`, so its empty "automatic" choice validates.
- The middleware reads `registry.get_preferences(user)["locale"]` directly. A person's stored
  language the project has since dropped already reads as the default in
  django-object-preferences (FR-009).

### Applying them: `mvp/middleware.py`, `PreferencesMiddleware`

```python
def __call__(self, request):
    user = getattr(request, "user", None)
    if not (user and user.is_authenticated):
        return self.get_response(request)
    locale = registry.get_preferences(user)["locale"]
    previous = translation.get_language()
    timezone.activate(zoneinfo.ZoneInfo(locale["timezone"]))
    if locale.get("language"):
        translation.activate(locale["language"])
        request.LANGUAGE_CODE = translation.get_language()
    try:
        response = self.get_response(request)
        response.headers.setdefault("Content-Language", translation.get_language())
        return response
    finally:
        timezone.deactivate()
        translation.activate(previous)
```

- `LocaleMiddleware` runs before authentication, so it cannot see the person. This runs after
  authentication and replaces what `LocaleMiddleware` chose.
- The language that was active before is put back after the response, and `Content-Language` is
  set here. A project without `LocaleMiddleware` has nothing else resetting the language per
  thread, so without this the next request on the same worker would get this person's language
  (FR-007, US-1 scenario 9).
- The timezone choices only hold names `zoneinfo` loads, and a stored name it no longer offers
  reads as the default, so no fallback is needed.

### The language switcher: `mvp/views/preferences.py`, `set_language`

- `POST` only, at `account/preferences/language/`, name `mvp-set-language`, in `mvp.urls`,
  decorated with `require_POST` and `csrf_protect`: Django's `set_language` relies on the project's
  CSRF middleware rather than enforcing it.
- For a signed-in person, a `language` the project offers, and a `locale` group that has a
  language field (it is removed when the project offers one language): `change("locale",
  language=code)`, then `save()`. Anything else changes no preference.
- Then returns `django.views.i18n.set_language(request)`, which sets the cookie, follows `next`
  safely, and ignores an unknown language as it does today.
- `language_switcher.html` and `language_switcher_modal.html` post to `mvp-set-language` for a
  signed-in person when the name reverses, and to `set_language` otherwise.

### The page: `mvp/views/preferences.py`, `AccountPreferencesView`

```python
class AccountPreferencesView(LoginRequiredMixin, PageMixin, PreferencesView):
    template_name = "mvp/account/preferences.html"
    page_title = _("Preferences")
    breadcrumbs = ...  # Account Center, then Preferences

    def get_object(self, queryset=None):
        return self.request.user
```

- `PageMixin` (`mvp/views/base.py`) is a plain mixin, the one `MVPTemplateView` composes, so it
  composes with the upstream `DetailView` the same way.
- Routed in the Account Center app's `urls`, `account/preferences/`, name `account-preferences`,
  so it is inside the mount and the sidebar shows the area's menu.
- `mvp/account/preferences.html` extends `mvp/account/base.html`. Each group is a `<fieldset>` with
  its name as the legend, drawn through crispy with the `mvp_forms` pack, and one Save button.
  Messages come from the shell.
- `AccountCenterMenu` gains an entry, `preferences`, with the `settings` icon.
- `mvp/account/overview.html` gains a card for the page in its own `account.cards` block. The
  landing page is therefore never empty any more. That supersedes FS-028 FR-019's empty region,
  so T006 also updates the three tests that assert it (`tests/test_views/test_account.py`
  `test_signed_in_request_shows_no_cards`, `test_with_neither_app_installed_the_region_is_empty`,
  and the single-card unpacking in `test_a_project_template_adds_its_card_to_the_region`), the
  "What it looks like with nothing installed" section of `docs/account-center.md`, and the
  `AccountCenterView` docstring.

### Demo and tests

- New app `demo.users`: `User(PreferencesMixin, AbstractUser)`, its own `0001_initial`,
  `AUTH_USER_MODEL = "users.User"`. It has to be an app of its own: the user model must be in its
  app's first migration, because `django.contrib.admin`'s first migration depends on it, and the
  `demo` app's first migration already exists.
- The demo installs `object_preferences` and lists the middleware. `seed_demo` keeps its three
  accounts and gives `regular.user@example.com` a stored timezone and language other than the
  defaults, so the walkthrough has a person who has chosen.
- `tests/settings.py` inherits all of it. The startup error is tested in a subprocess, with a
  settings module whose user model lacks the field.

## Story order and dispatch

US-2 → US-1 → US-3, one feature worktree, four dispatches (`tasks.md`). US-2 goes first because
nothing else starts until the user model carries the field.

## Risks

- **Every existing project stops on upgrade until it adds the field.** That is the decision. The
  error and the changelog say exactly what to add.
- **Swapping the demo's user model** invalidates the development database. It is rebuilt from
  `seed_demo`.
- **A 599-option select.** Grouped by region it is usable without a script. A searchable control
  waits until the shell ships one.
- **Language prefixes in URLs (`i18n_patterns`).** `LocaleMiddleware` redirects on the prefix
  before this middleware runs, so in such a project the stored language applies only to pages
  without a prefix. Not addressed, and no current project uses language prefixes.
