# Implementation Plan: Search the whole site from the navbar

**Branch**: `046-site-search` · **Spec**: [spec.md](spec.md) · **Research**: [research.md](research.md)

## Summary

A new package module, `mvp.search`, holds the kinds, the registry, the search across them, its
views and its addresses. A kind is a `Kind` subclass, a function registered as one, or a
`ModelKind` built on modelsearch. The reader's side is ported from the prototype: the navbar
widget `c-mvp.actions.search` (wide field, narrow button, dialog), the dialog's results as the
reader types, the hints, the results page and one result component, with their styles in the
package stylesheet and their keyboard handling in the shipped script. modelsearch becomes a
runtime dependency.

## Technical context

- Python 3.12+, Django 5.2, 6.0 and 6.1. modelsearch `>=1.3.2,<2`.
- Tests on SQLite with FTS5 (the suite's database). PostgreSQL checked by hand (D15).
- Browser behaviour (keyboard, focus, the dialog) in the repo's existing Playwright tests, the
  `*_e2e.py` modules, which are the exception Article XIV allows: a keyboard path cannot be read
  from rendered HTML.
- Front-end assets are committed build artifacts (Article XV): `npm run build:js:prod` and
  `invoke build-stylesheet` after editing `assets/js/` or `mvp/tailwind/base.css`.

## Constitution check

| Article | Applies | How |
|---|---|---|
| I Testing | yes | test-first per task. Wording and appearance untested. Escaping, permissions, counts, links, hooks tested |
| II Simplicity | yes | one module, no new settings beyond `MVP_CONFIG["search"]["kinds"]` |
| III Anti-abstraction | yes | `Kind` has three present uses: function kinds, `ModelKind`, a package's shipped kind (django-mvp-sphinx's, approved alongside) |
| IV Integration-first | yes | the registry, `Group` and the views are written and tested before the components |
| V Security | yes | each kind scopes to the request (D3, D12). Every part of a result is escaped by the template layer. The query is length-capped |
| VI Documentation | yes | `docs/developer/search.md`, configuration, components, CONTEXT, README, CHANGELOG, in the tasks that introduce each name |
| VII Dependencies | yes | modelsearch justified in D11 and its ADR. `deptry` green |
| VIII i18n | yes | every label, hint and message translatable |
| XI Components are the public API | yes | new `c-mvp.search.*` components. `c-mvp.actions.search` changes, recorded as breaking |
| XII Configuration-driven layout | yes | the widget is placed through `layout.navbar.end` |
| XIII Rendered markup is a contract | yes | the ids and `data-` hooks the script reads are tested |
| XIV Browser tests are the exception | yes | only the keyboard and focus paths |
| XV Build artifacts | yes | both bundles rebuilt and committed in the tasks that change them |
| XVI Compatibility | yes | CHANGELOG breaking entry for `c-mvp.actions.search` |

## Design

### `mvp/search/` (Python)

- `Result(title, url, where, passage="")`: a frozen dataclass.
- `Group(kind, results, total, more_url)`: with `more` (how many are not shown).
- `Kind`: class attributes `name`, `label`, `icon`, `description` (optional). Methods
  `find(query, request)` returning a sliceable, countable sequence, `result(item)` turning one item
  into a `Result` (identity for function kinds), `more_url(query)` returning `None` by default, and
  `group(query, request, limit)` building the `Group`. Labels and descriptions are lazy
  translations.
- `FunctionKind(function, name, label, icon, description="")`: what `register()` wraps a plain
  function in. The function takes `(query, request)` and returns a list of `Result`.
- `ModelKind(Kind)`: class attribute `model`. `get_queryset(request)` returns the records the
  request may see, and has no default: a model kind that does not define it raises
  `ImproperlyConfigured` naming the kind (SEC-002). `find()` removes every `"` from the query first, because modelsearch's SQLite
  backend passes it unescaped into an FTS5 `MATCH` and raises (SEC-001), then searches
  `model._default_manager.filter(pk__in=get_queryset(request).values("pk"))` through
  `modelsearch.backends.get_search_backend()`, whole-word first, completion when that finds nothing
  and the model has completion fields (D12, D13). `title(obj)` is `str(obj)`, `url(obj)` is
  `get_absolute_url()`, `where(obj)` is the model's `verbose_name`, `passage(obj)` is `""`. A
  subclass overrides any of them. The developer's model needs no special manager.
- `SearchRegistry`: one class holding the kinds in registration order, with the methods
  `register`, `registered`, `active` and `search` below, and one module-level instance.
  `mvp.search.register` and `mvp.search.search` are thin wrappers over it (Article X). Tests swap
  the instance.
