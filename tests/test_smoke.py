"""
Smoke tests – quick sanity-checks that the package imports cleanly and
the Django configuration is valid.
"""

import re
from pathlib import Path

import django
import pytest

from demo.models import OrderLine

BASE_DIR = Path(__file__).resolve().parent.parent


class TestPackageSanity:
    """The package imports cleanly and the Django config is valid."""

    def test_django_version(self):
        """Django is available and meets the minimum version."""
        major, minor, *_ = django.VERSION
        assert (major, minor) >= (4, 2), f"Django {major}.{minor} < 4.2"

    @pytest.mark.django_db
    def test_mvp_apps_load(self, client):
        """Django can resolve the root URL without raising configuration errors."""
        response = client.get("/")
        assert response.status_code in {200, 301, 302, 404}

    def test_mvp_imports(self):
        """The published package surface imports without errors."""
        import mvp  # noqa: F401
        from mvp import (
            renderers,  # noqa: F401
            views,  # noqa: F401
        )
        from mvp.templatetags import mvp as mvp_tags  # noqa: F401


# ---------------------------------------------------------------------------
# Styling docs discoverability (Tailwind/DaisyUI era)
# ---------------------------------------------------------------------------


class TestStylingDocs:
    """The styling documentation and Tailwind entry stay in step with the package."""

    def test_styling_doc_exists(self):
        """The styling guide exists and documents the consumer build command."""
        styling = BASE_DIR / "docs" / "styling.md"
        assert styling.exists(), (
            "docs/styling.md must exist — it is the canonical CSS/theming guide."
        )
        content = styling.read_text(encoding="utf-8")
        assert "mvp_tailwind" in content, (
            "docs/styling.md must document the 'python manage.py mvp_tailwind' command "
            "so Tier 2 consumers can find the CSS rebuild path."
        )

    def test_readme_references_styling_doc_and_command(self):
        """README.md points at the styling guide and the mvp_tailwind command."""
        readme = BASE_DIR / "README.md"
        content = readme.read_text(encoding="utf-8")
        assert "mvp_tailwind" in content, (
            "README.md must reference 'manage.py mvp_tailwind' so consumers discover "
            "the CSS rebuild path from the top-level documentation."
        )
        assert "docs/styling.md" in content, "README.md must link to docs/styling.md."

    def test_entry_css_imports_packaged_preset(self):
        """The package's own Tailwind entry uses the same preset shipped to consumers."""
        entry = (BASE_DIR / "assets" / "tailwind.css").read_text(encoding="utf-8")
        assert '@plugin "daisyui"' in entry, (
            "assets/tailwind.css must load the daisyui plugin — its removal once "
            "shipped a stylesheet with no DaisyUI classes at all."
        )
        assert "mvp/tailwind/base.css" in entry, (
            "assets/tailwind.css must import the packaged preset so the shipped "
            "stylesheet and consumer builds share one source of truth."
        )
        assert (BASE_DIR / "mvp" / "tailwind" / "base.css").exists()


# ---------------------------------------------------------------------------
# The shipped stylesheet carries the complete daisyUI component set (#190)
# ---------------------------------------------------------------------------


