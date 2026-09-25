# Tasks — 032 Mounted apps

**Branch**: `032-mounted-apps` · **Plan**: [plan.md](plan.md) · **Research**: [research.md](research.md) · **Spec**: [spec.md](spec.md)

Every task follows the red-green-refactor cycle of Article I. A task is done when its tests pass,
the tree is green, and the work is committed. Documentation for a public name lands in the task
that introduces it.

## Order

**US-1 → US-2 → US-3 → US-4, one at a time, in one worktree.** They share `mvp/mounted.py`, the
sidebar template and `docs/mounted-apps.md` (plan, *Story order*).

---

## US-1 — A host project mounts an app and its pages carry the app's menu (P1)

Issue: #404. Delivers FR-001–FR-011, FR-014, FR-015, FR-024, FR-026–FR-028, and US-1's parts of
FR-023 and FR-025.

### T001 — A test app to mount

**Files**: `tests/testapp_mounted/` (`__init__.py`, `apps.py`, `urls.py` with `app_name =
"testapp_mounted"`, `views.py`, `menus.py`, `mounted.py`, `templates/testapp_mounted/*.html`),
`tests/settings.py` (add the app to `INSTALLED_APPS`)

Two pages: `index` (landing, no title of its own) and `detail` (title "Detail"). Its menu,
`TestappMountedMenu`, a flex_menu `Menu` with one entry per page. `mounted.py` declares
`testapp_mounted = MountedApp(...)` once T003 exists. Until then this task is just the fixture
app and a test URLconf that includes it with plain `include()`, proving the pages render.

### T002 — Pin the no-app output before the shell changes

**Files**: `tests/test_mounted.py`

With the unchanged templates, render a demo shell page and a page with no title under the test
settings (which mount no app). Assert the exact sidebar menu (the `AppMenu` entries), the absence
of any back link, and the whitespace-normalised `<title>` text. These pass now and must keep
passing (FR-010, SC-004, US-1 scenario 8).

### T003 — `MountedApp`, `mount()` and the marked match

**Files**: `mvp/mounted.py`, `tests/test_mounted.py`, `tests/urls_mounted.py`

Implement research R1–R3: `MountedApp(name, icon, menu, urls, landing, check=None)`,
`MountedAppResolver`, `mount(route, app, main=False)`, `MountedApp.for_request(request)`. The
view wrapper carries the app and calls the original view. `check` is stored but not yet enforced
(US-4).

Tests:
- a page served through the mount resolves to the app; a host page resolves to `None`
- `resolve(...).func.view_class` is still the app's view class; `csrf_exempt` survives
- the landing reverses under two different prefixes (US-1 scenario 7): two test URLconfs
- an async view stays a coroutine function after wrapping
- a mounted app's menu entries are not in `AppMenu` (FR-003)
- mounting the app does not change `AppMenu`'s children (FR-003)

### T004 — The URL-tree registry and its refusals

**Files**: `mvp/mounted.py`, `mvp/apps.py`, `tests/test_mounted.py`, test URLconfs

Research R4. Walk the resolved URLconf for `MountedAppResolver`s, cache on the root resolver,
raise `ImproperlyConfigured` for a duplicate (naming the app) or a nested mount (naming both).
Register a `Tags.urls` system check that runs the walk and reports the message as an `Error`.

Tests:
- the same app mounted twice → the check returns one error naming the app (FR-014)
- an app mounted inside another mounted app's URLs → one error naming both (FR-015)
- a clean URLconf → no error
- switching `ROOT_URLCONF` with `override_settings` switches the registry (no stale mounts)

### T005 — `{% mounted_app %}` and the title (FR-008)

**Files**: `mvp/templatetags/mvp.py`, `mvp/templates/mvp/base.html`,
`mvp/templates/mvp/error_base.html`, `tests/test_templatetags.py`, `tests/test_mounted.py`

Research R5. The tag returns `MountedApp.for_request(request)` (and `None` with no request). The
filter joins the page title with the app's name. Error pages render no app segment.

Tests:
- `detail` page title reads `Detail | <app name> | <site name>` (US-1 scenario 4)
- `index` page title reads `<app name> | <site name>` (US-1 scenario 4)
- a host page title is unchanged (T002 still green)
- a 404 raised inside a mounted view renders a title with no app name (edge case)

