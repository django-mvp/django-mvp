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
        assert '@plugin "daisyui";' in entry, (
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

    @pytest.mark.parametrize(
        "theme",
        ["dracula", "synthwave", "cyberpunk", "retro", "valentine"],
    )
    def test_named_themes_are_not_shipped(self, theme):
        """Shipping every component must not pull in daisyUI's ~30 named themes.

        Only the default light/dark themes ship — daisyUI's own default when
        `@plugin "daisyui"` carries no `themes` option, unrelated to and
        unaffected by the component/utility @source additions this guards.
        """
        content = self.STYLESHEET.read_text(encoding="utf-8")
        assert f"[data-theme={theme}]" not in content, (
            f"[data-theme={theme}] found in the shipped stylesheet — issue #190 "
            "asked for complete components while explicitly excluding themes."
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
