# Decisions: The basic components come from daisy-cotton

Rationale too long to inline in `spec.md`, and the ambiguities settled while specifying. D1 to D6
were decided by the maintainer for the whole of roadmap item R29 and are recorded here as given.
D7 onward were settled while writing this specification, from the issue, the roadmap, the
constitution and the two packages' source, without a round of questions.

## Given for all of R29

### D1. A bare tag means daisy-cotton's component

**Chosen:** every component the package keeps is under the `mvp.` prefix (FS-034), so a bare tag
for a basic component reaches daisy-cotton's. The icon is the one exception and keeps its bare
name, so that it replaces daisy-cotton's plain icon everywhere, including inside daisy-cotton's
own components.

**Consequence here:** the sixteen templates this feature removes are not renamed first. They stay
at their bare paths until this feature deletes them.

### D2. Context leakage is handled where the component is called

**Chosen:** many of daisy-cotton's components declare attributes with no default, and Cotton fills
an attribute the caller did not pass from the surrounding context. Every call the package makes to
a daisy-cotton component therefore passes Cotton's `only`. FS-033 proves that slot content still
sees the page's context under `only`.

**Rejected:** asking daisy-cotton to give every attribute an empty default. It may still happen
upstream, but this package does not wait for it.

### D3. No compatibility aliases

**Chosen:** renamed tags and attributes are a breaking change recorded in the changelog
(FR-003, FR-024). The package is pre-1.0 and Article XVI allows it.

**Rejected:** thin wrapper templates that accept the old names. They would put this package's
templates back in front of daisy-cotton's, which is the thing R29 removes, and daisy-cotton's own
components call `<c-button>` internally and would be handed the narrower wrapper.

### D4. One breaking release for the whole roadmap item

**Chosen:** all of R29 accumulates on `main` and ships as one breaking minor release. No feature
under R29 cuts a release of its own (FR-024).

### D5. daisy-cotton#119 does not block this work

**Chosen:** the package's prebuilt stylesheet already scans all of daisyUI's components and
utilities, so a daisyUI class daisy-cotton builds at render time is present. What FS-033 adds is
coverage for the plain Tailwind classes daisy-cotton's templates write. This feature only has to
make sure the classes its own call sites pass are covered (FR-020).

### D6. Form rendering, the card, the modal and the avatar are not touched here

**Chosen:** forms stay with django-crispy-forms and django-mvp-forms. The card, modal and avatar
stay this package's under their `mvp.` names and are rebuilt on daisy-cotton's in FS-036.

## Settled while specifying

### D7. The menu container is part of this feature

**Ambiguous:** #435 lists button, alert, badge, avatar group, breadcrumbs, divider, link, dock and
the mockups. It does not name the menu.

**Chosen:** `<c-menu>` moves with them (FR-001). Only the container moves. The entries stay.

**Why defensible:** #438 depends on #435 and rebuilds the sidebar on daisy-cotton's menu, submenu
and drawer. If the bare `<c-menu>` still reached this package's template, FS-034's rule that a bare
name means daisy-cotton's would have one exception left for no reason. daisy-cotton's container is
a plain list with a slot, so this package's entries render inside it unchanged. The two things it
lacks, an accessible name and the classes that made the sidebar menu fill its column, are supplied
by the callers (FR-015).

### D8. `only` binds the package's templates, not the demo or the documentation

**Ambiguous:** D2 says every call the package makes. The demo application and the documentation
also contain calls.

**Chosen:** the rule and its check cover the templates the package ships (FR-017, FR-019). Demo
pages and documented examples are written the way a project writes them. The documentation explains
`only` once (FR-022).

**Why defensible:** a packaged template renders inside pages the package has never seen, so it
cannot know which variable names are in the context. A demo page's context is the demo's own. An
`only` on every example would also teach a reader that the attribute is part of every call.

**Rejected:** leaving the rule to review. FS-036 to FS-040 add many more calls, and a missing
`only` shows up only on a page that happens to use the colliding name.

