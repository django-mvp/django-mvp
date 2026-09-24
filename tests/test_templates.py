"""The default ``base.html`` django-mvp ships for hosts that do not write one.

``page_view.html`` and everything under it extend the unqualified ``base.html``.
That name is the project's to own, so a project template always wins — but a
reusable app cannot ask its host to write one, and without a fallback the whole
packaged chain raises ``TemplateDoesNotExist``. The package therefore ships a
``base.html`` that forwards to ``mvp/base.html`` and defines nothing of its own.

The first three tests run against a package-only engine, because the test
project (``demo``) ships its own ``base.html`` and shadows the packaged one in
the configured engine — which is what the last test asserts.
"""

import json
import re
from pathlib import Path

import pytest
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.shortcuts import get_current_site
from django.template import Engine, engines
from django.template.loader import get_template, render_to_string
from django.template.loader_tags import BlockNode, ExtendsNode
from django.test import RequestFactory

MVP_TEMPLATES = Path(apps.get_app_config("mvp").path) / "templates"
DEMO_TEMPLATES = Path(apps.get_app_config("demo").path) / "templates"


@pytest.fixture
def package_only_engine():
    """An engine that can see django-mvp's templates and nothing else.

    Stands in for a host that installed django-mvp and wrote no template of
    its own — the case the issue reported.
    """
    configured = engines["django"].engine
    return Engine(
        dirs=[str(MVP_TEMPLATES)],
        app_dirs=False,
        libraries=configured.libraries,
        builtins=configured.builtins,
    )


class TestDefaultBaseTemplate:
    def test_the_package_ships_one(self, package_only_engine):
        assert package_only_engine.get_template("base.html") is not None

    def test_it_forwards_to_the_packaged_shell(self, package_only_engine):
        template = package_only_engine.get_template("base.html")

        extends = [n for n in template.nodelist if isinstance(n, ExtendsNode)]

        assert len(extends) == 1
        assert extends[0].parent_name.var == "mvp/base.html"

    def test_it_defines_nothing_of_its_own(self, package_only_engine):
        """Forwarding only. A block here would silently override the shell's."""
        template = package_only_engine.get_template("base.html")
        extends = next(n for n in template.nodelist if isinstance(n, ExtendsNode))

        assert list(extends.blocks) == []
        assert extends.nodelist.get_nodes_by_type(BlockNode) == []

    def test_the_packaged_page_chain_resolves_without_a_project_template(
        self, package_only_engine
    ):
        """The reported symptom: ``page_view.html`` could not find its parent."""
        for name in (
            "page_view.html",
            "list_view.html",
            "detail_view.html",
            "form_view.html",
            "delete_view.html",
            "table_view.html",
        ):
            template = package_only_engine.get_template(name)
            extends = next(n for n in template.nodelist if isinstance(n, ExtendsNode))

            assert package_only_engine.get_template(extends.parent_name.var)

    def test_an_app_listed_above_mvp_still_wins(self):
        """The override rule getting-started documents, exercised for real.

        ``demo`` ships its own ``base.html`` and sits above ``mvp`` in
        ``INSTALLED_APPS``, so the app template loader reaches it first.
        """
        installed = settings.INSTALLED_APPS
        assert installed.index("demo") < installed.index("mvp")

        origin = get_template("base.html").origin.name

        assert MVP_TEMPLATES not in Path(origin).parents
        assert Path(origin).parts[-3:] == ("demo", "templates", "base.html")


class TestShowCodeTemplate:
    """``{% show_code %}`` (``mvp/templatetags/mvp.py``) renders through
    ``cotton/documentation.html`` — a host that installs django-mvp and writes
    no template of its own must still be able to resolve it (issue #379).
    """

    def test_the_package_ships_the_template_the_tag_renders(self, package_only_engine):
        assert package_only_engine.get_template("cotton/documentation.html") is not None


def _template_files():
    """Every .html template this repository owns, packaged and demo alike."""
    return [path for root in (MVP_TEMPLATES, DEMO_TEMPLATES) for path in sorted(root.rglob("*.html"))]


def multiline_brace_comments(source):
    """Line numbers of every ``{# ... #}`` in ``source`` that spans a newline.

    An unterminated ``{#`` counts too: it swallows the rest of the file the
    same way, and there is no reading of it that is correct.
    """
    found = []
    for match in re.finditer(r"\{#", source):
        start = match.start()
        end = source.find("#}", start)
        comment = source[start:] if end == -1 else source[start : end + 2]
        if "\n" in comment:
            found.append(source.count("\n", 0, start) + 1)
    return found


