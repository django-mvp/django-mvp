# 0027 — The package's URLconf is mounted at the site root, and places its own routes

**Status:** accepted

**Date:** 2026-09-24

## Context

[ADR 0019](0019-a-packaged-area-is-reached-by-including-a-urlconf.md) shipped `mvp.urls` as the
Account Center's URLconf and had a project mount it at a prefix of its own choosing, typically
`path("account/", include("mvp.urls"))`. The landing page sat at the URLconf's own root.

That worked while the Account Center was the only thing in the file. It stopped working once the
package began serving routes that belong to the whole site. The installable-app manifest and
service worker both arrived in `mvp.urls`, and so both landed under the prefix the project had
picked for the Account Center: `/account/manifest.webmanifest` and `/account/sw.js`. A service
worker controls only the pages at or below the path it is served from, so the worker needed a
`Service-Worker-Allowed` header to reach the rest of the site. Every future route the package adds
would inherit the same prefix, whether or not it has anything to do with accounts.

The prefix answered the wrong question. It was the project's choice of where the Account Center
lives, applied to everything in the file.

## Decision

A project includes `mvp.urls` once, at the site root:

```python
urlpatterns = [
    path("", include("mvp.urls")),
]
```

The URLconf chooses each route's address itself. The Account Center's pages sit under `account/`:
`/account/`, `/account/login/` and `/account/logout/`. The installable-app files sit at the root,
`/manifest.webmanifest` and `/sw.js`.

The rest of ADR 0019 stands. The URL names are not namespaced, there is no `app_name`, and
including the URLconf is still the only switch.

## Consequences

The Account Center's addresses do not move for a project that followed the old documentation and
changes its prefix from `"account/"` to `""`. A project that keeps the old prefix gets
`/account/account/`, which is a breaking change, listed in the changelog.

A project can no longer move the Account Center to another address by changing the prefix. One that
needs that routes its own path to `AccountCenterView` under the `account-center` name, ahead of
the include, which the Account Center page already documents for a customised landing page.

The worker keeps its `Service-Worker-Allowed` header, so it still controls every page when a
project mounts the URLconf somewhere other than the root.

## Alternatives considered

**Keep the prefix and ship a second URLconf for site-wide routes.** It keeps the Account Center
movable, at the cost of a second include every project has to remember, and a new file for every
route that does not fit the first. The package would be adding a moving part to preserve a freedom
nobody has used.

**A settings key naming the Account Center's prefix.** ADR 0019 already rejected a setting for what
exists at what address, because Django's URLconf answers that question. Nothing here changes the
reasoning.
