"""The base email template, and a sender that is not django-mvp's using it (FS-044).

The base template is a template, not a Python module, so there is nothing for
this module to mirror.
"""

import pytest
from bs4 import BeautifulSoup
from django.contrib.sites.models import Site
from django.template import Context, Template
from django_cotton.compiler_regex import CottonCompiler

from mvp.config import MVP_CONFIG
from mvp.email.brand import EmailBrand

compiler = CottonCompiler()

CHILD = """{% extends "mvp/email/base.html" %}
{% block preheader %}PREHEADER-MARKER{% endblock %}
{% block body %}
<h1>Heading</h1>
<p>Paragraph with a <a href="https://example.org/x">link</a>.</p>
<ul><li>One</li><li>Two</li></ul>
BODY-MARKER
{% endblock %}
"""


def render(source, **context):
    """Render ``source`` as a template with no request, unless the context holds one."""
    return Template(compiler.process(source)).render(Context(context))


def soup_of(source, **context):
    """Render ``source`` and parse the HTML."""
    return BeautifulSoup(render(source, **context), "html.parser")


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


class TestBaseTemplate:
    def test_plain_markup_in_the_body_is_styled_inline(self, site):
        soup = soup_of(CHILD)

        for tag in ("h1", "p", "ul", "li"):
            assert soup.find(tag).get("style"), tag
        assert soup.find("a", href="https://example.org/x").get("style")

    def test_a_body_link_takes_the_brands_text_colour(self, site):
        link = soup_of(CHILD).find("a", href="https://example.org/x")

        assert EmailBrand.current().light.text in link["style"]

    def test_the_dark_scheme_and_narrow_width_rules_stay_in_the_style_block(self, site):
        html = render(CHILD)

        assert "@media (prefers-color-scheme: dark)" in html
        assert "@media (max-width" in html
        assert EmailBrand.current().dark.surface in html

    def test_the_style_block_holds_only_the_rules_that_could_not_be_inlined(self, site):
        styles = soup_of(CHILD).find_all("style")

        assert styles
        for style in styles:
            assert style.string.strip().startswith("@media")

    def test_the_logo_is_an_absolute_address_named_for_the_site(self, site):
        logo = soup_of(CHILD).find("img")

        assert logo["src"] == f"https://mail.example.com{EmailBrand.current().logo}"
        assert logo["alt"] == "Acme Mail"

    def test_the_dark_logo_is_in_the_message_too(self, site):
        sources = [img["src"] for img in soup_of(CHILD).find_all("img")]

        assert f"https://mail.example.com{EmailBrand.current().logo_dark}" in sources

    def test_the_configured_site_name_names_the_logo(self, site, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG, "site_name", "Configured Name")

        assert soup_of(CHILD).find("img")["alt"] == "Configured Name"

    def test_the_default_footer_follows_the_body_and_names_the_site(self, site):
        html = render(CHILD)
        footer = html[html.index("BODY-MARKER") :]

        assert "Acme Mail" in footer
        assert 'href="https://mail.example.com/"' in footer

    def test_a_filled_footer_replaces_the_default(self, site):
        filled = CHILD.replace(
            "{% endblock %}\n",
            "{% endblock %}\n{% block footer %}FOOTER-MARKER{% endblock %}\n",
            1,
        )
        html = render(filled)

        assert "FOOTER-MARKER" in html
        assert html.index("BODY-MARKER") < html.index("FOOTER-MARKER")
        assert "Acme Mail" not in html[html.index("BODY-MARKER") :]

    def test_a_filled_preheader_appears(self, site):
        assert "PREHEADER-MARKER" in render(CHILD)

    def test_a_template_with_a_request_in_its_context_uses_the_requests_host(self, site, rf):
        request = rf.get("/", HTTP_HOST="request.example.org")

        logo = soup_of(CHILD, request=request).find("img")

        assert logo["src"].startswith("http://request.example.org/")

    def test_it_renders_with_nothing_in_the_context_but_the_sites_framework(self, site):
        assert "BODY-MARKER" in render(CHILD)
