"""The shipped front-end runtime, checked at the source and artifact level.

The package used to pull Alpine, its plugins and theme-change from a public
CDN, three of them on a floating ``3.x.x`` tag. Whoever controlled one of those
packages, or the path serving it, ran JavaScript on every page of every project
that extends the base template, and a project could neither see nor pin what it
got. The runtime is bundled into a committed artifact instead.

These are the source-level checks. ``test_frontend_runtime_e2e.py`` covers the
half a source check cannot reach: whether the bundle actually boots in a
browser and whether anything is fetched over the network at page load.
"""

import re
from pathlib import Path

import pytest
from django.apps import apps

MVP_TEMPLATES = Path(apps.get_app_config("mvp").path) / "templates"


class TestShippedFrontEndRuntime:
    """No shipped template fetches executable code from a third party.

    The package used to pull Alpine, its plugins and theme-change from a public
    CDN, three of them on a floating ``3.x.x`` tag. Whoever controlled one of
    those packages, or the path serving it, ran JavaScript on every page of
    every project that extends the base template, and a project could neither
    see nor pin what it got. The runtime is now bundled into a committed
    artifact instead, so these tests are what stops a remote ``<script>``
    coming back.
    """

    # <script src="https://..."> or "//..." — a protocol-relative src is the
    # same exposure and would otherwise slip past a plain "https" check.
    REMOTE_SCRIPT = re.compile(
        r"<script[^>]*\ssrc\s*=\s*[\"'](?:https?:)?//", re.IGNORECASE
    )

    BUNDLE = Path(apps.get_app_config("mvp").path) / "static" / "js" / "django-mvp.js"

    def _shipped_templates(self):
        return sorted(MVP_TEMPLATES.rglob("*.html"))

    def test_no_shipped_template_loads_remote_javascript(self):
        offenders = [
            path.relative_to(MVP_TEMPLATES).as_posix()
            for path in self._shipped_templates()
            if self.REMOTE_SCRIPT.search(path.read_text())
        ]

        assert offenders == [], (
            "these shipped templates load JavaScript from a remote origin, "
            f"which the bundled runtime exists to prevent: {offenders}"
        )

    def test_the_regex_catches_a_remote_script_tag(self):
        """A true-positive control.

        Without it, a regex that matched nothing would pass the test above for
        the wrong reason and keep passing after a CDN tag came back.
        """
        assert self.REMOTE_SCRIPT.search(
            '<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x"></script>'
        )
        assert self.REMOTE_SCRIPT.search('<script src="//example.test/x.js"></script>')
        assert not self.REMOTE_SCRIPT.search(
            "<script src=\"{% static 'js/django-mvp.js' %}\"></script>"
        )

    def test_base_template_loads_the_bundled_runtime(self):
        source = (MVP_TEMPLATES / "mvp" / "base.html").read_text()

        assert "js/django-mvp.js" in source, (
            "mvp/base.html must load the bundled runtime; without it no "
            "component that uses Alpine or htmx works"
        )

    def test_the_bundle_is_committed_and_not_empty(self):
        """Article XV: the artifact ships, so a project needs no build step."""
        assert self.BUNDLE.is_file(), f"{self.BUNDLE} is missing — run `invoke build-js`"
        assert self.BUNDLE.stat().st_size > 50_000, (
            "the bundle is far smaller than Alpine and htmx together, so the "
            "build almost certainly did not include them"
        )

    # A string each library emits into the built output and the others do not.
    # Deliberately not version numbers: this asserts what is in the bundle, not
    # which release of it, so a version bump does not fail the test.
    LIBRARY_MARKERS = {
        "alpinejs": "alpine:init",
        "@alpinejs/persist": "$persist",
        "htmx.org": "htmx",
        "theme-change": "data-toggle-theme",
    }

    @pytest.mark.parametrize("package,marker", sorted(LIBRARY_MARKERS.items()))
    def test_every_declared_library_reaches_the_bundle(self, package, marker):
        """Each library in assets/js/index.js is actually in the output.

        A library can vanish from the bundle without any other test noticing:
        theme-change and persist only fail at the point a control or a
        component reaches for them, and a stale committed artifact looks
        identical to a fresh one. This is what catches both.
        """
        assert marker in self.BUNDLE.read_text(), (
            f"{package} is missing from the built bundle (no {marker!r}) — "
            "either it was dropped from assets/js/index.js, or the committed "
            "artifact is stale and needs `invoke build-js`"
        )
