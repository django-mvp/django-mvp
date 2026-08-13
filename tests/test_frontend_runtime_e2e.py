"""The shipped front-end runtime boots, in a real browser, from local files.

``tests/test_frontend_runtime.py`` proves no shipped template *contains* a
remote ``<script>``. That is a source check, and a source check cannot tell
whether the bundle it points at actually works. A bundle that fails to parse,
or that forgets to register a plugin, leaves the templates looking correct and
every Alpine component dead.

These tests load real demo pages and assert three things the source cannot:
the libraries are present and started, nothing executable is fetched from a
third party while the page loads, and the behaviour built on the plugins still
works.
"""

import pytest
from playwright.sync_api import expect

from demo.settings import MVP_CONFIG as DEMO_MVP_CONFIG
from mvp.config import MVP_CONFIG
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

    def test_a_dropdown_entry_sets_that_theme_and_it_survives_a_reload(
        self, page, live_server, monkeypatch
    ):
        """A configured switcher entry actually applies its theme (SC-004).

        ``data-set-theme`` is markup this package has not shipped before. The
        rendered-markup tests prove the attribute is emitted and the bundle
        test proves the string is in the bundle, and neither can tell whether
        theme-change binds it — the same gap the toggle test above exists to
        close. Persistence needs a real browser too: a ``localStorage`` write
        read back by the pre-paint guard on the next load is not expressible
        with the Django test client.

        ``tests/settings.py`` pins a bare ``MVP_CONFIG`` with no
        ``theme.choices``, so the demo's own configuration is applied for this
        test's duration through the same ``monkeypatch.setitem`` seam
        ``tests/test_demo/test_theme_customization.py`` uses.
        """
        monkeypatch.setitem(
            MVP_CONFIG["theme"], "choices", DEMO_MVP_CONFIG["theme"]["choices"]
        )

        page.goto(f"{live_server.url}/theme/")

        # The navbar renders a switcher for each breakpoint, so only one is
        # visible at the viewport under test. Open that one, then pick from it.
        switcher = (
            page.locator('.dropdown:has([data-set-theme="dracula"])')
            .locator("visible=true")
            .first
        )
        expect(switcher).to_be_visible()
        switcher.locator('[role="button"][tabindex="0"]').first.click()

        entry = switcher.locator('[data-set-theme="dracula"]')
        expect(entry).to_be_visible()

        # Activated from the keyboard rather than by pointer. Entries are
        # <button>, so Enter fires the click theme-change binds — which is the
        # property that makes the switcher usable without a mouse, and the one
        # a rendered-markup assertion cannot establish.
        entry.focus()
        entry.press("Enter")
        page.wait_for_function(
            "() => document.documentElement.getAttribute('data-theme') === 'dracula'"
        )

        assert (
            page.evaluate("() => document.documentElement.getAttribute('data-theme')")
            == "dracula"
        ), (
            "clicking [data-set-theme=dracula] did not apply the theme — "
            "theme-change binds data-set-theme on DOMContentLoaded, which the "
            "deferred bundle must still run before"
        )

        page.reload()
        page.wait_for_function(
            "() => document.documentElement.getAttribute('data-theme') === 'dracula'"
        )

        assert (
            page.evaluate("() => document.documentElement.getAttribute('data-theme')")
            == "dracula"
        ), (
            "the selection did not survive a reload — the pre-paint guard "
            "reads localStorage.theme, so a selection inside the configured "
            "choices must come back on the next load"
        )

    def test_a_stored_theme_the_project_no_longer_offers_stays_rejected(
        self, page, live_server, monkeypatch
    ):
        """A dropped theme must not come back after the page settles (FR-010).

        The pre-paint guard resolving the right value is only half of it.
        theme-change re-applies ``localStorage.theme`` on ``DOMContentLoaded``
        with no membership check of its own, so a guard that sets the
        attribute without rewriting the stored value is correct for one frame
        and reverted immediately after. That is invisible to any assertion on
        the guard's source, which is why this waits for the page to settle
        before reading the attribute.
        """
        monkeypatch.setitem(MVP_CONFIG["theme"], "choices", ["light", "dark"])
        # Pin the default inside this scenario's own choices. It used to be
        # "light" package-wide, so the fixture read as self-consistent without
        # saying so; the packaged default is now "mvp" (docs/adr/0012), which
        # this project does not offer. Stating it here keeps the subject of the
        # test — a dropped theme staying dropped — independent of what the
        # package happens to default to.
        monkeypatch.setitem(MVP_CONFIG["theme"], "default", "light")

        page.goto(f"{live_server.url}/theme/")
        page.evaluate("() => localStorage.setItem('theme', 'dracula')")

        page.goto(f"{live_server.url}/theme/", wait_until="networkidle")

        assert (
            page.evaluate("() => document.documentElement.getAttribute('data-theme')")
            == "light"
        ), (
            "a stored theme outside the configured choices was applied — the "
            "guard must also rewrite localStorage, or theme-change restores "
            "the dropped theme on DOMContentLoaded"
        )
        assert page.evaluate("() => localStorage.getItem('theme')") == "light", (
            "the stale stored selection was left in place, so it would be "
            "restored again on the next load"
        )
