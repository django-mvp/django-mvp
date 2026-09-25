# Progress — 032 Mounted apps

- 2026-09-25 — Planning started on a fresh branch off main (f187b2b). Base suite green: 2093 passed, 3 skipped.
- 2026-09-25 — Design review: approve, no critical/high. Nine medium/low findings folded into tasks.md and decisions.md D9–D16.

## 2026-09-25T16:40Z · Implementer US1 · T001
- Did: added `tests/testapp_mounted/` (two pages, `TestappMountedMenu`), listed it in `tests/settings.py`, and a plain-include URLconf `tests/urls_mounted_plain.py`. `mounted.py` for the app follows with T003.
- Verified: `uv run pytest tests/test_mounted.py -q` → 2 passed.
- Next: T002.
- Watch: the fixture is test-only, so its tests pass on first run by design.

## 2026-09-25T16:50Z · Implementer US1 · T002
- Did: pinned, before any shell change, the sidebar entries (against what `AppMenu` resolves to, plus the first three literal entries), the absence of a back link and mounted entries, and the normalised `<title>` for a titled and an untitled page.
- Verified: `uv run pytest tests/test_mounted.py -q` → 8 passed.
- Next: T003.
- Watch: the sidebar pin compares against `AppMenu` rather than a literal list, so the demo entry T008 adds does not break it.

## 2026-09-25T17:05Z · Implementer US1 · T003
- Did: `mvp/mounted.py` with `MountedApp`, `MountedAppResolver` and `mount()`; the fixture app's `mounted.py`; three test URLconfs (plain prefix, another prefix, site root).
- Verified: `uv run pytest tests/test_mounted.py -q` → 30 passed. Mutation probe: replacing the `match.func` rebind with `pass` turned 4 tests red; restored, 30 passed.
- Next: T004.
- Watch: wrappers are cached per app in `MountedApp._bound_views`, keyed by the view, which makes the cache key `(app, view)`.

## 2026-09-25T17:25Z · Implementer US1 · T004
- Did: `MountedApp.mounts()` walks the resolved URLconf, caches on the root resolver, refuses a duplicate mount and a nested mount with `ImproperlyConfigured`; `check_mounted_apps` reports it as `mvp.E001` under the `urls` tag, registered from `MvpConfig.ready()`.
- Verified: `uv run pytest tests/test_mounted.py -q` → 40 passed; removing the `ready()` registration turned the registration test red; `uv run python manage.py check` clean.
- Next: T005.
- Watch: `bind()` is inlined rather than split into a leading-underscore helper, per the naming rule.

## 2026-09-25T17:50Z · Implementer US1 · T005
- Did: `{% mounted_app as shell %}` returns `.app` and `.menu` (both empty with no request); `mounted_title` filter escapes the app name; `mvp/base.html` resolves once and wraps the title in `head.title`; `mvp/error_base.html` overrides that block so error pages name no app. Fixture app gained a `missing/` page for the 404 case.
- Verified: `uv run pytest tests/test_templatetags.py tests/test_mounted.py -q` → 100 passed. A host page's `<title>` markup is unchanged byte for byte (read the raw `<title>` and compared it with what the old template produces).
- Next: T006.
- Watch: `title` is now nested inside `head.title`; error_base's default `Error` title moved into its `head.title` override, since a block name can appear once per template.

## 2026-09-25T18:20Z · Implementer US1 · T006
- Did: `<c-app.sidebar>` takes `menu` (default empty) and `mounted-app`; `mvp/base.html` passes both from `{% mounted_app %}`; new `cotton/app/sidebar/back.html` draws "Back to <site name>" above the menu. Explicit `menu` draws that menu with no back link; an app with nothing visible draws the back link alone. No committed CSS class was missing (`pb-0` present).
- Verified: `uv run pytest tests/test_mounted.py tests/test_components/test_app_sidebar.py tests/test_templatetags.py -q`; removing `:mounted-app` from base.html turned 4 tests red. Fixture menu icons changed to ones the icon set has (`home`, `list`).
- Next: T007.
- Watch: the site-name-less fallback label and the plain-list choice are in decisions.md D17 and D18.

## 2026-09-25T18:40Z · Implementer US1 · T007
- Did: `MountedApp.menu_item(name=None, **extra_context)` returns a per-app `MenuItem` subclass (the app lives on the class, which flex_menu's request copy keeps), whose `match_url()` is current on every page `for_request()` attributes to the app. The fixture's icon is now `book`, because the icon set has no `box`.
- Verified: `uv run pytest tests/test_mounted.py -q` → 60 passed; replacing the current-page test with `False` turned the current-page tests red. Tests draw through `render_menu` with the sidebar and dock renderers.
- Next: T008.
- Watch: the entry does not adapt the app's `check` into flex_menu's `check(request, **kwargs)`. Enforcing the check is US-4's, and the brief for this story says to store it only.

## 2026-09-25T19:20Z · Implementer US1 · T008
- Did: `docs/mounted-apps.md` (declaring, mounting, the host's entry, what changes inside an app, what is refused, reading the app in a template), linked from `docs/index.md` and `docs/navigation.md`; `CONTEXT.md` defines Mounted app and Host project; skill routing row; changelog Added and Changed entries; `demo/library/` mounted at `library/` with entries in `AppMenu` and the dock; `tests/test_demo/test_library.py`.
- Verified: `uv run pytest tests/test_demo/test_library.py -q` → 11 passed; `uv run invoke build-stylesheet` produced no change to the committed CSS, so every class used was already there.
- Next: full verify, then the report.
- Watch: the back-link strings are checked through Django's own `templatize`, the extractor `makemessages` uses.

## 2026-09-25T19:35Z · Implementer US1 · T008 (verify result)
- Verified: `uv run pytest -n auto --dist loadscope -q` → 2367 passed, 1 skipped, 1 failed. The failure is `tests/test_renderers.py::TestMobileDockSidebarToggle::test_dock_has_a_toggle_and_a_home_link[chromium]`, a test not written in this story. It expects exactly one link in the demo's dock, and the demo's dock now has two: Home and the library entry the story asks for.
- Left alone: changing that test is outside this story's rights. It needs a decision on whether the test selects the Home link by address or the dock entry goes.
