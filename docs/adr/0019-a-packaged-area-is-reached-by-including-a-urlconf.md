# 0019 — A packaged area is reached by including a URLconf, and its URL names are not namespaced

**Status:** accepted. How the URLconf is mounted is superseded by [ADR 0027](0027-the-package-urlconf-is-mounted-at-the-site-root.md).

**Date:** 2026-09-14

## Context

The Account Center is the first thing this package has shipped that a person can navigate to. Every
packaged view until now was wired up by the project: you imported it, you gave it a route, you
named that route. An area with its own landing page cannot work that way, because the shell's own
markup has to be able to link to it, and markup cannot link to a name a project may or may not have
chosen.

That raised two questions the package had never had to answer, and the answers set a precedent for
anything it ships next.

The first is how the route arrives. A package can export a view for the project to wire, or ship a
URLconf for the project to include. The second is whether the names in that URLconf are namespaced.
Namespacing is the ordinary advice for a reusable app, and it is good advice when a project might
mount the same app twice or collide with another package's names.

Neither default survives contact with what already exists here. The shell's user menu reverses the
bare name `account-center` today, and so does every page written against django-accounts-center,
which has used that name since it shipped. A namespace would break both, in exchange for a
collision that has never happened and a second mount that makes no sense for an area whose whole
premise is that it is *the* place a person manages their account.

There was also a third question hiding behind the first two: whether a project turns the area on
with a setting. `MVP_CONFIG` is how this package is configured, so reaching for a key there is the
reflex.

## Decision

A packaged area ships as an includable URLconf. A project mounts it at a prefix of its own
choosing:

```python
urlpatterns = [
    path("account/", include("mvp.urls")),
]
```

Its URL names are not namespaced, and `mvp/urls.py` declares no `app_name`.

Mounting is the only switch. No setting enables, disables or relocates an area. A project that does
not include the URLconf does not have the area, and nothing fails as a result: every reverse of an
area's name in shipped markup is written conditionally, so the link is simply absent.

Every link an area draws reverses by name. Nothing in the package assumes a prefix.

## Consequences

The package now has a URLconf, and a project adopting an area edits its own URLs once. That edit is
the whole installation step.

An un-namespaced name is a name the package owns globally, so each one has to be chosen as
deliberately as a settings key. There are two today, `account-center` among them.

A project that genuinely needs the area at two prefixes cannot have it, and would have to name its
own routes at its own view. Nothing suggests a project wants that.

Because presence is decided by the URLconf rather than a setting, shipped markup can never assume
an area exists. The conditional reverse is the mechanism that makes an unmounted area invisible
instead of fatal, and it stays a requirement for any future area.

## Alternatives considered

**Export the view and let the project name the route.** It is what the package already does for
every other view, and it fails the one thing this area needs: the shell cannot link to a name that
does not exist by convention.

**Namespace the URL names.** Correct in general, wrong here. It would break the shell's own markup
and every page in the ecosystem already written against the bare name, to prevent a collision
nobody has had.

**A settings key that mounts or unmounts the area.** Article XII reserves settings for layout and
behaviour a project cannot change from a template. What exists at what address is already Django's
own question, answered in the project's URLs, and a disable flag would have to be consulted by
every reverse in shipped markup — where a missing URL name is the same signal, already handled.