class TestShippedStylesheetShipsCompleteDaisyUI:
    """django-mvp.css ships every daisyUI component, not only the ones mvp's
    own templates happen to use.

    Before #190, the packaged Tailwind build only emitted a daisyUI class if
    the JIT scanner found it in mvp's own templates — so a consumer reaching
    for a component mvp never uses itself (`carousel`, `kbd`, `chat`, ...) got
    no styling at all. Forcing daisyUI's own component/utility source files
    into `@source` closes that gap regardless of what mvp's templates use.
    """

    STYLESHEET = BASE_DIR / "mvp" / "static" / "css" / "django-mvp.css"

    @staticmethod
    def _class_present(content: str, css_class: str) -> bool:
        return re.search(rf"\.{re.escape(css_class)}\b", content) is not None

    def test_entry_sources_daisyuis_own_component_and_utility_definitions(self):
        """assets/tailwind.css scans daisyUI's own class definitions, not just mvp's templates."""
        entry = (BASE_DIR / "assets" / "tailwind.css").read_text(encoding="utf-8")
        assert "node_modules/daisyui/components" in entry, (
            "assets/tailwind.css must scan daisyUI's component source files, or "
            "only the components mvp's own templates use ship (#190)."
        )
        assert "node_modules/daisyui/utilities" in entry, (
            "assets/tailwind.css must scan daisyUI's utility source files (glass, "
            "join, radius, typography), or the same gap applies to them (#190)."
        )

    def test_control_class_mvp_templates_already_use_is_present(self):
        """Known-present control, asserted with the same technique as the cases
        below: proves the substring/regex match actually finds a real class
        before any "still absent" or "now present" result is trusted. A built
        stylesheet escapes special characters (e.g. `lg:flex-row` is committed
        as `lg\\:flex-row`), so an untested assertion technique is worthless."""
        content = self.STYLESHEET.read_text(encoding="utf-8")
        assert self._class_present(content, "modal-top"), (
            ".modal-top is a component class mvp's own cotton/modal template "
            "renders — if this control fails, the assertion technique itself is "
            "broken, not the stylesheet."
        )

    @pytest.mark.parametrize(
        "css_class",
        [
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
        ],
    )
    def test_component_mvp_templates_never_reference_still_ships(self, css_class):
        """A daisyUI component none of mvp's own templates use is still emitted."""
        content = self.STYLESHEET.read_text(encoding="utf-8")
        assert self._class_present(content, css_class), (
            f".{css_class} is missing from the shipped stylesheet — daisyUI "
            "component coverage regressed (#190)."
        )


# ---------------------------------------------------------------------------
# The shipped stylesheet carries every prebuilt daisyUI theme (FS-026)
# ---------------------------------------------------------------------------

# node_modules is gitignored and the Python CI job never runs npm ci, so the
# discovery below must skip explicitly rather than fail when the front-end
# toolchain isn't installed — the same convention used elsewhere in this file
# for build-artifact checks.
_DAISYUI_THEME_DIR = BASE_DIR / "node_modules" / "daisyui" / "theme"
_DAISYUI_THEME_NAMES = (
    sorted(p.stem for p in _DAISYUI_THEME_DIR.glob("*.css"))
    if _DAISYUI_THEME_DIR.is_dir()
    else []
)


