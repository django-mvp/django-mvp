
## 2026-10-19T11:46:13Z · Forge · PLAN

Plan written: research.md answers every planning note; plan.md, tasks.md (T001-T028, US-1..US-5 in order). Spec refined after the sketch.

## 2026-10-19T12:11:08Z · Implementer US1 · T001

**Did**: pinned daisy-cotton (>=0.2,<0.3) with uv add (0.2.0 locked); passed `icon` to the seven alerts (login error, development notice, messages, formset non-form errors, delete page's protected, permanent and related-objects alerts). The related-objects alert takes `related_objects_attrs.icon`, else its variant.
**Verified**: new tests red (13 failed) before the templates changed; then `uv run pytest -q -p no:randomly tests/test_views/test_edit.py tests/test_views/test_account.py tests/test_components/test_messages.py tests/test_components/test_form_formset.py` 283 passed. Whole suite after the upgrade: 9 failed, 2208 passed, 1 skipped; the delete-page alert-layout e2e failure is now fixed by the icons.
**Next**: T002, c-mvp.modal on c-modal.
**Watch**: tests/test_components/test_icon.py::TestIconAnswersDaisyCottonComponents asserts that a bare `<c-alert variant='success'>` draws an icon, which 0.2 removed by design; not fixable in code and not in the retirement table, reported to Forge. Error-page axe e2e tests fail on CDN access (environment); a tom-select CDN script in demo/templates/base.html (sketch) fails the third-party-script e2e test.

## 2026-10-19T12:13:05Z · Implementer US1 · T002

**Did**: rebuilt c-mvp.modal on daisy-cotton 0.2's c-modal (isolated with `only`): the title names the dialog through aria-label and is drawn once by the card; size/position/closable/class and the three slots keep their behaviour. New tests/test_components/test_modal.py. docs/components.md's row updated.
**Verified**: against the pre-sketch component (ee2d896) the no-form, type=button and name tests failed (3 failed); with the sketch only the name test failed; after the rebuild `uv run pytest -q -p no:randomly tests/test_components/test_modal.py` 15 passed. Modal callers (page info, language switcher, create action, list/table pages, modal e2e): 452 passed, 1 failed (the expected TestAppliedFilterCountOnATableView, retired at T009).
**Next**: T003, django-filter as a runtime dependency.
**Watch**: c-modal's close button sits at end-2/top-2 where the old one sat at end-3/top-3.

## 2026-10-19T12:14:28Z · Implementer US1 · T003

**Did**: moved django-filter (>=26.1,<27) into [project].dependencies, out of the dev group and DEP004; demo settings list django_filters in INSTALLED_APPS (tests inherit it); ADR 0033; README install steps and Optional integrations; ROADMAP R16; integrations.md intro; CHANGELOG breaking entry.
**Verified**: `uv run deptry .` Success, no dependency issues; pre-commit on the changed files passed.
**Next**: T004, SearchFilter.
**Watch**: integrations.md's django-filter section still describes MVPFilteredListView until T008 deletes the module.