- `register(kind_or_function, *, name=None, label=None, icon=None, description="")`: registers a
  `Kind` instance under its name, or wraps a function. A second registration under one name
  replaces nothing and raises `ImproperlyConfigured`. `registered()` lists kinds in registration
  order. `active()` applies `MVP_CONFIG["search"]["kinds"]`: the named kinds in that order, or
  every registered kind when the list is empty, skipping unknown names (the check reports them).
- `search(request, query, limit)`: normalises the query (strip, whitespace-only is empty, cut to
  `QUERY_MAX = 100` characters) and returns one `Group` per active kind, in order. An empty query
  returns no groups. Nothing ranks across kinds (D4). An error raised by a kind propagates (D8).
- Checks, registered with the `urls` tag: `mvp.E004` a setting names an unregistered kind,
  `mvp.E005` the search's addresses are mounted but no kind is active, `mvp.E006` a model kind's
  model is not indexed by modelsearch, `mvp.E007` its model lacks a `FilterField` whose `get_attname(model)` equals
  `model._meta.pk.attname` (`index.FilterField("id")`, never `"pk"`, which modelsearch does not
  match), `mvp.E008` a model kind is registered and `modelsearch` is not in `INSTALLED_APPS`,
  `mvp.E009` `mvp.actions.search` is in `layout.navbar.end` and the search's addresses are not
  mounted.
- `mvp/search/urls.py`: `""` → `SearchView` (`mvp-search`), `"panel/"` → `search_panel`
  (`mvp-search-panel`). Mounted by the project with `include("mvp.search.urls")`, not part of
  `mvp.urls`, so mounting it is the opt-in.
- `SearchView(MVPTemplateView)`: `?q=` and `?kind=`. Every kind with its count for the chips. With
  no kind, the groups holding results, six each, with a link to the rest. With a known kind, that
  kind's results paged with `Paginator` at 20 a page and `c-mvp.pagination`. An unknown kind is
  treated as none. Works for anonymous requests.
- `search_panel(request)`: the dialog's partial. Four results a group, empty groups left out,
  the hints when the query is empty, the nothing-found message when every group is empty.

### Templates and components (ported, `planning-notes.md` note 3)

- `c-mvp.actions.search`: the widget. Draws `c-mvp.search.field` (wide, `mvp-desktop-only`),
  `c-mvp.search.button` (narrow, `mvp-mobile-only`) and `c-mvp.search.dialog`.
- `c-mvp.search.field`: the pill with the Ctrl K hint, `aria-keyshortcuts`, opens `#mvp-search`.
- `c-mvp.search.button`: the icon button, opens `#mvp-search`.
- `c-mvp.search.dialog`: daisy-cotton's `c-modal` at the top, id `mvp-search`, a `role="search"`
  form posting to `mvp-search`, the combobox input (`hx-get` the panel, `hx-trigger="input changed
  delay:180ms, search"`, `hx-sync="this:replace"`), and the `role="listbox"` results area holding
  the hints at first.
- `c-mvp.search.result`: one result, `compact` for the dialog (an option in the listbox) and full
  with the kind's icon on the results page.
- `mvp/search/panel.html`, `mvp/search/hints.html`, `mvp/search/results.html` (extends
  `page_view.html`, chips per kind with counts, groups, pagination).
- Styles: the prototype's search rules in `mvp/tailwind/base.css`, renamed `mvp-search-*`.
- Script: `assets/js/search.js`, `startSearch()` from `index.js`: Ctrl K and ⌘ K anywhere, `/`
  outside text fields, the ⌘ label on a Mac, arrow keys moving `aria-activedescendant` and the
  highlight while the field keeps focus, Enter on the highlight or the form's own submit, one Esc
  closing, a click on a result closing on the way, `aria-expanded` kept current after each swap.

### Demo

`ProductKind` and `ArticleKind` (drafts visible to staff only) on modelsearch, and a function kind
over the component pages in `demo/component_docs.py`. `modelsearch` in the demo's
`INSTALLED_APPS`, the search mounted at `search/`, the widget in the navbar.

## Story order and dispatch

US1 first, then US2. Four groups (`tasks.md`), each one dispatch on this worktree.

## Risks

- modelsearch's SQLite backend needs its FTS table created by its migration. The suite's test
  database runs migrations, and the demo's dev database needs `migrate` and
  `rebuild_modelsearch_index` once.
- `mvp-desktop-only` and `mvp-mobile-only` follow the sidebar breakpoint. Under `never` only the
  field is drawn, at every width, because `mvp-mobile-only` stands down there (ARCH-001).
