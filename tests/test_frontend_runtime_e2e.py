"""The shipped front-end runtime boots, in a real browser, from local files.

``tests/test_templates.py`` proves no shipped template *contains* a remote
``<script>``. That is a source check, and a source check cannot tell whether
the bundle it points at actually works — a bundle that fails to parse, or that
forgets to register a plugin, leaves the templates looking correct and every
Alpine component dead.

These tests load real demo pages and assert three things the source cannot:
the libraries are present and started, nothing executable is fetched from a
third party while the page loads, and the behaviour built on the plugins still
works.
"""

import pytest
from playwright.sync_api import expect

from tests.conftest import requires_browser

pytestmark = [pytest.mark.e2e, requires_browser]


class TestBundledRuntimeBoots:
    """Alpine, its plugins, htmx and theme-change all come up from the bundle."""

    def test_alpine_starts_and_exposes_the_global(self, page, live_server):
        page.goto(f"{live_server.url}/components/")

        # Alpine sets this on itself during start(); formset.js and any x-data
        # in a consuming project's templates reach for the same global.
        version = page.evaluate("() => window.Alpine && window.Alpine.version")

        assert version, "window.Alpine is missing — the bundle did not start Alpine"
        assert version.startswith("3."), f"unexpected Alpine major version: {version}"

    def test_htmx_is_available(self, page, live_server):
        page.goto(f"{live_server.url}/components/")

        version = page.evaluate("() => window.htmx && window.htmx.version")

        assert version, (
            "window.htmx is missing — the package advertises htmx support and "
            "ships HtmxFormMixin, so the runtime has to be there"
        )
        assert version.startswith("2."), f"unexpected htmx major version: {version}"

    def test_the_persist_plugin_is_registered(self, page, live_server):
        """``$persist`` is what the sidebar drawer state is built on.

        A plugin that is bundled but never passed to ``Alpine.plugin()`` fails
        only at the point a component uses it, which is why this is asserted
        directly rather than inferred from the bundle contents.
        """
        page.goto(f"{live_server.url}/components/")

        registered = page.evaluate(
            """() => {
                const el = document.createElement('div');
                el.setAttribute('x-data', "{ v: $persist('ok').as('probe-key') }");
                document.body.appendChild(el);
                window.Alpine.initTree(el);
                return el._x_dataStack?.[0]?.v;
            }"""
        )

        assert registered == "ok", (
            "$persist did not resolve — the persist plugin was not registered "
            "before Alpine.start()"
        )

    # The sort plugin registers only a directive, and Alpine exposes no way to
    # enumerate those — binding `x-sort` to an element behaves identically
    # whether or not the plugin loaded, so there is nothing to assert here that
    # would fail if it were dropped. It is covered instead by the bundle
    # composition test in tests/test_templates.py, which does fail when the
    # plugin is removed from the entry point.


class TestNothingExecutableComesFromAThirdParty:
    """The property the whole change exists to establish."""

    def test_no_script_is_fetched_from_a_remote_origin(self, page, live_server):
        """Watches the network rather than the markup.

        This is the test that would have caught the original defect, and it
        catches a reintroduction by any route — a template, an included
        component, or a script that injects another script at run time.
        """
        remote_scripts = []

        def record(request):
            if request.resource_type == "script" and not request.url.startswith(
                live_server.url
            ):
                remote_scripts.append(request.url)

        page.on("request", record)
        page.goto(f"{live_server.url}/components/", wait_until="networkidle")

        assert remote_scripts == [], (
            "these scripts were fetched from a third party during page load: "
            f"{remote_scripts}"
        )

    def test_the_watcher_would_notice_a_remote_script(self, page, live_server):
        """A true-positive control for the test above.

        Without it, a watcher that never fires — wrong event name, wrong
        resource type — reports a clean page forever.
        """
        remote_scripts = []

        def record(request):
            if request.resource_type == "script" and not request.url.startswith(
                live_server.url
            ):
                remote_scripts.append(request.url)

        page.on("request", record)
        page.goto(f"{live_server.url}/components/")
        page.evaluate(
            """() => new Promise((resolve) => {
                const s = document.createElement('script');
                s.src = 'https://cdn.jsdelivr.net/npm/alpinejs@3.16.1/dist/cdn.min.js';
                s.onload = s.onerror = () => resolve();
                document.head.appendChild(s);
            })"""
        )

        assert remote_scripts, (
            "the request watcher did not fire for a deliberately injected "
            "remote script, so a clean result from it proves nothing"
        )


class TestThemeChangeStillWorks:
    """theme-change moved from an eager CDN tag into the deferred bundle."""

    def test_the_theme_toggle_flips_the_document_theme(self, page, live_server):
        page.goto(f"{live_server.url}/components/")

        toggle = page.locator("[data-toggle-theme]").first
        expect(toggle).to_be_attached()

        before = page.evaluate(
            "() => document.documentElement.getAttribute('data-theme')"
        )
        toggle.click()
        page.wait_for_function(
            "before => document.documentElement.getAttribute('data-theme') !== before",
            arg=before,
        )
        after = page.evaluate(
            "() => document.documentElement.getAttribute('data-theme')"
        )

        assert after != before, (
            "clicking [data-toggle-theme] did not change the theme — "
            "themeChange() binds on DOMContentLoaded, which a deferred bundle "
            "must still run before"
        )
