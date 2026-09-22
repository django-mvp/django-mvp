# Decisions — 030 Sign-in and sign-out pages in the package

Rationale too long to carry inline in `spec.md`, plus every ambiguity resolved without
escalation. Each entry records what was unclear, what was chosen, and why the choice is
defensible on evidence already in this repository.

## D1 — The packaged pages stand down when allauth is installed, rather than being shadowed by mount order

**Ambiguous because** the obvious reading of "register the same URL names and let the
account-management package take over" is that mount order decides which view answers. It does
not, and the way it fails is silent.

**Chosen**: the packaged sign-in and sign-out entries are not registered at all when allauth's
account application is installed. Which view answers an address never depends on the order two
URLconfs were mounted in.

**Why this is defensible on this repository's own evidence.** Django resolves a request by
walking the URL patterns and taking the **first** match, and reverses a name by taking the
**last** registration of it. The two disagree whenever a name is registered twice. Both packages
are documented to mount at the same prefix, and every example of that mounting puts this
package's URLconf first:

- `mvp/urls.py` is included before `dac.urls` in django-accounts-center's `example/urls.py`.
- The same order appears in its `tests/urls.py`.
- `dac/urls.py`'s own module docstring documents that order to consumers.

With that order and duplicate names, a request for the sign-in address is answered by this
package's page while every link in shipped markup points at allauth's registration. The address
string is identical, so nothing looks wrong: the page renders, the form submits, a session is
created. What is missing is everything the project installed allauth for — sign-up, password
reset, email verification, whatever second factor is configured. Nothing raises, nothing warns,
and the check for it is a browser visit nobody makes because sign-in appears to work.

Reversing the documented mount order would make requests resolve correctly, but it makes
correctness depend on a rule with no local cue, contradicts the order three existing files
already teach, and fails the same silent way when someone gets it wrong.

Registering conditionally has none of those properties, and it is already how the other side of
this pairing behaves: `dac/urls.py` guards its own integration URLs with
`mvp.utils.app_is_installed`, a helper this package already exports and documents.

**Keyed on allauth's account application, not on django-accounts-center.** allauth is what
registers the competing addresses. django-accounts-center is one way it arrives in a project, and
a project may install allauth directly.

## D2 — The pages are not gated on `DEBUG`

**Ambiguous because** the pages exist for development, which invites a debug gate to keep them
out of production.

**Chosen**: no gate. The pages work wherever they are mounted, and the on-page notice is what
stops them being relied on.

**Why.** A gate would make a project's URL configuration differ between environments, so the
first time anyone discovers the pages are absent is after a deployment, on a staging build that
still needs to be signed in to. It also contradicts the notice: telling a reader to install
account management before production only makes sense if the pages would otherwise still be
there. The failure mode a gate prevents — someone shipping these as their real sign-in — is a
decision a person makes, and the honest place to intervene is on the page they are looking at
when they make it.

## D3 — The pages live in the Account Center's URLconf, not a second include

**Ambiguous because** a separate includable URLconf would let a project take the pages without
taking the Account Center.

**Chosen**: they are part of `mvp.urls`, which is what a project already mounts to get the
Account Center.

**Why.** The problem being solved is that a developer has to wire something up before they can
sign in. A second include is another thing to find, read about and wire up, which leaves most of
the problem in place. The combination a separate include would serve — a project that wants the
sign-in pages but not the Account Center — is not one this package has seen, and the shell's
sign-in and sign-out controls both live in the sidebar footer beside the Account Center link, so
the three already travel together.

## D4 — Signing in lands on the Account Center by default

**Ambiguous because** Django has a default for this and the feature statement did not mention it.

**Chosen**: the Account Center, unless the project has set its own destination, which wins.

**Why.** Django's default is `/accounts/profile/`, an address most projects do not have, so
leaving it in place turns a successful sign-in into a 404. The Account Center is guaranteed to
exist in any project that has mounted these pages, since they are mounted by the same URLconf.
Deferring to `LOGIN_REDIRECT_URL` when the project has set one keeps this a default rather than a
policy.

## D5 — The notice has no setting to suppress it

**Ambiguous because** a project that has deliberately chosen to keep these pages might want the
notice gone.

**Chosen**: the notice is part of the page template, with no setting.

**Why.** A setting whose only effect is to hide a warning gets set by the person the warning is
for. The package already has the right answer for a project that wants different markup, and it
is the same answer it gives for every other packaged template: ship your own at the same path.
That requires the project to own the page, which is the appropriate price for removing the
warning on it.

## D6 — Django's own auth URL names are left alone

**Ambiguous because** `c-actions.login` falls back to a URL named `login` when the
account-management name does not resolve, and `django.contrib.auth.urls` registers that name, so
a project mounting both hits the same duplicate-registration question one level down.

**Chosen**: out of scope. The packaged pages register the account-management names the shell
prefers and nothing about Django's auth URLconf changes.

**Why.** A project that mounts `django.contrib.auth.urls` has made that choice explicitly, and
the fallback continues to behave exactly as it does today, so nothing regresses. Widening this
feature to arbitrate between the package's pages and Django's auth URLconf would change behaviour
for projects that never asked for these pages. It is recorded as an edge case in `spec.md` so
that planning reads it rather than rediscovering it.