### D9. The check for a missing `only` is specified here

**Ambiguous:** FS-033 owns the proof that slot content survives `only`. Nothing said who owns the
check that a call has it.

**Chosen:** this feature adds the check (FR-019), because it is the first to add such calls. The
later features under R29 inherit it.

### D10. A demo page may pass the one class daisy-cotton documents

**Ambiguous:** Article XI and `CONTEXT.md` say demo templates never carry raw utility classes.
daisy-cotton's avatar group has no attribute for the overlap and documents a Tailwind class for it.

**Chosen:** the demo passes that class (FR-021). No other raw class is added to a demo page. The
button's former `reverse` is shown with the icon in the default slot, which needs no class.

**Why defensible:** the rule protects this package's own attribute APIs. It does not make another
library's documented usage wrong. Without the class the demo would show an avatar group that does
not overlap, which is not what the component is for.

**Follow-up:** Article XI is amended in FS-034. Its wording should limit the no-raw-classes rule
to components this package owns, or this allowance stays an exception recorded only here.

### D11. A variant daisy-cotton's alert does not accept degrades quietly

**Ambiguous:** this package's alert accepted eight variants and daisy-cotton's accepts four.
Messages take their variant from the message's level tag, which a project can extend.

**Chosen:** the content renders with no variant and nothing raises (FR-009). This is what
daisy-cotton's component already does with a value outside its list. No packaged template passes
one of the four that went, and `related_objects_attrs` defaults to `info`.

**Rejected:** mapping unknown level tags to a fallback variant in this package. That is a
translation layer of the kind D3 rules out, and drawing messages belongs to #440.

### D12. Tests of markup daisy-cotton owns are removed, not ported

**Chosen:** FR-023. daisy-cotton tests its own components. What this package still promises is
what its call sites pass and what its pages do, and those tests are rewritten.

**Why defensible:** Article XIII asks for a test of a rendered contract. The contract for the
button's markup is now daisy-cotton's. Porting those tests would pin another package's markup
here and break on its releases.

### D13. No prototype stage

**Chosen:** the feature goes straight from specification to build with no prototype for the
maintainer to look at first.

**Why defensible:** it swaps one implementation of each component for another of the same
component. No page, card or flow is designed. The differences in how a component is drawn follow
daisy-cotton and are covered by the assumption in `spec.md`.

## Open items

- **Article XI wording (FS-034).** Closed: Article XI now limits the no-raw-classes rule to this
  package's own components.
- **Packages built on this one.** Any that call the sixteen tags with former attribute names must
  move in their own repositories around the breaking release. Not this feature's work.
- **`.github/`.** Nothing in this specification needs a change there. If the stylesheet workflow
  turns out to need one during the build, it is raised as its own issue and not edited here.

## Settled while planning, 2026-10-05

### D14. The dock toggle's keyboard operation is carried as unmet

**Found:** on `main` the dock's sidebar toggle is a `<label>` with `role="button"` and
`tabindex="0"`. It takes focus, but Enter and Space do nothing: a label is not activated from the
keyboard, and no script handles the key. A browser probe confirmed it. daisy-cotton's dock item
writes neither attribute. FR-014 and acceptance scenario 10 of US-2 ask for a toggle that is
operable from the keyboard.

**Ruling given during the build (2026-10-05):** passing `role`, `tabindex` and key handlers from
`menus/dock/item.html` would be a workaround for a gap in daisy-cotton's component, and is not
done. The keyboard clause of FR-014 and scenario 10 are carried as unmet, waiting on
django-mvp/daisy-cotton#135. No test is written for it, and no skipped or expected-failure test
either. The rest of FR-014 stands: the configured class, the accessible name, and the current
item marked.

**Why:** the toggle did nothing from the keyboard before this feature, so nothing a person could
do is lost. The fix belongs in daisy-cotton's `dock.item`, where every project gets it.

