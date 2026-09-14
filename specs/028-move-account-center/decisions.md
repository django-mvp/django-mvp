# Decisions — FS-028

Rationale too long for the spec, plus every ambiguity resolved without asking the maintainer.

## D1 — The menu keeps the name django-accounts-center already uses

**Ambiguous:** django-accounts-center declares a root menu named `AccountCenterMenu`. This
feature declares one too. Menus attach to a single global tree and templates look them up by
name, and the lookup returns the first match in tree order, so in a project running both, one
package's entries render and the other's silently do not. Which one wins depends on app import
order, so it is not even reliably wrong.

**Chosen:** keep the name here. The overlap is resolved by django-accounts-center dropping its own
declaration in its next release, and this package's changelog states the version relationship.

**Why defensible:** the alternative is a name chosen to dodge a collision that lasts one release
of one downstream package, and that name would then be the package's permanent public vocabulary.
CONTEXT.md's rule against two names for one concept applies to the code's own vocabulary, and the
area is called the Account Center. Article XVI permits the change pre-1.0 against a changelog
entry. The maintainer's instruction at intake was explicit that django-accounts-center's reduced
scope is decided separately and is not this feature's concern.

**ADR:** none — a transitional compatibility call that ends when django-accounts-center adopts this surface. The standing record is the changelog entry, not an architectural rule.

## D2 — An includable URLconf, un-namespaced

**Ambiguous:** the package ships no URLconf at all today, so nothing establishes how a project
would reach a packaged view.

**Chosen:** ship a URLconf the project includes at a prefix of its choosing, with the landing
page's URL name un-namespaced as `account-center`.

**Why defensible:** the shell's own user menu already reverses `account-center`, and so does every
page any project has written against django-accounts-center. Namespacing would break both for no
gain the package can name today. The prefix is the project's because the package has no basis to
choose one, and every link the area draws reverses by name rather than assuming a path.

**ADR:** docs/adr/0019-a-packaged-area-is-reached-by-including-a-urlconf.md

## D3 — Mounting is the only switch

**Ambiguous:** whether the area needs a setting to disable or relocate it.

**Chosen:** neither. A project that does not include the URLconf does not have the area.

**Why defensible:** Article XII reserves settings for layout and behaviour that a project must
change without touching templates. Presence of a URL is not that: Django projects already decide
what exists by what they include. A disable setting would also have to be consulted by every
reverse in shipped markup, where a missing URL name is already the natural signal and is already
handled conditionally.

**ADR:** docs/adr/0019-a-packaged-area-is-reached-by-including-a-urlconf.md

## D4 — The area gates its own page and nothing else

**Ambiguous:** whether a page an app contributes inherits an authentication requirement from the
area.

**Chosen:** the landing page requires a signed-in user. A contributed page decides for itself.

**Why defensible:** the area contributes a layout and a menu entry, and neither sits in the
request path of another app's view, so an inherited guarantee would be one the package cannot
keep. The honest mechanism already exists for the visible half: an entry carries a check and is
hidden from people it does not apply to.

**ADR:** docs/adr/0020-an-area-gates-its-own-pages-and-no-others.md

## D5 — The landing page lists cards, not menu entries

**Ambiguous:** what the landing page shows when no app has contributed a card.

**Chosen:** its own heading and introduction, with an empty card region.

**Why defensible:** the menu is on the same page, so a fallback listing would draw the same links
twice, in two visual languages, and would change what the page means depending on what is
installed. Article II asks for the simplest design that satisfies the spec.

**ADR:** none — how one page presents itself when nothing is contributed; nothing downstream inherits it.

## D6 — The layout stays account-specific

**Ambiguous:** the two-column arrangement is not specific to accounts, and a general version would
serve any section of an application.

**Chosen:** build it for the account area alone.

**Why defensible:** raised at intake and deferred by the maintainer in the same exchange, together
with the general question of attaching a menu to a view class or a group of addresses. Designing
for a generalisation that has not been specified is the abstraction Article III rules out.

**ADR:** none — a deferral, recorded in the specification's assumptions. An ADR would record a rule where there is only a not-yet.

## D7 — The trail rides the shell's header, not a second bar in the content

**Ambiguous:** FR-015 asks for a trail above the content naming the area and the current section.
django-accounts-center draws one inside the page, which is where the package's own trail used to
be.

