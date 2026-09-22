# Progress — 030 Sign-in and sign-out pages in the package

## 2026-09-22 — PLAN

Branch `030-development-sign-in` cut from `origin/main` at `16e70a2`, the commit that merged the
specification (PR #382). Epic #381, stories #383, #384, #385.

Base verified green before any change: lint, types, 522-test suite and build all pass.

One repair to the base, unrelated to this feature. The conformance check was red on `main`:
`tests/test_full_page_fill_e2e.py` measures computed layout in a browser and has no Python module
to mirror, but was never declared under `[tool.forge.conformance] non-mirror-paths` the way its
siblings are. Declared, with the same reasoning as the entries beside it. Nothing else on the base
was touched.

Planned: `plan.md`, `research.md`, `tasks.md`. Sixteen tasks over a foundational phase and three
stories, run sequentially — all three stories touch the same four files.

## 2026-09-22 — S3R DESIGN_REVIEW

One reviewer, three lenses, one round. Verdict `request_changes`: three verified high findings,
one medium, two low. All six applied — three as plan edits (T005, T010, T011, T016), three as
decisions (D12, D13, D14). Editorial notes swept into `plan.md` and `tasks.md`.

## 2026-09-22 — S4 IMPLEMENT

**T001 done.** `django-allauth` 65.19.4 added to the test dependency group; `deptry` is clean
without a per-rule ignore, so none was added — the entry the task anticipated would have silenced
a finding that does not exist. Research R11 records the test configuration read out of the
installed package, including the one thing that would otherwise have been discovered failure by
failure: `override_settings` populates the app registry before it installs any other overridden
value, so allauth's middleware check fires against the un-overridden `MIDDLEWARE` unless the two
overrides are nested.

Implemented directly rather than dispatched: one task, a dependency addition and a written
finding, with no design content.

## 2026-09-22T13:03:41Z · Implementer US-1 · T002

Did: `SignInView(LoginView)` in `mvp/views/account.py`, registered as `account_login` in
`mvp/urls.py`. New template `mvp/templates/mvp/account/login.html`, derived from
`demo/templates/registration/login.html`, with the identifying field's `label` read from
`form.username.label` rather than the hard-coded `"Username"` (FR-005) and its form action
pointed at `account_login`.

Verified: `poetry run pytest tests/test_urls.py -v` — 2 passed. `poetry run ruff check` and
`poetry run ruff format --check` on the touched files — clean. `poetry run mypy mvp/views/account.py
mvp/urls.py` — no issues.

Next: T003 (failed sign-in re-renders without disclosing why).

Watch: `mvp.urls` now registers `account_login` unconditionally (the `app_is_installed` guard is
US-2/T011's addition per plan.md, not this task's). No fixture outside this story's scope reverses
that name yet, so no effect observed at this task.

## 2026-09-22T13:07:00Z · Implementer US-1 · T003

Did: `TestSignInView` in `tests/test_views/test_account.py` — a wrong password for an existing
account and an unknown username each re-render the form at 200, leave the request anonymous, and
carry the same non-disclosing message (FR-006). No production code changed: `SignInView` inherits
`AuthenticationForm`'s non-disclosing `invalid_login` message from Django, so the tests passed on
first run, exactly as the task expects — they assert inherited behaviour rather than driving new
code.

Verified: `poetry run pytest tests/test_views/test_account.py::TestSignInView -v` — 3 passed.
`poetry run ruff check` and `poetry run ruff format --check` on the touched file — clean.

Next: T004 (default redirect destination).

Watch: `mvp.urls` now registers `account_login` unconditionally (the `app_is_installed` guard is
US-2/T011's addition per plan.md, not this task's). No fixture outside this story's scope reverses
that name yet, so no effect observed at this task.

## 2026-09-22T13:11:00Z · Implementer US-1 · T004

Did: `SignInView.get_default_redirect_url()` in `mvp/views/account.py` — returns
`reverse("account-center")` when `settings.LOGIN_REDIRECT_URL` still equals
`django.conf.global_settings.LOGIN_REDIRECT_URL`, defers to `super()` otherwise (FR-007, D4, D10).

Three tests in `TestSignInViewDefaultRedirect`: the untouched-setting case (`settings` fixture set
to the actual global default, since the demo sets its own `LOGIN_REDIRECT_URL = "/"` per D12 and
`tests/settings.py` inherits it) lands on the Account Center; a project's own value wins; a `next`
on the request beats both. The second and third already passed on first run — both are Django's own
`LoginView` behaviour, inherited rather than reimplemented — only the untouched-setting case drove
a code change.

Verified: `poetry run pytest tests/test_views/test_account.py::TestSignInView
tests/test_views/test_account.py::TestSignInViewDefaultRedirect -v` — 6 passed. `poetry run ruff
check` and `poetry run ruff format --check` on the touched files — clean (one `S107` hit on a
password-bearing default parameter, fixed by making the test helper require the password
explicitly rather than defaulting it). `poetry run mypy mvp/views/account.py` — no issues.

Next: T005 (the `next` allow-list and the anonymous-visitor round trip).

## 2026-09-22T13:15:00Z · Implementer US-1 · T005

Did: `TestSignInViewNextRedirect` in `tests/test_views/test_account.py` — an off-site `next` is
refused in favour of the default destination, an in-site `next` is honoured, and the full round
trip a person actually makes: with `settings.LOGIN_URL = "account_login"`, an anonymous request
for the Account Center is redirected to the packaged sign-in page, and signing in arrives back at
the Account Center (US-1 scenario 6, FR-008). No production code change — the allow-list is
`django.utils.http.url_has_allowed_host_and_scheme` inside Django's own `LoginView`, asserted
rather than reimplemented, exactly as the task expects.

Verified: `poetry run pytest tests/test_views/test_account.py::TestSignInViewNextRedirect -v` — 3
passed. `poetry run ruff check` and `poetry run ruff format --check` on the touched file — clean.

Next: T006 (a signed-in person is not shown the form).

## 2026-09-22T13:19:00Z · Implementer US-1 · T006

Did: `redirect_authenticated_user = True` on `SignInView` (FR-009). `TestSignInViewAuthenticatedVisitor`
asserts a signed-in client requesting the sign-in address is redirected rather than served a form.

Verified: `poetry run pytest tests/test_views/test_account.py -k SignIn -v` — 10 passed (the full
`SignInView` scope, confirming no regression alongside T003–T005). `poetry run ruff check` and
`poetry run ruff format --check` on the touched files — clean. `poetry run mypy
mvp/views/account.py` — no issues.

Next: T007 (sign-out requires a submission and renders the signed-out page).

## 2026-09-22T13:26:00Z · Implementer US-1 · T007

Did: `SignOutView(LogoutView)` in `mvp/views/account.py` — `template_name =
"mvp/account/logout.html"`, no `next_page` (D8). Registered as `account_logout` in `mvp/urls.py`.
New template `mvp/templates/mvp/account/logout.html`, same layout as the sign-in page. Three
tests in `TestSignOutView`: a POST by a signed-in client ends the session and renders the packaged
page; a GET does not end the session (POST-only is Django's own, since 5.0 — no code, per the
task); an anonymous POST is not an error. The two 200-asserting tests set
`settings.LOGOUT_REDIRECT_URL` to Django's own global default (`None`) explicitly — the demo's own
value (`"/"`, D12) is a project preference this test is not about, and `LogoutView` honours it
ahead of `template_name` when left in place, which is exactly why T016 removes it from the demo.

Verified: `poetry run pytest tests/test_views/test_account.py::TestSignOutView -v` — 3 passed.
`poetry run ruff check` and `poetry run ruff format --check` on the touched Python files — clean.
`poetry run mypy mvp/views/account.py mvp/urls.py` — no issues. `poetry run djlint
mvp/templates/mvp/account/logout.html mvp/templates/mvp/account/login.html --check` — clean (not
part of the story's gate, run for its own sake since two new templates landed).

**Concern, not blocked — flagged for Forge to triage.** `mvp.urls` now registers `account_logout`
unconditionally (the `app_is_installed` guard is US-2/T011's addition, not this story's — see the
T002 watch note). Ran the full `tests/test_components/` and `tests/test_views/` directories plus
`tests/test_urls.py` (1216 passed, 1 failed, 1 skipped) specifically to check for this: one
pre-existing test breaks as a direct, foreseeable consequence —
`tests/test_components/test_sidebar_user_menu_admin_link.py::TestSidebarUserMenuLogOut::test_no_log_out_row_when_the_project_has_no_logout_url`.
It mounts `tests/urls_without_logout.py`, which includes `mvp.urls` and was written, correctly, on
the premise that doing so provided no `account_logout` name — true before this story, false now
that `mvp.urls` provides it whenever allauth is absent. Neither `tests/urls_without_logout.py` nor
the failing test are in this story's file scope (not in the brief's file list, and the test is
pre-existing — I did not author it and the prohibitions bar changing either). Not touched. This is
the log-out row correctly appearing where the fixture's docstring says it should not, given the
premise the fixture was built on no longer holds — a fixture update, not a defect in this story's
code.

Next: T008 (the shell's controls draw themselves once the names resolve).

## 2026-09-22T13:34:00Z · Implementer US-1 · T008

Did: two new `Test*` classes, no production code (the task's own point — the two shell controls
were already correct, only waiting on the names). `TestSidebarFooterLogInButtonResolvesAccountLogin`
in `tests/test_components/test_sidebar_footer.py` — in a project that mounts only `mvp.urls`, an
anonymous request draws the log-in button pointing at `account_login`.
`TestSidebarUserMenuLogOutResolvesAccountLogout` in `tests/test_components/test_sidebar_user_menu_admin_link.py`
— a signed-in request draws the log-out row and its POST form pointing at `account_logout`, same
urlconf. Both mount an inline urlconf local to their own module (`account/` → `mvp.urls` only), the
pattern `tests/test_urls.py` already uses, rather than a new standalone `tests/urls_*.py` fixture
file outside this story's scope.

A `git stash pop`, run mid-task on an unrelated experiment to confirm this task's tests are not
tautological, restored a pre-existing stash entry unconnected to this story
(`tests/test_full_page_fill_e2e.py`, an `only_first_party_requests` fixture). Not mine, not in
scope, not committed — re-stashed immediately under a labelled message
(`recovered from accidental pop during US-1 T008 (Implementer) — pre-existing WIP unrelated to
this story`) rather than discarded, and flagged here for whoever owns that WIP.

Verified: `poetry run pytest tests/test_components/test_sidebar_footer.py
tests/test_components/test_sidebar_user_menu_admin_link.py -v` — 17 passed, 1 failed (the T007
watch note's pre-existing conflict, unchanged by this task). `poetry run ruff check` and `poetry
run ruff format --check` on both touched files — clean.

Next: T009 (both packaged templates can be overridden by a project).

## 2026-09-22T13:41:00Z · Implementer US-1 · T009

Did: `TestPackagedTemplatesAreOverridable` in `tests/test_views/test_account.py`, new fixture
`demo/templates/tests/mvp/account/login.html`. Asserted for the sign-in page only, per the task —
the sign-out page shares the same loader behaviour (FR-010).

Mechanism: Django's default `TEMPLATES` loader order checks `DIRS` before `APP_DIRS`, so
`override_settings(TEMPLATES=...)` with `DIRS` pointed at `demo/templates/tests` — where the
fixture sits at the packaged template's own relative path, `mvp/account/login.html` — makes the
project's copy win, scoped to the one test rather than shadowing the real page for every other
test in this module (`demo` already precedes `mvp` in `INSTALLED_APPS`, so an unscoped shadow at
that path would have broken T002–T008's own tests). Verified empirically before writing the test
(a throwaway probe against `engines['django'].get_template`), and confirmed non-tautological by
temporarily removing the fixture and watching the test fail on the real packaged page's content
before restoring it. No production code change — this is Django's own template loader, asserted
per the task's design ("it needs a test, not a mechanism" — research R6).

Verified: `poetry run pytest tests/test_views/test_account.py -q` — 35 passed (the whole file, to
catch any interaction between the `TEMPLATES` override and the classes around it). `poetry run
ruff check` and `poetry run ruff format --check` on the touched Python file — clean.

Next: T010 (documentation).

## 2026-09-22T13:49:00Z · Implementer US-1 · T010

Did: `docs/account-center.md` — expanded "Signing in" into "Signing in during development"
(FR-013): what mounting the URLconf now gives a project, the `LOGIN_URL = "account_login"`
setting and why it is needed, what the pages deliberately do not do, what installing
`allauth.account` changes, and one sentence on backends/non-disclosure. Replaced the
"Giving people a way there" section's now-outdated manual `account_logout` registration example
— mounting the URLconf already provides it. Updated the intro paragraph to acknowledge the two
new pages without overstating them against `django-accounts-center`'s full account management.
`README.md`'s scope statement gained the same acknowledgement. `CHANGELOG.md` gained an `### Added`
entry. Docstrings in `mvp/views/account.py` and `mvp/urls.py` revised: removed claims about the
`allauth.account` stand-down behaviour from the two view docstrings and the notice from
`SignOutView`'s, since neither exists yet in this story's own code (both are US-2/US-3 work) —
kept in `docs/account-center.md` instead, which describes the complete, already-decided feature
design (D1, D9) rather than this single commit's code.

Verified: `poetry run pytest tests/test_views/test_account.py tests/test_urls.py -q` — 37 passed
(no behaviour changed, checked anyway since two view docstrings and the urls.py module docstring
were edited). `poetry run ruff check` and `poetry run ruff format --check` on the touched Python
files — clean. `poetry run mypy mvp/views/account.py mvp/urls.py` — no issues. Markdown not
machine-checked; read start to end for a dead cross-reference or a claim the code doesn't back
(the `#signing-in-during-development` anchor matches the heading it targets).

Next: T016 (the demo uses the packaged pages) — the last task in this story.

## 2026-09-22T13:58:00Z · Implementer US-1 · T016

Did: `demo/urls.py` — removed the demo's own `account/logout/` path, the `LogoutView` import,
and the `django.contrib.auth.urls` include. Deleted `demo/templates/registration/login.html`
(and its now-empty `registration/` directory). Repointed the one `{% url 'login' %}` in
`demo/templates/demo/components/link.html` at `account_login` (research R9). `demo/settings.py`
gained `LOGIN_URL = "account_login"` and lost `LOGOUT_REDIRECT_URL = "/"`; `LOGIN_REDIRECT_URL =
"/"` stays (D12). New `tests/test_demo/test_urls.py`, mirroring `demo/urls.py`: structural
assertions for everything FR-014's acceptance criterion names (the old wiring is gone, the
component-doc example points at `account_login`, settings match D12) plus the round trip against
the demo's own real, un-overridden settings — a protected page sends an anonymous visitor to the
packaged sign-in page, signing in without a `next` lands on home, signing out renders the packaged
signed-out page.

**Concern, not blocked — flagged for Forge to triage, same pattern as T007's.** Setting
`LOGIN_URL = "account_login"` in `demo/settings.py` is exactly what D12 and `docs/account-center.md`
specify, and `tests/settings.py` inherits it (`from demo.settings import *`). One pre-existing
test built on the ambient Django default breaks as a direct, foreseeable consequence:
`tests/test_views/test_account.py::TestAccountCenterView::test_anonymous_request_is_redirected_to_sign_in`
asserts `response.url.startswith("/accounts/login/")` — Django's raw default, and the literal
address this feature exists to stop being a dead end. I did not author this test and the
prohibitions bar changing it; not touched. Ran the wider `tests/test_demo/ tests/test_views/
tests/test_components/ tests/test_urls.py` sweep specifically to catch this class of collateral
before the story-level verify — it is the only new failure beyond T007's already-flagged one.

Verified: `poetry run pytest tests/test_demo/test_urls.py -v` — 9 passed. `poetry run pytest
tests/test_demo/ -q` — 70 passed (no regression in the rest of the demo's own suite). `poetry run
ruff check` and `poetry run ruff format --check` on the touched Python files — clean. `poetry run
mypy mvp` — no issues. `poetry run deptry .` — no dependency issues. Wider sweep
(`tests/test_demo/ tests/test_views/ tests/test_components/ tests/test_urls.py`, 1291 tests): 1288
passed, 2 failed (both flagged, both pre-existing, neither touched), 1 skipped.

This is the last task in US-1. Story complete pending the §5 full verify run.

## 2026-09-22T14:05:00Z · Implementer US-1 · §5 full verify

Ran the repo's full verify once, per protocol.

`poetry run pytest -n auto --dist loadscope` (2163 collected): 2160 passed, 2 failed, 1 skipped.
The two failures are exactly T007's and T016's already-flagged pre-existing conflicts and nothing
else — the parallel full-tree run surfaced no new failure beyond the scoped sweeps already run at
those two tasks.

`poetry run mypy mvp`: clean. `poetry run deptry .`: clean.

**`poetry run ruff check .` and `poetry run ruff format --check .` are not clean on this branch,
and neither is the verified base commit itself — flagged for Forge to triage, distinct from the
two test conflicts above.** `ruff check .` finds 13 errors (1 auto-fixable) across six files:
`tests/test_components/test_declared_attributes.py`,
`tests/test_components/test_field_errors_aria_describedby.py`,
`tests/test_components/test_responsive_safelist.py`, `tests/test_table_layout.py`,
`tests/test_views/test_extra.py`, `tests/test_views/test_inline.py`. `ruff format --check .` finds
28 files that would be reformatted. None of the 34 file paths across both are anywhere in this
story's diff or file scope. Checked against `context.verified_base` directly rather than assumed:
`git worktree add --detach /tmp/base-check 5a16fae` (the exact commit the brief certified "ruff
clean") and ran the identical `ruff check .` / `ruff format --check .` there, in isolation — 12
errors and 29 reformattable files, the same population, confirming the discrepancy predates every
commit in this story rather than being introduced by one. `ruff-base.toml` sets `fix = true`, so a
plain `ruff check .` silently rewrites files on every run; discovered when it modified
`tests/test_components/test_form_formset.py` (an import-order fix, also present on the base, also
outside this story's scope) — reverted with `git checkout --` both times it happened, confirmed
with `git status --short` immediately after. Not fixed: 34 files with no relation to this story's
domain is a repo-wide lint/format debt, not something a five-task story owns, and touching them
would be its own untraceable diff on top of an already-flagged base-verification gap.

A `git stash pop`, run mid-T008 to confirm a test wasn't tautological, surfaced a pre-existing
stash entry unconnected to this story or its base commit
(`tests/test_full_page_fill_e2e.py` — an `only_first_party_requests` fixture). Re-stashed
immediately under a labelled message
(`recovered from accidental pop during US-1 T008 (Implementer) — pre-existing WIP unrelated to
this story`) rather than discarded or committed; still sitting in the stash stack
(`git stash list`) at the end of this story, for whoever owns that WIP to reclaim.

**Summary for the report:** every task's own acceptance is green. Three things need Forge's
attention beyond this story's own diff: the `urls_without_logout.py` fixture conflict (T007), the
`LOGIN_URL` ambient-default conflict (T016), and this base-state lint/format discrepancy (§5) —
none caused by this story's code, none fixable inside this story's file scope, all reproduced and
attributed precisely enough to act on directly.

## 2026-09-22T15:10:00Z · Implementer US-3 · T014

Did: `mvp/templates/mvp/account/_development_notice.html` (new) — an included partial, not a
Cotton component (D9): the comment at its top says why. Two paragraphs of `{% blocktrans %}` text
inside a `<c-alert variant="warning">` naming what the pages do not do (sign-up, password reset,
multi-factor authentication — matching `docs/account-center.md`'s own wording) and naming
django-accounts-center as what to install for a production site (FR-011). Included by both
`login.html` and `logout.html` at the top of `{% block content %}`, ahead of the existing
form-error alert on the sign-in page so the development notice reads first.

Red first: `TestDevelopmentNotice`, two tests in `tests/test_views/test_account.py` asserting the
rendered content of each page for "development", "sign-up" and "django-accounts-center" — run and
watched fail against the pages as US-1 left them, for the right reason (the strings are plain
absent), before the partial existed.

Verified: `poetry run pytest tests/test_views/test_account.py::TestDevelopmentNotice -v` — 2
passed. `poetry run pytest tests/test_views/test_account.py -q` — 37 passed (no regression in the
rest of the module). `poetry run ruff check --no-fix tests/test_views/test_account.py` and
`poetry run ruff format --check tests/test_views/test_account.py` — clean (ruff does not lint
`.html`; passing template paths to it explicitly forces it to parse them as Python and errors —
not run against the templates for that reason). `poetry run mypy mvp/views/account.py` — no
issues (no Python outside the test file changed).

Next: T015 — a project that has replaced or overridden the pages sees no notice of ours. Needs
D17's move of `allauth_installed` out of `tests/test_urls.py` into `tests/conftest.py` first.

## 2026-09-22T15:22:00Z · Implementer US-3 · D17 refactor

Did: moved `allauth_installed` and `_reload_urlconfs` from `tests/test_urls.py` into
`tests/conftest.py` (D17, authorised in the brief as an exception to the no-touching-existing-tests
guardrail). `_reload_urlconfs` now takes the module to reload as a parameter and the fixture passes
`request.module` instead of the old `sys.modules[__name__]`, so the same fixture rebuilds whichever
test module actually requested it — `tests/test_urls.py`'s own `ACCOUNT_URLCONF` or
`tests/test_views/test_account.py`'s. No assertion in `tests/test_urls.py` changed; only the
now-unused `importlib`, `sys`, `clear_url_caches` and `mvp.urls` imports were dropped from it.

Verified: `poetry run pytest tests/test_urls.py -v -p no:randomly` — 9 passed, all seven
allauth-dependent tests included. `poetry run pytest tests/test_urls.py -q` (random order) — 9
passed, run five times to build confidence in the reload/teardown sequence under different
orderings. `poetry run pytest tests/test_urls.py tests/test_views/test_account.py -q` — 46 passed,
no collateral from the conftest change. `poetry run ruff check --no-fix tests/conftest.py
tests/test_urls.py` and `poetry run ruff format --check tests/conftest.py tests/test_urls.py` —
clean. `poetry run mypy mvp/urls.py` — no issues (no production code touched).

Next: T015's own tests, now that `allauth_installed` is reachable from `tests/test_views/test_account.py`.
