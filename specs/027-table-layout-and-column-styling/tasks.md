# Tasks — 027 Full-screen tables and column styling helpers

**Branch**: `027-table-layout-and-column-styling` · **Spec**: [`spec.md`](./spec.md) · **Plan**: [`plan.md`](./plan.md)

Test-first throughout, per Article I: every task that changes behaviour writes its failing test
first. `[P]` marks tasks that touch disjoint files and may run in parallel within their phase.

Per-task test scope is the class or module the task touches. The full suite runs once per story, at
the story's report.

## Phase F — Foundational (sequential, blocks every story)

- **T001** Add the column behaviour classes to `mvp/tailwind/base.css`: grow, shrink, wrap, no-wrap,
  and a fixed set of maximum widths. Name them for behaviour, not implementation. Each carries a
  comment stating what it does, in the style of the existing `.mvp-page-fill` block.
- **T002** Add `table-pin-rows` to the `@source inline(...)` safelist in `mvp/tailwind/base.css`, so
  a consumer generating their own stylesheet gets the pinned-row rules the packaged markup relies
  on. Today they survive only via the blanket daisyUI scan in `assets/tailwind.css`, which a
  consumer's own entry does not carry (research R1).
- **T003** Rebuild the stylesheet (`invoke build-stylesheet`) and commit `django-mvp.css` and its
  brotli sibling. Assert by grep that every class from T001 and T002 is present in the built file —
  including the escaped forms, and using a control class known to be absent as well as one known to
  be present.

## Phase 1 — US-1: A table that fills the application shell (P1) → #254

### Tests first

- **T004** `tests/test_table_layout.py::TestTableArea` — the component renders a scroll container
  carrying the pinned-row class, `overflow` on both axes, a stable scrollbar gutter, `tabindex="0"`,
  `role="region"` and a translatable accessible name. Red before T008.
- **T005** [P] `tests/test_table_layout.py::TestTableViewTemplate` — the page renders as a filled
  page, with an action bar carrying the page title and the view's actions, a pagination bar carrying
  the result count, and no card wrapper. Covers the unpaginated case rendering no empty bar, and the
  no-footer case rendering no footer row. Red before T009.
- **T006** [P] `tests/test_integrations.py::TestTableViewOrdering` — a table view class declaring an
  ordering fails with a message naming the table as where ordering belongs. Red before T010.
- **T007** [P] `tests/test_integrations.py::TestTableViewActions` — the default action set is search,
  filter and create, with sort absent. Red before T010.

### Then implementation

- **T008** Rewrite `mvp/templates/cotton/addons/django_table.html` as the table area: the scroll
  container with the pinned-row class, both overflow axes, the accessibility attributes from T004.
  Remove the `min_height` attribute and the inline `style` it was interpolated into, and drop the
  undefined `.table-container` class.
- **T009** Rewrite `mvp/templates/table_view.html`: `<c-page fill>`, the action bar above with the
  page title leading and the view's actions trailing, the component in the middle as the flex child
  that shrinks, the count-and-pagination bar below. No card. The middle child needs `min-h-0` or it
  will refuse to shrink and nothing will scroll (research R5).
- **T010** `mvp/integrations/django_tables/views.py`: refuse a declared ordering with the message
  from T006, and set the default action set from T007.
- **T011** Add `table-pin-rows` to the table's own classes in
  `mvp/templates/django_tables2/bootstrap5-mvp.html`, so the heading and footer rows pin against the
  container from T008.
- **T012** Demo: point the existing data-tables page at the new layout and confirm it reads as
  intended at both viewports.
- **T013** `tests/test_table_layout.py::TestExistingViewsNeedNoChange` — a table view and table class
  written against the current integration, with no attribute added and nothing subclassed, renders
  the new layout. The only permitted edit is removing a declared ordering. Covers SC-008, which
  otherwise has no evidence.

### Then the browser evidence

- **T014** `tests/test_table_layout_e2e.py` — at 1440x900 and at 390x844: the window's scroll
  position is unchanged after scrolling the rows end to end, the heading row is inside the visible
  table area at the last scroll position, a declared footer row is too, and the pagination controls
  are visible without scrolling. Both viewports fail for different reasons, so both are run
  (research R5).

## Phase 2 — US-2: Column behaviour a table author can choose (P2) → #255

### Tests first

- **T015** `tests/test_config.py::TestTableConfig` — the table section exists with the wrap default
  off, and a project's `MVP_CONFIG` override merges as the existing tests do, by deep-copying the
  defaults rather than patching settings. Red before T017.
- **T016** [P] `tests/test_table_layout.py::TestColumnBehaviourClasses` — a column declaring each
  behaviour class in its `attrs` renders cells carrying it; the project-wide wrap default applies to
  a column that declares nothing; a column-level class overrides the project default. Red before
  T018.

### Then implementation

- **T017** Add the table section to `mvp/config.py` with the wrap default, following the
  comment-per-default convention.
- **T018** Wire the wrap default into the table markup so it applies where no column class says
  otherwise, in the resolution order component attribute, then `MVP_CONFIG`, then package default.
