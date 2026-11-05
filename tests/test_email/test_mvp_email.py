"""Tests for mvp.templatetags.mvp_email: the site's address and name inside an email (FS-044).

The tags' module cannot be mirrored as ``tests/test_templatetags/`` because
``tests/test_templatetags.py`` already holds that name, so these tests sit with
the other email tests.
"""

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured
from django.template import Context, Template
from django.urls import NoReverseMatch, path

from mvp.config import MVP_CONFIG
from mvp.email.brand import EmailBrand
from tests.conftest import urlconf_of

ITEMS = urlconf_of(path("items/<int:pk>/", lambda request, pk: None, name="item"))


def render(source, request=None, **context):
    """Render ``source`` with ``{% load mvp_email %}`` in front of it."""
    if request is not None:
        context["request"] = request
    return Template("{% load mvp_email %}" + source).render(Context(context))


@pytest.fixture(autouse=True)
def fresh_brand():
    """Read the brand afresh for each test."""
    EmailBrand.current.cache_clear()
    yield
    EmailBrand.current.cache_clear()


@pytest.fixture
def request_on_mail_host(rf):
    """A request to ``mail.example.org``, a host that is not the current Site's."""
    return rf.get("/somewhere/", HTTP_HOST="mail.example.org")


@pytest.fixture
def site(db):
    """The current Site, ready to be changed, with the Site cache emptied around the test."""
    Site.objects.clear_cache()
    current = Site.objects.get_current()
    yield current
    Site.objects.clear_cache()


def set_site(site, **fields):
    """Change the current Site and forget the cached copy."""
    Site.objects.filter(pk=site.pk).update(**fields)
    Site.objects.clear_cache()


@pytest.fixture
def stylesheet_server():
    """The address of a local server that answers with ``p{margin:0}``."""

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/css")
            self.end_headers()
            self.wfile.write(b"p{margin:0}")

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}/style.css"
    server.shutdown()
    server.server_close()


class TestEmailUrl:
    def test_a_path_is_absolute_on_the_requests_host(self, request_on_mail_host):
        assert render("{% email_url '/a/' %}", request_on_mail_host) == "http://mail.example.org/a/"

    def test_a_path_is_absolute_on_the_current_site_over_https_without_a_request(self, site):
        set_site(site, domain="mail.example.com")

        assert render("{% email_url '/a/' %}") == "https://mail.example.com/a/"

    def test_the_current_site_is_addressed_over_http_while_debug_is_on(self, site, settings):
        settings.DEBUG = True
        set_site(site, domain="mail.example.com")

        assert render("{% email_url '/a/' %}") == "http://mail.example.com/a/"

    def test_a_path_from_a_variable_is_made_absolute(self, request_on_mail_host):
        output = render("{% email_url target %}", request_on_mail_host, target="/items/3/")

        assert output == "http://mail.example.org/items/3/"

    @pytest.mark.urls(ITEMS)
    def test_a_url_name_with_arguments_reverses_like_the_url_tag(self, request_on_mail_host):
        output = render("{% email_url 'item' 7 %}|{% email_url 'item' pk=7 %}|{% url 'item' 7 %}", request_on_mail_host)

        assert output == "http://mail.example.org/items/7/|http://mail.example.org/items/7/|/items/7/"

    @pytest.mark.urls(ITEMS)
    def test_a_url_name_that_does_not_reverse_raises_like_the_url_tag(self, request_on_mail_host):
        with pytest.raises(NoReverseMatch):
            render("{% email_url 'no-such-name' %}", request_on_mail_host)

    def test_an_address_on_another_site_is_returned_unchanged(self, request_on_mail_host):
        output = render("{% email_url 'https://other.example/x?y=1' %}", request_on_mail_host)

        assert output == "https://other.example/x?y=1"

    def test_an_absolute_address_needs_neither_a_request_nor_a_site(self):
        assert render("{% email_url 'https://other.example/x' %}") == "https://other.example/x"

    def test_the_result_can_be_kept_in_a_variable(self, request_on_mail_host):
        output = render("{% email_url '/a/' as link %}{{ link }}", request_on_mail_host)

        assert output == "http://mail.example.org/a/"


class TestSiteAddressFailures:
    """Without a request the address comes from the Site, and says so when it cannot."""

    @staticmethod
    def assert_names_the_sites_framework_and_site_id():
        with pytest.raises(ImproperlyConfigured) as error:
            render("{% email_url '/a/' %}")
        assert "django.contrib.sites" in str(error.value)
        assert "SITE_ID" in str(error.value)

    def test_sites_not_installed(self, settings):
        settings.INSTALLED_APPS = [app for app in settings.INSTALLED_APPS if app != "django.contrib.sites"]

        self.assert_names_the_sites_framework_and_site_id()

    def test_no_site_matches_site_id(self, site, settings):
        settings.SITE_ID = site.pk + 1000

        self.assert_names_the_sites_framework_and_site_id()

    def test_the_site_has_no_domain(self, site):
        set_site(site, domain="")

        self.assert_names_the_sites_framework_and_site_id()

    def test_a_request_makes_the_site_irrelevant(self, request_on_mail_host, settings):
        settings.SITE_ID = 99999

        assert render("{% email_url '/a/' %}", request_on_mail_host) == "http://mail.example.org/a/"


