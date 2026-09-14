# Tasks — 028 An Account Center in the shell that any app can add a page to

**Branch**: `028-move-account-center` · **Spec**: [`spec.md`](./spec.md) · **Plan**: [`plan.md`](./plan.md)

Test-first throughout, per Article I: every task that changes behaviour writes its failing test
first. `[P]` marks tasks that touch disjoint files and may run in parallel within their phase.

Per-task test scope is the class or module the task touches. The full suite runs once per story, at
the story's report.

**No foundational phase.** US-1 delivers the area itself and the two later stories attach to what it
leaves behind, so there is nothing that has to exist before the first story starts.

## Phase 1 — US-1: An account area that comes with the shell (P1) → #339

### Tests first

- **T001** `tests/test_menus.py::TestAccountCenterMenu` — `AccountCenterMenu` is importable from
  `mvp.menus` and ships exactly one child, named `overview`, pointing at the `account-center` view
  name. Assert the exact child count, not that a child exists. Red before T006.
- **T002** [P] `tests/test_views/test_account.py::TestAccountCenterView` — a signed-in request
  renders the landing page inside the application shell, with the navigation panel present and no
  cards; an anonymous request is redirected to the configured sign-in location; the response
  carries the area's heading and its introduction. Red before T008.
- **T003** [P] `tests/test_components/test_account_nav.py::TestAccountNav` — the navigation panel
  renders as a `nav` landmark with a translatable accessible name, draws every visible entry, and
  renders twice: a persistent panel carrying the class derived from the shell's configured
  breakpoint, and a collapsed control below it carrying the packaged dropdown's markup.
  `tests/test_components/test_layout_config.py` is the pattern for the breakpoint assertions. Red
  before T009.
- **T004** [P] `tests/test_views/test_account.py::TestAccountLayout` — a page that extends the
  area's layout and fills its content block renders that content inside the shell with the
  navigation panel beside it, and the layout extends `base.html` rather than `mvp/base.html`, so a
  project's own base still applies. Red before T009.
- **T005** [P] `tests/test_utils.py` — `account_center` and `overview` resolve through the packaged
  icon pack. Pin both names; a test that only asserts the pack is non-empty proves nothing. Red
  before T010.

### Implementation

- **T006** `mvp/menus.py` — declare `AccountCenterMenu` beside `AppMenu` and `MobileFooterMenu`,
  carrying the single `overview` entry, and extend the module docstring to document the third menu
  and how an app adds to it.
- **T007** `mvp/urls.py` — new module, one route: the landing page at `""`, named `account-center`,
  un-namespaced (decision D2).
- **T008** `mvp/views/account.py` — `AccountCenterView` (`LoginRequiredMixin` + `MVPTemplateView`),
  its page title and introduction translatable; export it from `mvp/views/__init__.py` and add it
  to `__all__`.
- **T009** Templates — `mvp/templates/mvp/account/base.html` (the layout, extending `base.html`,
  overriding the content block with the panel beside the page's own content block),
  `mvp/templates/mvp/account/overview.html` (heading, introduction, empty card region), and
  `mvp/templates/cotton/account/nav.html` (`<c-account.nav>`, the panel, built from packaged
  components with no raw utility class standing in for one).
- **T010** [P] `mvp/utils.py` — add `account_center` and `overview` to `BS5_ICONS`.
- **T011** [P] `demo/urls.py` — mount the area in the demo application so the feature is visible
  without writing a project.
- **T012** Documentation — `docs/account-center.md` covering what the area is, mounting it, and
  where the later sections will go; add it to the documentation index; name the third menu in
  `docs/navigation.md`; restate the README's "deliberately not an authentication system" bullet
  (FR-026); add the changelog entry, including the django-accounts-center version relationship
  (FR-023).
- **T013** [P] `skills/django-mvp/references/menus.md` and `references/layout.md` — the same surface
  for the agent-facing skill (Article XVIII).
- **T014** Rebuild the stylesheet (`invoke build-stylesheet`) and commit `django-mvp.css` and its
  brotli sibling. Assert by grep that classes the new templates introduce are present in the built
  artifact, using a class known to be absent as the control.

## Phase 2 — US-2: An app adds its own page to the area (P2) → #340

### Fixture

- **T015** `tests/testapp_account/` — a minimal installed app that appends one entry and one grouped
  entry to the area's menu from its own `menus.py`, serves one page extending the area's layout and
  one page below that entry's address, and carries an entry whose check answers from the request.
  Inert fixture code, not behaviour: it exists so the story is proved from outside this package,
  which is the whole claim US-2 makes. Registered in the test settings' installed apps.

### Tests first

- **T016** `tests/test_menus.py::TestAccountMenuContribution` — the test app's entries appear
  alongside the landing-page entry, a grouped entry renders under its label, an entry whose check
  answers no for the request is absent while the same entry is present for a request it answers yes
  for, and an entry pointing at an unresolvable address is omitted without disturbing the rest.
  Assert exact entry counts. Red before T017.
- **T017** [P] `tests/test_views/test_account.py::TestAccountSectionTrail` — the trail the shell
  draws in its header names the area and the current section, the last crumb carrying no link; a
  page below a section's own address names that section and links to it; a page in the area that no
  entry points at renders with a trail naming the area alone; and the entry matching the current
  page is marked as current in the panel. Red before T018 and T019.

### Implementation

- **T018** `mvp/menus.py` — `get_active_section(request)`: process the menu for the request, return
  the entry the request is on, or the section it sits below, resolved from the URL-name prefixes an
  entry declares in its `extra_context`. Document that declaration in the module docstring, since
  it is the public half of section membership.
- **T019** `mvp/views/account.py` — `AccountPageMixin`, supplying `page.breadcrumbs` for a page in
  the area from `get_active_section`; `AccountCenterView` uses it and yields the single crumb.
  Document that a contributing app composes it with its own access rules, because the area does not
  decide them (FR-004).
- **T020** [P] `docs/account-center.md` — the sections on adding a menu entry, writing a page
  against the layout, per-request visibility, and declaring section membership for pages below a
  section, each with a worked example; mirror into the skill references.

## Phase 3 — US-3: An app contributes a card to the landing page (P3) → #341

### Tests first

- **T021** `tests/test_views/test_account.py::TestAccountCards` — a card declared by an installed
  app renders in the landing page's card region; information that app supplies for its card reaches
  the card's template; two contributing apps both get their card; an app declaring no card
  contributes nothing and the page still renders; an app that contributes a card without adding a
  menu entry is still collected. Assert the exact number of cards rendered. Red before T022.

### Implementation

- **T022** `mvp/views/account.py` — collect `account_center_card_template` from every installed app
  config, calling `account_center_card_context(request)` where it exists and merging what it
  returns; hand the collected template names to the page.
- **T023** `mvp/templates/cotton/account/card.html` (`<c-account.card>`, the shared outer shape a
  contributed card renders inside) and the card region in
  `mvp/templates/mvp/account/overview.html`.
- **T024** [P] `tests/testapp_account/` — contribute a card, and a second minimal app that
  contributes a card without a menu entry, to prove FR-020 from outside the package.
- **T025** [P] `demo/` — the demo application contributes one card, so the landing page in the demo
  shows what a populated area looks like (G9).
- **T026** [P] `docs/account-center.md` — the section on contributing a card, with a worked example
  and the note that two apps merging context under the same key collide, so keys are prefixed;
  mirror into the skill references.

## Close

- **T027** Full suite, lint, format, type-check and dependency check green; stylesheet rebuilt and
  committed if any later story introduced a class; every documented example run against the branch.
