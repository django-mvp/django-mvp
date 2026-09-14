# Progress — FS-028

## 2026-09-14

- **S0 INTAKE** — feature grilled from a free-text request; interpretation restated and confirmed.
  The generic version of the two-column layout, and a general way to attach a menu to a view class
  or a group of addresses, were raised and deferred by the maintainer in the same exchange. Issue
  #338 filed.
- **S1 SPECIFY** — `spec.md` written: three stories, 26 functional requirements, 6 success
  criteria. Five ambiguities found by the coverage scan and self-resolved; rationale in
  `decisions.md`. Spec lint green (no unresolved markers, every requirement mapped to a story).
- **S2 SETUP** — spec pushed on `028-move-account-center` as the bot. Issue #338 promoted to the
  epic in place. Story sub-issues #339 (P1), #340 (P2), #341 (P3) created and linked. Draft pull
  request #342 opened by the bot, milestone `v1.0.0`, description carrying one `Closes` line per
  issue. Title lint green.
- **Spec gate — APPROVED** by Sam at 2026-09-14, in session, without changes. Recorded here at the
  moment of approval; copied into `feature-state.json` when S3 creates the ledger.

## 2026-09-14 · Implementer US1 · T001

Did: added `tests/test_menus.py::TestAccountCenterMenu` — exact child-count assertion for
`AccountCenterMenu`, plus the child's name and `view_name`.
Verified: `poetry run pytest tests/test_menus.py::TestAccountCenterMenu -q` — collection failed with
`ImportError: cannot import name 'AccountCenterMenu'`, confirming red for the right reason.
Next: T002. Watch: —

## 2026-09-14 · Implementer US1 · T002

Did: added `tests/test_views/test_account.py::TestAccountCenterView` — anonymous redirect, signed-in
render with the navigation panel, an empty card region, heading and introduction text. Mounted
through a purpose-built urlconf (`include("mvp.urls")` + `include("demo.urls")`) rather than
depending on T011's demo mount.
Verified: `poetry run pytest tests/test_views/test_account.py::TestAccountCenterView -q` — collection
failed with `ModuleNotFoundError: No module named 'mvp.urls'`.
Next: T003. Watch: this file's tests stay collection-red until T007/T008/T009 all land.

## 2026-09-14 · Implementer US1 · T003

Did: added `tests/test_components/test_account_nav.py::TestAccountNav` and the fixture
`demo/templates/tests/account_nav.html`, following `test_layout_config.py`'s render pattern.
Verified: `poetry run pytest tests/test_components/test_account_nav.py -q` —
`TemplateDoesNotExist: cotton/account/nav/index.html` (cotton's fallback path; the primary
`cotton/account/nav.html` attempt failed the same way).
Next: T004. Watch: —

## 2026-09-14 · Implementer US1 · T004

Did: added `TestAccountLayout` to `tests/test_views/test_account.py` and the fixture
`demo/templates/tests/account_layout_content.html`.
Verified: same file, still collection-red on `mvp.urls`.
Next: T005. Watch: —

## 2026-09-14 · Implementer US1 · T005

