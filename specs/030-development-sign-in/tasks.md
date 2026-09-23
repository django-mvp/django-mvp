# Tasks — 030 Sign-in and sign-out pages in the package

**Branch**: `030-development-sign-in` · **Plan**: [plan.md](plan.md) · **Spec**: [spec.md](spec.md)

Every task follows the red-green-refactor cycle of Article I. A task is done when its tests pass,
the tree is green, and the work is committed.

## Order

**Phase 0 → US-1 → US-2 → US-3, one at a time.** The stories are not dispatched in parallel: all
three touch `mvp/urls.py`, `mvp/views/account.py` and the same two packaged templates, and US-2's
whole subject is what US-1 registered. Running them together would mean three worktrees editing
the same four files.

This is authentication, so Article V applies throughout: every claim about non-disclosure,
redirect safety and the POST-only sign-out is asserted directly, never assumed from "Django does
that".

---

## Phase 0 — Foundational (sequential, before any story)

### T001 — allauth becomes a test dependency, and the test configuration it needs is written down

**Files**: `pyproject.toml`, `poetry.lock`, `specs/030-development-sign-in/research.md`

Add `django-allauth` to the **test** dependency group and add it to `[tool.deptry.per_rule_ignores]`
`DEP001`, beside `pytest` and `bs4`, for the same reason those are there: it is imported only by
the test suite. Extend the comment block under that list with allauth's own one-line reason —
the entries there each carry one, and a bare addition would be the only silent entry.

The published runtime dependency set does not change.

Reasoning is in research R8 — US-2's claim is about what happens when allauth is present, and
there is no way to execute that claim without it.

**Then read allauth's own system checks and write down the complete test configuration it
needs** — the `INSTALLED_APPS` entries and the `MIDDLEWARE` entry — as a new section in
`research.md`. It is not in the virtualenv today, so nothing before this task could read it, and
US-2's tasks must not discover it one failure at a time. Name the URLconf module US-2 mounts
while you are there.

Verify `poetry run deptry .` stays clean and the suite still collects.

---

## US-1 — A developer signs in and out of a project built on django-mvp (P1)

Issue: #383. Delivers FR-001, FR-002, FR-004 through FR-010, FR-012, FR-013, and FR-014 through
T016, which runs with this story and is listed at the end of it.

### T002 — The sign-in page exists at `account_login` and renders the shell

**Files**: `mvp/views/account.py`, `mvp/urls.py`,
`mvp/templates/mvp/account/login.html` (new), `tests/test_views/test_account.py`,
`tests/test_urls.py` (new)

Red first: a test that reverses `account_login` through `mvp.urls` and gets a 200 whose HTML
carries a form with the user model's identifying field and a password field.

`SignInView(LoginView)` with `template_name = "mvp/account/login.html"`. The template extends
`mvp/entrance.html` and overrides `{% block entrance %}` for a narrower card, following
`demo/templates/registration/login.html`, with one difference that matters: the identifying
field's label comes from `form.username.label`, never a hard-coded string, so a project whose
user model identifies by email gets the word its own model declares (FR-005).

`tests/test_urls.py` is new and mirrors `mvp/urls.py`. Build the test's urlconf the way
`tests/test_views/test_account.py` already builds its own rather than leaning on `demo/urls.py`.

Article VIII: `{% load i18n %}` and `{% trans %}` on every string the template writes itself.

### T003 — A failed sign-in re-renders with the error and does not say why

**Files**: `tests/test_views/test_account.py`

Red first, and no implementation is expected to follow: post invalid credentials, assert the
response is a 200 that re-renders the form, that the request is still anonymous, and that the
error text is the same whether the account exists or not. Assert against the rendered HTML that
the message is present where a person will see it (FR-006, Article XIII).

Two cases — a username that exists with a wrong password, and a username that does not exist —
asserting the same message for both. That equality is the requirement.

### T004 — Signing in lands on the Account Center, unless the project said otherwise

**Files**: `mvp/views/account.py`, `tests/test_views/test_account.py`

`get_default_redirect_url()` returns `reverse("account-center")` when `settings.LOGIN_REDIRECT_URL`
still equals `django.conf.global_settings.LOGIN_REDIRECT_URL`, and defers to `super()` otherwise
(FR-007, D4).

Three tests: the untouched-setting case lands on the Account Center; a project that set its own
`LOGIN_REDIRECT_URL` lands there instead; and a `next` supplied on the request beats both.

Import the global default from `django.conf.global_settings` rather than writing the literal
`"/accounts/profile/"` anywhere — the comparison must stay true if Django ever changes it.

### T005 — A `next` destination is honoured only when it points at this site, and a protected page supplies one

**Files**: `tests/test_views/test_account.py`

Red first, no implementation expected: sign in with `?next=` pointing at another host and assert
the response goes to the default destination rather than off-site; then with an in-site path and
assert it is honoured (FR-008, Article V).

