# Implementation Plan: Sign-in and sign-out pages in the package

**Branch**: `030-development-sign-in` | **Date**: 2026-09-22 | **Spec**: [`spec.md`](./spec.md)

**Input**: Feature specification from `/specs/030-development-sign-in/spec.md`

## Summary

The package gains a sign-in page and a sign-out endpoint inside `mvp/urls.py`, registered under
`account_login` and `account_logout` — the two names the shell's existing sidebar controls
already reverse and today never find. Both are thin subclasses of Django's own `LoginView` and
`LogoutView`, rendering packaged templates that extend `mvp/entrance.html`, and both carry a
notice naming django-accounts-center as what to install for a production site. The two entries
are not added to `urlpatterns` at all when `allauth.account` is installed, so which view answers
those addresses never depends on the order two URLconfs were mounted in. The demo application
drops the sign-in and sign-out wiring it carries today and uses the packaged pages.

Almost every functional requirement here is already Django's behaviour — the redirect allow-list,
the identifying field, the non-disclosing failure message, the POST-only sign-out. The work is
registering them in the right place, defaulting one destination, writing two templates, and
proving each claim with a test.

## Technical Context

**Language/Version**: Python 3.12+ / Django 5.2+ (CI also runs 3.13 and Django 6.0)

**Primary Dependencies**: Django, django-cotton, django-crispy-forms + crispy-tailwind (all
already present). One new **test-group** dependency: `django-allauth` — see research R8.

**Storage**: N/A. This feature stores nothing and introduces no model or migration.

**Testing**: pytest + pytest-django. Rendered-markup assertions through BeautifulSoup, the way
`tests/test_views/test_account.py` already does. No browser test: nothing here is a claim about
computed layout (Article XIV).

**Target Platform**: A published Django package and its demo project.

**Project Type**: Single package (`mvp/`) with a demo application (`demo/`) and one test suite.

**Performance Goals**: N/A.

**Constraints**: The published runtime dependency set does not grow (Article VII). No new Cotton
component, because a component is public API (Article XI) and nothing here is meant to be one.

**Scale/Scope**: Two views, two URL entries, two templates and one shared partial, one demo
cleanup, one documentation section. No model, no migration, no JavaScript.

## Constitution Check

*GATE: passed before design; re-checked after.*

| Article | How this plan satisfies it |
|---|---|
| I — Test-First | Every task below names its failing test first. The behaviours that are Django's own are still asserted here, because the claim the package makes is that they hold at these addresses. |
| II — Simplicity | Two subclasses that set attributes. The only method written is the one destination default FR-007 requires. |
| III — Anti-Abstraction | No base class, no registry, no settings hook. The notice is an `{% include %}`d partial, not a component, because it has no second consumer and a component would be public API. |
| IV — Integration-First | The contract is the URLconf: which names are registered, and under which conditions. US-2's tests exercise it exactly as a consuming project meets it, including with allauth genuinely installed. |
| V — Security | This is authentication, so it is not fast-lane work: FR-006 (non-disclosure), FR-008 (redirect allow-list) and FR-004 (POST-only sign-out) each get a test of their own rather than resting on "Django does that". |
| VI — Documentation | The documentation task sits in US-1, the story that introduces the public names, not batched at the end. README scope sentence, `docs/account-center.md` section, CHANGELOG, docstrings. |
| VII — Dependency discipline | `django-allauth` is test-group only, justified in research R8. `deptry`'s DEP001 ignore list gains it for the same reason `pytest` and `bs4` are there. |
| VIII — i18n | Every string in both templates and both views is wrapped. The sign-in page reads its field label off the form rather than writing one. |
| IX — Data-model conventions | N/A — no model, no migration. |
| X — Test structure | `mvp/views/account.py` is mirrored by `tests/test_views/test_account.py`, which exists; the new tests are new `Test*` classes in that module, not new files. `mvp/urls.py` is mirrored by `tests/test_urls.py`, which does not exist yet and is created. |
| XI — Components are the public API | No component is added or changed. The two shell controls start rendering because the names resolve. |
| XIII — Rendered markup is a contract | The notice, the form's field names and the sign-out form's method are asserted against rendered HTML. |
| XIV — Browser tests are the exception | None needed. |
| XVII — Cohesion | The two views are classes in the module that already holds this area's view. |
| XIX — Views forward component attributes as a dict | N/A — neither view configures a component. |

No violations. Complexity Tracking is empty.

## Design

