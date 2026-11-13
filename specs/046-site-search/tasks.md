# Tasks — 046 Search the whole site from the navbar

**Branch**: `046-site-search` · **Plan**: [plan.md](plan.md) · **Research**:
[research.md](research.md) · **Spec**: [spec.md](spec.md)

Every task follows Article I's test-first cycle. A task is done when its tests pass, the tree is
green and the work is committed. Documentation for a public name lands in the task that introduces
it, in `docs/developer/search.md`. Tests live under `tests/test_search/`, browser tests in
`tests/test_search/test_search_e2e.py`.

## Checklist

- [ ] T001 [US1] modelsearch, `Result`, `Group`, `Kind`, function kinds and the registry
- [ ] T002 [US1] The search across kinds: settings, order, limits and the query
- [ ] T003 [US1] `ModelKind`: visibility by primary key, completion fallback, defaults
- [ ] T004 [US1] The start-up checks for kinds and settings
- [ ] T005 [US2] The search's addresses, the dialog's partial and the results page
- [ ] T006 [US2] The navbar widget, field, button, dialog and result components, and their styles
- [ ] T007 [US2] The keyboard: shortcuts, highlight, Enter, one Esc, focus
- [ ] T008 [US2] The demo's kinds and the documentation pass

## Order

T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008.

---

## Phase 1 — User Story 1: A developer offers the kinds of thing their site's search finds (P1)

Delivers FR-001–FR-011, FR-023, SC-002, SC-003, SC-005, SC-006.

### Group 1

#### T001 — modelsearch, `Result`, `Group`, `Kind`, function kinds and the registry

**Files**: `pyproject.toml`, `uv.lock`, `mvp/search/__init__.py`, `mvp/search/kinds.py`,
`mvp/search/registry.py`, `tests/test_search/__init__.py`, `tests/test_search/conftest.py`, `tests/test_search/test_kinds.py`,
`tests/test_search/test_registry.py`, `docs/developer/search.md`

Add `modelsearch (>=1.3.2,<2)` to the runtime dependencies (`uv add`). `Result`, `Group` with
`more`, `Kind` with `group()`, `FunctionKind`, `register()` (a kind instance, or a function with
name, label, icon and description), a duplicate name raising `ImproperlyConfigured`,
`registered()` in registration order, all on one `SearchRegistry` instance with module-level
wrappers (Article X). Registry isolation is a shared fixture in `tests/test_search/conftest.py`,
used by every search test except the demo's. Start
`docs/developer/search.md` with registering a function kind. `deptry` green.

#### T002 — The search across kinds: settings, order, limits and the query

**Files**: `mvp/config.py`, `mvp/search/registry.py`, `mvp/search/search.py`,
`mvp/search/__init__.py`, `tests/test_search/test_search.py`, `docs/developer/search.md`,
`docs/configuration.md`

`MVP_CONFIG["search"] = {"kinds": []}`. `active()` per the plan. `search(request, query, limit)`:
groups in active order, each kind's own order kept, totals, `more`, empty and whitespace-only
query returning no groups, a query over 100 characters cut before it reaches the kinds, a kind's
own `more_url` used when it gives one, an error from a kind not caught. Spec US1 scenarios 3, 5,
6 and 10.

### Group 2

#### T003 — `ModelKind`: visibility by primary key, completion fallback, defaults

**Files**: `mvp/search/kinds.py`, `mvp/search/__init__.py`, `tests/test_search/models.py` or a
test app under `tests/testapp_search/`, `tests/settings.py`, `demo/settings.py`, `tests/factories.py`, `tests/test_search/conftest.py`,
`tests/test_search/test_model_kind.py`,
`docs/developer/search.md`

A test app with an indexed model (`SearchField`s, an `AutocompleteField` on the title, a
`FilterField` on the primary key) and a visibility rule on an unindexed field. `ModelKind` per the
plan. Tests: matching records returned with title, address and where line; a record the request's
queryset excludes neither listed nor counted (scenario 2, SC-002); a partly typed word found
through completion (scenario 9); a subclass overriding `title`, `where`, `passage` and `more_url`;
the model needs no special manager; a query holding a double quote returns the matching records
rather than raising; a model kind without `get_queryset` raises `ImproperlyConfigured`. Add
`modelsearch` to `demo/settings.py`'s `INSTALLED_APPS` (the tests inherit it) and only the test
app to `tests/settings.py`. One factory for the test model in `tests/factories.py`. Then run
`tests/test_search/test_model_kind.py` once against PostgreSQL (`DATABASE_URL`) and record the
command and result as evidence: US1 scenario 11, SC-005.

#### T004 — The start-up checks for kinds and settings

**Files**: `mvp/search/checks.py`, `mvp/apps.py`, `tests/test_search/test_checks.py`,
`docs/developer/search.md`

`mvp.E004`, `mvp.E006`, `mvp.E007`, `mvp.E008` per the plan, each a pure function over its inputs
tested directly, with a model declaring `FilterField("pk")` expected to get `mvp.E007`, registered in `MvpConfig.ready()`. Scenario 7.

