# 0024 — A stand-in page withdraws when the real application arrives, rather than competing with it

**Status:** accepted

**Date:** 2026-09-22

## Context

The package ships a sign-in and a sign-out page so that a page behind `LoginRequiredMixin` is
reachable while someone is still building. They are deliberately thin: no sign-up, no password
reset, no second factor. The moment a project installs a real account-management application,
those pages have a competitor, and both register the same two URL names at the same prefix.

The obvious reading is that mount order settles it — whichever URLconf is included first wins.
It does not, and the way it fails is silent.

Django resolves a request by walking the URL patterns and taking the **first** match. It reverses
a name by taking the **last** registration of it. Those two rules disagree whenever one name is
registered twice. Every documented way of mounting these two packages puts this URLconf first, so
in practice a request for the sign-in address is answered by the thin packaged page while every
link built with `reverse()` in shipped markup points at the other one.

The addresses are identical strings, so nothing looks wrong. The page renders, the form submits,
a session is created. What is missing is everything the project installed the account-management
app for. Nothing raises, and nothing warns.

## Decision

When `allauth.account` is in `INSTALLED_APPS`, `mvp/urls.py` does not register `account_login` or
`account_logout` at all. It is a guard around the two `path()` entries:

```python
if not app_is_installed("allauth.account"):
    urlpatterns += [
        path("login/", SignInView.as_view(), name="account_login"),
        path("logout/", SignOutView.as_view(), name="account_logout"),
    ]
```

The landing page at `account-center` is unaffected and always registered.

The guard keys on `allauth.account` rather than on any particular account-management distribution,
because allauth is what registers the competing addresses and a project may install it directly.

This generalises: anything this package ships as a stand-in for software a project will eventually
install withdraws when that software appears. It does not try to win a contest of precedence.

## Consequences

Which view answers those two addresses never depends on the order two URLconfs were mounted in.
Each name is registered exactly once in every supported combination, which is asserted directly
rather than assumed.

A project cannot keep the packaged pages alongside a real account application. That is intended:
wanting both means wanting two sign-in pages, and the one a person reaches would be decided by
something as incidental as a line's position in a list.

Testing this requires allauth to be importable, so it is a test-group dependency of this package.
It is not, and must not become, a runtime dependency.

The guard runs at import time, which means a test that changes `INSTALLED_APPS` has to reload the
URLconf modules and clear Django's resolver caches to see the effect. The fixture that does this
lives in `tests/conftest.py`.

## Alternatives considered

**Let mount order decide, and document the recommended order.** This is the failure the decision
exists to prevent. It is silent, it depends on a project reading the documentation in the right
order, and the symptom — a sign-in page that works but skips everything the account app offers —
looks like correct behaviour.

**Register the packaged names only as a fallback, checked at reverse time.** Django offers no such
hook, and building one would mean a resolver wrapper the package would then own forever.

**Namespace the packaged names so they cannot collide.** The shell's own markup reverses the bare
names, and so does every page already written against them. Namespacing would break those to
prevent a collision that this guard removes outright.
