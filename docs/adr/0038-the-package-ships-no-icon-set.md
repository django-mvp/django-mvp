# ADR 0038 — The package ships no icon set

**Status:** accepted

## Decision

The package does not ship the files of any third-party icon provider. `MVP_CONFIG["icon_stylesheet"]` names the stylesheet that draws the icon set, as a URL, a static file path, or `None` for a renderer that needs none. The default is Bootstrap Icons from jsDelivr, the set `mvp.utils.BS5_ICONS` names.

This is the one exception to G14. Everything else the shell and the components need ships inside the package.

## Why

Icons are replaceable by design: a project picks its renderer and its names through django-easy-icons. Shipping one provider's font would tie every install to that provider's files, whether or not the project uses them, and put a third party's release cycle into this package's.

A setting leaves the choice with the project. A site that can't send its visitors' addresses to a CDN, or can't reach one, hosts the files itself or names another provider, in one line and without overriding the `head` block.

The default stays on a CDN so that a new project shows icons with nothing to install. It is a default, and it carries the cost that every page calls jsDelivr until the project sets its own.
