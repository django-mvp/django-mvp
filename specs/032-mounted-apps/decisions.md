# Decisions: Mount one django-mvp app inside another

Rationale too long to inline in `spec.md`, and the ambiguities resolved while specifying.

## D1. The host mounts an app in its own URLs, not through a setting

**Chosen:** a host project mounts an app with one line in its own `urls.py` (FR-002). The package
keeps track of which apps are mounted from that line.

**Rejected:** a setting listing each app with its mount path, which the package's own URLs would
loop over. That puts the mount path in two places, the setting and the address the app answers
at. It also moves the URL prefix, the pattern order and the namespace out of the project's URLs,
which is where a Django developer looks for them.

## D2. A page belongs to an app because of the URLs it was served through

**Chosen:** the package decides which app a page belongs to from the URL patterns that matched the
request (FR-006).

**Rejected:** comparing the request's path with each app's mount prefix. A prefix comparison breaks
on language-prefixed URLs and on a project served under a sub-path. It also cannot tell two mounts
apart when one prefix begins with the other, and it misreads an app mounted at the site root as
owning every page.

## D3. The back link and the title use the site name

**Chosen:** the back link reads "Back to <site name>" and the title reads
`<page title> | <app name> | <site name>` (FR-007, FR-008). The site name is the one the page title
already ends with.

**Rejected:** the sidebar title, which is empty unless a project sets it. A back link that could
read "Back to" with nothing after it is worse than one that uses a name the page is already
guaranteed to show.

The maintainer asked for `<app name> | <site name>` on an app's pages. Keeping the page's own title
in front follows the shape every page already has, and a page with no title of its own reads
exactly as asked.

## D4. A failed visibility check refuses the way Django already does

**Chosen:** an anonymous visitor goes to the sign-in page and a signed-in person gets a forbidden
response (FR-013).

**Rejected:** answering "not found" to hide that the app exists. Django's own access mixins answer
this way, so a project gets the error pages and sign-in flow it already has, and a person who
could gain access by signing in is told how.

## D5. Mounting twice, and mounting inside a mounted app, are refused at startup

The maintainer has no current use for either, and ruled them out of scope until one appears.
Refusing them loudly, rather than tolerating them, keeps the choice of sidebar from ever depending
on the order of URL patterns. Adding support later loosens the rule without breaking any project
that works today.

## D6. A standalone deployment names a main app

**Chosen:** a project names one mounted app as its main app, and that app's menu is the sidebar on
every page outside other mounted apps (FR-016, FR-017).

**Why this is needed:** the motivating packages are each deployable on their own, and a package
that wrote its entries into the host's menu when imported would leak them into every project that
mounts it. The package therefore never touches the host's menu (FR-003), and a standalone project
needs a way to say "this app's menu is my menu". Mounting the app at the site root does not say
that, because the project's other pages, and pages of apps like the Account Center, are not the
app's pages.

## D7. The Account Center loses its second navigation panel

The maintainer wants the Account Center to behave as a mounted app and has never liked the panel
beside its pages. Once the sidebar carries the Account Center menu, a second copy beside the
content would draw the same links twice. The layout's content block keeps its name, so a page an
app has written against the layout renders unchanged (FR-021). The package is pre-1.0, so
Article XVI allows the change to the layout with a changelog entry (FR-025).

## D8. The Account Center carries no visibility check

FS-028 decided that the Account Center gates its own landing page and nothing else, and that a page
another app contributes answers access for itself. A check on the whole app would gate those pages
too, which would change behaviour an app has already been written against. The landing page keeps
its own requirement for a signed-in person (FR-022).
