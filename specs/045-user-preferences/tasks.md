# Tasks — 045 Preferences for each signed-in person

**Branch**: `045-user-preferences` · **Plan**: [plan.md](plan.md) · **Research**:
[research.md](research.md) · **Spec**: [spec.md](spec.md)

Every task follows Article I's test-first cycle. A task is done when its tests pass, the tree is
green and the work is committed. Documentation for a public name lands in the task that introduces
it. Tests mirror the source tree: `tests/test_models.py`, `tests/test_preferences.py`,
`tests/test_middleware.py`, `tests/test_views/test_preferences.py`, `tests/test_checks.py`, and the
switcher's existing component tests.

## Checklist

- [ ] T001 [US2] The dependency, the mixin and the demo's own user model
- [ ] T002 [US2] A user model without preferences stops startup with a message naming the mixin
- [ ] T003 [US2] Startup checks for the app and the middleware, and the installation guide
- [ ] T012 [US2] Document the startup error for a user model without preferences
- [ ] T004 [US1] The timezone and language group
- [ ] T005 [US1] The middleware applies a signed-in person's timezone and language
- [ ] T006 [US1] The preferences page, its menu entry and its card
- [ ] T007 [US1] The language switcher saves a signed-in person's choice
- [ ] T008 [US1] The demo has a person who has chosen
- [ ] T013 [US1] The Account Center menu ships the preferences entry: menu test and navigation docs
- [ ] T014 [US1] Document LocalePreferences on the preferences page
- [ ] T009 [US3] An app's group appears on the page and saves with the others
- [ ] T010 [US3] Preferences are read the same way under a field of another name
- [ ] T011 [US3] The developer guide for declaring and reading preferences, and the changelog

## Order

US-2 (Group 1) → US-1 (Groups 2 and 3) → US-3 (Group 4), in the feature worktree.

---

## Phase 1 — User Story 2: A developer gives their user model preferences when installing django-mvp (P1)

### Group 1

#### T001 — The dependency, the mixin and the demo's own user model

- `django-object-preferences>=0.2,<0.3` in `pyproject.toml` dependencies, lock updated.
- `mvp/models.py` with the abstract `PreferencesMixin` (plan.md).
- `demo/users/` app with `User(PreferencesMixin, AbstractUser)`, `verbose_name`s, one migration;
  `AUTH_USER_MODEL = "users.User"`, `object_preferences` in `INSTALLED_APPS`, the middleware
  line held for T005.
- Tests: the mixin is abstract and gives a concrete model exactly one `PreferencesField`; a model
  using it gets one migration from `makemigrations` and no other model or table (US-2 scenario 4);
  the full suite passes on the swapped user model.

#### T002 — A user model without preferences stops startup with a message naming the mixin

- `mvp/preferences.py` checks the user model's field before registering (plan.md).
- Tests, in a subprocess with a minimal settings module: Django's own user model, and a custom one
  without the field, each stop `django.setup()` with `ImproperlyConfigured` whose message names
  `mvp.models.PreferencesMixin` (US-2 scenario 3); a custom model with a `PreferencesField` named
  `options` starts, and its existing `preferences` attribute is untouched (scenario 2).

#### T003 — Startup checks for the app and the middleware, and the installation guide

- `mvp.E004` and `mvp.W006` in `mvp/checks.py`, registered in `MvpConfig.ready()`.
- `docs/getting-started.md`: the two installation lines and "Your user model", with the mixin and a
  field under another name (US-2 scenario 5, FR-014). `docs/troubleshooting.md` lists both checks.
- Tests: each check fires on its condition and is silent otherwise, including the middleware
  listed before `AuthenticationMiddleware`.

#### T012 — Document the startup error for a user model without preferences

- `docs/troubleshooting.md` describes the error and names `mvp.preferences.require_preferences_field`, found by the documentation check after Group 1.

## Phase 2 — User Story 1: A person chooses their timezone and language (P1)

### Group 2

#### T004 — The timezone and language group

