# Decisions: The sidebar and user menus are built from daisy-cotton's menu

Rationale too long to inline in `spec.md`, and the ambiguities resolved while specifying.

The maintainer handed this specification over on 2026-10-05, so the reading of #438 was not put to
him as questions. Sections G1 to G5 are rulings he had already given for the whole of R29, recorded
as given. Sections D1 to D9 are readings made while specifying, each one open to his veto on the
pull request.

## Rulings given for R29

### G1. Calls to daisy-cotton's components are isolated at the call site

Many of daisy-cotton's components declare attributes with everyday names such as `text`, `icon`,
`class` and `open`. When a caller leaves one out, Cotton fills it from a page variable of the same
name. The maintainer ruled that this package handles it where it calls the component, with
Cotton's `only` attribute, and does not ask daisy-cotton to change. #433 proves that slot content
still sees the page's context under `only`. Here it becomes FR-008 and the eighth scenario of the
first story.

**ADR:** none here. The rule belongs to R29 as a whole and is recorded with #433.

### G2. No compatibility aliases, and no release from this feature

Renamed tags and attributes are breaking and are recorded in the changelog. Everything under R29
gathers on the main branch and ships as one breaking minor release, so the packages built on this
one move once. Here it becomes FR-022, FR-024 and FR-029.

**ADR:** none. Article XVI already allows a component API to change between minor versions with a
changelog entry.

### G3. A gap in daisy-cotton is raised there, not worked around here

R29 says so in its own text, and names django-mvp/daisy-cotton#120 as one of the two gaps that
shape it. Here it becomes FR-021 and the third assumption.

**ADR:** none. It is the roadmap item's own rule.

### G4. A bare component name means daisy-cotton's

Every component this package keeps moves under the `mvp.` prefix in #434, the icon excepted. This
specification writes names that way and does not restate the rule.

**ADR:** none here. #434 amends Article XI.

### G5. The prebuilt stylesheet already covers daisyUI's component classes

The package's stylesheet build scans all of daisyUI's components and utilities, so a daisyUI class
that daisy-cotton writes is present whatever it builds at render time. Plain utility classes that
daisy-cotton's templates write literally, and breakpoint-prefixed forms, are #433's to cover. For
this feature that leaves FR-026: rebuild the stylesheet if the changed templates use a class it
does not carry.

**ADR:** none. Article XV already requires the rebuild.

## Readings made while specifying

### D1. This feature moves the drawer shell, and #440 keeps the navbar's opener

**What was ambiguous:** #438 asks for the sidebar to be drawn with daisy-cotton's "menu, submenu
and drawer". #440 lists the drawer among the shell markup it composes from daisy-cotton, and its
dependency line says the drawer is shared with this work.

**Chosen:** the drawer shell moves here (FR-012 to FR-017). #440 keeps the button in the navbar
that opens the drawer.

**Why:** #438 names the drawer in the request itself. The rail's tooltips only show if the drawer's
side region lets them overflow, which daisy-cotton's drawer has an attribute for since 0.1.2, so
the rail cannot be finished without touching the drawer. #440 depends on #438, so the drawer is in
place by the time #440 starts whichever issue owns it. The other reading leaves a real chance that
each issue assumes the other did it.

**Rejected:** leaving the whole drawer to #440. This feature would then have to reach into the
drawer shell for the rail anyway, and two features would change the same template.

**ADR:** none. It settles a boundary between two issues.

### D2. The requirements do not depend on how daisy-cotton closes #120

**What was ambiguous:** django-mvp/daisy-cotton#120 proposes sending an entry's extra attributes
to its link or button. Its discussion records that the current behaviour was deliberate, and
raises a second way out: an entry whose content fills the list item, so a caller writes the link.

**Chosen:** the specification asks only that a caller can put attributes on an entry's link or
button (FR-021). Either answer satisfies it.

**Why:** which way daisy-cotton goes is its maintainer's design decision. Pinning one here would
make this specification wrong if the other is chosen.

**If daisy-cotton declines both:** the feature stops and goes back to the maintainer. Keeping a
menu entry in this package to get around it is the second copy R29 exists to remove.

**ADR:** none. Nothing is decided here that outlives the upstream decision.

### D3. Every caller of the package's menu entry moves

**What was ambiguous:** #438 names the sidebar, the rail and the user menu, then the sign-out
entry, share links and rail tooltips.

**Chosen:** every place the package calls its own menu entry moves: the sidebar renderer's
templates, the link back to the host on a mounted app's pages, the user menu, the share menu and
the theme chooser's list, plus the demo pages and documentation that show one.

