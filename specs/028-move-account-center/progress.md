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
