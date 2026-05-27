# Vendored AdminLTE SCSS Sources

This directory contains AdminLTE 4 SCSS sources copied from the npm package.

## Ownership

These files are **vendored** — they are owned by the upstream AdminLTE project,
not by this repository. Do **not** edit files under `scss/` directly. Instead,
place all app-specific overrides in `mvp/static/_bootstrap_variables.scss` (Bootstrap tokens)
or `mvp/static/_adminlte_variables.scss` (AdminLTE vars referencing Bootstrap tokens).

## Refresh Process

Run the repository's Invoke vendor-refresh task to update this tree:

```
invoke refresh-adminlte-scss
```

The task will:

1. Install the latest AdminLTE 4 package with npm.
2. Delete the current `scss/` tree in full.
3. Copy the refreshed AdminLTE SCSS sources into `scss/`.
4. Preserve the lockfile as the version-pinning mechanism.

## Lockfile Pinning

The resolved AdminLTE version is pinned by the committed `package-lock.json`.
Run `npm install` (not `npm update`) to reproduce the exact pinned versions.