**Why:** the package's entry cannot be removed while anything still calls it, and the share links
are in the issue's own text. The link back to the host and the theme chooser are the two callers
the issue does not mention. Both are menu rows that need an attribute on the link or button.

**Left out:** the dropdown each of those menus sits in, and its trigger, which are #437's.

**ADR:** none. It only settles scope.

### D4. Rail entries get an accessible name

**What was ambiguous:** #438 says the rail tooltips keep working. It says nothing about what a
screen reader announces for an entry whose label is hidden.

**Chosen:** every rail entry keeps an accessible name equal to its label (FR-009).

**Why:** today a collapsed entry hides its label with `display: none`, which removes it from the
accessible name, and the tooltip is drawn by the stylesheet, which is not a name. Only the link
back to the host carries a name of its own. Article XIII asks for components that are accessible
by default, daisy-cotton's entry documents exactly this case, and the entries are being redrawn
anyway.

**This is an addition** to what the issue asked for. It changes nothing a sighted person sees.

**ADR:** none. It applies Article XIII.

### D5. How a project declares a menu does not change, and an overridden renderer template does

**Chosen:** the Python declaration, the renderer registry and the name of the menu the sidebar
draws are untouched (FR-007). A project that overrides the sidebar renderer's templates with its
own, or writes a menu entry by hand, has to follow the changelog's table.

**Why:** R29 is about which package draws the markup. The declaration is the part of menus this
package keeps.

**The case to warn about:** a template that still passes `label`, `badge` or `tip` to
`<c-menu.item>` does not fail. The tag reaches daisy-cotton's entry, which does not know those
names, and the entry renders without its label. FR-024 puts that first in the changelog entry.

**ADR:** none. Covered by the changelog.

### D6. Hooks on the drawer are kept or listed

**Chosen:** an id or `data-` attribute on the drawer that a project's script or stylesheet could
depend on is either kept or listed in the changelog with its replacement (FR-017).

**Why:** daisy-cotton's drawer names its toggle differently from this package's drawer shell, so
some hook may have to move. Deciding which is planning work. The specification only makes sure a
moved hook is not a silent break.

**ADR:** to be decided when the work is planned, if a documented hook changes.

### D7. What the pages look like is not specified, and there is no prototype stage

**Chosen:** no scenario or requirement states an appearance. A visible difference that comes from
daisy-cotton's markup is judged when the pull request is reviewed. The feature goes straight from
specification to planning.

**Why:** this is a like-for-like swap of the markup behind components that already exist. Nothing
new is being designed, so there is nothing for a prototype to settle.

**ADR:** none.

### D8. The spec number was fixed in advance

Eight specifications under R29 were written side by side. Their numbers, 033 to 040, were assigned
before any of them was written, in the order of their issues, so this directory was created by hand
as `038-menus-from-daisy-cotton` and no script chose the number.

**ADR:** none.

### D9. The interpretation was not put to the maintainer as questions

The reading of #438 in `spec.md` was written from the issue, its seven sibling issues, R29, the
goals and the rulings above, and was treated as confirmed. The places where the issue was silent
are D1 to D7.

**ADR:** none.

## Open risks

- django-mvp/daisy-cotton#120 is open, and its last comment hands the decision back to
  daisy-cotton's maintainer. This feature cannot start before a release carries the outcome.
- daisy-cotton's drawer puts no caller attributes on its toggle. The drawer shell's toggle carries
  the binding to the layout store and the key the remembered state is stored under, and as of
  daisy-cotton 0.1.2 the drawer's checkbox takes neither. Planning has to establish whether the
  shell can attach both from outside the component. If it cannot, that is a second gap to raise on
  daisy-cotton and a second dependency.
- daisy-cotton's entry writes its text as a bare text node, and the rail's stylesheet hides a
  label by matching an element inside the link. daisy-cotton documents passing the label as markup
  for a collapsing sidebar, on the submenu's summary. Planning has to confirm the same works for an
  entry, and adjust the rail's rules to the new markup.
- daisy-cotton has no menu divider. The user menu separates sign-out from the rows above it, so
  FR-019 keeps the separation and leaves how it is drawn to planning.
- The rail needs a browser to prove. Its rules depend on the exact shape of an entry, and a
  rendered-markup test cannot show a tooltip being cut off. The existing browser tests for the
  rail and the remembered state will need extending.
- #434 and #435 are not merged yet, and their specifications were written alongside this one. If
  either changes shape at review, the first two assumptions in `spec.md` need rechecking.
- Packages built on this one call the removed tags and attributes. They move in their own
  repositories around the release, and nothing here changes them.
