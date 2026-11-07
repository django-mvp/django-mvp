"""A project replaces the email base template and each piece by writing a template at the same path (FS-044)."""

import pytest
from bs4 import BeautifulSoup
from django.template import Context, Template
from django.test import RequestFactory
from django_cotton.compiler_regex import CottonCompiler

from mvp.config import MVP_CONFIG

compiler = CottonCompiler()

CHILD = """{% extends "mvp/email/base.html" %}
{% block body %}<p>Hello</p><c-mvp.email.button href="https://example.org/go" text="Go" />{% endblock %}
"""


@pytest.fixture
def project_templates(tmp_path, settings, monkeypatch):
    """A project template directory searched before the packages', and a function writing templates into it."""
    monkeypatch.setitem(MVP_CONFIG, "site_name", "Acme")
    settings.TEMPLATES = [{**settings.TEMPLATES[0], "DIRS": [tmp_path]}]

    def write(name, text):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    return write


def render(source):
    """Render ``source`` as a template with a request."""
    request = RequestFactory().get("/")
    return Template(compiler.process(source)).render(Context({"request": request}))


class TestEmailTemplateOverrides:
    def test_a_project_base_template_replaces_the_packages(self, project_templates):
        project_templates("mvp/email/base.html", "<main>PROJECT-BASE{% block body %}{% endblock %}</main>")

        html = render(CHILD)

        assert "PROJECT-BASE" in html
        assert "<p>Hello</p>" in html
        assert "mvp-email-card" not in html

    def test_without_an_override_the_packages_base_template_is_used(self, project_templates):
        assert "mvp-email-card" in render(CHILD)

    def test_a_project_piece_replaces_the_packages(self, project_templates):
        project_templates(
            "cotton/mvp/email/button.html",
            '<c-vars href text /><a class="project-button" href="{{ href }}">{{ text }}</a>',
        )

        soup = BeautifulSoup(render(CHILD), "html.parser")

        button = soup.find("a", class_="project-button")
        assert button["href"] == "https://example.org/go"
        assert button.get_text() == "Go"
        assert soup.find("td", class_="mvp-email-button") is None

    def test_without_an_override_the_packages_piece_is_used(self, project_templates):
        soup = BeautifulSoup(render(CHILD), "html.parser")

        assert soup.find("td", class_="mvp-email-button") is not None