### The two views — `mvp/views/account.py`

`SignInView(LoginView)`:

- `template_name = "mvp/account/login.html"`
- `redirect_authenticated_user = True` — FR-009.
- `get_default_redirect_url()` returns `reverse("account-center")` when
  `settings.LOGIN_REDIRECT_URL` still equals `django.conf.global_settings.LOGIN_REDIRECT_URL`,
  and defers to `super()` otherwise — FR-007 and decision D4. This is the only method the feature
  writes. Comparing against the global default is what makes "the project has not expressed a
  preference" a fact rather than a guess (research R3).
- Everything else — the `next` allow-list (FR-008), `AuthenticationForm` reading
  `USERNAME_FIELD` (FR-005), the non-disclosing `invalid_login` message (FR-006) — is inherited
  and asserted, never reimplemented.

`SignOutView(LogoutView)`:

- `template_name = "mvp/account/logout.html"`, and **no** `next_page`, so a successful sign-out
  renders the packaged signed-out page rather than redirecting. That page is what carries the
  notice US-3 requires on both pages.
- POST-only is Django's since 5.0; FR-004 is a test, not code (research R2).

Both get a docstring in the module's established voice, naming the URL name each is registered
under and what a project installing account management gets instead.

### The URLconf — `mvp/urls.py`

```
urlpatterns = [path("", AccountCenterView.as_view(), name="account-center")]

if not app_is_installed("allauth.account"):
    urlpatterns += [
        path("login/", SignInView.as_view(), name="account_login"),
        path("logout/", SignOutView.as_view(), name="account_logout"),
    ]
```

The guard is `mvp.utils.app_is_installed`, the helper this package already exports and
django-accounts-center already guards its own integration URLs with (research R7). The module
docstring gains the reason, written for a consumer: with duplicate names Django answers a request
from the first match and reverses from the last, so two registrations disagree, and the
documented mount order puts this URLconf first.

### The templates

- `mvp/templates/mvp/account/login.html` — extends `mvp/entrance.html`, overrides
  `{% block entrance %}` for a narrower card, and renders the form's non-field errors, the
  identifying field by `form.username.label` / `.html_name` / `.errors`, the password field, the
  submit button and the hidden `next`. Derived from the demo's existing template (research R4/R5)
  with the hard-coded `Username` label removed.
- `mvp/templates/mvp/account/logout.html` — the signed-out confirmation, same layout, with a link
  back to the sign-in page.
- `mvp/templates/mvp/account/_development_notice.html` — the notice, included by both. A partial
  rather than a component: it is not something a project is invited to compose with, and it is
  overridable at the same path as everything else if a project takes the pages on.

### The demo — `demo/`

Delete its `account_logout` path, its `django.contrib.auth.urls` include and
`demo/templates/registration/login.html`; repoint the one `{% url 'login' %}` in
`demo/templates/demo/components/link.html` at `account_login` (research R9).
`LOGIN_REDIRECT_URL = "/"` stays: it is a project preference, and leaving it is what shows
FR-007's precedence working in the thing a person can open.

## Project Structure

### Documentation (this feature)

```text
specs/030-development-sign-in/
├── spec.md              # on main from the specification pull request
├── decisions.md         # on main; appended to, never restarted
├── plan.md              # this file
├── research.md          # what was read before planning
├── tasks.md             # the task list
├── progress.md          # run log
└── feature-state.json   # the ledger
```

No `data-model.md` (no model) and no `contracts/` (no API surface beyond the URLconf, which is
specified inline above).

### Source Code (repository root)

```text
mvp/
├── urls.py                                   # two conditional entries
├── views/account.py                          # SignInView, SignOutView
└── templates/mvp/account/
    ├── login.html                            # new
    ├── logout.html                           # new
    └── _development_notice.html              # new

demo/
├── urls.py                                   # wiring removed
├── templates/registration/login.html         # deleted
└── templates/demo/components/link.html       # example link repointed

docs/
└── account-center.md                         # new section

tests/
├── test_urls.py                              # new — mirrors mvp/urls.py
└── test_views/test_account.py                # new Test* classes
```

**Structure Decision**: the package's existing layout, unchanged. The sign-in and sign-out views
join the module that already holds this area's view, and their tests join the module that already
mirrors it (Article X). `mvp/urls.py` gains its own mirrored test module because this feature is
the first to make that file's contents conditional, and the condition is the feature's central
claim.

## Complexity Tracking

No Constitution Check violations. Table intentionally empty.