class TestEmailSiteName:
    def test_the_configured_site_name_is_used(self, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG, "site_name", "Acme Portal")

        assert render("{% email_site_name %}") == "Acme Portal"

    def test_the_site_name_is_the_current_sites_when_none_is_configured(self, site, monkeypatch, request_on_mail_host):
        monkeypatch.setitem(MVP_CONFIG, "site_name", None)
        set_site(site, name="Shop")

        assert render("{% email_site_name %}", request_on_mail_host) == "Shop"

    def test_the_site_name_is_found_without_a_request(self, site, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG, "site_name", None)
        set_site(site, name="Shop")

        assert render("{% email_site_name %}") == "Shop"

    def test_the_site_name_is_escaped(self, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG, "site_name", "Tom & <Jerry>")

        assert render("{% email_site_name %}") == "Tom &amp; &lt;Jerry&gt;"

    def test_no_name_can_be_found_without_a_request_or_a_site(self, site, monkeypatch, settings):
        monkeypatch.setitem(MVP_CONFIG, "site_name", None)
        settings.SITE_ID = site.pk + 1000

        with pytest.raises(ImproperlyConfigured) as error:
            render("{% email_site_name %}")

        assert "SITE_ID" in str(error.value)


class TestEmailBrandTag:
    def test_the_palettes_are_put_in_the_context(self, request_on_mail_host):
        brand = EmailBrand.current()

        output = render("{% email_brand as brand %}{{ brand.light.surface }}|{{ brand.dark.surface }}", request_on_mail_host)

        assert output == f"{brand.light.surface}|{brand.dark.surface}"

    def test_the_logos_are_absolute_on_the_requests_host(self, request_on_mail_host):
        brand = EmailBrand.current()

        output = render("{% email_brand as brand %}{{ brand.logo }}|{{ brand.logo_dark }}", request_on_mail_host)

        assert output == f"http://mail.example.org{brand.logo}|http://mail.example.org{brand.logo_dark}"

    def test_a_logo_that_is_already_absolute_is_left_as_it_is(self, request_on_mail_host, settings):
        settings.STATIC_URL = "https://cdn.example/static/"

        output = render("{% email_brand as brand %}{{ brand.logo }}", request_on_mail_host)

        assert output == "https://cdn.example/static/brand/email/logo.png"

    def test_no_dark_logo_stays_none(self, request_on_mail_host, tmp_path, settings, monkeypatch):
        (tmp_path / "css").mkdir()
        (tmp_path / "css" / "project.css").write_text(
            "[data-theme=brandx]{--color-base-100:#111111;--color-base-200:#222222;--color-base-300:#333333;"
            "--color-base-content:#eeeeee;--color-primary:#ff8800;--color-primary-content:#000000}"
        )
        settings.STATICFILES_DIRS = [tmp_path]
        settings.STATICFILES_FINDERS = ["django.contrib.staticfiles.finders.FileSystemFinder"]
        monkeypatch.setitem(MVP_CONFIG["theme"], "default", "brandx")
        monkeypatch.setitem(MVP_CONFIG["theme"], "dark", "brandx")

        output = render("{% email_brand as brand %}{{ brand.logo_dark|default:'none' }}", request_on_mail_host)

        assert output == "none"


class TestEmailInline:
    def test_styles_are_inlined_onto_the_markup_they_match(self):
        output = render("{% email_inline %}<style>p{margin:0}</style><p>x</p>{% endemail_inline %}")

        assert "<p style=" in output
        assert "margin" in output.split("<p style=")[1].split(">")[0]

    def test_rules_in_the_style_block_are_taken_out_of_it(self):
        output = render("{% email_inline %}<style>p{margin:0}</style><p>x</p>{% endemail_inline %}")

        assert "p{margin:0}" not in output.replace(" ", "")

    def test_at_rules_survive_in_the_style_block(self):
        output = render(
            "{% email_inline %}<style>p{margin:0} @media (prefers-color-scheme: dark){p{color:#fff !important}}</style><p>x</p>{% endemail_inline %}"
        )

        assert "@media (prefers-color-scheme: dark)" in output
        assert "color:#fff!important" in output.replace(" ", "")

    def test_a_linked_stylesheet_is_not_fetched(self, stylesheet_server):
        output = render(f'{{% email_inline %}}<link rel="stylesheet" href="{stylesheet_server}"><p>x</p>{{% endemail_inline %}}')

        assert "<p>x</p>" in output

    def test_what_the_contents_render_is_inlined(self):
        output = render(
            "{% email_inline %}<style>p{margin:0}</style>{% for word in words %}<p>{{ word }}</p>{% endfor %}{% endemail_inline %}",
            words=["a", "b"],
        )

        assert output.count("<p style=") == 2