- **T019** Document the classes in `docs/styling.md` with an example of each in a column's `attrs`,
  and update `docs/components.md` for the component's changed attributes.
- **T020** `tests/test_table_layout.py::TestDocumentedClassesMatchShipped` — every class named in the
  documentation exists in the built stylesheet and every class this feature ships is named in the
  documentation. Checked in both directions, per FR-016 and SC-005.
- **T021** Demo: a page showing each behaviour class against a column that makes its effect obvious.

## Phase 3 — US-3: Alignment nobody had to ask for (P3) → #256

### Tests first

- **T022** `tests/test_templatetags.py::TestColumnAlignment` — the tag returns leading alignment for
  a text field, trailing for integer, decimal and float fields, centre for a boolean column and for
  a column with no resolvable field that is not orderable, and nothing at all when the table's data
  has no model. Red before T024.
- **T023** [P] `tests/test_table_layout.py::TestInferredAlignment` — rendered cells and their heading
  carry the same alignment; a column carrying an explicit alignment class in its `attrs` keeps it;
  a table over non-queryset data renders unchanged. Red before T025.

### Then implementation

- **T024** Add the alignment tag to `mvp/templatetags/mvp.py`. It takes the bound column and the
  table, because `BoundColumn._table` is private and a template cannot reach it (research R2). It
  resolves the model from `table.data.model`, the field via `Accessor(column.accessor).get_field`,
  and returns no class when either is absent. It contributes an alignment class only when the
  column's computed classes carry none, because django-tables2 replaces rather than merges attr
  dicts (research R3). Carry the safelist comment the package's other class-emitting tags carry.
- **T025** Apply the tag to the heading and body cells in
  `mvp/templates/django_tables2/bootstrap5-mvp.html`, once per column rather than once per cell.
- **T026** Demo: extend the demo table with numeric, boolean and action columns so the inferred
  alignment is visible without anything declared.
- **T027** Document the inference in `docs/integrations.md`: what it decides, when it declines, and
  how an author overrides it.

## Phase 4 — Convergence

- **T028** Changelog: the table view's changed default appearance and the removal of the component's
  minimum-height attribute, both as behaviour changes under the pre-1.0 compatibility article.
- **T029** Full suite, lint, format, type and dependency checks green; coverage floors met.
- **T030** Rebuild and recommit the stylesheet if any template changed after T003, since the class
  scan reads the templates.

## Dependencies

- Phase F blocks Phases 1, 2 and 3 — the classes have to exist before markup can carry them or docs
  can name them.
- T008 blocks T009 and T011. T009 blocks T014.
- T017 blocks T018. T018 blocks T020.
- T024 blocks T025. T025 blocks T023's render assertions.
- Phase 3 depends on Phase 1 only for where the markup lives. It can be dropped entirely without
  touching Phases 1 and 2, per the spec's priority ordering.
- Phase 4 runs last and depends on everything.

## Coverage

Every requirement and success criterion, against the task that provides its evidence. Checked at the
end of planning; a blank cell here is a planning defect, not a discovery for later.

| Requirement | Tasks |
|---|---|
| FR-001 filled page | T005, T009 |
| FR-002 table owns scrolling, window does not scroll | T004, T008, T014 |
| FR-003 heading row stays visible | T011, T014 |
| FR-004 footer row stays visible | T011, T014 |
| FR-005 scrollbar spans the full height | T008, T014 |
| FR-006 action bar, title leading, actions trailing | T005, T009 |
| FR-007 action set is search, filter, create | T007, T010 |
| FR-008 pagination bar, absent when unpaginated | T005, T009 |
| FR-009 declared ordering refused | T006, T010 |
| FR-010 no card, edge to edge | T005, T009 |
| FR-011 holds at both viewports; wide tables scroll sideways | T008, T014 |
| FR-012 behaviour classes exist, max width from a fixed set | T001, T016 |
| FR-013 applied through django-tables2 attrs, no new surface | T016, T021 |
| FR-014 project-wide wrap default, off | T015, T017 |
| FR-015 resolution order | T016, T018 |
| FR-016 documented set matches shipped set | T019, T020 |
| FR-017 alignment by column kind | T022, T024 |
| FR-018 no determinable kind, no alignment | T022, T024 |
| FR-019 explicit class wins | T023, T024 |
| FR-020 heading matches its cells | T023, T025 |
| FR-021 nothing to declare, unchanged when undeterminable | T023 |
| FR-022 demo shows all three | T012, T021, T026 |
| FR-023 changelog records the behaviour change | T028 |
| FR-024 classes present in the shipped stylesheet | T003, T030 |
| FR-025 keyboard-reachable, labelled scroll region | T004, T008 |
| FR-026 component becomes the table area, min-height removed | T004, T008 |
| SC-001 window scroll unchanged, both viewports | T014 |
| SC-002 heading visible at every scroll position | T014 |
| SC-003 pagination reachable without scrolling | T014 |
| SC-004 ordering declaration fails with a message | T006 |
| SC-005 documentation and stylesheet agree both ways | T020 |
| SC-006 each column kind aligned, nothing declared | T023 |
| SC-007 no-model table renders as before | T023 |
| SC-008 existing views need no change | T013 |