class TestShippedStylesheetShipsEveryPrebuiltTheme:
    """Every theme the pinned daisyUI version publishes ships in the built
    stylesheet, and the pre-existing default/dark-mode behaviour survives
    enabling them (FS-026).

    This is the deliberate inverse of the guard #190 added, which asserted
    named themes were *absent* — right when shipping only light/dark was the
    goal. #190's own reasoning (shipping every component regardless of what
    mvp's templates use) is untouched above; only the themes guard flips,
    because this feature makes shipping every prebuilt theme the point. See
    decisions.md D1 in specs/026-ship-prebuilt-daisyui for the record of why.
    """

    STYLESHEET = BASE_DIR / "mvp" / "static" / "css" / "django-mvp.css"

    def test_daisyui_theme_source_is_discoverable(self):
        """Guards the discovery mechanism itself, before it parametrizes the
        next test. Skips explicitly when node_modules/daisyui/theme is
        absent. When present, the glob must be non-empty: an empty list
        handed to parametrize produces pytest's empty-parameter-set skip,
        which reports green while asserting nothing."""
        if not _DAISYUI_THEME_DIR.is_dir():
            pytest.skip(
                "node_modules/daisyui/theme not installed — front-end "
                "toolchain not present in this environment"
            )
        assert _DAISYUI_THEME_NAMES, (
            "node_modules/daisyui/theme is present but no theme *.css files "
            "were discovered under it"
        )

    @pytest.mark.skipif(
        not _DAISYUI_THEME_DIR.is_dir(),
        reason="node_modules/daisyui/theme not installed",
    )
    @pytest.mark.parametrize("theme", _DAISYUI_THEME_NAMES)
    def test_every_daisyui_theme_ships(self, theme):
        """Every theme daisyUI publishes has a [data-theme=<name>] block in
        the shipped stylesheet (FR-001), so a project can select any of them
        by name alone with no build step of its own."""
        content = self.STYLESHEET.read_text(encoding="utf-8")
        assert f"[data-theme={theme}]" in content, (
            f"[data-theme={theme}] is missing from the shipped stylesheet — "
            "every daisyUI theme must ship (FR-001, FR-006)."
        )

    # The five names #190's guard listed when it asserted the opposite. Kept as
    # the unconditional arm because the completeness test above is skipped in
    # CI, where node_modules is absent — without this, reverting `themes: all`
    # would leave the suite green while shipping none of them (FR-001).
    REPRESENTATIVE_THEMES = ("dracula", "synthwave", "cyberpunk", "retro", "valentine")

    @pytest.mark.parametrize("theme", REPRESENTATIVE_THEMES)
    def test_representative_named_themes_ship(self, theme):
        """A named theme ships, asserted without needing node_modules.

        The completeness test above is the real guard, but it can only run
        where the front-end toolchain is installed. This one reads the
        committed stylesheet alone, so FR-001 keeps a check in CI rather than
        resting entirely on a case that is skipped there.
        """
        content = self.STYLESHEET.read_text(encoding="utf-8")
        assert f"[data-theme={theme}]" in content, (
            f"[data-theme={theme}] is missing from the shipped stylesheet — "
            "the prebuilt themes must ship inside the package (FR-001)."
        )

    def test_default_theme_still_bound_through_where_root(self):
        """The default theme stays bound through the zero-specificity
        :where(:root) arm, so a data-theme value matching nothing falls
        through to it instead of rendering unstyled (FR-014, SC-008). Reads
        only the committed stylesheet and stays unconditional — this is what
        proves FR-006 in CI, where the completeness case above is skipped."""
        content = self.STYLESHEET.read_text(encoding="utf-8")
        assert ":where(:root)" in content, (
            "the :where(:root) fall-through binding for the default theme "
            "is missing from the shipped stylesheet"
        )

    def test_prefers_color_scheme_dark_block_still_emitted(self):
        """The pre-existing @media (prefers-color-scheme: dark) block still
        ships, so enabling every theme does not disturb dark-mode behaviour
        (FR-006). Reads only the committed stylesheet and stays
        unconditional, for the same reason as the test above."""
        content = self.STYLESHEET.read_text(encoding="utf-8")
        assert "@media (prefers-color-scheme:dark)" in content, (
            "the @media (prefers-color-scheme: dark) block is missing from "
            "the shipped stylesheet"
        )


# ---------------------------------------------------------------------------
# Demo pages that extend page_view.html directly — the placeholder leak (#145)
# ---------------------------------------------------------------------------


class TestDemoPagesDontLeakTheScaffoldPlaceholder:
    """page_view.html's default page.content block reads "Coming soon...".

    That default is deliberate for a scaffold nobody has extended yet — see
    mvp/templates/page_view.html. A demo page is not a scaffold: it ships as a
    worked example, so it must supply its own content rather than fall through
    to the placeholder.
    """

    @pytest.mark.django_db
    def test_layout_demo_page_supplies_its_own_content(self, client):
        response = client.get("/layout/")
        assert response.status_code == 200
        assert "Coming soon" not in response.content.decode()

    @pytest.mark.django_db
    def test_theme_customization_demo_page_supplies_its_own_content(self, client):
        response = client.get("/theme/")
        assert response.status_code == 200
        assert "Coming soon" not in response.content.decode()


# ---------------------------------------------------------------------------
# Packaged form rendering works on a clean install (FR-001)
# ---------------------------------------------------------------------------


class TestCrispyIsARuntimeDependency:
    """crispy is required for the packaged form rendering to work at all.

    Parses pyproject.toml itself rather than installed distribution metadata:
    `.dist-info/METADATA` is written at install time and would not change when
    the source is fixed, so a metadata-based assertion would stay red after
    the declaration moves.
    """

    def test_crispy_pair_declared_in_project_dependencies(self):
        import tomllib

        pyproject = tomllib.loads(
            (BASE_DIR / "pyproject.toml").read_text(encoding="utf-8")
        )
        declared = pyproject["project"]["dependencies"]
        assert any("django-crispy-forms" in dep for dep in declared), (
            "django-crispy-forms must be declared in [project].dependencies — "
            "packaged form rendering requires it on every install."
        )
        assert any("crispy-tailwind" in dep for dep in declared), (
            "crispy-tailwind must be declared in [project].dependencies — "
            "packaged form rendering requires it on every install."
        )