### T006 — The sidebar swaps and draws the back link (FR-005, FR-007)

**Files**: `mvp/templates/cotton/app/sidebar/index.html`,
`mvp/templates/cotton/app/sidebar/back.html` (new), `tests/test_components/test_app_sidebar.py`
(or the existing sidebar test module), `tests/test_mounted.py`

Load `openclaw-skills:craft-interface-design` before writing the markup. The back link sits
under the sidebar header, above the menu, labelled `{% blocktrans %}Back to {{ site_name
}}{% endblocktrans %}` with the site name resolved the way the title does
(`mvp_config.site_name`, then `request.site.name`), linking to the sidebar's `brand_url`. In the
`icons` rail it shows an icon with the label as its accessible name. With no site name, the label
falls back to the same text the title uses and never renders "Back to" alone.

Tests:
- an app page's sidebar carries the app's menu entries and none of `AppMenu`'s (US-1 scenario 1)
- the back link's text is `Back to <site name>` and its `href` is the brand URL (scenario 2)
- a host page's sidebar carries `AppMenu` and no back link (scenario 3)
- `<c-app.sidebar menu="X">` renders menu X and no back link even on an app page (edge case)
- an app whose menu has nothing visible renders the back link alone (edge case)
- the dock is unchanged on an app page (FR-011)

### T007 — The host's entry for an app (FR-004, FR-009)

**Files**: `mvp/mounted.py`, `tests/test_mounted.py`

`MountedApp.menu_item(name=None, **extra_context)` returns a flex_menu `MenuItem` subclass whose
`view_name` is the app's landing, whose `extra_context` carries the app's name and icon, and whose
`match_url()` marks it current whenever `for_request()` returns this app.

Tests:
- an `AppMenu`-style test menu holding the entry renders the app's name, icon and landing address
  (US-1 scenario 5)
- a `MobileFooterMenu`-style entry is marked current on the app's `detail` page, not only on its
  landing (scenario 6)
- the entry is not current on a host page

### T008 — Docs, glossary, skill, changelog, demo

**Files**: `docs/mounted-apps.md` (new), `docs/index.md`, `docs/navigation.md`, `CONTEXT.md`,
`skills/django-mvp/SKILL.md`, `CHANGELOG.md`, `demo/library/` (new), `demo/settings.py`,
`demo/urls.py`, `demo/menus.py`, `tests/test_demo/…`

`docs/mounted-apps.md`: declaring, mounting, adding the entry, what changes inside an app, what is
refused, each with one worked example. `CONTEXT.md` defines **Mounted app** and **Host project**
(FR-024). The skill's routing table gains a row pointing at the page (FR-028). Changelog entry
under Unreleased. The demo mounts `demo/library/` at `library/` with an entry in `AppMenu` and the
dock (research R10). Rebuild the stylesheet if T006 used a class the committed CSS lacks
(FR-027): `invoke build-stylesheet`.

Tests:
- the demo's library page renders with the library menu and the back link
- `makemessages` would pick up the back-link string: the template uses `{% blocktrans %}` or
  `{% trans %}` (asserted by rendering under a test translation, or by the existing i18n test
  pattern, FR-026)

---

## US-2 — The Account Center is a mounted app (P2)

Issue: #405. Delivers FR-019–FR-022 and US-2's parts of FR-023, FR-025, FR-027.

### T009 — Pages an app's menu marks as current belong to it (R7)

**Files**: `mvp/mounted.py`, `tests/test_mounted.py`

When no mount claims the request, `for_request()` processes each mounted app's menu (skipping a
main app, which does not exist until US-3) and returns the first whose menu is `selected`.

Tests:
- a host page linked from the test app's menu resolves to the test app
- a host page no app's menu links to resolves to `None`

### T010 — `mvp.urls` mounts the Account Center

**Files**: `mvp/views/account.py`, `mvp/urls.py`, `tests/test_urls.py`,
`tests/test_views/test_account.py`

Declare `account_center = MountedApp(name=_("Account Center"), icon=<the icon the user menu's
Account Center row already uses>, menu=AccountCenterMenu, urls=[path("", AccountCenterView…,
name="account-center")], landing="account-center")`. `mvp.urls` mounts it at `account/`. The
sign-in and sign-out pages stay outside it.