**Chosen:** supply `page.breadcrumbs`, which the shell renders in its header, and draw nothing in
the layout.

**Why defensible:** `mvp/templates/cotton/app/header/navbar.html` renders the trail for every page
that sets one, and `mvp/templates/page_view.html` records the move out of the content. Drawing a
second trail would put two of them on one page in two visual languages. The cost is that the trail
comes from a view rather than a template, so a contributed page gets it by using the packaged page
mixin; a page that uses neither still renders correctly, without a trail.

**ADR:** none — applies the existing decision to draw the trail in the app header (v0.21.0) to this area. It introduces no rule of its own.

## D8 — The icon keys overlap the same way the menu name does

**Ambiguous:** the two icon keys this package adds are also defined in django-accounts-center's
pack, and django-easy-icons merges packs with last-wins precedence
(`easy_icons/utils.py::load_and_merge_packs`), so in a project running both under that package's
documented settings its glyphs win.

**Chosen:** add the keys anyway and state the overlap in the changelog beside the menu name.

**Why defensible:** both keys resolve to a valid glyph either way, so the consequence is a
different picture rather than a broken page, and the alternative is leaving the shell naming an
icon that no pack in this package defines — which is the defect US-1 exists to close.

**ADR:** none — the same transitional overlap as D1, and recorded in the same changelog entry.

## D9 — Implemented T008 before T007

**Ambiguous:** `tasks.md` lists T007 (`mvp/urls.py`) before T008 (`mvp/views/account.py`), but
`mvp/urls.py` imports `AccountCenterView` from the module T008 creates.

**Chosen:** implement T008 first, so every commit's tree stays importable, and commit each under
its own task id regardless of the swap.

**Why defensible:** the tree has to parse and lint between slices; writing
`urls.py` first would commit a module that raises `ModuleNotFoundError` on import. The task graph's
numbering is a presentation order, not a dependency graph — nothing in the brief or the tasks
themselves says T007 must land first, and the commit messages and `progress.md` still tie each
change to its task id.

**ADR:** none — the order two commits landed in, inside one story.

## D10 — The navigation panel builds its own landmark rather than delegating to the shared sidebar container

**Ambiguous:** `{% render_menu "AccountCenterMenu" renderer="sidebar" %}` is the one-line way to
render a menu through the packaged sidebar renderer, and it is what django-accounts-center's own
implementation calls (`dac/templates/dac/base.html`). But the renderer's depth-0 template,
`menus/sidebar/container.html`, hardcodes `<c-menu label="{% trans "Main Navigation" %}">` — every
menu rendered through it gets that exact label, regardless of which menu it is.

**Chosen:** `<c-account.nav>` calls `{% process_menu "AccountCenterMenu" as account_menu %}`
directly and iterates `account_menu.visible_children` with `{% render_item child renderer="sidebar" %}`,
wrapped in its own `<c-menu label="{% trans "Account navigation" %}">` — built twice, once per
breakpoint region, rather than through the shared container.

**Why defensible:** T003's acceptance criterion is a landmark with an accessible name for *this*
panel, and the app shell's own sidebar already renders a landmark labelled "Main Navigation" on
every page the Account Center appears on (`mvp/templates/cotton/app/sidebar/index.html` ->
`menus/sidebar/container.html`). Reusing the same hardcoded label would put two navigation
landmarks with an identical accessible name on one page — worse accessibility than what django-
accounts-center shipped, not parity with it. `process_menu`/`render_item` are the documented public
seam for exactly this (`skills/django-mvp/references/menus.md` "Rendering a menu elsewhere"), so
this is not new machinery, just skipping the one template that assumes it is always the app's main
sidebar.

**Revisit if:** a later story wants a shared "menu panel with landmark" component — at that point
this and the app sidebar's own wrapping become two callers of one abstraction, which is when
Article III says building it is justified.

**ADR:** none — a local workaround for a defect in the shared renderer, filed as issue #343. The fix belongs there, not in a rule about this panel.

## D11 — The icon dependency makes "red before T009" read as "red before T010" in practice

