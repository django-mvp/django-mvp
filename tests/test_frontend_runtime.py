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

from django.apps import apps

MVP_TEMPLATES = Path(apps.get_app_config("mvp").path) / "templates"


class TestShippedFrontEndRuntime:
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
        assert self.REMOTE_SCRIPT.search(
            '<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x"></script>'
        )
        assert self.REMOTE_SCRIPT.search('<script src="//example.test/x.js"></script>')
        assert not self.REMOTE_SCRIPT.search(
            "<script src=\"{% static 'js/django-mvp.js' %}\"></script>"
        )

    # A string each library emits into the built output and the others do not.
    # Deliberately not version numbers: this asserts what is in the bundle, not
    # which release of it, so a version bump does not fail the test.
    LIBRARY_MARKERS = {
        "alpinejs": "alpine:init",
        "@alpinejs/persist": "$persist",
        "htmx.org": "htmx",
        "theme-change": "data-toggle-theme",
        # The default `boundary` its collision detection measures against. The
        # placement strings would have been the obvious choice and are useless
        # here, because assets/js/dropdown.js writes the same literals itself.
        "@floating-ui/dom": "clippingAncestors",
        # The author line of the licence comment the build keeps in the bundle.
        "sortablejs": "RubaXa",
        # The list row's Alpine component.
        "the list row component": "mvpRowActions",
    }

    def test_every_declared_library_reaches_the_bundle(self):
        bundle = self.BUNDLE.read_text()

        missing = [
            f"{package} (no {marker!r})"
            for package, marker in self.LIBRARY_MARKERS.items()
            if marker not in bundle
        ]

        assert not missing, (
            f"missing from the built bundle: {missing}. Either it was dropped from "
            "assets/js/index.js, or the committed artifact is stale and needs "
            "`invoke build-js`"
        )
