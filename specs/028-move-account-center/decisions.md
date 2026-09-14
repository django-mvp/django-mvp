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

## D2 — An includable URLconf, un-namespaced

**Ambiguous:** the package ships no URLconf at all today, so nothing establishes how a project
would reach a packaged view.

**Chosen:** ship a URLconf the project includes at a prefix of its choosing, with the landing
page's URL name un-namespaced as `account-center`.

**Why defensible:** the shell's own user menu already reverses `account-center`, and so does every
page any project has written against django-accounts-center. Namespacing would break both for no
gain the package can name today. The prefix is the project's because the package has no basis to
choose one, and every link the area draws reverses by name rather than assuming a path.

## D3 — Mounting is the only switch

**Ambiguous:** whether the area needs a setting to disable or relocate it.

**Chosen:** neither. A project that does not include the URLconf does not have the area.

**Why defensible:** Article XII reserves settings for layout and behaviour that a project must
change without touching templates. Presence of a URL is not that: Django projects already decide
what exists by what they include. A disable setting would also have to be consulted by every
reverse in shipped markup, where a missing URL name is already the natural signal and is already
handled conditionally.

## D4 — The area gates its own page and nothing else

**Ambiguous:** whether a page an app contributes inherits an authentication requirement from the
area.

**Chosen:** the landing page requires a signed-in user. A contributed page decides for itself.

**Why defensible:** the area contributes a layout and a menu entry, and neither sits in the
request path of another app's view, so an inherited guarantee would be one the package cannot
keep. The honest mechanism already exists for the visible half: an entry carries a check and is
hidden from people it does not apply to.

## D5 — The landing page lists cards, not menu entries

**Ambiguous:** what the landing page shows when no app has contributed a card.

**Chosen:** its own heading and introduction, with an empty card region.

**Why defensible:** the menu is on the same page, so a fallback listing would draw the same links
twice, in two visual languages, and would change what the page means depending on what is
installed. Article II asks for the simplest design that satisfies the spec.

## D6 — The layout stays account-specific

**Ambiguous:** the two-column arrangement is not specific to accounts, and a general version would
serve any section of an application.

**Chosen:** build it for the account area alone.

**Why defensible:** raised at intake and deferred by the maintainer in the same exchange, together
with the general question of attaching a menu to a view class or a group of addresses. Designing
for a generalisation that has not been specified is the abstraction Article III rules out.

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

## D8 — The icon keys overlap the same way the menu name does

**Ambiguous:** the two icon keys this package adds are also defined in django-accounts-center's
pack, and django-easy-icons merges packs with last-wins precedence
(`easy_icons/utils.py::load_and_merge_packs`), so in a project running both under that package's
documented settings its glyphs win.

**Chosen:** add the keys anyway and state the overlap in the changelog beside the menu name.

**Why defensible:** both keys resolve to a valid glyph either way, so the consequence is a
different picture rather than a broken page, and the alternative is leaving the shell naming an
icon that no pack in this package defines — which is the defect US-1 exists to close.

## Design review (S3R) — dispositions

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
