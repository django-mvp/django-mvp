/*
 * The shipped front-end runtime.
 *
 * Everything the components need at page load is bundled here and built into
 * mvp/static/js/django-mvp.js, a committed artifact. Nothing is fetched from
 * a third party at run time, so a project that installs the package gets a
 * front end that works without depending on a CDN staying up or staying honest.
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
import htmx from "htmx.org";
import { themeChange } from "theme-change";

import { startDropdowns } from "./dropdown.js";
import { registerLayoutStore } from "./layout.js";

// htmx reads hx-* attributes off the DOM itself; the global is what its own
// documentation, `hx-on:` handlers and browser-console debugging expect to find.
window.htmx = htmx;

// Attaches on DOMContentLoaded, which still fires since the tag is deferred.
// The inline script in base.html applies the stored theme before first
// paint; this call only wires the [data-*-theme] controls.
themeChange();

// Moves each dropdown panel into the top layer so it opens where there is
// room for it. See assets/js/dropdown.js for why this runs here rather
// than being written into the template.
startDropdowns();

// theme-change can't notice controls added after it runs, and a boosted
// navigation swaps the body for identical markup with no listeners: the
// toggle renders but stops responding.
//
// Rebinding is safe only when *every* bound control went with the swap —
// a surviving one would get a second listener, and two clicks per click
// un-toggles the theme. A body-targeted swap is exactly that case.
//
// Dropdowns are rebound on the same terms: a narrower swap would leave
// already-upgraded panels for a second listener set to attach to.
document.addEventListener("htmx:afterSettle", (event) => {
  if (event.detail?.target === document.body) {
    themeChange(false);
    startDropdowns();
    // The swapped-in drawer is a new, server-closed element; re-derive the
    // resting position rather than keep whatever it held before the swap.
    Alpine.store("mvp").rebindAfterNavigation();
  }
});

// Plugins must register before start(). Only persist is bundled — the CDN
// tags this replaces also loaded @alpinejs/sort, unused in the package and
// a quarter of the built output; a project wanting x-sort adds it itself.
Alpine.plugin(persist);

// Registered after the persist plugin and before start(): the plugin
// defines Alpine.$persist, which the store's desktop-open property needs
// at construction. See assets/js/layout.js.
registerLayoutStore(Alpine);

// mvp/static/js/formset.js reaches for the global, as does any x-data in a
// consuming project's own templates.
window.Alpine = Alpine;

Alpine.start();
