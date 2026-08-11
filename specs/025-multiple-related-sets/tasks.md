# FS-025 — tasks

Test-first throughout (Article I): every `[test]` task is written and observed failing for the
right reason before its `[impl]` partner runs. Per-task test scope is one class or file; the full
suite runs once per story, at the completion report.

Story order: US1 → (US2 ‖ US3) → US4 → US5 → converge.

---

## US1 — A row set is declared as its own class (#210)

Files: `mvp/views/inline.py`, `mvp/views/init.py`, `mvp/templates/form_view.html`,
`mvp/templates/cotton/form/index.html`, `tests/test_views/test_inline.py`, `tests/factories.py`,
`tests/testapp/models.py` (fixture models only).

- **T001** `[test]` Fixture models for the whole feature: a parent with two distinct related models, plus a second relation from one related model back to the same parent (exercises R3's per-relation prefix and FR-018). Factories for each, per Article X.
- **T002** `[test]` `InlineFormSetFactory` declaring no `model` raises `ImproperlyConfigured` naming the declaration class. (FR-006, US1 s3)
- **T003** `[impl]` `InlineFormSetFactory`: attributes, the `init` that takes the parent model, request, instance and view, and the `model`-stays-the-related-model rule (R2). Raise on a missing `model`. `exclude`'s docstring carries the multi-relation warning from S3R SEC-001.
- **T004** `[test]` `get_factory_kwargs()` folds the shorthands in, and an explicit `factory_kwargs` key wins over its shorthand. `validate_max` is set exactly when `max_num` is; `absolute_max` is never present. (FR-002, FR-013, R9)
- **T005** `[impl]` `get_factory_kwargs()` and `get_form_kwargs()`.
- **T006** `[test]` `get_formset_kwargs()` carries `instance`, and on POST carries `data` and `files`. A declaration setting `prefix` puts it in; a declaration leaving it unset omits the key entirely, so Django's per-relation default applies. Mutating the returned nested `form_kwargs` does not alter the class attribute across two constructions. (FR-004, R3, R6)
- **T007** `[impl]` `get_formset_kwargs()` with both dicts copied at both levels and the `prefix` override assembled in; `get_formset_class()`; `construct_formset()` attaching `title` and `description`. The prefix wiring is what makes FR-005's error message actionable — its suggested fix is to set a prefix. (S3R SPEC-001)
- **T008** `[test]` `get_title()` defaults to the related model's plural name and an explicit `title` overrides it. (FR-011)
- **T009** `[impl]` `get_title()` / `get_description()`.
- **T010** `[test]` `get_parent_model()` resolves from `model`, from a loaded object, and from `queryset` alone. (FR-007, US1 s5)
- **T011** `[impl]` `InlinesMixin.get_inlines()` / `get_parent_model()` / `construct_inlines()` (memoised, no collision check yet) / `get_context_data()`.
- **T012** `[test]` An update page with one declaration renders the parent form and the set's rows through the packaged components, from a real request through `as_view()`. (US1 s1)
- **T013** `[test]` The standalone case still works: a plain `MVPFormView` with a `formset` in its context renders it. This is FS-024's shipped capability and `tests/test_views/test_edit.py:2091` already pins it — the task is to run it and keep it green, not to rewrite it. (S3R ARCH-001)
- **T014** `[impl]` `form_view.html` gains the `inlines` loop and **keeps** `formset` for the standalone case; both media blocks iterate the sets as well as the standalone formset, so a row widget's CSS and JS still reach the page. `cotton/form/index.html` gains an attribute for the list and keeps its existing `formset` attribute; the multipart decision stays on the component, never read from ambient context. (S3R ARCH-001, ARCH-002, SPEC-004)
- **T015** `[test]` A row form whose widget carries media renders that media on the page. (S3R SPEC-004, Article XIII)
- **T016** `[test]` A valid submission saves the parent and the set's rows and redirects; the parent is saved exactly once. (US1 s2, and the guard behind R9's second decision)
- **T017** `[impl]` `form_valid()`: validate with `all_valid`, save parent then sets inside one `transaction.atomic()`, resolve the success URL after the block, emit the flash directly. Never call `super().form_valid()`.
- **T018** `[test]` A subclass overriding `get_factory_kwargs()` reaches a parameter the shorthands do not expose. (FR-019, US1 s6)
- **T019** `[impl]` Delete `InlineFormsetMixin` and the six `inline_*` attributes. Export `InlineFormSetFactory` from `mvp.views`; leave `MVPInlineCreateView` / `MVPInlineUpdateView` named as they are. (FR-020)

## US2 — Several row sets on one page (#211)

Files: `mvp/views/inline.py`, `tests/test_views/test_inline.py`.