Tests:
- `reverse("account-center")` is still `/account/` (FS-028 D2)
- `/account/` resolves to `account_center`; `/account/login/` resolves to `None`
- the landing still redirects an anonymous visitor to sign-in (US-2 scenario 6, FR-022)
- the landing title names the Account Center and the site (scenario 5)

### T011 — The layout loses its second panel (FR-020, FR-021)

**Files**: `mvp/templates/mvp/account/base.html`, `mvp/templates/mvp/account/overview.html`,
`mvp/menus.py` (docstring), `tests/test_views/test_account.py`,
`tests/test_components/test_responsive_visibility.py`, `demo/templates/tests/…`

`account/base.html` keeps extending `base.html` and keeps `account.content`, inside a container.
Remove the dropdown, the card and the breakpoint plumbing. Remove the tests that asserted the
panel (`TestAccountLayout`'s panel tests) and replace them with tests for the new contract. This
is a behaviour the spec removes, so deleting those tests is the change, not tampering; record it
in `decisions.md`.

Tests:
- the landing's sidebar carries `AccountCenterMenu` under "Back to <site name>" and not `AppMenu`
  (scenario 1)
- no `c-dropdown` or card navigation is rendered in the main content at any breakpoint setting
  (scenario 2)
- the fixture app's `plain` page, written against the layout and unchanged, renders inside the
  Account Center with its entry current in the sidebar (scenario 3)
- the fixture card apps still render their cards on the landing (scenario 4)

### T012 — Docs and changelog

**Files**: `docs/account-center.md`, `docs/navigation.md`, `docs/layout.md`,
`docs/mounted-apps.md`, `CHANGELOG.md`

Rewrite the Account Center page's description of the panel to the sidebar swap. The mounted-apps
page names the Account Center as the example. Changelog: the layout change, under Changed.
Rebuild the stylesheet if a class disappeared that the CSS carries only for the panel (FR-027).

---

## US-3 — A package runs as a site in its own right (P2)

Issue: #406. Delivers FR-016–FR-018 and US-3's parts of FR-023, FR-025.

### T013 — `main=True`

**Files**: `mvp/mounted.py`, `mvp/templates/cotton/app/sidebar/index.html`,
`tests/test_mounted.py`, `tests/urls_mounted_main.py`

Research R8. The walk records the main app, and refuses a second one naming both. The tag
distinguishes "the page's app" from "the menu to draw": a main app draws its menu with no back
link and no title segment, on its own pages and every unclaimed page. The menu rule (T009) skips
the main app.

Tests:
- a host page in a project with a main app renders the main app's menu, no back link, and the
  title unchanged (scenarios 1, 2)
- the main app's own page renders the same way
- the Account Center landing in the same project swaps to its own menu with a back link
  (scenario 3)
- the same test app mounted without `main` behaves as in US-1 (scenario 4)
- two `main=True` mounts → a check error naming the problem (scenario 5)
- `main` is a keyword of `mount()` only: `MountedApp` accepts no such argument, so an unmounted
  app cannot be named main (scenario 5, second half; research R8)

### T014 — Docs and changelog

**Files**: `docs/mounted-apps.md`, `CHANGELOG.md`

A "Running an app as a site of its own" section with the one-line example.

---

## US-4 — A mounted app is visible only to the people it applies to (P3)

Issue: #407. Delivers FR-012, FR-013 and US-4's parts of FR-023, FR-025.

### T015 — The check refuses and hides

**Files**: `mvp/mounted.py`, `tests/test_mounted.py`, `tests/testapp_mounted/…`

Research R6. The wrapper calls `app.allows(request)`: anonymous → redirect to `LOGIN_URL` with
`next`; signed in → `PermissionDenied`. `menu_item()` passes the check to the item. The menu rule
(T009) skips an app whose check fails.

Tests (staff-only check):
- the host menu holds the entry for staff and not for a regular user (scenario 1)
- anonymous request to the app's page → 302 to sign-in with `next` (scenario 2)
- regular user → 403, and the 403 page's title carries no app name (scenario 3, edge case)
- staff → 200 with the app's sidebar (scenario 4)
- an app with no check → entry and pages open as in US-1 (scenario 5)

### T016 — Docs and changelog

**Files**: `docs/mounted-apps.md`, `CHANGELOG.md`

A "Limiting who can reach an app" section with a staff-only example.
