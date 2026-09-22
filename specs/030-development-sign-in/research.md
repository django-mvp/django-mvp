# Research — 030 Sign-in and sign-out pages in the package

What was read in this repository before planning, and what each reading settles. Every finding
below is a fact about code that is on `main` today, not a proposal.

## R1 — The shell's two controls, and exactly which names they look for

`mvp/templates/cotton/actions/login.html` reverses `account_login` first and falls back to
`login`, and renders nothing when neither resolves.
`mvp/templates/cotton/user/sidebar_menu.html` reverses `account_logout`, and draws both the
log-out row and the POST form it submits only when that name resolves.

**Settles**: the names the packaged entries must register are `account_login` and
`account_logout` — allauth's names, which is also why FR-003's stand-down is the whole of the
interoperation story. Nothing in either component changes for this feature; they start drawing
because the names begin resolving.

## R2 — The sign-out control already submits a form, so a POST-only endpoint is what it needs

The user menu's log-out row is `type="submit" form="logoutForm"`, and the hidden form beside it
carries `{% csrf_token %}` and `method="post"`. Django's `LogoutView` has been POST-only since
Django 5.0 and answers a GET with 405.

**Settles**: FR-004 needs no code — it is Django's own behaviour, and the assertion is a test,
not an implementation.

## R3 — `LOGIN_REDIRECT_URL` has a global default, so "the project has not set one" is testable

`django.conf.global_settings.LOGIN_REDIRECT_URL` is `"/accounts/profile/"`. A project that has
expressed no preference has exactly that value; any other value came from the project.

**Settles**: FR-007's precedence is implemented by comparing `settings.LOGIN_REDIRECT_URL`
against the global default and falling back to `account-center` only when they are equal. The
demo sets `LOGIN_REDIRECT_URL = "/"` (`demo/settings.py:98`), so the demo exercises the
project-wins branch and the test suite exercises both.

## R4 — Django's `AuthenticationForm` already asks for the user model's own field

`AuthenticationForm.__init__` reads `UserModel.USERNAME_FIELD` and sets the first field's label
from that field's `verbose_name`, and its `invalid_login` error is a non-field error phrased
identically whether or not the account exists.

**Settles**: FR-005 and FR-006 are Django's, provided the template renders `form.username` by
its own attributes rather than hard-coding a label. The demo's current template
(`demo/templates/registration/login.html`) hard-codes `Username`, which is the one thing the
packaged version must not carry over.

## R5 — The package already has the layout an anonymous-facing page wants

`mvp/templates/mvp/entrance.html` is documented as "the page anonymous-facing views extend": a
full-screen background with one centred card, with `{% block entrance %}` available to a page
that wants a different card width. The demo's login template already extends it and overrides
that block for a narrower card.

**Settles**: the packaged sign-in page extends `mvp/entrance.html`; no new layout template and
no new component. `mvp/entrance.html` extends `mvp/base.html`, so the page is inside the shell's
document — the stylesheet, the theme script and the front-end runtime all apply.

## R6 — Where a packaged Account Center template lives, and how a project overrides it

`mvp/templates/mvp/account/overview.html` is the existing packaged page in this area, reached by
`AccountCenterView.template_name`. A project overrides any packaged template by shipping its own
at the same path, because `mvp` is an app template directory like any other.

**Settles**: the two new templates are `mvp/templates/mvp/account/login.html` and
`mvp/templates/mvp/account/logout.html`, and FR-010's override point is the ordinary one — it
needs a test, not a mechanism.

## R7 — `app_is_installed` is already the package's answer to "is that other app here"

`mvp/utils.py:63` exports `app_is_installed`, a thin wrapper over `django.apps.apps.is_installed`,
and django-accounts-center's own `dac/urls.py` guards its integration URLs with it.

**Settles**: FR-003's guard is `app_is_installed("allauth.account")` in `mvp/urls.py`. Both sides
of the pairing then use the same helper for the same purpose.

## R8 — Testing FR-003 honestly requires allauth to be importable

`override_settings(INSTALLED_APPS=[..., "allauth.account"])` calls `apps.set_installed_apps()`,
which imports the app. There is no way to assert "the packaged entries are absent when allauth is
installed" without allauth present, and `mvp/urls.py` is a module Django caches, so the
assertion also needs `importlib.reload` under the overridden setting.

**Settles**: `django-allauth` joins the **test** dependency group, not the runtime one. The
justification is Article VII's: US-2's entire claim is about what happens when allauth is
present, and D1 exists because that failure is silent. A claim about allauth that is never
executed against allauth is the failure mode the decision was written to prevent. The published
package's runtime dependency set is unchanged.

## R9 — What the demo wires today, and what depends on it

`demo/urls.py` registers `account_logout` itself with Django's `LogoutView`, mounts
`django.contrib.auth.urls` at `accounts/`, and ships `demo/templates/registration/login.html`.
The only other reference to a name from that URLconf is
`demo/templates/demo/components/link.html:8`, which reverses `login` in a component-docs example.

**Settles**: FR-014/SC-006 remove all three, and the one example link moves to `account_login`.
Nothing in `demo/` reverses `password_change`, `password_reset` or any other name that URLconf
provides, so dropping the include costs the demo nothing.

## R10 — The test suite already has the fixtures this feature's URL tests need

`tests/urls_without_logout.py` and `tests/urls_logout_only.py` are purpose-built URLconfs used by
the sidebar-menu component tests, and `tests/test_views/test_account.py` builds its own urlconf
inline rather than leaning on `demo/urls.py`.

**Settles**: the new URL-resolution tests follow the pattern that is already there.