**Where it is stated:** the changelog entry, as a known gap with the upstream link, and the pull
request's deviations.

**Revisit if:** daisy-cotton#135 is released. Raising the floor then closes the gap with no
change to this package's templates.

**ADR:** none — a known gap tracked on an upstream issue, not a design choice.

### D15. The isolation requirement is read as FR-017 states it

**Ambiguous:** SC-004 says a packaged page renders identically whatever attribute-named variables
its context holds. FR-017 says every call to a daisy-cotton component is isolated. This package's
own components also declare attributes with no default, and Cotton fills those from the page's
context in the same way. Isolating daisy-cotton's calls does not change that.

**Chosen:** FR-017 is the requirement built and tested. The test compares each element a
daisy-cotton component draws, with and without the colliding variables, on packaged pages. It
does not claim the whole page is identical.

**Why:** FR-001 to FR-004 keep every kept component as it is, and the specification's own
out-of-scope list gives the kept components to the later features. A whole-page comparison would
fail on components this feature may not change.

**Revisit if:** the kept components are to be isolated from the page's context too. That is a
change to their templates and to the specification, and is reported at the merge gate.

**ADR:** none — a reading of one success criterion, recorded for the reviewer.

### D16. The callers move first and are isolated second

**Chosen:** US-1 and US-2 delete the templates and move the callers without `only`. US-3 then
writes the check, sees it fail on those calls, and adds `only`.

**Why:** the check is only worth having if it has been seen to fail for the right reason
(Article I). Adding `only` while moving each caller would leave the check passing on its first
run.

**Rejected:** one pass. It is fewer edits and a weaker test.

**ADR:** none — an ordering inside one pull request.

### D17. The safelist for the divider and the menu stays

**Chosen:** the breakpoint-prefixed entries for `divider-horizontal` and `menu-horizontal` in
`mvp/tailwind/base.css` are kept. The planning notes suggested they might go.

**Why:** daisy-cotton builds those class names while a template renders, so no scan can find
them. They are needed at least as much as when this package's templates built them.

**ADR:** none — no change is made.

### D18. A menu in a dropdown is named with `aria-label` on the list

**Chosen:** the theme chooser and the share menu pass `aria-label` to `<c-menu>`, which forwards
it to the list. The sidebar menu is wrapped in a `nav` that carries the label, as FR-015 says.
The user menu had no name and gains none.

**Why:** the dropdown menus are not page navigation, so a navigation landmark around each would
add landmarks a screen-reader user has to step over. The former template put
`role="navigation"` on the list itself, which is what the planning notes call out as wrong.

**ADR:** none — follows FR-015 and the planning notes.

## Design review, 2026-10-05

One reviewer, three lenses, at `8157ca7`. Verdict: approve, risk medium, no critical or high
finding. Every finding was checked against the code before it was acted on.

### D19. What the design review changed

- **The leak test's reach (medium).** A kept component that declares an attribute with no default
  and forwards it to a daisy-cotton call still carries a page variable into that call after
  `only` is added: the log-in action's `variant`, the share dropdown's `size`. The plan's test
  now compares only elements drawn by a call the package makes directly, and names its pages.
  D15's reading of SC-004 is put to the maintainer's delegate before US-3 is built, not at the
  merge gate.
- **The dock toggle (medium).** Overtaken by the ruling in D14.
- **The demo scan's table (low).** It holds only names daisy-cotton's component does not
  declare. Changes of value or meaning are moved by hand.
- **The check's name mapping (low).** Hyphens become underscores as Cotton does it, `only` is
  read with Cotton's own tag parser, dynamic `<c-component>` calls are outside it, and the
  self-test uses a hyphenated name.
- **The reader's home (low).** One class in a helper module under `tests/`.
- **Carried, no edit here (low, speculative):** the research ran against daisy-cotton 0.1.3 and
  the package declares `>=0.1.2`. To the release that ships R29: check 0.1.2 or raise the floor.

**ADR:** none — corrections to this feature's plan.