**Then the round trip a person actually makes.** With `LOGIN_URL = "account_login"`, request the
Account Center as an anonymous visitor, follow `LoginRequiredMixin`'s redirect to the packaged
sign-in page, sign in, and assert arrival back at the Account Center. That is US-1 scenario 6 end
to end, and hand-supplying `?next=` tests only its second half.

Without that setting, `LoginRequiredMixin` uses Django's global default `/accounts/login/`
(`django/conf/global_settings.py`), which the packaged URLconf does not register, so a
zero-configuration project sends an anonymous visitor from the Account Center to a 404. The
package does not write a consumer's settings; the fix is that T010 documents the setting and this
test proves the documented configuration works.

### T006 — A signed-in person is not shown the form

**Files**: `mvp/views/account.py`, `tests/test_views/test_account.py`

`redirect_authenticated_user = True`. Test: a signed-in client requesting the sign-in address is
redirected rather than served a form (FR-009).

### T007 — Signing out requires a submission and renders the signed-out page

**Files**: `mvp/views/account.py`, `mvp/urls.py`,
`mvp/templates/mvp/account/logout.html` (new), `tests/test_views/test_account.py`

`SignOutView(LogoutView)` with `template_name = "mvp/account/logout.html"` and **no** `next_page`,
so the packaged page renders after a successful sign-out rather than a redirect happening.

Tests: a POST by a signed-in client ends the session and renders that page; a GET does not end the
session (FR-004); an anonymous POST is not an error (spec edge case).

### T008 — The shell's controls draw themselves once the names resolve

**Files**: `tests/test_components/test_sidebar_footer.py` (the sign-in button — the footer's fixed
composition renders `actions/login.html` for an anonymous request) and
`tests/test_components/test_sidebar_user_menu_admin_link.py` (the user menu's log-out row and its
POST form, which that module already asserts against a urlconf chosen per test)

Red first, no implementation expected — this is the feature's point, and nothing in either
component changes. Render in a project that mounts only `mvp.urls`: an anonymous request draws the
sign-in button pointing at `account_login`, a signed-in request draws the user menu with a log-out
row and its POST form pointing at `account_logout` (FR-002, US-1 scenario 5).

New `Test*` classes in those two existing modules, never new files (Article X).

### T009 — Both packaged templates can be overridden by a project

**Files**: `tests/test_views/test_account.py`, a test template under `demo/templates/tests/`
following the existing ones there

A project shipping its own template at the same path decides what renders (FR-010). Assert it for
the sign-in page; the same loader behaviour covers the sign-out page and does not need asserting
twice.

### T010 — Documentation ships with the names it documents

**Files**: `docs/account-center.md`, `README.md`, `CHANGELOG.md`, docstrings in
`mvp/views/account.py` and `mvp/urls.py`

A section in `docs/account-center.md`: what mounting the URLconf now gives a project, the two URL
names, what the pages deliberately do not do, and what installing account management changes
(FR-013). A working example of the one line of URL configuration.

**The example states `LOGIN_URL = "account_login"` beside the include.** Django's global default
is `/accounts/login/`, which the packaged URLconf does not register, so without that setting every
page using `LoginRequiredMixin` — including this package's own Account Center — sends an anonymous
visitor to a 404. It is a project setting and the package does not write it; documenting it is
what makes the documented setup correct. Say what it is for in one sentence rather than listing it
as a magic line.

**One sentence on non-disclosure and authentication backends.** The pages authenticate through
whatever backends the project configures, and the guarantee that a failed sign-in does not reveal
whether an account exists holds for backends that reject inactive users, as Django's default
`ModelBackend` does. A project configuring `AllowAllUsersModelBackend` gets Django's distinct
"This account is inactive" message instead. A package cannot decide a consumer's backend; it can
say which one it is describing.

`README.md`'s scope statement says this package is not an authentication system. That stays true
and needs one sentence acknowledging these pages, or a reader comparing the two concludes the
statement is contradicted.

This task is in US-1 and not at the end of the run on purpose: the verify step reads the branch
diff for documentation at every story exit, and US-1 is where the public names appear.

---

## US-2 — Installing the account-management package takes over (P2)

Issue: #384. Delivers FR-003.

### T011 — The packaged entries are absent when allauth is installed

**Files**: `mvp/urls.py`, `tests/test_urls.py`

Red first: with allauth installed, `mvp.urls` contributes no `account_login` and no
`account_logout`.

**Build the test mechanism as one fixture, and build it completely.** Reloading `mvp.urls` alone
is not enough and leaves the process broken for every later test:

- `include("mvp.urls")` imports the module once and hands the module object to a `URLResolver`
  whose `url_patterns` is a `cached_property`, frozen to the list it first read. A reload rebinds
  `mvp.urls.urlpatterns` and that resolver never sees it, so the assertion reads the stale list
  and passes for the wrong reason. `tests/test_views/test_account.py` already builds such a
  resolver at module import, so one exists before any test in this feature runs.
