# Decisions: FS-041

Rationale for the choices the specification makes that the intake discussion on #536 did not
settle in so many words.

## The search keeps today's matching

**Ambiguous:** whether the shipped search filter should match the way the search box does now,
or follow some other rule (all words rather than any word, whole words, no word limit).

**Chosen:** today's rule. Any word in any named field, ignoring case, each record once, the first
ten words only.

**Why:** the feature changes where search is declared, not what it finds. A project moving its
`search_fields` into a filterset should get the same results it had. The ten-word limit is a
safeguard, not a taste call: the expression grows with words times fields, and an unbounded term
lets the requester decide how deep the query gets.

## Changing anything returns the list to its first page

**Ambiguous:** whether a filter change keeps the page number.

**Chosen:** it goes back to the first page.

**Why:** the new result can have fewer pages, and a page number past the end is answered with a
404. The remove links in the refinements row already drop the page number for the same reason.

## Two clear actions, two different reaches

**Ambiguous:** once some filters live in the toolbar and some in the modal, what the modal's
clear action should clear.

**Chosen:** the modal's clear removes the modal's fields only. The refinements row's clear-all
removes the search and every filter. Neither touches the sort.

**Why:** the modal's action sits inside the modal, so a reader expects it to act on what the modal
shows. Clearing a toolbar value from inside the modal would change something they can't see from
there. The refinements row lists everything applied, so its clear-all removes everything listed.
The sort was never a refinement, and clearing filters has never reset it.

## The Filter button counts only the modal's filters

**Ambiguous:** what the count on the Filter button includes once some filters are in the toolbar.

**Chosen:** only the applied filters in the modal.

**Why:** the count tells the reader that something hidden is applied. A toolbar value is on
screen next to the button.

## A bad value is ignored, not fatal

**Ambiguous:** django-filter's own view, by default, shows an empty list when any field fails to
validate.

**Chosen:** the invalid value is ignored for its own filter, the other filters apply, and the list
is not emptied.

**Why:** addresses outlive the options they were built from: a bookmark made before a sort option
was renamed, a link to a status that was retired. Today an unknown sort value is ignored, and an
empty "nothing matches" page for a stale bookmark would look to the reader like the data had
gone. Keeping today's behaviour for the sort and extending it to every filter is the consistent
choice.

## A table page ignores the sort without an error

Sam's ruling at intake (2026-10-19). The table view today refuses a view-level ordering when the
class is defined, because the table has its own column sorting. Sam asked that a sort filter on a
table page's filterset be ignored silently, so one filterset can serve a list page and a table
page. Refusing it would make a developer keep two copies of the same filterset.

## Toolbar fields do not move into the modal on small screens

**Ambiguous:** #536 suggests the filter modal stays for narrow screens.

**Chosen:** toolbar fields stay in the toolbar at every width and wrap.

**Why:** a field hidden by a style is still submitted, so a field drawn in both places would send
its value twice. Moving it properly needs a screen-width check in the page, and ADR 0021 leaves
responsive visibility to the browser. Agreed with Sam at intake as out of scope.