---

## Phase 2 — User Story 2: A reader searches the whole site from any page (P1)

Delivers FR-012–FR-022, FR-024, FR-025, SC-001, SC-004.

### Group 3

#### T005 — The search's addresses, the dialog's partial and the results page

**Files**: `mvp/search/urls.py`, `mvp/search/views.py`, `mvp/search/checks.py`, `mvp/apps.py`,
`mvp/templates/mvp/search/panel.html`, `mvp/templates/mvp/search/hints.html`,
`mvp/templates/mvp/search/results.html`, `mvp/templates/cotton/mvp/search/result.html`,
`tests/urls_search.py`, `tests/test_search/test_views.py`, `tests/test_search/test_checks.py`,
`docs/developer/search.md`

Ported from the prototype's `search_panel.html`, `search_hints.html` and `search.html`. The
partial: hints for an empty query, groups with totals and the rest, empty groups left out, the
link to every result, the nothing-found state. The results page: every kind with its count,
narrowing and back, a narrowed kind paged at 20, an unknown kind treated as none, the
nothing-found message when every group is empty (FR-018), anonymous readers, markup in a result escaped. `mvp.E005` and `mvp.E009`. Scenarios 4, 5, 10–15 of US2,
scenario 8 of US1.

### Group 4

#### T006 — The navbar widget, field, button, dialog and result components, and their styles

**Files**: `mvp/templates/cotton/mvp/actions/search.html`,
`mvp/templates/cotton/mvp/search/field.html`, `mvp/templates/cotton/mvp/search/button.html`,
`mvp/templates/cotton/mvp/search/dialog.html`, `mvp/tailwind/base.css`,
`mvp/static/css/django-mvp.css`, `tests/test_search/test_components.py`,
`tests/test_components/test_render_all.py`,
`docs/components.md`, `docs/configuration.md`, `CONTEXT.md`

Ported from the prototype's `search_toggle.html`, `search_icon.html`, `search_dialog.html` and the
search rules in `navigation.css`, renamed `mvp-search-*`. Tests on the hooks the script and htmx
read: the dialog's id, the field's and button's `commandfor`, the input's name, `hx-get`
target, `role`, `aria-controls`, the form's action. The smoke test that renders every component renders the search components under
`tests/urls_search.py`. The narrow button uses `mvp-mobile-only`. The stylesheet rebuilt. Scenario 1 of US2,
FR-024.

#### T007 — The keyboard: shortcuts, highlight, Enter, one Esc, focus

**Files**: `assets/js/search.js`, `assets/js/index.js`, `mvp/static/js/django-mvp.js`,
`tests/test_search/test_search_e2e.py`

Ported from the search half of the prototype's `navigation.js`, with `aria-activedescendant` added
for the combobox pattern. Listeners sit on `document` and look up `#mvp-search` when each event
fires, so a boosted navigation's body swap needs no rebinding. Browser tests: Ctrl K and the navbar open the dialog with the field
focused, `/` opens it outside a text field and types inside one, arrow keys move the highlight
with focus kept in the field, Enter opens the highlighted result and otherwise the results page,
one Esc with text in the field closes and returns focus, a newer answer is the one shown.
Scenarios 2, 3, 6–9 and 16 of US2, SC-004. The bundle rebuilt.

### Group 5

#### T008 — The demo's kinds and the documentation pass

**Files**: `demo/models.py`, `demo/search.py`, `demo/apps.py`, `demo/settings.py`, `demo/urls.py`,
`tests/test_demo/test_search_demo.py`, `docs/developer/search.md`, `docs/index.md`, `README.md`,
`CHANGELOG.md`, `CONTEXT.md`

`ProductKind`, `ArticleKind` (drafts staff-only) and a function kind over the component pages,
registered in the demo's `ready()`, leaving `INSTALLED_APPS` as T003 set it, the search mounted at `search/`, `mvp.actions.search` in the
navbar. A test that the demo's search finds a product and a component page from one query
(SC-001). `docs/developer/search.md` complete and in the table of contents, the README feature list,
CONTEXT glossary entries for kind, result and group, the CHANGELOG entry with the breaking change
to `c-mvp.actions.search`.

---

## Review fixes

#### T009 [US1] — A kind counts and slices without loading every match

`Kind.group` takes the total and the slice the way Django's `Paginator` does, with `count()` when
the sequence has one. `ModelKind.find` tests `count()` before falling back to completion. The
narrowed results page searches its kind once. A test pins the query count and fails on the old
`len()`.

#### T010 [US2] — The dialog's results follow the listbox pattern

Each group in the panel is `role="group"` labelled by its heading, the list markup is
presentational, and every result and link is an option. A test reads that structure from the
rendered panel.

#### T011 [US2] — Documentation and the empty narrowed kind

The worked override in `docs/configuration.md`, the kind-class example's imports, two comments
pointing at the old page path, the description of the old navbar widget, the order the groups
follow, and the component row naming the mount it needs. A results page narrowed to a kind that
found nothing says so.