- `django.urls.clear_url_caches()` clears the root resolver cache and the callable cache, not a
  nested resolver's `url_patterns`.
- `override_settings` restores `INSTALLED_APPS` but re-imports nothing, so without a teardown the
  module stays in its allauth-installed shape for the rest of the process. Under `pytest-xdist`
  that surfaces as `NoReverseMatch` in whichever worker happened to run T008 or T013 afterwards.

So the fixture, on entry: apply the settings override, reload `mvp.urls`, reload the test's own
URLconf module so `include()` re-runs and a fresh resolver is built, and call
`clear_url_caches()`. On teardown: repeat all three under the restored settings. **T012, T013 and
T015 use this fixture rather than each reloading by hand.**

Green: guard the two entries with `app_is_installed("allauth.account")` — the helper this package
already exports and django-accounts-center already uses for the same purpose. `mvp/urls.py` needs
no change beyond the guard; it was only the test mechanism that was under-specified.

The module docstring gains the reason, written for a consumer rather than for us: with a name
registered twice Django answers a request from the first match and reverses the name from the
last, so the two disagree, and every documented mounting puts this URLconf first.

### T012 — allauth answers those addresses whichever order the URLconfs were mounted in

**Files**: `tests/test_urls.py`

Uses T011's fixture. Mount `mvp.urls` before allauth's URLconf at the same prefix — the order this project's own
documentation and django-accounts-center's example both use — and assert that requesting the
sign-in address reaches allauth's view and that reversing the name gives allauth's address. Then
assert the same for the opposite order (US-2 scenarios 2 and 3, SC-003).

### T013 — Each name is registered exactly once, in every supported combination

**Files**: `tests/test_urls.py`

Uses T011's fixture. Walk the resolved URL patterns and count registrations of `account_login` and `account_logout`:
with allauth, without allauth, and in both mount orders. Each name appears once (FR-003, SC-004).

Without allauth, assert the packaged pages are present and answer those addresses (US-2
scenario 5).

---

## US-3 — The developer is told not to ship this (P3)

Issue: #385. Delivers FR-011.

### T014 — Both packaged pages carry the notice

**Files**: `mvp/templates/mvp/account/_development_notice.html` (new),
`mvp/templates/mvp/account/login.html`, `mvp/templates/mvp/account/logout.html`,
`tests/test_views/test_account.py`

Red first: rendering each packaged page produces a notice that names what these pages do not do
and names django-accounts-center as what to install for a production site. Assert against the
rendered HTML.

One partial, included by both pages. Not a Cotton component: a component is this package's public
API (Article XI) and this is not something a project is invited to compose with. Every string is
translatable (FR-012).

### T015 — A project that has replaced the pages sees no notice

**Files**: `tests/test_views/test_account.py`

Uses T011's fixture. With allauth installed, its sign-in page carries no notice of ours — which follows from the
packaged templates not being reached at all, and is worth asserting because it is the claim US-3
scenario 3 makes. A project that overrides the packaged template decides for itself whether the
notice appears (US-3 scenario 4); T009 already proves the override point, so assert the notice's
absence in the overriding template rather than rebuilding that fixture.

---

## Demo cleanup — part of US-1, verified again at converge

T016 belongs to US-1 (issue #383) and delivers FR-014. It is listed separately only because it
touches `demo/` rather than the package.

### T016 — The demo uses the packaged pages

**Files**: `demo/urls.py`, `demo/settings.py`, `demo/templates/registration/login.html` (deleted),
`demo/templates/demo/components/link.html`, `tests/test_demo/`

Remove the demo's own `account_logout` path, its `django.contrib.auth.urls` include and its
`registration/login.html`. Repoint the one `{% url 'login' %}` in the components-documentation
example at `account_login` (research R9).

`demo/settings.py` changes in two ways:

- `LOGIN_URL = "account_login"` is added, so the demo configures itself the way T010 documents and
  a person opening a protected page as a visitor is sent to the packaged sign-in form.
- `LOGOUT_REDIRECT_URL = "/"` is **removed**. Django's `LogoutView` honours it ahead of
  `template_name`, so leaving it means the demo redirects to the home page and the packaged
  signed-out page — with the FR-011 notice on it — is never rendered anywhere a person can see.
  FR-014 exists to make the demo show what the package does, and that setting stops it.
- `LOGIN_REDIRECT_URL = "/"` **stays**. It is a project preference and leaving it is what
  demonstrates FR-007's precedence in a thing a person can open.

Verify by running the demo: open a protected page as a visitor and arrive on the packaged sign-in
form, sign in, land on the home page because the demo asks for it, use the user menu's log-out
row, and arrive on the packaged signed-out page with its notice (FR-014, SC-006).

---

## Exit

The feature is done when: every task above is green, `forge verify` passes on the whole diff,
`deptry` is clean, the published runtime dependency set is unchanged, and a project that mounts
only `mvp.urls` can sign in and out with no view, template or URL entry of its own (SC-001).