Did: added `tests/test_utils.py::TestAccountCenterIcons`, pinning `icon("account_center")` and
`icon("overview")` by name.
Verified: `poetry run pytest tests/test_utils.py::TestAccountCenterIcons -q` —
`easy_icons.exceptions.IconNotFoundError` for both names (pytest-django forces `DEBUG=False`
during tests, so `EASY_ICONS_FAIL_SILENTLY` defaults false too — a harder failure than the "empty
string" #294 symptom the module docstring describes, but red for the same underlying reason).
Next: T006 — all five tests-first tasks are now confirmed red. Watch: —

## 2026-09-14 · Implementer US1 · T006

Did: declared `AccountCenterMenu` in `mvp/menus.py` beside `AppMenu`/`MobileFooterMenu`, carrying
the single `overview` entry (`view_name="account-center"`, translatable label); extended the module
docstring.
Verified: `poetry run pytest tests/test_menus.py -q` — 10 passed. `ruff check`/`ruff format --check`
clean.
Next: T008 (taken ahead of T007 — see decisions.md D9: writing the urlconf before the view it
imports would leave an unimportable module on this commit). Watch: —

## 2026-09-14 · Implementer US1 · T007/T008

Did: `mvp/views/account.py` (`AccountCenterView`, `LoginRequiredMixin` + `MVPTemplateView`,
translatable title/subtitle), exported from `mvp/views/__init__.py` and `__all__` (T008); then
`mvp/urls.py`, the un-namespaced `account-center` route (T007). Also fixed the T002/T004 tests'
`override_settings` usage — it cannot decorate a plain pytest class, only a `SimpleTestCase`
subclass or a function — with an autouse fixture instead.
Verified: `poetry run pytest tests/test_views/test_account.py -q` — the anonymous-redirect test now
passes; the rest fail on `TemplateDoesNotExist: mvp/account/base.html`, the correct next gap.
`ruff check`/`ruff format --check` clean on both new/changed `.py` files.
Next: T009. Watch: —

## 2026-09-14 · Implementer US1 · T009

Did: `mvp/templates/mvp/account/base.html` (extends `base.html`, two-column `content` override,
`account.content` block for a page to fill), `mvp/templates/mvp/account/overview.html` (heading,
introduction, empty `#account-center-cards` region), `mvp/templates/cotton/account/nav.html`
(`<c-account.nav>` — `<c-card.wrapper>` panel at/above the breakpoint, `<c-dropdown>` collapsed
control below it, one processed `AccountCenterMenu` tree, each rendered inside its own
`<c-menu label="Account navigation">` rather than the shared `menus/sidebar/container.html`, which
hardcodes "Main Navigation" — see decisions.md D10). Also fixed two of this story's own tests found
while wiring this up (see decisions.md D9 area / commit message for detail): the nav test's
missing urlconf override, and the layout test's extends-line assertion, which false-positived on
the prose in this file's own comment.
Verified: `poetry run pytest tests/test_views/test_account.py tests/test_components/test_account_nav.py -q`
— all failures now `IconNotFoundError` for `overview`/`account_center` (the T010 gap). `djlint
--check` clean after `--reformat`.
Next: T010. Watch: this confirms T003's "red before T009" marker undersold the dependency — the
nav item's `icon="overview"` needs T010 too before the suite is fully green (decisions.md D11).

## 2026-09-14 · Implementer US1 · T010

Did: added `account_center` (`bi-person-gear`) and `overview` (`bi-grid`) to `BS5_ICONS` in
`mvp/utils.py`, matching django-accounts-center's own values for the overlap (D8). Also corrected
`tests/test_utils.py`'s module docstring and the `SUPPLIED_BY_A_COMPANION_PACKAGE` comment, both of
which asserted BS5_ICONS "deliberately does not carry" `account_center` — now false. Prose only; no
assertion, frozenset membership or test method touched.
Verified: `poetry run pytest tests/test_utils.py tests/test_views/test_account.py tests/test_components/test_account_nav.py tests/test_menus.py -q`
— 347 passed. `ruff check`/`ruff format --check` clean.
Next: T011. Watch: —

## 2026-09-14 · Implementer US1 · T011

Did: mounted `path("account/", include("mvp.urls"))` in `demo/urls.py`.
Verified: `poetry run pytest -q` (full suite, once, to catch any regression from a global mount) —
1847 passed, 1 skipped, no new failures. `reverse("account-center")` resolves to `/account/` under
`demo.settings`/`demo.urls` directly (no override needed). `ruff check`/`ruff format --check` clean.
Next: T012. Watch: —

## 2026-09-14 · Implementer US1 · T012

Did: `docs/account-center.md` (what the area is, mounting it, signing in, the empty-state rule, a
stub for the two sections US-2/US-3 add); added it to `docs/index.md`'s guide table; named
`AccountCenterMenu` in `docs/navigation.md`; restated README's "deliberately not an authentication
system" bullet (FR-026); added the `[Unreleased]` `CHANGELOG.md` entry recording the surface and
the django-accounts-center menu-name/icon-key overlap through its v0.7.1 (FR-023, D1, D8).
Verified: read-through against the branch as it stands — the mounting example matches
`mvp/urls.py`/`demo/urls.py` exactly.
Next: T013. Watch: —

## 2026-09-14 · Implementer US1 · T013

Did: `skills/django-mvp/references/menus.md` — "two menus" → "three", `AccountCenterMenu` bullet
and classes-table row; `skills/django-mvp/references/layout.md` — two rows in the template-chain
table for `mvp/account/base.html` and `mvp/account/overview.html`.
Verified: read-through against `docs/account-center.md` and `docs/navigation.md` for consistency.
Next: T014. Watch: —

## 2026-09-14 · Implementer US1 · T014

Did: `poetry run invoke build-stylesheet`; committed the rebuilt `mvp/static/css/django-mvp.css`
and `.br` sibling. Added `tests/test_smoke.py::TestStylesheetShipsAccountCenterClasses` — an
absent-control class plus five classes the new templates introduce
(`lg:flex-row`, `lg:items-start`, `lg:gap-6`, `sm:grid-cols-2`, `lg:shrink-0`), matched with a
regex that reproduces the build's colon-escaping (`lg:flex-row` ships as `lg\:flex-row`) rather than
reusing the file's existing `_class_present` helper, which does not.
Verified: `poetry run pytest tests/test_smoke.py -q` — 81 passed. `ruff check`/`ruff format --check`
clean.
Next: verify (§5), completion report. Watch: —

## 2026-09-14 · Implementer US2 · T015

Did: `tests/testapp_account/` — a minimal installed app (`apps.py`, not importing `menus` from
`ready()`) with `menus.build_entries()` returning four fresh top-level entries per call (plain,
grouped-with-one-child, per-request-checked, unresolvable); three fixture views extending
`mvp/account/base.html` via `MVPTemplateView` (not yet `AccountPageMixin`, which T019 adds); its
own `urls.py`/templates. Registered in `tests/settings.py`'s `INSTALLED_APPS`. Added
`testapp_account_entries` to `tests/conftest.py`: applies `build_entries()` to `AccountCenterMenu`
and detaches every entry in a `finally`, so nothing outlives the test that asked for it (ARC-001).
Verified: `poetry run pytest tests/test_menus.py -q` — 10 passed, `TestAccountCenterMenu`'s
exact-count assertion still green with the fixture app installed and no test applying its entries.
`poetry run ruff check`/`ruff format --check` clean; `poetry run djlint --check
tests/testapp_account/templates/` clean after one reflow. Sanity-loaded `tests.settings` directly
to confirm the app registers without an import error.
Next: T016. Watch: fixture views intentionally don't use `AccountPageMixin` yet — T019 adds it to
their bases once it exists, which is what T017's trail assertions depend on turning green.

## 2026-09-14 · Implementer US2 · T016

Did: `tests/test_menus.py::TestAccountMenuContribution` — seven tests against `AccountCenterMenu`
processed with the fixture app's entries applied: exact-count presence alongside the landing-page
entry, a grouped entry's label and its one visible child, the checked entry absent/present across
two requests, the unresolvable entry dropped without disturbing the rest, and FR-008's other
half — reordering via `children` assignment and removal via `.pop()` — both plain
django-flex-menus behaviour, asserted rather than implemented (plan.md "The menu"). No production
code changed: T016 characterises capability the library already provides.
Verified: probed before trusting the green run — flipped the checked entry's `check` to always-True
and confirmed `test_an_entry_whose_check_answers_no_is_absent` and the unresolvable-entry exact-count
assertion failed for the right reason (3 failed), then restored it. `poetry run pytest
tests/test_menus.py -q` — 17 passed. `poetry run ruff check`/`ruff format --check` clean (one
autofix applied to `tests/test_menus.py`'s import block).
Next: T017. Watch: —

## 2026-09-14 · Implementer US2 · T017

Did: `tests/test_views/test_account.py::TestAccountSectionTrail` — four tests against a fixture
urlconf (`mvp.urls` + `tests.testapp_account.urls` + `demo.urls`, the last needed because the
shell's sidebar renders `AppMenu` and several of `demo/menus.py`'s entries resolve against it — a
urlconf missing it 500s on any full-page render): a page at a section's own address gets
`[area(linked), section(unlinked)]`; a page below it gets `[area(linked), section(linked)]`; a page
no entry points at (the landing page itself, no fixture entries applied) gets the single unlinked
area crumb; the fixture's own entry is marked `menu-active` when its page is current.
Verified: `poetry run pytest tests/test_views/test_account.py::TestAccountSectionTrail -q` — 3
failed (`[] == [...]`, `page.breadcrumbs` still the `PageMixin` default empty list — the right
reason, since `AccountPageMixin` doesn't exist until T019) and 1 passed (the current-page marking:
pre-existing `flex_menu`/`menu-active` behaviour from US-1, nothing new to implement there).
`poetry run pytest tests/test_views/test_account.py -q` — 3 failed, 9 passed (the other 9 are
US-1's, untouched). `poetry run ruff check`/`ruff format --check` clean (one autofix applied).
Next: T018 (`get_active_section`), then T019 turns these three green.
Watch: T019 must also add `AccountPageMixin` to `tests/testapp_account/views.py`'s bases (D15) —
without it these three tests stay red past T018 too.

## 2026-09-14 · Implementer US2 · T018

Did: `mvp/menus.py` — `get_active_section(request)` and its `_iter_leaves` helper, mirroring
django-accounts-center's `dac/menus.py:41-71` (read as reference, not imported): processes
`AccountCenterMenu`, excludes the `"overview"` entry from section consideration, returns the
selected leaf (`is_current=True`) or the leaf whose declared `extra_context["url_names"]` prefixes
the request's URL name (`is_current=False`), or `None`. Descends through grouped entries via
`visible_children` rather than dac's `_processed_children` — the public equivalent. Documented
`url_names` in the module docstring (T018's own requirement: it's the public half of section
membership) alongside a worked example.
Verified: `poetry run ruff check`/`ruff format --check mvp/menus.py` clean. `poetry run pytest
tests/test_menus.py -q` — 17 passed, no regression. Manually exercised `get_active_section` against
the fixture app's section/below-section/overview pages outside the test suite (not committed) —
returns exactly the three shapes T017 expects: `is_current=True` on the section's own page,
`is_current=False` one level below it, `None` on the overview page.
Next: T019 — `AccountPageMixin`, plus wiring it into `tests/testapp_account/views.py` (D15), is
what turns T017's three red tests green. Watch: —

## 2026-09-14 · Implementer US2 · T019

Did: `mvp/views/account.py` — `AccountPageMixin.get_breadcrumbs()`: the single unlinked area crumb
when `get_active_section` returns `None`, otherwise `[area(linked to account-center), section]`
with the section crumb linked or unlinked per `is_current`. `AccountCenterView` now composes it
(`LoginRequiredMixin, AccountPageMixin, MVPTemplateView`) ahead of `MVPTemplateView` in the MRO so
it overrides `PageMixin`'s default `get_breadcrumbs`. Docstring states the composition contract —
a contributing app supplies its own access mixin, this one supplies none (D4, FR-004). Closed out
D15: `tests/testapp_account/views.py`'s three fixture views now compose `AccountPageMixin` too.
Verified: `poetry run pytest tests/test_views/test_account.py -q` — 12 passed (T017's three
previously-red tests now green, the other 9 undisturbed). `poetry run pytest tests/test_menus.py
tests/test_views/test_account.py tests/test_components/test_account_nav.py -q` — 35 passed.
`poetry run ruff check`/`ruff format --check` clean on both changed files.
`python manage.py makemigrations --check --dry-run` — no changes detected.
Next: T020 (docs). Watch: —

## 2026-09-14 · Implementer US2 · T020

Did: `docs/account-center.md` — replaced the "Where the later sections go" placeholder with
"Adding a menu entry and a page", four worked examples (a menu entry, a page against the layout
composing `AccountPageMixin`, per-request visibility via `check`, and declaring section membership
via `extra_context["url_names"]`) plus a shortened stub for the still-unbuilt US-3 section.
Corrected the `url_names` example while writing it: the prefix match is against
`request.resolver_match.url_name`, which excludes the app's namespace, so the worked example uses
`"notifications"` rather than `"yourapp:notifications"` — verified against `mvp/menus.py`'s actual
`get_active_section` and T018's manual check, not assumed. Mirrored into
`skills/django-mvp/references/menus.md`'s `AccountCenterMenu` paragraph: `url_names`, the
unnamespaced-match caveat, and a cross-reference to the full docs example. Left `CHANGELOG.md`,
`docs/views.md` and `docs/navigation.md` untouched — none are in this story's declared file scope.
Verified: `python3 kit/forge docs-check --repo . --base origin/main` (run from the engineering
workspace) — clean, 0 findings; confirms every new public name this story added
(`AccountPageMixin`, `get_active_section`) is quoted as code somewhere under `docs/`. Read-through
of both changed pages against the branch as it stands — the `AccountPageMixin` composition example
matches `mvp/views/account.py` exactly, and the `url_names` example matches the fixture app's own
working `("grouped",)` declaration in shape.
Next: §5 — the full verify, then the completion report. Watch: —

## 2026-09-14 · Implementer US3 · T024

Did: Two card-contributing fixture apps, separate from `tests/testapp_account/`:
`tests/testapp_card_no_menu/` (only `account_center_card_template` +
`account_center_card_context`) and `tests/testapp_card_with_menu/` (the same pair, plus
`menus.py::build_entries()` pointing its entry at the existing `testapp_account:plain` page rather
than adding a view/URL of its own). Neither appends to `AccountCenterMenu` from `ready()` — same
ARC-001 reasoning as `testapp_account`. Added `card_with_menu_entries` to `tests/conftest.py`,
mirroring `testapp_account_entries`, to apply/detach the with-menu entry per test. Committed ahead
of T021 in task-ID order: the red test needs both apps importable as real `INSTALLED_APPS` entries
before it can fail for the right reason rather than an `ImportError` — same ordering
`ba0e254`/`61799d9` (US-2, T015 before T016) already established for this story.
Verified: manual `override_settings(INSTALLED_APPS=...)` probe (see D16) confirms both apps'
`account_center_card_template` is visible via `apps.get_app_configs()`. `poetry run ruff check`/
`ruff format --check` clean on all new files and `tests/conftest.py`.
Next: T021 — the red test using these fixtures. Watch: —

## 2026-09-14 · Implementer US3 · T021

Did: `tests/test_views/test_account.py::TestAccountCenterCards`, four tests against
`ACCOUNT_FIXTURE_URLCONF`: a card renders with its app's context reaching the template; two
contributing apps both get their card, in `INSTALLED_APPS` order; an app declaring no card
contributes nothing and the page still 200s; and (FR-020, from the with-menu side) a real,
resolved menu entry alongside a card disturbs neither. Asserts both `response.context
["account_center_cards"]` (the exact list, order and count) and rendered `data-testid` markers.
Verified: `poetry run pytest tests/test_views/test_account.py::TestAccountCenterCards -v` — 4
failed, each `KeyError: 'account_center_cards'` — the right reason, since `AccountCenterView`
doesn't collect anything yet. `poetry run ruff check`/`ruff format --check` clean.
Next: T022 — the view side that turns the `KeyError`s into real (if still content-incomplete)
context. Watch: —

## 2026-09-14 · Implementer US3 · T022

Did: `mvp/views/account.py` — `AccountCenterView.get_context_data` walks
`django.apps.apps.get_app_configs()`, collecting `account_center_card_template`, calling
`account_center_card_context(request)` where present and merging its return value into the page
context, then hands the collected template names to the page as `account_center_cards`. Same shape
as `dac/views.py:25-37` (read for reference only, not imported).
Verified: `poetry run pytest tests/test_views/test_account.py -q` — 13 passed, 3 failed. The 3
failures are exactly T021's content-marker assertions (`data-testid="..."` not yet in the rendered
HTML) — the context list itself is now correct, confirming this task's slice is done; T023 is what
turns the remaining 3 green. `poetry run ruff check`/`ruff format --check` clean.
Next: T023 — `<c-account.card>` and the card region loop. Watch: —

## 2026-09-14 · Implementer US3 · T023

Did: `mvp/templates/cotton/account/card.html` — `<c-account.card>`, built from `<c-card>` alone (no
raw utility class standing in for it). `mvp/templates/mvp/account/overview.html` — the card region
now loops `account_center_cards`, wrapping each collected template's `{% include %}` in
`<c-account.card>`; removed the now-stale T022/T023 forward-reference from the region's comment.
`djlint --reformat` moved `{{ slot }}` and `{% include %}` to their own lines in both files.
Verified: `poetry run pytest tests/test_views/test_account.py -q` — 16 passed (T021's four tests
now fully green, US-1's and US-2's twelve undisturbed — including
`test_signed_in_request_shows_no_cards`, whose empty-div regex still matches the djlint-reformatted
whitespace). Wider scope: `poetry run pytest tests/test_views/ tests/test_menus.py
tests/test_components/ tests/test_utils.py -q` — 1339 passed, 1 skipped (pre-existing Playwright
skip, unrelated). `poetry run djlint --check` clean on both templates. `poetry run ruff check`/
`ruff format --check` clean.
Next: T025 — the demo's own card. Watch: contributing a card to `demo`'s main `AppConfig` would
also contribute it under `tests/settings.py` (which inherits `demo/settings.py`'s
`INSTALLED_APPS` wholesale), turning `test_signed_in_request_shows_no_cards` red — see D16.

## 2026-09-14 · Implementer US3 · T025

Did: `demo/account_showcase/` — a new, small `AppConfig` (`account_center_card_template` only, no
context method) contributing a "Component Library" card linking to the demo's existing `layout`
page. Added to `demo/settings.py`'s `INSTALLED_APPS`; filtered back out in `tests/settings.py`
with a one-line list comprehension mirroring the file's existing "pin things independent of demo"
style (D16).
Verified: `DJANGO_SETTINGS_MODULE=demo.settings poetry run python -c "..."` — confirms
`demo.account_showcase` is installed and its card template is in `apps.get_app_configs()` under
`demo.settings`, and renders cleanly standalone (`render_to_string`, `{% url 'layout' %}`
resolves). `DJANGO_SETTINGS_MODULE=tests.settings poetry run python -c "..."` — confirms
`demo.account_showcase` is absent from `tests.settings.INSTALLED_APPS` while `demo` itself remains.
`poetry run pytest tests/test_views/test_account.py -q` — 16 passed, including
`test_signed_in_request_shows_no_cards`. `poetry run djlint --check`/`--reformat` and `ruff
check`/`ruff format --check` clean on all new/changed files.
Next: T026 — docs. Watch: —

## 2026-09-14 · Implementer US3 · T026

Did: `docs/account-center.md` — replaced the "Where the next section goes" placeholder with
"Contributing a card": the `AppConfig` attribute pair, the card's own template, the
independent-of-menu-entries note, and the context key-collision/prefix note. Mirrored a short
version into `skills/django-mvp/references/layout.md`, placed after the landing-page table row (the
same spot T020 used for the menu-entry/page mirror), linking back to the full docs example.
Left `CHANGELOG.md` untouched — not in this story's declared file scope.
Verified: the doc's `account_center_card_context(self, request)` signature matches
`mvp/views/account.py`'s `getattr(app_config, "account_center_card_context", None)` call shape
exactly, and both fixture apps (`tests/testapp_card_no_menu`, `tests/testapp_card_with_menu`) and
the demo's own `demo/account_showcase` already implement the identical pattern the doc describes,
proven working by T021's and T025's own test/manual runs.
Next: T027 — the closing check. Watch: —

## 2026-09-14 · Implementer US3 · T027

Did: the story's closing check.
Verified: `poetry run pytest -q` — 1870 passed, 1 skipped (pre-existing Playwright skip), 0 failed.
`poetry run mypy` — no issues, 30 source files. `poetry run deptry .` — no dependency issues, 53
files scanned. `poetry run pre-commit run --all-files` — every hook passed (trim trailing
whitespace, end-of-file, check yaml, poetry-check, ruff lint, ruff format, mypy, deptry); it also
auto-fixed an import-sort in `tests/test_components/test_form_formset.py`, a file outside this
story's scope — reverted with `git checkout --` before continuing, confirmed by a clean `git
status` afterward (Article on scope containment: tamper-check runs against the story's own diff,
not the wider tree, so this collateral edit would have been an out-of-scope finding had it landed).
Re-verified scoped: `git diff --name-only origin/main...HEAD -- '*.py' | xargs poetry run ruff
check` and `... ruff format --check` — both clean, 26 files. `git diff --name-only
origin/main...HEAD -- '*.html' | xargs poetry run djlint --check` — clean, 12 files.
`DJANGO_SETTINGS_MODULE=tests.settings poetry run python manage.py makemigrations --check
--dry-run` — no changes detected. `poetry run invoke build-stylesheet` then `git status --short
mvp/static/css/` — no diff, confirming no template in this story introduced a class the build
hadn't already seen (verified by actually rebuilding, not by inspection alone).
Documentation examples: `docs/account-center.md`'s new "Contributing a card" `YourAppConfig`
snippet run standalone against `mvp/views/account.py`'s actual collection logic (getattr +
`account_center_card_context(request)` + template render) — renders as documented. The section's
shape is also the exact pattern three real, tested implementations already use
(`tests/testapp_card_no_menu`, `tests/testapp_card_with_menu`, `demo/account_showcase`), each
covered by T021's or T025's own runs. US-1's and US-2's doc sections (menu entry, page,
`url_names`, per-request visibility) were not touched by this story and remain covered by their own
stories' full-suite runs (still green above). `python3 kit/forge docs-check --repo . --base
origin/main` (from the engineering workspace) — clean, 0 findings.
Concerns: `CHANGELOG.md`'s Unreleased entry (added earlier in this feature) describes the landing
page and `AccountCenterMenu` but not the card-contribution surface T021–T026 added. `CHANGELOG.md`
is not in this story's declared file scope, so left untouched — flagging for Forge to reconcile
before the feature's PR lands.
Next: the completion report. Watch: —
