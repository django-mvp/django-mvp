
## 2026-10-19T11:46:13Z · Forge · PLAN

Plan written: research.md answers every planning note; plan.md, tasks.md (T001-T028, US-1..US-5 in order). Spec refined after the sketch.

## 2026-10-19T12:11:08Z · Implementer US1 · T001

**Did**: pinned daisy-cotton (>=0.2,<0.3) with uv add (0.2.0 locked); passed `icon` to the seven alerts (login error, development notice, messages, formset non-form errors, delete page's protected, permanent and related-objects alerts). The related-objects alert takes `related_objects_attrs.icon`, else its variant.
**Verified**: new tests red (13 failed) before the templates changed; then `uv run pytest -q -p no:randomly tests/test_views/test_edit.py tests/test_views/test_account.py tests/test_components/test_messages.py tests/test_components/test_form_formset.py` 283 passed. Whole suite after the upgrade: 9 failed, 2208 passed, 1 skipped; the delete-page alert-layout e2e failure is now fixed by the icons.
**Next**: T002, c-mvp.modal on c-modal.
**Watch**: tests/test_components/test_icon.py::TestIconAnswersDaisyCottonComponents asserts that a bare `<c-alert variant='success'>` draws an icon, which 0.2 removed by design; not fixable in code and not in the retirement table, reported to Forge. Error-page axe e2e tests fail on CDN access (environment); a tom-select CDN script in demo/templates/base.html (sketch) fails the third-party-script e2e test.
