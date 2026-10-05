"""
Smoke tests – quick sanity-checks that the package imports cleanly and
the Django configuration is valid.
"""

import re
from pathlib import Path

import pytest

from demo.models import OrderLine

BASE_DIR = Path(__file__).resolve().parent.parent


class TestPackageSanity:
    @pytest.mark.django_db
    def test_mvp_apps_load(self, client):
        response = client.get("/")
        assert response.status_code in {200, 301, 302, 404}

    def test_mvp_imports(self):
        import mvp  # noqa: F401
        from mvp import (
            renderers,  # noqa: F401
            views,  # noqa: F401
        )
        from mvp.templatetags import mvp as mvp_tags  # noqa: F401


class TestStylingDocs:
    def test_styling_doc_exists(self):
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
        readme = BASE_DIR / "README.md"
        content = readme.read_text(encoding="utf-8")
        assert "mvp_tailwind" in content, (
            "README.md must reference 'manage.py mvp_tailwind' so consumers discover "
            "the CSS rebuild path from the top-level documentation."
        )
        assert "docs/styling.md" in content, "README.md must link to docs/styling.md."

    def test_entry_css_imports_packaged_preset(self):
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


class TestShippedStylesheetShipsCompleteDaisyUI:
    STYLESHEET = BASE_DIR / "mvp" / "static" / "css" / "django-mvp.css"

    @staticmethod
    def _class_present(content: str, css_class: str) -> bool:
        return re.search(rf"\.{re.escape(css_class)}\b", content) is not None

    def test_entry_sources_daisyuis_own_component_and_utility_definitions(self):
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
        content = self.STYLESHEET.read_text(encoding="utf-8")
        assert self._class_present(content, "modal-top"), (
            ".modal-top is a component class mvp's own cotton/mvp/modal template "
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
        content = self.STYLESHEET.read_text(encoding="utf-8")
        assert self._class_present(content, css_class), (
            f".{css_class} is missing from the shipped stylesheet — daisyUI "
            "component coverage regressed (#190)."
        )


class TestStylesheetShipsAccountCenterClasses:
    STYLESHEET = BASE_DIR / "mvp" / "static" / "css" / "django-mvp.css"

    @staticmethod
    def _class_present(content: str, css_class: str) -> bool:
        """A responsive class is committed with its colon escaped
        (``lg:flex-row`` -> ``lg\\:flex-row``), so matching the bare class
        name against the built file always finds nothing. The escape has to
        be reproduced here, in the pattern, not just avoided by picking
        classes that happen not to need it."""
        escaped_class = re.escape(css_class.replace(":", "\\:"))
        return re.search(rf"\.{escaped_class}\b", content) is not None

    def test_absent_control_class_is_not_present(self):
        content = self.STYLESHEET.read_text(encoding="utf-8")
        assert not self._class_present(content, "not-a-real-django-mvp-class")

    @pytest.mark.parametrize(
        "css_class",
        [
            "lg:flex-row",
            "lg:items-start",
            "lg:gap-6",
            "sm:grid-cols-2",
            "lg:shrink-0",
        ],
    )
    def test_account_center_template_class_is_present(self, css_class):
        content = self.STYLESHEET.read_text(encoding="utf-8")
        assert self._class_present(content, css_class), (
            f".{css_class} is missing from the shipped stylesheet — rebuild it "
            "with `invoke build-stylesheet` (Article XV)."
        )


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
    STYLESHEET = BASE_DIR / "mvp" / "static" / "css" / "django-mvp.css"

    def test_daisyui_theme_source_is_discoverable(self):
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
        content = self.STYLESHEET.read_text(encoding="utf-8")
        assert f"[data-theme={theme}]" in content, (
            f"[data-theme={theme}] is missing from the shipped stylesheet — "
            "the prebuilt themes must ship inside the package (FR-001)."
        )

    def test_default_theme_still_bound_through_where_root(self):
        content = self.STYLESHEET.read_text(encoding="utf-8")
        assert ":where(:root)" in content, (
            "the :where(:root) fall-through binding for the default theme "
            "is missing from the shipped stylesheet"
        )

    def test_prefers_color_scheme_dark_block_still_emitted(self):
        content = self.STYLESHEET.read_text(encoding="utf-8")
        assert "@media (prefers-color-scheme:dark)" in content, (
            "the @media (prefers-color-scheme: dark) block is missing from "
            "the shipped stylesheet"
        )


class TestProductOrderLinesWorkedExample:
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
    def test_product_field_has_help_text(self):
        field = OrderLine._meta.get_field("product")
        assert str(field.help_text) != ""

    def test_quantity_field_has_help_text(self):
        field = OrderLine._meta.get_field("quantity")
        assert str(field.help_text) != ""


class TestFormsetComponentDocPage:
    @pytest.mark.django_db
    def test_page_renders_a_bound_orderline_formset(self, client):
        response = client.get("/components/formset/")

        assert response.status_code == 200
        content = response.content.decode()
        assert 'name="form-TOTAL_FORMS"' in content


class TestComplexFormDemoPage:
    @pytest.mark.django_db
    def test_page_renders_every_fieldset_and_the_layout(self, client):
        response = client.get("/forms/complex/")

        assert response.status_code == 200
        content = response.content.decode()
        # One legend per Fieldset in the helper's layout.
        assert content.count("<legend") == 3
        # <c-mvp.form> (form_view.html) is the only real <form> wrapping the
        # fields — form_tag=False must stop crispy nesting a second one
        # inside it. x-data="{form: {}}" is <c-mvp.form>'s own signature
        # attribute; the page also carries unrelated chrome forms (the
        # language switcher, a couple of dialogs), so counting every <form>
        # on the page would not isolate this.
        assert content.count('<form x-data="{form: {}}"') == 1

    @pytest.mark.django_db
    def test_valid_submission_redirects_and_flashes_success(self, client):
        response = client.post(
            "/forms/complex/",
            {
                "name": "Jane Doe",
                "email": "jane@example.com",
                "address": "1 Example Street",
                "city": "Springfield",
                "postal_code": "12345",
                "shipping_method": "standard",
            },
        )

        assert response.status_code == 302
        assert response.url == "/forms/complex/"


_CUSTOM_PROPERTY_RE = re.compile(r"--[a-zA-Z0-9-]+")


def _extract_custom_properties(css: str) -> set[str]:
    return set(_CUSTOM_PROPERTY_RE.findall(css))


# SC-003: the compressed stylesheet a project downloads may grow by at most
# 8 KB against the release this feature started from.
V0_18_0_COMPRESSED_BYTES = 41670
SC003_GROWTH_BUDGET_BYTES = 8192


class TestThemingDocVariableCoverage:
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
        for row in self._documented_variable_table():
            cells = [c.strip() for c in row.strip("|").split("|")]
            assert len(cells) >= 2 and cells[1], (
                f"this variable table row has no description: {row}"
            )

    def test_the_compressed_stylesheet_stays_within_its_budget(self):
        compressed = BASE_DIR / "mvp" / "static" / "css" / "django-mvp.css.br"
        size = compressed.stat().st_size

        assert size <= V0_18_0_COMPRESSED_BYTES + SC003_GROWTH_BUDGET_BYTES, (
            f"the compressed stylesheet is {size} bytes, more than "
            f"{SC003_GROWTH_BUDGET_BYTES} above the {V0_18_0_COMPRESSED_BYTES}"
            " byte baseline this feature started from (SC-003)"
        )
