"""Tests for the icon alias map ``mvp.utils.BS5_ICONS`` and its two small
brand-asset resolvers.

Source: mvp/utils.py

BS5_ICONS is what docs/getting-started.md calls "covering every icon its own
components use" — a hand-maintained dict, checked by nothing, that both
consuming projects and django-mvp's own shipped templates depend on to
resolve an ``icon="..."`` name to a real Bootstrap Icons class. #294 reported
``icon("import") -> ""``: an unregistered name renders as an empty string
rather than an error, so a gap in this dict is silent everywhere it is used.
Auditing the package's own templates against the map (below) found the same
failure already shipping in mvp/templates/cotton/user/sidebar_menu.html,
whose ``icon="account_center"`` had never resolved to anything.

The class list a value is checked against is vendored at
tests/fixtures/bootstrap-icons-1.13.1-names.txt, matching the release pinned
in mvp/templates/mvp/base.html — a typo'd or renamed Bootstrap Icons class is
exactly as silent as a missing alias (the demo/settings.py "sidebar-right"
entry fixed alongside this had one: bi-layout-sidebar-right, which has never
existed in any Bootstrap Icons release).
"""

import re
from pathlib import Path

import pytest
from easy_icons import icon

from mvp.utils import BS5_ICONS, app_is_installed

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
VALID_BOOTSTRAP_ICON_NAMES = frozenset(
    FIXTURES_DIR.joinpath("bootstrap-icons-1.13.1-names.txt").read_text().split()
)

PACKAGE_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "mvp" / "templates"

# A literal icon="name" attribute. Deliberately excludes anything starting
# with "{" — a template variable (icon="{{ page.icon }}") names nothing this
# map can check statically — and a leading ":" — Cotton's :icon="expr" binds
# a template expression, not a literal name (mvp/templates/menus/dock/item.html
# passes the item's own icon straight through as :icon="icon").
ICON_ATTR_RE = re.compile(r'(?<!:)icon="([^"{][^"]*)"')


def _expanded_aliases() -> dict[str, str]:
    """BS5_ICONS with every comma-separated key split to its own entry.

    Mirrors easy_icons.utils._expand_aliases's documented behaviour (strip
    whitespace, drop empties) without importing a private helper from a
    dependency — this is the same expansion the renderer applies at request
    time, re-derived so the test does not depend on that function's name.
    """
    expanded = {}
    for key, value in BS5_ICONS.items():
        for alias in key.split(","):
            alias = alias.strip()
            if alias:
                expanded[alias] = value
    return expanded


def _icon_names_referenced_in_package_templates() -> set[str]:
    names = set()
    for template in PACKAGE_TEMPLATES_DIR.rglob("*.html"):
        names.update(ICON_ATTR_RE.findall(template.read_text(encoding="utf-8")))
    return names


class TestBS5IconsData:
    """The dict itself: every class it names is real, every alias is unique."""

    def test_no_alias_is_declared_twice(self):
        """A repeated alias across two keys would silently shadow the first
        one's value with dict-construction order rather than error."""
        all_aliases = [
            alias.strip()
            for key in BS5_ICONS
            for alias in key.split(",")
            if alias.strip()
        ]

        assert len(all_aliases) == len(set(all_aliases)), (
            "duplicate alias across BS5_ICONS keys: "
            f"{[a for a in set(all_aliases) if all_aliases.count(a) > 1]}"
        )

    @pytest.mark.parametrize("alias, bootstrap_class", _expanded_aliases().items())
    def test_value_is_a_bi_prefixed_class(self, alias, bootstrap_class):
        assert bootstrap_class.startswith("bi bi-"), (
            f"{alias!r} -> {bootstrap_class!r} does not use the 'bi bi-<name>' "
            "convention every other entry in the pack follows"
        )

    @pytest.mark.parametrize("alias, bootstrap_class", _expanded_aliases().items())
    def test_class_exists_in_the_pinned_bootstrap_icons_release(
        self, alias, bootstrap_class
    ):
        """A class that does not exist in the pinned release renders no
        glyph — the same silent failure as a missing alias, just harder to
        spot because the dict entry looks correct."""
        icon_name = bootstrap_class.removeprefix("bi bi-")

        assert icon_name in VALID_BOOTSTRAP_ICON_NAMES, (
            f"{alias!r} -> {bootstrap_class!r}: 'bi-{icon_name}' is not in "
            "Bootstrap Icons 1.13.1 (tests/fixtures/bootstrap-icons-1.13.1-names.txt)"
        )


class TestBS5IconsResolution:
    """The reported symptom, reproduced through the real renderer config."""

    @pytest.mark.parametrize(
        "name", ["import", "upload", "export", "download", "account_center"]
    )
    def test_previously_unregistered_name_now_resolves(self, name):
        """icon("import") -> "" was the exact repro in #294; account_center
        is the same failure already present in a shipped template."""
        rendered = icon(name)

        assert rendered != "", f'icon("{name}") rendered nothing'
        assert "bi-" in rendered

    @pytest.mark.parametrize("name", ["add", "filter", "search", "logout"])
    def test_pre_existing_aliases_still_resolve(self, name):
        """A pack rewrite that silently drops an old alias breaks every
        caller using it, with the same empty-string symptom as a gap."""
        assert icon(name) != ""


class TestPackageTemplatesReferenceKnownIcons:
    """django-mvp's own components only ever use icons the pack defines.

    This is docs/getting-started.md's claim made into a check: a name any
    shipped cotton template hands to icon="..." has to resolve, or a
    consumer using django-mvp's own components gets the same silent gap
    #294 reported from a third-party call site.
    """

    def test_every_referenced_icon_name_is_registered(self):
        expanded = _expanded_aliases()
        referenced = _icon_names_referenced_in_package_templates()

        unregistered = {name for name in referenced if name not in expanded}

        assert not unregistered, (
            f"mvp's own templates reference icon name(s) {sorted(unregistered)} "
            "that BS5_ICONS does not define — each renders as an empty string"
        )

    def test_the_scan_itself_finds_something(self):
        """A regex that stopped matching would make the test above pass by
        finding zero templates to check, which is not the same as finding
        zero problems."""
        assert len(_icon_names_referenced_in_package_templates()) > 10


class TestAppIsInstalled:
    def test_true_for_an_installed_app(self):
        assert app_is_installed("mvp") is True

    def test_true_for_an_installed_app_given_its_full_path(self):
        assert app_is_installed("django.contrib.admin") is True

    def test_false_for_an_uninstalled_app(self):
        assert app_is_installed("not_a_real_app_anyone_installed") is False