# ---------------------------------------------------------------------------
# Worked example: a parent and its rows on one page (US6, T036)
# ---------------------------------------------------------------------------


class TestProductOrderLinesWorkedExample:
    """demo.ProductOrderLinesView — the parent-and-rows page docs/formsets.md walks through."""

    @pytest.mark.django_db
    def test_get_renders_the_parent_form_and_its_existing_rows(self, client):
        from tests.factories import OrderLineFactory, ProductFactory

        product = ProductFactory()
        OrderLineFactory(product=product, quantity=3)

        response = client.get(f"/products/{product.pk}/order-lines/")

        assert response.status_code == 200
        content = response.content.decode()
        assert 'value="3"' in content

    @pytest.mark.django_db
    def test_post_saves_the_parent_and_its_rows_in_one_submission(self, client):
        from tests.factories import ProductFactory

        product = ProductFactory(name="Original")
        data = {
            "name": "Renamed via the worked example",
            "order_lines-TOTAL_FORMS": "1",
            "order_lines-INITIAL_FORMS": "0",
            "order_lines-MIN_NUM_FORMS": "0",
            "order_lines-MAX_NUM_FORMS": "1000",
            "order_lines-0-quantity": "5",
        }

        response = client.post(f"/products/{product.pk}/order-lines/", data=data)

        assert response.status_code == 302
        product.refresh_from_db()
        assert product.name == "Renamed via the worked example"
        assert list(product.order_lines.values_list("quantity", flat=True)) == [5]


class TestOrderLineArticleIXCompliance:
    """demo.OrderLine's fields carry help text — Article IX, and T037's reason for existing:
    the worked example renders both fields, and a page demonstrating the packaged look
    cannot demonstrate help text with a field that has none."""

    def test_product_field_has_help_text(self):
        field = OrderLine._meta.get_field("product")
        assert str(field.help_text) != ""

    def test_quantity_field_has_help_text(self):
        field = OrderLine._meta.get_field("quantity")
        assert str(field.help_text) != ""


class TestFormsetComponentDocPage:
    """The formset component doc page (US6, T040) — the standalone formset case.

    Registered like every other entry in demo.component_docs.COMPONENTS, but the
    only one whose live example needs a real, bound formset in context rather
    than static markup.
    """

    @pytest.mark.django_db
    def test_page_renders_a_bound_orderline_formset(self, client):
        response = client.get("/components/formset/")

        assert response.status_code == 200
        content = response.content.decode()
        assert "Add row" in content
        assert 'name="form-TOTAL_FORMS"' in content


# ---------------------------------------------------------------------------
# docs/theming.md's variable table stays honest against the installed daisyUI
# version (FS-026 US-3, SC-007)
# ---------------------------------------------------------------------------

_CUSTOM_PROPERTY_RE = re.compile(r"--[a-zA-Z0-9-]+")


def _extract_custom_properties(css: str) -> set[str]:
    return set(_CUSTOM_PROPERTY_RE.findall(css))


# SC-003: the compressed stylesheet a project downloads may grow by at most
# 8 KB against the release this feature started from.
V0_18_0_COMPRESSED_BYTES = 41670
SC003_GROWTH_BUDGET_BYTES = 8192


