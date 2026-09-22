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

---

Decisions from planning (S3). Same bar as the entries above: what was unclear, what was chosen,
and why the choice is defensible on evidence already in this repository.

## D7 — allauth becomes a test dependency of this package

**Ambiguous because** FR-003 is a claim about what happens when allauth is installed, and allauth
is not a dependency of this package in any group.

**Chosen**: `django-allauth` joins the **test** dependency group. The published runtime
dependency set does not change.

**Why.** `override_settings(INSTALLED_APPS=[..., "allauth.account"])` calls
`apps.set_installed_apps()`, which imports the app, so there is no way to execute FR-003's claim
without allauth present. The alternative is to assert the guard against a fabricated app list,
which tests the helper rather than the requirement and leaves the requirement itself unexecuted.
D1 exists precisely because this failure is silent — a sign-in page that renders, submits and
creates a session while everything the project installed allauth for is missing. An untested
claim about allauth is the same class of thing D1 was written to prevent.

Article VII asks for a stated justification and gets one; `deptry`'s `DEP001` ignore list gains
`allauth` beside `pytest` and `bs4`, which are there for the same reason.

## D8 — Signing out renders a page rather than redirecting

**Ambiguous because** Django's `LogoutView` can either redirect to `next_page` or render a
template, and `demo/settings.py` already sets `LOGOUT_REDIRECT_URL = "/"`.

**Chosen**: the packaged view sets `template_name` and no `next_page`, so a successful sign-out
renders `mvp/account/logout.html`.

**Why.** FR-011 requires the notice on *both* packaged pages, and a redirect leaves only one page
to put it on. The moment after signing out is also the moment a developer is most likely to be
looking at what these pages are, which is where the notice is worth its space. A project that
prefers a redirect sets `LOGOUT_REDIRECT_URL` and gets one, because Django's own view honours it
ahead of the template.

## D9 — The notice is an included partial, not a Cotton component

**Ambiguous because** this package's answer to reusable markup is normally a Cotton component,
and the notice appears on two pages.

**Chosen**: `mvp/templates/mvp/account/_development_notice.html`, included by both pages.

**Why.** Article XI makes a component this package's public API — something a project is invited
to use, compose with and override by name. The notice is none of those: it exists to be read once
by a developer and then to stop existing, because installing account management takes the pages
away. Shipping it as a component would publish an interface with no consumer and no successor.
The override point a project actually needs is the page template, which it already has.

## D10 — "The project has not chosen a destination" is decided against Django's global default

**Ambiguous because** FR-007 makes the Account Center a default that a project's own
`LOGIN_REDIRECT_URL` beats, and `LOGIN_REDIRECT_URL` always has a value.

**Chosen**: compare `settings.LOGIN_REDIRECT_URL` with
`django.conf.global_settings.LOGIN_REDIRECT_URL`, and use the Account Center only when they are
equal.

**Why.** A project that has expressed no preference has exactly the framework's default, so the
comparison is a fact rather than a guess. Importing the default from `global_settings` rather
than writing `"/accounts/profile/"` into this package keeps it a fact if Django ever changes it.

## D11 — One repair to the base, recorded because it is not this feature's work

**Ambiguous because** the conformance check was already red on `main` when this branch was cut,
and a feature branch is not where unrelated drift belongs.

**Chosen**: declare `tests/test_full_page_fill_e2e.py` under `[tool.forge.conformance]
non-mirror-paths` on this branch, and nothing else.

**Why.** That module measures computed layout in a real browser; its subject is a stylesheet and
two templates, so the Python module the mirror rule looks for can never exist. Every sibling in
that position — the other `_e2e` modules, the template and brand-asset suites — is already
declared there for the same reason. The declaration is one line and the accurate statement about
that file; leaving the check red would have meant either building on an ungated base or fixing
something larger inside a feature branch.

## D12 — The demo drops `LOGOUT_REDIRECT_URL`, and gains `LOGIN_URL`

**Ambiguous because** FR-014 says the demo must use the packaged pages, and the demo already has
settings that decide where sign-in and sign-out land.

