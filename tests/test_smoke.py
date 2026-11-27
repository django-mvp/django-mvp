"""
Checks on the committed stylesheet and the theming docs: that the shipped
stylesheet carries what the package's templates and consumers rely on.
"""

import re
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
STYLESHEET = BASE_DIR / "mvp" / "static" / "css" / "django-mvp.css"


@pytest.fixture(scope="module")
def stylesheet() -> str:
    return STYLESHEET.read_text(encoding="utf-8")


def _class_present(content: str, css_class: str) -> bool:
    """Whether ``css_class`` has a rule in ``content``.

    A responsive class is committed with its colon escaped
    (``lg:flex-row`` -> ``lg\\:flex-row``), so matching the bare class name
    against the built file finds nothing. The escape is reproduced in the
    pattern.
    """
    escaped_class = re.escape(css_class.replace(":", "\\:"))
    return re.search(rf"\.{escaped_class}\b", content) is not None


#: Component classes no template of the package uses, which still have to ship
#: so a project can use any daisyUI component without rebuilding.
UNUSED_DAISYUI_CLASSES = (
    "carousel",
    "chat-bubble",
    "kbd",
    "rating",
    "countdown",
    "timeline",
    "diff",
    "fab",
    "radial-progress",
    "validator",
    "glass",
)

#: Responsive classes the Account Center templates use.
ACCOUNT_CENTER_CLASSES = (
    "lg:flex-row",
    "lg:items-start",
    "lg:gap-6",
    "sm:grid-cols-2",
    "lg:shrink-0",
)

# node_modules is gitignored and the Python CI job never runs npm ci, so the
# sweep over every daisyUI theme skips rather than fails when the front-end
# toolchain isn't installed.
_DAISYUI_THEME_DIR = BASE_DIR / "node_modules" / "daisyui" / "theme"

#: Always checked, because the full sweep below is skipped without node_modules:
#: reverting ``themes: all`` would otherwise leave the suite green.
REPRESENTATIVE_THEMES = ("dracula", "synthwave", "cyberpunk", "retro", "valentine")


class TestShippedStylesheet:
    def test_it_ships_the_classes_no_package_template_uses(self, stylesheet):
        missing = [
            css_class
            for css_class in UNUSED_DAISYUI_CLASSES
            if not _class_present(stylesheet, css_class)
        ]

        assert not missing, f"missing from the shipped stylesheet: {missing}"

    def test_it_ships_the_responsive_classes_the_account_center_uses(self, stylesheet):
        missing = [
            css_class
            for css_class in ACCOUNT_CENTER_CLASSES
            if not _class_present(stylesheet, css_class)
        ]

        assert not missing, (
            f"missing from the shipped stylesheet: {missing}. "
            "Rebuild it with `invoke build-stylesheet`."
        )

    def test_it_ships_the_representative_themes(self, stylesheet):
        missing = [
            theme
            for theme in REPRESENTATIVE_THEMES
            if f"[data-theme={theme}]" not in stylesheet
        ]

        assert not missing, f"themes missing from the shipped stylesheet: {missing}"

    @pytest.mark.skipif(
        not _DAISYUI_THEME_DIR.is_dir(),
        reason="node_modules/daisyui/theme not installed",
    )
    def test_it_ships_every_daisyui_theme(self, stylesheet):
        themes = sorted(path.stem for path in _DAISYUI_THEME_DIR.glob("*.css"))
        assert themes, "node_modules/daisyui/theme holds no theme files"

        missing = [t for t in themes if f"[data-theme={t}]" not in stylesheet]

        assert not missing, f"themes missing from the shipped stylesheet: {missing}"


_CUSTOM_PROPERTY_RE = re.compile(r"--[a-zA-Z0-9-]+")

# SC-003: the compressed stylesheet a project downloads may grow by at most
# 13 KB against the release this feature started from.
V0_18_0_COMPRESSED_BYTES = 41670
SC003_GROWTH_BUDGET_BYTES = 13312


class TestThemingDocVariableCoverage:
    THEMING_DOC = BASE_DIR / "docs" / "theming.md"

    def test_every_shipped_custom_property_is_in_the_variable_table(self, stylesheet):
        start = stylesheet.find(":where(:root)")
        assert start != -1, "the shipped stylesheet has no default theme block to read"
        default_theme = stylesheet[start : stylesheet.index("}", start)]
        properties = set(_CUSTOM_PROPERTY_RE.findall(default_theme))
        assert properties, "no custom properties were found in the default theme block"

        # Only the table's rows: the worked example further down sets every
        # property too, so a search of the whole page passes with the table gone.
        rows = [
            line
            for line in self.THEMING_DOC.read_text(encoding="utf-8").splitlines()
            if line.startswith("| `")
        ]
        assert rows, "no variable table rows found in docs/theming.md"

        missing = sorted(
            prop for prop in properties if not any(f"`{prop}`" in row for row in rows)
        )
        assert not missing, (
            f"docs/theming.md's variable table is missing these variables: {missing}"
        )

    def test_the_compressed_stylesheet_stays_within_its_budget(self):
        compressed = BASE_DIR / "mvp" / "static" / "css" / "django-mvp.css.br"
        size = compressed.stat().st_size

        assert size <= V0_18_0_COMPRESSED_BYTES + SC003_GROWTH_BUDGET_BYTES, (
            f"the compressed stylesheet is {size} bytes, more than "
            f"{SC003_GROWTH_BUDGET_BYTES} above the {V0_18_0_COMPRESSED_BYTES}"
            " byte baseline this feature started from (SC-003)"
        )