- **T020** `[test]` Two declarations render as two sets, each under its own heading, in the declared order. (US2 s1)
- **T021** `[impl]` Whatever T020 needs beyond US1's loop (expected: nothing — the test pins it).
- **T022** `[test]` Two sets on the same related model through different relations both build, with different prefixes, neither declaring one. (US2 s6, R3)
- **T023** `[test]` Two declarations resolving to the same prefix raise `ImproperlyConfigured` naming both and the fix, **when the page is built** rather than at render. (FR-005, US2 s5)
- **T024** `[impl]` The collision check in `construct_inlines()`.
- **T025** `[test]` A submission adding a row to each set saves both against the parent. (US2 s2)
- **T026** `[test]` A row invalid in the second set leaves nothing saved — not the first set's rows, not the parent. Asserted by counting rows and re-reading the parent, not by trusting the response. (US2 s3, FR-009)
- **T027** `[test]` Two sets carrying a same-named field each receive only their own rows' values. (US2 s4)
- **T028** `[test]` A page where one set needs multipart encodes the form for uploads, and `tests/test_components/test_form_index.py` stays green — the component is still driven by its attributes, not by context. (FR-012, US2 s7, S3R ARCH-002)
- **T029** `[test]` Two sets with different caps: a submission within one and above the other rejects only the set that is over, and a submission within a cap after removals is accepted. (FR-013, US2 s8, R9)
- **T030** `[impl]` Anything T025–T029 require.
- **T031** `[test]` A declaration naming `fk_name` builds against that relation and reaches its rows. (FR-018, US2 s9)

## US3 — Every set reports its own errors (#212)

Files: `mvp/views/inline.py`, `tests/test_views/test_inline.py`.

- **T032** `[test]` Two sets each with an invalid row: both errors present on redisplay, asserted from the response context's formsets, not from HTML alone. (US3 s1, FR-008)
- **T033** `[test]` **An invalid parent form with invalid sets shows both.** Django routes this path straight to `form_invalid`, where nothing has called `is_valid()` on the sets.
  **The assertion must not touch `formset.errors` or `formset.non_form_errors`.** Both are properties that call `full_clean()` on access (verified in `django/forms/formsets.py`), so a test written that way passes whether or not the view validated, and T034 could be deleted with it still green — the vacuous-test shape FS-024's design review caught. Read `formset._errors is not None` on the response context's sets *before* touching any error attribute, which is populated only if the view validated. (US3 s2, R11, S3R SPEC-002)
- **T034** `[impl]` Validate every set on the `form_invalid` path too; keep `all_valid` as the left operand so parent failure never suppresses set errors.
- **T035** `[test]` A refused submission redisplays every set with the submitted values while the page title and breadcrumbs show the stored record. (US3 s3, FR-010)
- **T036** `[impl]` Re-read `self.object` before re-rendering on update.

## US4 — A page that edits only the related rows (#213)

Files: `mvp/views/inline.py`, `tests/test_views/test_inline.py`.

- **T037** `[test]` An update view with `fields = []` renders no parent field and every set against the record the URL identifies. (FR-014, US4 s1)
- **T038** `[test]` `fields = None` still raises Django's own error — only an empty collection selects this page. (plan risk 4)
- **T039** `[impl]` The rows-only branch: no parent form fields, sets bound to the loaded instance.
- **T040** `[test]` A valid submission saves the rows and leaves the record's own stored values untouched, asserted on a field with `auto_now` so a no-op UPDATE is detectable. (FR-015, US4 s2, R8)
- **T041** `[impl]` Skip the parent save when the page carries no parent fields.
- **T042** `[test]` A refused submission redisplays with the set's errors and still no parent fields. (US4 s3)
- **T043** `[test]` A create view with `fields = []` raises, and an update view with neither fields nor inlines raises. (FR-016, FR-017, US4 s4/s5)
- **T044** `[impl]` Both guards, at page-build time.

## US5 — The migration is documented and demonstrated (#214)

Files: `docs/formsets.md`, `docs/views.md`, `CONTEXT.md`, `CHANGELOG.md`, `README.md`, `demo/`.

- **T045** `[test]` A search over **live guidance** finds no `inline_*` attribute described as supported configuration: `docs/` excluding `docs/adr/`, plus `README.md`, `demo/` and `mvp/`, plus the CHANGELOG's Unreleased section. ADRs, released CHANGELOG entries and `specs/` are historical records and are deliberately out of the search — rewriting them would erase decisions rather than supersede them. (FR-021, US5 s4, S3R SPEC-003)
- **T046** `[impl]` Rewrite `docs/formsets.md`: two models to a two-set page, and the rows-only page. Include the multi-relation guidance — when a related model reaches the parent by more than one relation, name `fields` explicitly, because a set declared with `exclude` renders the sibling relation as a chooser over every parent record. (S3R SEC-001)
- **T047** `[impl]` `docs/views.md:123` documents `inline_model` / `inline_fields` as supported configuration. Rewrite it against the new surface. (S3R SPEC-003 — the reference plan Risk 3 predicted)
- **T048** `[impl]` `CHANGELOG.md`: breaking, with each removed attribute mapped to its replacement. (FR-022, US5 s1)
- **T049** `[impl]` `CONTEXT.md`: the declaration term, beside the row set and related row it already defines. (US5 s6)
- **T050** `[impl]` Demo: a page carrying two sets, and a rows-only page. (US5 s3)
- **T051** `[test]` The demo pages render and submit. (US5 s3)

## Converge (driven by the pipeline, not a story)

- **T052** Simplification pass over the feature diff.
- **T053** Confirm no new stylesheet class was introduced; rebuild only if one was. (Article XV)
- **T054** Full machine gate: verify, tamper-check, ADR verdicts, story comments, humanizer pass on every public markdown the run wrote.
