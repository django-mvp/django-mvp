# 0028 — A mounted app is mounted in the host's URLs and known by the view its mount resolved

**Status:** accepted

**Date:** 2026-09-25

## Context

A package built on django-mvp can also run inside another django-mvp project. On its own pages the
sidebar has to carry the package's menu instead of the host's. That needs two answers: where the
host says it is including the app, and how a request is later tied back to the app that served it.

## Decision

A host mounts an app with one line in its own `urls.py`:

```python
from mvp.mounted import mount

urlpatterns = [
    mount("literature/", literature),
]
```

`mount()` returns a `MountedAppResolver`, a `URLResolver` subclass. When it resolves a request,
it wraps the matched view in a thin function that carries the app and runs the app's check. That
wrapper becomes `request.resolver_match.func`, and `MountedApp.for_request()` reads the app from
it. Nothing is written to a global list when `mount()` runs. The set of mounted apps is found by
walking the resolved URLconf and cached on its root resolver. The same walk refuses an app
mounted twice, an app mounted inside another, and a second `main=True` mount, both from a system
check and on first use.

## Why

- **A setting listing apps and prefixes** puts each mount path in two places. It also moves the
  prefix, the pattern order and the namespace out of the file where a Django developer looks for
  them.
- **Comparing the path with a prefix** breaks under `i18n_patterns` and sub-path deployments.
  It can't tell apart two mounts where one prefix starts with the other, and it reads an app
  mounted at the root as owning every page.
- **Namespaces** can't identify the Account Center, whose landing page is deliberately
  un-namespaced ([ADR 0019](0019-a-packaged-area-is-reached-by-including-a-urlconf.md)).
- **Marking the `ResolverMatch` itself** is lost, because every outer resolver builds a new match
  and copies only the view across.
- **A middleware** would be a second edit for every host.

The wrapper keeps `view_class`, `csrf_exempt` and the view's name through `functools.wraps`,
so code reading those attributes off `resolve(...).func` is unaffected. Reading the registry back
from the URL tree means a changed `ROOT_URLCONF` or a per-request `urlconf` needs nothing reset.

## Revisit if

Django gives `ResolverMatch` a way to carry data from an inner resolver to the final match, or a
project needs one app mounted in more than one place.