**Observed, not chosen:** `tasks.md` marks T002/T003/T004 "Red before T009", but every one of them
renders `<c-account.nav>`, whose `overview` menu entry carries `icon="overview"`. `easy_icons.icon()`
raises `IconNotFoundError` for an unregistered name whenever `EASY_ICONS_FAIL_SILENTLY` is false —
and pytest-django forces `DEBUG=False` during tests regardless of `demo/settings.py`'s own
`DEBUG=True`, so `fail_silently` (which defaults to `DEBUG`) is false in every test run. T009's
templates alone are not enough; T010's icon registration is load-bearing for the same three test
files to go green.

**Left as-is:** the task graph's ordering (T009 immediately before T010) already puts them one
commit apart, so this did not change the plan, only the point at which "confirmed green" actually
lands — recorded here so a future run does not read "red before T009" as a promise the suite goes
green the moment T009's commit lands.

**ADR:** none — an observation about a task's stated dependencies, not a decision anything inherits.

## D12 — The empty card region is a static anchor, not app-walk logic

**Ambiguous:** the plan's Design section describes `AccountCenterView.get_context_data` walking
installed app configs to collect cards, and lists `overview.html`'s card region as part of that
same description — but T022 (US-3) is the task that actually implements the walk, and this
story's prohibitions rule out building US-2/US-3 mechanisms early.

**Chosen:** `overview.html` renders `<div id="account-center-cards" class="grid gap-4 sm:grid-cols-2"></div>`
with nothing inside it — no context variable, no loop, no app-config walk. FR-019's "empty card
region" is satisfied because nothing populates it yet, not because a mechanism is proven to
produce zero results.