- `LocalePreferences` registered as `locale` for the user model.
- Tests: timezone choices are the `zoneinfo` names, grouped, defaulting to `TIME_ZONE`; language
  choices are "automatic" plus `LANGUAGES`, defaulting to automatic (FR-005, FR-006, FR-007); with
  one language the field is absent (scenario 7); a value outside the choices does not validate
  (scenario 8); a stored language the project no longer offers reads as automatic (FR-009);
  the timezone choices are built once.

#### T005 — The middleware applies a signed-in person's timezone and language

- `mvp/middleware.py`, `PreferencesMiddleware`; listed in the demo after
  `AuthenticationMiddleware`.
- Tests through the test client: a page rendering a time shows it in the person's timezone
  (scenario 2); a page renders in their language and `Content-Language` says so (scenario 3); a
  second client signed in as the same person gets both without choosing again (scenario 4); a
  person who chose nothing gets the project defaults and the browser's negotiated language
  (scenario 5); a visitor gets exactly what they get today (scenario 9); the timezone is
  deactivated after the response; with `LocaleMiddleware` removed, a visitor's request on the
  same thread after a signed-in person's gets the default language, not theirs (SEC-001).

#### T006 — The preferences page, its menu entry and its card

- `AccountPreferencesView`, `mvp/account/preferences.html`, the route, the `AccountCenterMenu`
  entry, the card in `mvp/account/overview.html`. `docs/account-center.md` gains the page and its
  "nothing installed" section says the preferences card is always there. The three existing
  tests asserting an empty card region and the `AccountCenterView` docstring change to match
  (plan.md, "The page").
- Tests: the landing page and the menu offer the page (scenario 1); the page requires sign-in and
  only ever shows and saves the signed-in person (FR-002), including a POST that names another
  user's id; saving a timezone and a language redirects back with a success message and the next
  page uses them; an invalid submission saves nothing and marks the field (scenario 8); the page
  sits inside the Account Center's mount, so the sidebar draws the area's menu.

### Group 3

#### T007 — The language switcher saves a signed-in person's choice

- `set_language` wrapper in `mvp/views/preferences.py`, routed in `mvp.urls`; both switcher
  templates choose their action.
- Tests: a signed-in person's switch changes the stored language and the preferences page shows it
  (scenario 6); a visitor's switch posts to Django's `set_language` and stores nothing; a language
  the project does not offer stores nothing; `next` and the cookie behave as Django's view does;
  GET is refused; a POST without a CSRF token is refused; in a project offering one language a
  signed-in person's switch stores nothing and does not fail.

#### T008 — The demo has a person who has chosen

- `seed_accounts` stores a timezone and a language for `regular.user@example.com`.
- Tests: in `tests/test_demo/test_seed_accounts.py`, that account reads back the stored choices and
  the other two read the defaults.

#### T013 — The Account Center menu ships the preferences entry

- `tests/test_menus.py` expects the new entry, and `docs/navigation.md` lists it. Found after Group 2.

#### T014 — Document LocalePreferences on the preferences page

- `docs/account-center.md` names the form and its group name. Found by the documentation check after Group 3.

## Phase 3 — User Story 3: An app's developer adds their own preferences to the page (P2)

### Group 4

#### T009 — An app's group appears on the page and saves with the others

- A test app in `tests/` registers a group for the user model in its own `preferences.py`.
- Tests: the group appears on the page as a fieldset of its own beside `locale` (scenario 1);
  changing values in both groups saves both (scenario 2); an invalid value in one saves nothing in
  either and is marked in its own group (scenario 3); the app reads a person's value, or the
  default, through `registry.get_preferences` (scenario 4).

#### T010 — Preferences are read the same way under a field of another name

- In the T002 subprocess harness, a user model whose field is named `options`.
- Tests: the page saves, the middleware applies, and the test app's group reads,
  all with no change to their code (scenario 5, FR-011).
- Note for every task: preferences are always read through `registry.get_preferences`, never
  through the `preferences` attribute.

#### T011 — The developer guide for declaring and reading preferences, and the changelog

- `docs/developer/preferences.md`, listed in the docs index: declaring a group for people, reading a person's
  values with `registry.get_preferences`, and why never through the attribute name.
- `CHANGELOG.md` under Unreleased: Added (the page, the group, the middleware, the mixin) and a
  breaking-change line saying what to add to a user model.
