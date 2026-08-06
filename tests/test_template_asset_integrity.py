"""Every third-party asset loaded by a shipped template is pinned and hashed.

No Python module owns "the external <script>/<link> tags in mvp/templates/" — this
walks the packaged template tree directly rather than exercising a view, so it is
declared under `[tool.forge.conformance] non-mirror-paths` in pyproject.toml instead
of mirroring a source module that does not exist.

Regression coverage for issue #170: a floating version (`@3.x.x`) or a missing
version entirely made subresource integrity impossible, and two tags carried
`crossorigin` without the `integrity` hash it is meant to protect.
"""

import re
from pathlib import Path

TEMPLATES_ROOT = Path(__file__).resolve().parent.parent / "mvp" / "templates"

_TAG_RE = re.compile(r"<(?:script|link)\b[^>]*>", re.IGNORECASE | re.DOTALL)
_URL_RE = re.compile(r'(?:src|href)\s*=\s*"(https://[^"]+)"', re.IGNORECASE)

# An exact version has no wildcard component: `@3.15.12`, never `@3.x.x`, and the
# URL must carry a version at all — `.../npm/parallaxx-js/dist/...` with no `@version`
# floats to whatever the registry currently calls "latest".
_EXACT_VERSION_RE = re.compile(r"@(\d+\.\d+\.\d+)(?:[/?]|$)")


def _external_asset_tags():
    """Yield (path, tag) for every <script>/<link> tag loading an https:// asset
    in the shipped `mvp/templates/` tree."""
    for html_file in sorted(TEMPLATES_ROOT.rglob("*.html")):
        text = html_file.read_text()
        for match in _TAG_RE.finditer(text):
            tag = match.group(0)
            if "https://" in tag:
                yield html_file.relative_to(TEMPLATES_ROOT.parent.parent), tag


class TestShippedTemplatesPinAndHashExternalAssets:
    """Every external <script>/<link> tag in the shipped templates carries an exact
    version, a subresource-integrity hash and crossorigin (issue #170)."""

    def test_every_external_asset_is_version_pinned(self):
        offenders = []
        for path, tag in _external_asset_tags():
            url_match = _URL_RE.search(tag)
            url = url_match.group(1) if url_match else tag.strip()
            if not _EXACT_VERSION_RE.search(url):
                offenders.append(f"{path}: {url}")
        assert not offenders, (
            "external asset tags must pin an exact version, never a floating "
            "range or an unpinned latest:\n" + "\n".join(offenders)
        )

    def test_every_external_asset_carries_integrity(self):
        offenders = [
            f"{path}: {tag.strip()}"
            for path, tag in _external_asset_tags()
            if "integrity=" not in tag.lower()
        ]
        assert not offenders, (
            "external asset tags must carry a subresource-integrity hash:\n"
            + "\n".join(offenders)
        )

    def test_every_external_asset_carries_crossorigin(self):
        offenders = [
            f"{path}: {tag.strip()}"
            for path, tag in _external_asset_tags()
            if "crossorigin=" not in tag.lower()
        ]
        assert not offenders, (
            "external asset tags must carry crossorigin, or the integrity check "
            "browsers perform on cross-origin resources never runs:\n"
            + "\n".join(offenders)
        )

    def test_finds_the_known_external_assets(self):
        """Sanity check: the scan itself is not vacuous — it sees the tags we
        expect it to see, so a passing suite means the assertions ran, not that
        rglob found nothing."""
        seen = list(_external_asset_tags())
        assert len(seen) >= 5
