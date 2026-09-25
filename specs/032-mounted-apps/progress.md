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
