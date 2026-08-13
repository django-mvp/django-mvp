/*
 * The shipped front-end runtime.
 *
 * Everything the components need at page load is bundled here and built into
 * mvp/static/js/django-mvp.js, a committed artifact (see Article XV of
 * memory/constitution.md). Nothing is fetched from a third party at run time,
 * so a project that installs the package gets a front end that works without
 * depending on a CDN staying up or staying honest.
 *
 * The bundle is not configurable. These libraries are what the components are
 * written against, so a project cannot swap or drop one without breaking the
 * markup the package ships. A project adding its own Alpine plugins or htmx
 * extensions does so from its own base template, in `{% block head %}`.
 *
 * Build:  npm run build:js        (readable, for local work)
 *         npm run build:js:prod   (minified, what ships)
 */

import Alpine from "alpinejs";
import persist from "@alpinejs/persist";
import sort from "@alpinejs/sort";
import htmx from "htmx.org";
import { themeChange } from "theme-change";

// htmx reads hx-* attributes off the DOM itself; the global is what its own
// documentation, `hx-on:` handlers and browser-console debugging expect to find.
window.htmx = htmx;

// Binds the [data-toggle-theme] / [data-set-theme] / [data-choose-theme]
// controls. Defaults to attaching on DOMContentLoaded, which still fires after
// this bundle runs because the tag is deferred. The inline script in base.html
// applies the stored theme before first paint; this only wires the controls.
themeChange();

// Plugins register before start(), which is why the CDN tags this replaces had
// to be ordered with the plugins ahead of core.
Alpine.plugin(persist);
Alpine.plugin(sort);

// mvp/static/js/formset.js reaches for the global, as does any x-data in a
// consuming project's own templates.
window.Alpine = Alpine;

Alpine.start();