class TestTemplateComments:
    """``{# ... #}`` is single-line only, and a multiline one renders as text.

    Django's lexer tokenises comments with ``{#.*?#}`` compiled without
    ``re.DOTALL`` (``django/template/base.py``), so ``.`` never matches the
    newline. A comment written across two lines is therefore not recognised as
    a comment at all — it is emitted verbatim into the response and the reader
    sees the note in the page. There is no error and no warning, which is why
    three of them reached the shipped templates before anyone noticed.

    Multi-line notes go in ``{% comment %} ... {% endcomment %}``, which is a
    real tag pair and spans lines safely.
    """

    def test_the_lexer_really_does_leak_a_multiline_comment(self):
        """The defect itself, pinned so this suite explains why it exists."""
        rendered = engines["django"].from_string("A{# one\ntwo #}B").render({})

        assert rendered == "A{# one\ntwo #}B"

        single_line = engines["django"].from_string("A{# one #}B").render({})

        assert single_line == "AB"

    @pytest.mark.parametrize("path", _template_files(), ids=lambda p: p.name)
    def test_no_template_has_a_multiline_brace_comment(self, path):
        lines = multiline_brace_comments(path.read_text(encoding="utf-8"))

        assert not lines, (
            f"{path} has a {{# ... #}} comment spanning lines "
            f"{lines} — it will render as visible text. "
            "Use {% comment %} ... {% endcomment %} instead."
        )


BASE_HEAD_FIXTURE = Path(__file__).parent / "fixtures" / "base_head_off.html"


def render_shell_head(script_name=""):
    """Render the ``<head>`` of a shell page for a fixed anonymous request."""
    request = RequestFactory().get("/", HTTP_HOST="testserver", SCRIPT_NAME=script_name)
    request.user = AnonymousUser()
    request.site = get_current_site(request)
    page = render_to_string("mvp/base.html", request=request)
    return page[page.index("<head>") : page.index("</head>") + len("</head>")]


@pytest.mark.django_db
class TestShellHeadWithInstallableAppOff:
    def test_head_matches_the_pinned_render_byte_for_byte(self):
        """The head of a shell page is unchanged when ``pwa`` is off.

        ``tests/fixtures/base_head_off.html`` is the ``<head>`` rendered by
        ``mvp/base.html`` for an anonymous ``GET /`` on host ``testserver``
        with the test settings and the default site. After a deliberate change
        to the head, regenerate it by writing ``render_shell_head()``'s return
        value to that file (as UTF-8, no trailing newline) and review the diff.
        """
        assert render_shell_head() == BASE_HEAD_FIXTURE.read_text(encoding="utf-8")


def head_soup():
    from bs4 import BeautifulSoup

    return BeautifulSoup(render_shell_head(), "html.parser")


@pytest.fixture
def installable_app_on(monkeypatch):
    from mvp.config import MVP_CONFIG

    monkeypatch.setitem(MVP_CONFIG, "pwa", True)


