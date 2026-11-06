"""What a person reading the email in a mail client relies on (FS-044).

The base template is a template, not a Python module, so there is nothing for
this module to mirror. Each test reads the rendered HTML for a behaviour mail
clients depend on: a message that reads with images blocked, the dark scheme,
the phone width, and colours Outlook honours.
"""

import re

import pytest
from bs4 import BeautifulSoup
from django.contrib.sites.models import Site
from django.template import Context, Template
from django_cotton.compiler_regex import CottonCompiler

from mvp.config import MVP_CONFIG
from mvp.email import brand as brand_module
from mvp.email.brand import LOGO_DARK, EmailBrand

compiler = CottonCompiler()

CHILD = """{% extends "mvp/email/base.html" %}
{% block body %}
<h1>Heading</h1>
<p>BODY-MARKER</p>
<c-mvp.email.button href="https://example.org/go" text="Go" />
{% endblock %}
"""

DARK_SCHEME = "@media (prefers-color-scheme: dark)"


def render():
    """Render the child template with no request in the context."""
    return Template(compiler.process(CHILD)).render(Context())


def block_of(html, at_rule):
    """Return the text of the style-block rule that opens with ``at_rule``."""
    start = html.index(at_rule)
    return html[start : html.index("\n    }", start)]


@pytest.fixture(autouse=True)
def fresh_brand():
    """Read the brand afresh for each test."""
    EmailBrand.current.cache_clear()
    yield
    EmailBrand.current.cache_clear()


@pytest.fixture
def site(db, monkeypatch):
    """The current Site, named and addressed, with no configured site name."""
    monkeypatch.setitem(MVP_CONFIG, "site_name", None)
    Site.objects.clear_cache()
    Site.objects.filter(pk=1).update(domain="mail.example.com", name="Acme Mail")
    Site.objects.clear_cache()
    yield Site.objects.get_current()
    Site.objects.clear_cache()


@pytest.fixture
def no_dark_logo(monkeypatch):
    """Make the static finders find no dark logo file."""
    find = brand_module.finders.find
    monkeypatch.setattr(
        brand_module.finders,
        "find",
        lambda path, *args, **kwargs: (
            None if path == LOGO_DARK else find(path, *args, **kwargs)
        ),
    )


class TestImagesBlocked:
    def test_every_image_is_named_for_the_site(self, site):
        images = BeautifulSoup(render(), "html.parser").find_all("img")

        assert images
        assert {img.get("alt") for img in images} == {"Acme Mail"}

    def test_the_message_reads_without_its_images(self, site):
        soup = BeautifulSoup(render(), "html.parser")
        for image in soup.find_all("img"):
            image.decompose()
        text = soup.get_text(" ", strip=True)

        assert "BODY-MARKER" in text
        assert "Heading" in text
        assert "Go" in text
        assert "Acme Mail" in text

    def test_no_colour_or_shape_is_drawn_by_an_image(self, site):
        html = render()

        assert "background-image" not in html
        assert "url(" not in html
        assert not re.search(r"background=[\"']", html)


class TestDarkScheme:
    def test_the_dark_rules_carry_the_dark_palette(self, site):
        dark = block_of(render(), DARK_SCHEME)
        palette = EmailBrand.current().dark

        for colour in (
            palette.page,
            palette.surface,
            palette.border,
            palette.text,
            palette.muted,
            palette.primary,
            palette.primary_content,
        ):
            assert colour in dark

    def test_the_dark_rules_do_not_carry_a_light_only_colour(self, site):
        brand = EmailBrand.current()
        dark = block_of(render(), DARK_SCHEME)

        for colour in set(vars(brand.light).values()) - set(vars(brand.dark).values()):
            assert colour not in dark

    def test_a_dark_logo_is_shown_when_the_brand_has_one(self, site):
        brand = EmailBrand.current()
        html = render()
        sources = [
            img["src"] for img in BeautifulSoup(html, "html.parser").find_all("img")
        ]

        assert brand.logo_dark
        assert sources == [
            f"https://mail.example.com{brand.logo}",
            f"https://mail.example.com{brand.logo_dark}",
        ]
        assert "display: block !important" in block_of(html, DARK_SCHEME)

    def test_the_dark_logo_is_hidden_until_the_dark_scheme(self, site):
        soup = BeautifulSoup(render(), "html.parser")
        light, dark = soup.find_all("img")

        assert "display: none" not in light["style"]
        assert "display: none" in dark["style"]

    def test_there_is_no_dark_logo_element_when_the_brand_has_none(
        self, site, no_dark_logo
    ):
        html = render()
        sources = [
            img["src"] for img in BeautifulSoup(html, "html.parser").find_all("img")
        ]

        assert EmailBrand.current().logo_dark is None
        assert sources == [f"https://mail.example.com{EmailBrand.current().logo}"]
        assert "logo_dark" not in html
        assert "display: none !important" not in block_of(html, DARK_SCHEME)


class TestNarrowScreen:
    def test_a_narrow_width_rule_is_present(self, site):
        html = render()

        assert re.search(r"@media \(max-width: \d+px\)", html)
        assert "width: 100% !important" in block_of(html, "@media (max-width")


class TestOutlookColours:
    @staticmethod
    def cell_colours(html):
        """Collect the background colours table cells carry, as attribute or inline style."""
        colours = set()
        for cell in BeautifulSoup(html, "html.parser").find_all("td"):
            if cell.get("bgcolor"):
                colours.add(cell["bgcolor"].lower())
            match = re.search(
                r"background-color:\s*(#[0-9a-fA-F]{3,8})", cell.get("style", "")
            )
            if match:
                colours.add(match.group(1).lower())
        return colours

    @pytest.mark.parametrize("colour", ["page", "surface", "primary"])
    def test_the_palette_colour_is_on_a_table_cell(self, site, colour):
        expected = getattr(EmailBrand.current().light, colour).lower()

        assert expected in self.cell_colours(render())
