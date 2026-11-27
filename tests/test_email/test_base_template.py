"""The base email template, and a sender that is not django-mvp's using it (FS-044).

The base template is a template, not a Python module, so there is nothing for
this module to mirror.
"""

from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from django.contrib.sites.models import Site
from django.core import mail
from django.template import Context, Template
from django_cotton.compiler_regex import CottonCompiler

from mvp.config import MVP_CONFIG
from mvp.email.brand import EmailBrand
from tests.testapp_email.mailer import ConfirmationMailer

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


_RENDERED = {}


@pytest.fixture
def child_html(site):
    """The child template rendered once for the module: most tests only read it."""
    if "child" not in _RENDERED:
        _RENDERED["child"] = render(CHILD)
    return _RENDERED["child"]


class TestBaseTemplate:
    def test_plain_markup_in_the_body_is_styled_inline(self, child_html):
        soup = BeautifulSoup(child_html, "html.parser")

        for tag in ("h1", "p", "ul", "li"):
            assert soup.find(tag).get("style"), tag
        assert soup.find("a", href="https://example.org/x").get("style")

    def test_a_body_link_takes_the_brands_text_colour(self, child_html):
        link = BeautifulSoup(child_html, "html.parser").find(
            "a", href="https://example.org/x"
        )

        assert EmailBrand.current().light.text in link["style"]

    def test_the_logo_is_an_absolute_address_named_for_the_site(self, child_html):
        logo = BeautifulSoup(child_html, "html.parser").find("img")

        assert logo["src"] == f"https://mail.example.com{EmailBrand.current().logo}"
        assert logo["alt"] == "Acme Mail"

    def test_the_configured_site_name_names_the_logo(self, site, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG, "site_name", "Configured Name")

        assert soup_of(CHILD).find("img")["alt"] == "Configured Name"

    def test_the_default_footer_follows_the_body_and_names_the_site(self, child_html):
        footer = child_html[child_html.index("BODY-MARKER") :]

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

    def test_a_filled_preheader_appears(self, child_html):
        assert "PREHEADER-MARKER" in child_html


@pytest.fixture
def project_overrides(settings):
    """A project directory that overrides the sender's HTML template, ahead of the app's own."""
    overrides = Path(__file__).parent.parent / "testapp_email" / "project_templates"
    settings.TEMPLATES = [{**settings.TEMPLATES[0], "DIRS": [overrides]}]


class TestThirdPartySender:
    """A sender written without django-mvp carries the brand once its HTML template is overridden."""

    URL = "https://shop.example.com/confirm/abc/"

    def send(self, request=None):
        ConfirmationMailer(request).send_confirmation_mail(
            "ada@example.org", "Ada", self.URL
        )
        return mail.outbox[0]

    @staticmethod
    def html_of(message):
        ((html, mimetype),) = message.alternatives
        assert mimetype == "text/html"
        return BeautifulSoup(html, "html.parser")

    def test_the_overridden_html_carries_the_logo_site_name_and_inline_styles(
        self, site, project_overrides
    ):
        soup = self.html_of(self.send())
        logo = soup.find("img")

        assert logo["src"] == f"https://mail.example.com{EmailBrand.current().logo}"
        assert logo["alt"] == "Acme Mail"
        assert soup.find("h1").get("style")

    def test_the_overridden_html_follows_the_request_when_the_sender_passes_one(
        self, site, project_overrides, rf
    ):
        request = rf.get("/", HTTP_HOST="request.example.org")

        logo = self.html_of(self.send(request)).find("img")

        assert logo["src"].startswith("http://request.example.org/")

    def test_without_the_override_the_apps_html_carries_no_brand(self, site):
        soup = self.html_of(self.send())

        assert soup.find("img") is None
        assert soup.find("a", href=self.URL)