**Chosen**: `LOGOUT_REDIRECT_URL = "/"` is removed from `demo/settings.py` and
`LOGIN_URL = "account_login"` is added. `LOGIN_REDIRECT_URL = "/"` stays.

**Why.** Django's `LogoutView` returns `resolve_url(settings.LOGOUT_REDIRECT_URL)` whenever
`next_page` is unset and that setting is truthy, and only falls through to rendering its template
when it is not. With the setting in place the demo redirects to the home page on sign-out, so the
packaged signed-out page — the one carrying the notice FR-011 requires — is never rendered
anywhere a person can look. FR-014 exists to make the demo show what the package does, and that
setting is what stops it.

`LOGIN_URL` is added for the opposite reason: without it the demo is not configured the way the
documentation tells a consumer to configure a project, and the first protected page a visitor
opens sends them to Django's global default, which this URLconf does not register.

`LOGIN_REDIRECT_URL` stays because it is the one of the three that is genuinely a project
preference, and leaving it is what demonstrates FR-007's precedence in something that can be
opened rather than only in a test.

## D13 — A `next` that points back at the sign-in page is left to Django

**Ambiguous because** `redirect_authenticated_user` plus an attacker-supplied `next` pointing at
the sign-in address makes Django's own loop detector raise `ValueError` for a signed-in visitor.

**Chosen**: inherited and left alone.

**Why.** It is `LoginView.dispatch`'s own guard, it requires a same-host URL that a person has to
be handed, and the consequence is a 500 for the person who followed it, not a security boundary
crossed. Overriding `dispatch` to catch it would be a second mechanism no requirement asks for,
against a constitution that asks for the simplest design satisfying the spec. Recorded so the
next reader knows it was seen rather than missed.

## D14 — Non-disclosure is stated against the backend the package ships for

**Ambiguous because** FR-006 requires that a failed sign-in not reveal whether an account exists,
and `AuthenticationForm.confirm_login_allowed` raises a distinct "This account is inactive"
message when a backend authenticates an inactive user.

**Chosen**: no code, and one sentence in the documentation naming the condition.

**Why.** Django's default `ModelBackend` rejects inactive users before that branch is reachable,
so under the configuration this package ships against both failure cases collapse to the same
message and FR-006 holds. A project configuring `AllowAllUsersModelBackend` has chosen the other
behaviour. A package cannot decide a consumer's authentication backend, and pretending otherwise
by overriding the form would override a decision that is properly the project's.

## D15 — T009's override test uses a scoped `TEMPLATES` `DIRS` override, not a fixture app

**Ambiguous because** FR-010 needs a test proving a project's own template at the same path wins,
and the codebase's one existing precedent for that shape (`TestAccountCenterCards`, overriding
`mvp/account/overview.html`) uses a dedicated fixture app inserted into `INSTALLED_APPS` ahead of
`mvp` via `override_settings`. `demo` already precedes `mvp` in `INSTALLED_APPS`, so a template
placed at `demo/templates/mvp/account/login.html` would shadow the packaged page permanently, for
every test in the module — including T002 through T008's own assertions against the real page,
run in the same file.

**Chosen**: `demo/templates/tests/mvp/account/login.html`, reached only through
`override_settings(TEMPLATES=...)` with `DIRS` pointed at `demo/templates/tests` for the one test
that needs it. Django's default `TEMPLATES` loader order checks `DIRS` before each app's own
`APP_DIRS` entry, so the fixture wins there without touching `INSTALLED_APPS` at all.

**Why.** A fixture app would have worked too, but costs a new `tests/testapp_*` package for a
single assertion, and reordering `INSTALLED_APPS` for one test — even scoped — reads as if
`INSTALLED_APPS` order is what this story's override point depends on, when the real, documented
mechanism (`docs/account-center.md`, research R6) is the ordinary Django app-template convention.
Verified empirically before writing the test: a throwaway probe against
`engines['django'].get_template`, and confirmed non-tautological by removing the fixture and
watching the test fail against the real packaged page's content before restoring it.

**Revisit if**: a later story needs to override more than one packaged template in the same test
module — at that point a small fixture app pays for itself and this per-test `DIRS` override stops
being the cheaper option.