**Why defensible:** this is a landing-page template decision (T009's own scope) that gives T023
(US-3) a concrete, already-tested anchor to render into, without guessing at the context variable
name US-3 will actually choose or building any part of the collection logic itself. `T002`'s "no
cards" test asserts against this exact div via regex, which stays meaningful once T023 starts
rendering cards inside it — a card appearing between the tags is what turns that specific
assertion red, which is the point of the div's id existing at all.

**ADR:** none — markup detail inside one template.

## D13 — The introduction reuses `page_subtitle`, not a new field

**Ambiguous:** FR-019 and the acceptance scenarios ask for a "heading and introduction", which
`PageMixin` has no field named for.

**Chosen:** `AccountCenterView.page_subtitle` carries the introduction text, rendered through the
existing `<c-page.title :subtitle="page.subtitle" />`.

**Why defensible:** `page_subtitle` already renders as a paragraph under the heading — exactly the
shape "introduction" describes — and `PageMixin` is already the mechanism every other MVP view
uses for this. Adding an `page_introduction` field alongside it would be a second name for the same
concept, which Article III's anti-abstraction rule and CONTEXT.md's one-name-per-concept rule both
rule out before a second, differently-shaped caller exists.

**ADR:** none — reuses a field the package already has rather than adding one.

## D14 — Corrected `tests/test_utils.py`'s stale companion-package prose, touched nothing else in it

**Ambiguous:** the module docstring and the `SUPPLIED_BY_A_COMPANION_PACKAGE` comment both stated,
as fact, that `BS5_ICONS` "deliberately does not carry" `account_center` — true before T010, false
after it. A story may not modify or delete a test authored in an earlier one, and this file
predates FS-028 entirely.

**Chosen:** rewrote the two explanatory comments to describe the post-T010 reality (D8's overlap),
without touching a single assertion, the `SUPPLIED_BY_A_COMPANION_PACKAGE` frozenset's membership,
or any test method — verified by re-running the full file (323 passed, unchanged count) before and
after.

**Why defensible:** the prohibition protects test *behaviour* — what a story cannot know it is safe
to change. A comment stating something this story makes false is not behaviour; leaving it would
mean landing a change that makes existing documentation incorrect on sight, in the same PR that
had the context to fix it. Removing "account_center" from the frozenset itself was considered and
rejected: it is unowned by this task, still true in the sense that the companion package's pack
wins the glyph when both are installed (D8), and removing it changes what
`test_the_companion_package_exemption_is_still_referenced` actually verifies even though it would
still pass.

**ADR:** none — a prose correction in one test file.

## Design review — dispositions

One reviewer, three lenses, over `spec.md`, `plan.md`, `research.md`, `tasks.md`, the constitution
and targeted reads of the code the plan names. Verdict `approve`, risk medium, no critical or high
findings, so no re-plan. The security lens reported nothing: the only new surface is the landing
page, card content is trusted app-authored code rather than user input, and no dependency or
setting is added. Findings file:
`engineering-org/runs/django-mvp/028-move-account-center/design-review-findings.json` in the
engineering workspace.

- **ARC-001 (medium, verified) — fixed in the task graph.** The fixture app carrying US-2's menu
  entries was also going to carry US-3's card, which would have turned T002's "renders with no
  cards" assertion red two stories after it was written, with no task owning the repair. T024 now
  uses separate card-contributing apps, activated per test rather than installed globally, and T021
  says so.
- **ARC-002 (low, verified) — recorded as D8** and folded into T012's changelog entry.
- **SPC-001 (low, verified) — closed by a test rather than a spec change.** FR-008 claims entries
  can be reordered and removed, and no acceptance scenario exercised either. T016 now covers both,
  which is the smallest thing that makes the requirement provable under SC-006. The requirement
  itself is unchanged, so the approved spec stands.

## D15 — Fixture views compose `AccountPageMixin` at T019, not T015

**Decision:** `tests/testapp_account/views.py`'s three pages extend `MVPTemplateView` alone at
T015. T019 edits this file to add `AccountPageMixin` to their bases once that mixin exists.

**Why:** `AccountPageMixin` is T019's own deliverable. Importing it from the fixture at T015 would
leave the tree with a broken import the moment anything resolves `tests.testapp_account.urls` —
never leaving the package in a state where an import fails is a hard rule between commits, and it
outranks having the fixture "complete" a few commits early. T017's trail
tests still get a correct red: with the mixin absent, `page.breadcrumbs` is the `PageMixin` default
(`[]`), so the assertions against the expected trail fail on their own terms — an assertion
failure, not a collection error — until T019 wires the mixin in.

**Revisit if:** a future story needs the fixture's breadcrumbs before T019 lands, e.g. a reordered
task graph. Then either bring the mixin's creation forward or stub a matching
`get_breadcrumbs()` on the fixture view directly, rather than importing ahead of its own task.

**ADR:** none — fixture wiring inside one story.

## D16 — The demo's card lives in its own `demo.account_showcase` app, excluded from `tests/settings.py`

**Decision:** T025's "the demo application contributes one card" (G9) is not implemented by adding
`account_center_card_template` to `demo`'s own `DemoConfig`. It is a separate, tiny app,
`demo/account_showcase/`, added to `demo/settings.py`'s `INSTALLED_APPS` and explicitly filtered
back out in `tests/settings.py`.

**Why:** `AccountCenterView.get_context_data` (T022) walks *every* installed app config with no
scoping — that is the spec (FR-018) and the reference shape (`dac/views.py:25-37`). `demo` is
installed in `tests/settings.py` for every test in the suite (it owns the `Product`/`Category`/
`Article` models `tests/factories.py` builds on), via `from demo.settings import *`. Putting the
card attributes directly on `DemoConfig` would therefore make `demo` contribute a card to *every*
account-center test that doesn't explicitly override `INSTALLED_APPS` — including
`TestAccountCenterView.test_signed_in_request_shows_no_cards` (US-1, not mine to change, D5,
ARC-001) and every one of T021's `TestAccountCenterCards` list-equality assertions, which depend on
`account_center_cards` containing exactly the fixtures each test installs. A satellite app that
`demo/settings.py` lists and `tests/settings.py` filters out gets the demo project a real, visible
card (a human running `manage.py runserver` sees it) without `demo` itself — the app the rest of
the suite depends on — ever declaring the attribute. This mirrors T024's own reasoning for keeping
the card fixtures separate from `testapp_account` (ARC-001), applied to the demo project instead of
the test suite.

**Alternatives rejected:** (1) a settings flag (e.g. `DEMO_ACCOUNT_CARD_ENABLED`) checked in
`DemoConfig.ready()`, defaulted differently per settings module — functionally equivalent but
invents a new mechanism where the story already has one (a separate app, exactly like T024's
fixtures); (2) removing `demo` from `tests/settings.py`'s `INSTALLED_APPS` entirely — breaks every
test that uses `demo`'s models, far outside this story's scope; (3) modifying
`test_signed_in_request_shows_no_cards` — prohibited outright.

**Revisit if:** a future story wants the demo to showcase two or more cards, or wants the demo's
card content to react to demo data (a product count, say) — the satellite-app shape still holds,
it would just gain an `account_center_card_context`.

**ADR:** none — demo wiring; the demo is not part of the shipped package.