class TestThemingDocVariableCoverage:
    """Every custom property a shipped theme defines appears in
    docs/theming.md's variable table (FR-015, SC-007), checked mechanically
    rather than by hand.

    The ground truth is the *committed stylesheet*, not node_modules. Reading
    the installed daisyUI would be equivalent — the two property sets match
    exactly — but node_modules is gitignored and the Python CI job never runs
    `npm ci`, so that version of this check skips in the one environment where
    it has to hold. Reading the artifact keeps SC-007 asserted everywhere, and
    checks what actually ships rather than what happens to be installed.
    """

    THEMING_DOC = BASE_DIR / "docs" / "theming.md"
    STYLESHEET = BASE_DIR / "mvp" / "static" / "css" / "django-mvp.css"

    def _shipped_default_theme_block(self):
        """The :where(:root) default-theme block from the built stylesheet."""
        content = self.STYLESHEET.read_text(encoding="utf-8")
        start = content.find(":where(:root)")
        assert start != -1, (
            "the :where(:root) default-theme binding is missing from the "
            "shipped stylesheet, so there is no theme block to read"
        )
        return content[start : content.index("}", start)]

    def _documented_variable_table(self):
        """Rows of the variable table, not the whole page.

        Scoping matters: the worked example further down sets every property
        too, so a check for the name appearing *anywhere* in the file passes
        with the table deleted outright. FR-015 asks for a table that says
        what each variable controls, so that is what gets checked.
        """
        rows = [
            line
            for line in self.THEMING_DOC.read_text(encoding="utf-8").splitlines()
            if line.startswith("| `")
        ]
        assert rows, "no variable table rows found in docs/theming.md"
        return rows

    def test_every_shipped_custom_property_is_in_the_variable_table(self):
        properties = _extract_custom_properties(self._shipped_default_theme_block())
        assert properties, (
            "no --custom-property names were extracted from the shipped "
            "stylesheet's default theme block — the extraction pattern "
            "itself may be broken, not the documentation"
        )

        rows = self._documented_variable_table()
        missing = sorted(
            prop for prop in properties if not any(f"`{prop}`" in r for r in rows)
        )
        assert not missing, (
            "docs/theming.md's variable table is missing these theme "
            f"variables: {missing}"
        )

    def test_each_documented_variable_says_what_it_controls(self):
        """A row naming a variable with an empty description satisfies the
        coverage check above while telling a reader nothing (FR-015)."""
        for row in self._documented_variable_table():
            cells = [c.strip() for c in row.strip("|").split("|")]
            assert len(cells) >= 2 and cells[1], (
                f"this variable table row has no description: {row}"
            )

    def test_the_compressed_stylesheet_stays_within_its_budget(self):
        """SC-003: the payload a project downloads may grow by at most 8 KB.

        Measured at 41,670 bytes before this feature and 46,532 after. The
        bound exists to catch a later change that adds rules rather than
        variables, so it is asserted rather than left as a one-off
        measurement in a decision record.
        """
        compressed = BASE_DIR / "mvp" / "static" / "css" / "django-mvp.css.br"
        size = compressed.stat().st_size

        assert size <= V0_18_0_COMPRESSED_BYTES + SC003_GROWTH_BUDGET_BYTES, (
            f"the compressed stylesheet is {size} bytes, more than "
            f"{SC003_GROWTH_BUDGET_BYTES} above the {V0_18_0_COMPRESSED_BYTES}"
            " byte baseline this feature started from (SC-003)"
        )


# ---------------------------------------------------------------------------
# The shipped stylesheet is linked once, not once per encoding (#227)
# ---------------------------------------------------------------------------


class TestShippedStylesheetLinkedOnce:
    """``base.html`` used to link both ``django-mvp.css.br`` and
    ``django-mvp.css`` unconditionally — two separate downloads of the same
    rules, with the larger uncompressed file arriving second and winning the
    cascade. A host whose static server negotiates brotli on the plain URL
    (whitenoise's precompressed storage, nginx ``brotli_static``, any CDN)
    never needed the explicit ``.br`` link; a host that does not would have
    sent the uncompressed file regardless of whether the ``.br`` link was
    there.
    """

    BASE_HTML = BASE_DIR / "mvp" / "templates" / "mvp" / "base.html"

    def test_the_br_variant_is_not_linked_directly(self):
        source = self.BASE_HTML.read_text(encoding="utf-8")
        assert "django-mvp.css.br" not in source, (
            "mvp/base.html must not link django-mvp.css.br directly — a "
            "server that negotiates brotli on the plain URL already serves "
            "it, and linking both downloads the stylesheet twice (#227)"
        )

    def test_the_stylesheet_is_linked_exactly_once(self):
        source = self.BASE_HTML.read_text(encoding="utf-8")
        count = source.count("django-mvp.css")
        assert count == 1, (
            "mvp/base.html must link the shipped stylesheet exactly once "
            f"(found {count}) — every extra link is a redundant download of "
            "the same rules (#227)"
        )