@pytest.mark.django_db
@pytest.mark.usefixtures("installable_app_on")
class TestShellHeadWithInstallableAppOn:
    @pytest.fixture(autouse=True)
    def urls_mounted(self, settings):
        settings.ROOT_URLCONF = "tests.urls_shell_pwa"

    def test_it_links_the_manifest(self):
        link = head_soup().find("link", rel="manifest")

        assert link["href"] == "/account/manifest.webmanifest"

    def test_it_sets_no_theme_colour_when_none_is_configured(self):
        assert head_soup().find("meta", attrs={"name": "theme-color"}) is None

    def test_it_links_the_apple_touch_icon(self):
        link = head_soup().find("link", rel="apple-touch-icon")

        assert link["href"] == "/static/brand/pwa/apple-touch-icon.png"

    def test_the_apple_title_carries_the_short_name(self, monkeypatch):
        from mvp.config import MVP_CONFIG

        monkeypatch.setitem(MVP_CONFIG, "short_name", "Shop")
        monkeypatch.setitem(MVP_CONFIG, "site_name", "The Corner Shop")

        meta = head_soup().find("meta", attrs={"name": "apple-mobile-web-app-title"})

        assert meta["content"] == "Shop"

    def test_it_marks_the_page_as_a_web_app(self):
        meta = head_soup().find("meta", attrs={"name": "mobile-web-app-capable"})

        assert meta["content"] == "yes"

    def test_it_registers_the_worker_by_its_reversed_url(self):
        soup = head_soup()

        data = soup.find("script", id="mvp-pwa-worker-url")
        registration = [
            script.string
            for script in soup.find_all("script")
            if script.string and "serviceWorker.register" in script.string
        ]

        assert json.loads(data.string) == "/account/sw.js"
        assert len(registration) == 1

    def test_it_registers_the_worker_with_the_site_root_as_its_scope(self):
        data = head_soup().find("script", id="mvp-pwa-worker-scope")

        assert json.loads(data.string) == "/"
        assert "{scope:" in "".join(
            script.string for script in head_soup().find_all("script") if script.string
        ).replace(" ", "")

    def test_the_scope_follows_the_script_prefix(self):
        from bs4 import BeautifulSoup
        from django.urls import set_script_prefix

        set_script_prefix("/app/")
        try:
            head = render_shell_head(script_name="/app")
        finally:
            set_script_prefix("/")
        soup = BeautifulSoup(head, "html.parser")

        assert json.loads(soup.find("script", id="mvp-pwa-worker-scope").string) == "/app/"
        assert json.loads(soup.find("script", id="mvp-pwa-worker-url").string) == (
            "/app/account/sw.js"
        )

    def test_the_apple_title_is_the_site_name_without_a_configured_name(self):
        meta = head_soup().find("meta", attrs={"name": "apple-mobile-web-app-title"})

        assert meta["content"] == "example.com"

    def test_the_apple_title_is_the_configured_site_name_without_a_short_name(
        self, monkeypatch
    ):
        from mvp.config import MVP_CONFIG

        monkeypatch.setitem(MVP_CONFIG, "site_name", "The Corner Shop")

        meta = head_soup().find("meta", attrs={"name": "apple-mobile-web-app-title"})

        assert meta["content"] == "The Corner Shop"

    def test_the_apple_title_is_the_host_when_the_site_has_no_name(self):
        from django.contrib.sites.models import Site

        Site.objects.filter(pk=settings.SITE_ID).update(name="")
        Site.objects.clear_cache()

        meta = head_soup().find("meta", attrs={"name": "apple-mobile-web-app-title"})

        assert meta["content"] == "testserver"

    def test_it_sets_the_theme_colour_when_one_is_configured(self, monkeypatch):
        from mvp.config import MVP_CONFIG

        monkeypatch.setitem(MVP_CONFIG, "pwa", {"theme_color": "#123456"})

        meta = head_soup().find("meta", attrs={"name": "theme-color"})

        assert meta["content"] == "#123456"

    def test_a_hostile_name_stays_escaped(self):
        from django.contrib.sites.models import Site

        name = 'A "b" </script><img src=x onerror=alert(1)>'
        Site.objects.filter(pk=settings.SITE_ID).update(name=name)
        head = render_shell_head()
        soup = head_soup()

        title = soup.find("meta", attrs={"name": "apple-mobile-web-app-title"})

        assert title["content"] == name
        assert "<img src=x" not in head

    def test_it_adds_no_url_to_another_host(self):
        from bs4 import BeautifulSoup

        on = head_soup()
        off = BeautifulSoup(
            BASE_HEAD_FIXTURE.read_text(encoding="utf-8"), "html.parser"
        )

        def urls(soup):
            tags = soup.find_all(["link", "script"])
            return {t.get("href") or t.get("src") for t in tags} - {None}

        assert all(url.startswith("/") for url in urls(on) - urls(off))


@pytest.mark.django_db
@pytest.mark.usefixtures("installable_app_on")
class TestShellHeadWithoutMvpUrls:
    @pytest.fixture(autouse=True)
    def urls_unmounted(self, settings):
        settings.ROOT_URLCONF = "tests.urls_shell_no_pwa"

    def test_the_page_renders_without_a_manifest_or_registration(self):
        head = render_shell_head()
        soup = head_soup()

        assert soup.find("link", rel="manifest") is None
        assert "serviceWorker" not in head


@pytest.mark.django_db
@pytest.mark.usefixtures("installable_app_on")
class TestShellHeadWithConfiguredValues:
    @pytest.fixture(autouse=True)
    def urls_mounted(self, settings):
        settings.ROOT_URLCONF = "tests.urls_shell_pwa"

    def test_configured_colour_reaches_the_theme_colour_meta_tag(self, monkeypatch):
        from mvp.config import MVP_CONFIG

        monkeypatch.setitem(MVP_CONFIG, "pwa", {"theme_color": "#123456"})

        meta = head_soup().find("meta", attrs={"name": "theme-color"})

        assert meta["content"] == "#123456"

    def test_a_project_head_template_replaces_the_packaged_one(self, settings):
        project_templates = Path(__file__).parent / "pwa_templates"
        engine = settings.TEMPLATES[0]
        settings.TEMPLATES = [
            {**engine, "DIRS": [str(project_templates), *engine.get("DIRS", [])]}
        ]

        soup = head_soup()

        assert soup.find("meta", attrs={"name": "project-head"})["content"] == "mine"
        assert soup.find("link", rel="manifest") is None


@pytest.mark.django_db
class TestShellTitle:
    def title(self):
        from bs4 import BeautifulSoup

        return " ".join(BeautifulSoup(render_shell_head(), "html.parser").title.text.split())

    def test_the_suffix_is_the_site_name_by_default(self):
        assert self.title() == "| example.com"

    def test_the_suffix_is_the_configured_site_name(self, monkeypatch):
        from mvp.config import MVP_CONFIG

        monkeypatch.setitem(MVP_CONFIG, "site_name", "The Corner Shop")

        assert self.title() == "| The Corner Shop"
