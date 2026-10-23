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
from bs4 import BeautifulSoup
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.shortcuts import get_current_site
from django.template import Context, Engine, engines
from django.template.loader import get_template, render_to_string
from django.template.loader_tags import BlockNode, ExtendsNode
from django.test import RequestFactory, override_settings

from demo import urls as demo_urls
from tests.conftest import urlconf_of
from tests.factories import CategoryFactory, ProductFactory

MVP_TEMPLATES = Path(apps.get_app_config("mvp").path) / "templates"
DEMO_TEMPLATES = Path(apps.get_app_config("demo").path) / "templates"


@pytest.fixture
def package_only_engine():
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
        template = package_only_engine.get_template("base.html")
        extends = next(n for n in template.nodelist if isinstance(n, ExtendsNode))

        assert list(extends.blocks) == []
        assert extends.nodelist.get_nodes_by_type(BlockNode) == []

    def test_the_packaged_page_chain_resolves_without_a_project_template(
        self, package_only_engine
    ):
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
            # page_view.html extends a variable with "base.html" as its default.
            parent = extends.parent_name.resolve(Context(), ignore_failures=True)

            assert package_only_engine.get_template(parent)

    def test_an_app_listed_above_mvp_still_wins(self):
        installed = settings.INSTALLED_APPS
        assert installed.index("demo") < installed.index("mvp")

        origin = get_template("base.html").origin.name

        assert MVP_TEMPLATES not in Path(origin).parents
        assert Path(origin).parts[-3:] == ("demo", "templates", "base.html")


class TestShowCodeTemplate:
    def test_the_package_ships_the_template_the_tag_renders(self, package_only_engine):
        assert (
            package_only_engine.get_template("cotton/mvp/documentation.html")
            is not None
        )


def _template_files():
    """Every .html template this repository owns, packaged and demo alike."""
    return [
        path
        for root in (MVP_TEMPLATES, DEMO_TEMPLATES)
        for path in sorted(root.rglob("*.html"))
    ]


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
    def test_the_lexer_really_does_leak_a_multiline_comment(self):
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
class TestShellHeadWithPwaOff:
    def test_head_carries_no_install_tags(self):
        head = render_shell_head()
        soup = head_soup()

        assert soup.find("link", rel="manifest") is None
        assert soup.find("meta", attrs={"name": "theme-color"}) is None
        assert soup.find("link", rel="apple-touch-icon") is None
        assert "serviceWorker" not in head


def head_soup():
    from bs4 import BeautifulSoup

    return BeautifulSoup(render_shell_head(), "html.parser")


@pytest.mark.django_db
@pytest.mark.usefixtures("pwa_enabled")
class TestShellHeadWithPwaOn:
    @pytest.fixture(autouse=True)
    def urls_mounted(self, settings):
        settings.ROOT_URLCONF = "demo.urls"

    def test_it_links_the_manifest(self):
        link = head_soup().find("link", rel="manifest")

        assert link["href"] == "/manifest.webmanifest"

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

        assert json.loads(data.string) == "/sw.js"
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

        assert (
            json.loads(soup.find("script", id="mvp-pwa-worker-scope").string) == "/app/"
        )
        assert json.loads(soup.find("script", id="mvp-pwa-worker-url").string) == (
            "/app/sw.js"
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

    def test_it_sets_the_configured_theme_colour(self):
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
@pytest.mark.usefixtures("pwa_enabled")
class TestShellHeadWithoutMvpUrls:
    @pytest.fixture(autouse=True)
    def urls_unmounted(self, settings):
        settings.ROOT_URLCONF = urlconf_of(
            *[
                pattern
                for pattern in demo_urls.urlpatterns
                if getattr(getattr(pattern, "urlconf_name", None), "__name__", None)
                != "mvp.urls"
            ]
        )

    def test_the_page_renders_without_a_manifest_or_registration(self):
        head = render_shell_head()
        soup = head_soup()

        assert soup.find("link", rel="manifest") is None
        assert "serviceWorker" not in head


@pytest.mark.django_db
@pytest.mark.usefixtures("pwa_enabled")
class TestShellHeadWithConfiguredValues:
    @pytest.fixture(autouse=True)
    def urls_mounted(self, settings):
        settings.ROOT_URLCONF = "demo.urls"

    def test_a_project_head_template_replaces_the_packaged_one(self, settings):
        project_templates = Path(__file__).parent / "fixtures" / "override_templates"
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

        return " ".join(
            BeautifulSoup(render_shell_head(), "html.parser").title.text.split()
        )

    def test_the_suffix_is_the_site_name_by_default(self):
        assert self.title() == "| example.com"

    def test_the_suffix_is_the_configured_site_name(self, monkeypatch):
        from mvp.config import MVP_CONFIG

        monkeypatch.setitem(MVP_CONFIG, "site_name", "The Corner Shop")

        assert self.title() == "| The Corner Shop"


def render_shell(source):
    """Render a template string as a shell page for a fixed anonymous request."""
    request = RequestFactory().get("/", HTTP_HOST="testserver")
    request.user = AnonymousUser()
    request.site = get_current_site(request)
    return engines["django"].from_string(source).render({}, request)


@pytest.mark.django_db
class TestShellDockBlock:
    def test_a_page_keeps_the_dock_by_default(self):
        page = render_shell('{% extends "mvp/base.html" %}')

        assert 'class="mvp-dock-only"' in page

    def test_a_page_that_empties_the_block_has_no_dock(self):
        page = render_shell(
            '{% extends "mvp/base.html" %}{% block app.dock %}{% endblock %}'
        )

        assert 'class="mvp-dock-only"' not in page


def render_component(markup, **context):
    """Render Cotton ``markup`` with ``context`` for a fixed anonymous request."""
    from bs4 import BeautifulSoup
    from django_cotton.compiler_regex import CottonCompiler

    request = RequestFactory().get("/", HTTP_HOST="testserver")
    request.user = AnonymousUser()
    request.site = get_current_site(request)
    template = engines["django"].from_string(CottonCompiler().process(markup))
    return BeautifulSoup(template.render(context, request), "html.parser")


def shell_soup(blocks=""):
    """Parse a page that extends the shell and fills the given blocks."""
    from bs4 import BeautifulSoup

    source = '{% extends "mvp/base.html" %}' + blocks
    return BeautifulSoup(render_shell(source), "html.parser")


def fill(name, marker):
    """A block override that draws one marked element."""
    return (
        f"{{% block {name} %}}<span data-filled='{marker}'></span>"
        f"{{% endblock {name} %}}"
    )


@pytest.mark.django_db
class TestShellSidebarBlocks:
    def test_empty_blocks_draw_the_packaged_sidebar(self):
        sidebar = shell_soup().select_one("aside.mvp-sidebar")

        assert sidebar.select_one(".mvp-sidebar-header") is not None
        assert sidebar.select_one("ul.menu") is not None
        assert sidebar.select_one("[data-toggle-theme]") is not None

    def test_a_filled_header_replaces_the_packaged_one(self):
        sidebar = shell_soup(fill("app.sidebar.header", "header")).select_one(
            "aside.mvp-sidebar"
        )

        assert sidebar.select_one("[data-filled='header']") is not None
        assert sidebar.select_one(".mvp-sidebar-header") is None
        assert sidebar.select_one("ul.menu") is not None

    def test_a_filled_body_replaces_the_menu(self):
        sidebar = shell_soup(fill("app.sidebar.body", "body")).select_one(
            "aside.mvp-sidebar"
        )

        assert sidebar.select_one("[data-filled='body']") is not None
        assert sidebar.select_one("ul.menu") is None
        assert sidebar.select_one(".mvp-sidebar-header") is not None

    def test_a_filled_footer_replaces_the_packaged_one(self):
        sidebar = shell_soup(fill("app.sidebar.footer", "footer")).select_one(
            "aside.mvp-sidebar"
        )

        assert sidebar.select_one("[data-filled='footer']") is not None
        assert sidebar.select_one("[data-toggle-theme]") is None

    def test_the_regions_keep_their_order(self):
        blocks = "".join(
            fill(f"app.sidebar.{region}", region)
            for region in ("footer", "body", "header")
        )
        sidebar = shell_soup(blocks).select_one("aside.mvp-sidebar")

        drawn = [element["data-filled"] for element in sidebar.select("[data-filled]")]

        assert drawn == ["header", "body", "footer"]


@pytest.mark.django_db
class TestShellNavbarBlocks:
    def test_empty_blocks_draw_the_packaged_navbar(self):
        navbar = shell_soup().select_one(".mvp-header .navbar")

        assert navbar.select_one(".navbar-start .mvp-navbar-brand") is not None
        assert navbar.select_one(".navbar-center") is None
        assert navbar.select_one(".navbar-end [data-toggle-theme]") is not None

    def test_a_filled_start_replaces_the_toggle_and_site_icon(self):
        start = shell_soup(fill("app.navbar.start", "start")).select_one(
            ".mvp-header .navbar-start"
        )

        assert start.select_one("[data-filled='start']") is not None
        assert start.select_one(".mvp-navbar-brand") is None

    def test_a_filled_center_sits_between_start_and_end(self):
        navbar = shell_soup(fill("app.navbar.center", "center")).select_one(
            ".mvp-header .navbar"
        )

        regions = [
            next(name for name in child["class"] if name.startswith("navbar-"))
            for child in navbar.find_all(recursive=False)
        ]

        assert regions == ["navbar-start", "navbar-center", "navbar-end"]
        assert navbar.select_one(".navbar-center [data-filled='center']") is not None

    def test_a_filled_end_is_drawn_before_the_configured_widgets(self):
        end = shell_soup(fill("app.navbar.end", "end")).select_one(
            ".mvp-header .navbar-end"
        )

        filled = end.select_one("[data-filled='end']")

        assert filled is not None
        assert filled.find_next(attrs={"data-toggle-theme": True}) is not None
        assert filled.find_previous(id="mvp-htmx-indicator") is not None

    def test_a_filled_navbar_replaces_the_row_and_keeps_the_tray(self):
        header = shell_soup(
            fill("app.navbar", "navbar") + fill("app.header.tray", "tray")
        ).select_one(".mvp-header")

        assert header.select_one(".navbar") is None
        drawn = [element["data-filled"] for element in header.select("[data-filled]")]
        assert drawn == ["navbar", "tray"]

    def test_the_header_draws_a_navbar_when_called_with_nothing_inside(self):
        soup = render_component("<c-app.header />")

        assert soup.select_one(".mvp-header .navbar") is not None


#: The trail an MVP view puts in the page context.
VIEW_TRAIL = {"breadcrumbs": [{"text": "From the view"}]}

#: A template's own trail: the block holds the steps and nothing around them.
TEMPLATE_TRAIL = (
    "{% block app.breadcrumbs %}<li data-filled='trail'></li>"
    "{% endblock app.breadcrumbs %}"
)


def trail_soup(blocks="", **context):
    """Parse a shell page rendered with ``context``, as a view would supply it."""
    from bs4 import BeautifulSoup

    request = RequestFactory().get("/", HTTP_HOST="testserver")
    request.user = AnonymousUser()
    request.site = get_current_site(request)
    source = '{% extends "mvp/base.html" %}' + blocks
    page = engines["django"].from_string(source).render(context, request)
    return BeautifulSoup(page, "html.parser")


@pytest.mark.django_db
class TestShellBreadcrumbsBlock:
    def test_an_empty_block_and_no_view_trail_draw_no_landmark(self):
        assert trail_soup().select_one("nav.breadcrumbs") is None

    def test_an_empty_block_draws_the_trail_the_view_declared(self):
        trail = trail_soup(page=VIEW_TRAIL).select_one(".mvp-header nav.breadcrumbs")

        assert [step.get_text(strip=True) for step in trail.select("li")] == [
            "From the view"
        ]

    def test_a_filled_block_is_drawn_as_the_steps_of_the_trail(self):
        trail = trail_soup(TEMPLATE_TRAIL).select_one(".mvp-header nav.breadcrumbs")

        assert trail.select_one("ul > li[data-filled='trail']") is not None

    def test_a_filled_block_keeps_the_toggle_and_site_icon(self):
        start = trail_soup(TEMPLATE_TRAIL).select_one(".mvp-header .navbar-start")

        assert start.select_one(".mvp-navbar-brand") is not None
        assert start.select_one("nav.breadcrumbs") is not None

    def test_a_filled_block_replaces_the_trail_the_view_declared(self):
        soup = trail_soup(TEMPLATE_TRAIL, page=VIEW_TRAIL)

        steps = soup.select("nav.breadcrumbs li")

        assert len(soup.select("nav.breadcrumbs")) == 1
        assert [step.get("data-filled") for step in steps] == ["trail"]

    def test_a_page_variable_named_like_the_slot_is_not_drawn(self):
        navbar = render_component("<c-app.navbar />", breadcrumbs="leaked-trail")

        assert "leaked-trail" not in navbar.get_text()
        assert navbar.select_one("nav.breadcrumbs") is None


@pytest.mark.django_db
class TestRegionSlotsIgnoreThePageContext:
    """A page variable that shares a slot's name is not drawn as that region."""

    def test_the_navbar_draws_no_page_variable(self):
        leak = {name: f"leaked-{name}" for name in ("start", "center", "end")}

        navbar = render_component("<c-app.navbar />", **leak)

        assert "leaked-" not in navbar.get_text()
        assert navbar.select_one(".mvp-navbar-brand") is not None

    def test_the_sidebar_draws_no_page_variable(self):
        leak = {name: f"leaked-{name}" for name in ("header", "body", "footer")}

        sidebar = render_component("<c-app.sidebar />", **leak)

        assert "leaked-" not in sidebar.get_text()
        assert sidebar.select_one(".mvp-sidebar-header") is not None


@pytest.mark.django_db
class TestShellMessagesBlock:
    def test_a_filled_block_is_drawn_inside_main(self):
        soup = shell_soup(fill("app.messages", "messages"))

        assert soup.select_one("main [data-filled='messages']") is not None


@pytest.mark.django_db
class TestComponentOverridePath:
    @pytest.fixture(autouse=True)
    def override_templates_first(self, settings):
        project_templates = Path(__file__).parent / "fixtures" / "override_templates"
        engine = settings.TEMPLATES[0]
        settings.TEMPLATES = [
            {**engine, "DIRS": [str(project_templates), *engine.get("DIRS", [])]}
        ]

    def test_an_override_at_the_packaged_path_replaces_the_packaged_component(self):
        soup = BeautifulSoup(
            render_shell('{% extends "mvp/base.html" %}'), "html.parser"
        )

        assert soup.find(attrs={"data-footer-override": "prefixed"}) is not None


def _controls(html):
    """Every control on a page, keyed by what makes it work rather than its wording."""
    soup = BeautifulSoup(html, "html.parser")
    keys = ("href", "name", "id", "form", "type", "action", "method", "for", "role")
    return sorted(
        (el.name, *(str(el.get(key, "")) for key in keys))
        for el in soup.find_all(
            ["a", "button", "input", "select", "textarea", "form", "nav", "dialog", "label"]
        )
    )


@pytest.fixture
def seeded_pages(db):
    category = CategoryFactory()
    product = ProductFactory(category=category)
    ProductFactory.create_batch(6, category=category)
    return {
        "list": "/products/many/?page=2&o=name_desc",
        "table": "/django-tables2/?page=1",
        "detail": f"/products/{product.pk}/",
        "form": f"/products/{product.pk}/edit/",
        "create": "/products/create/",
        "dashboard": "/",
        "error": "/errors/404/",
    }


class TestPackagedPagesUnderCottonIsolation:
    """A project can switch Cotton's context isolation on without losing any control.

    With ``COTTON_ISOLATE_BY_DEFAULT`` on, a component sees only what its caller
    passes and what the context processors supply. A packaged component that
    reads the filter form, the ordering or the page title from the view instead
    of being handed it draws without that control, so each packaged page must
    draw the same controls with isolation on as with it off.
    """

    @pytest.mark.parametrize(
        "page", ["list", "table", "detail", "form", "create", "dashboard", "error"]
    )
    def test_the_page_draws_the_same_controls(self, client, user, seeded_pages, page):
        client.force_login(user)
        url = seeded_pages[page]
        with override_settings(COTTON_ISOLATE_BY_DEFAULT=False):
            leaky = client.get(url)
        with override_settings(COTTON_ISOLATE_BY_DEFAULT=True):
            isolated = client.get(url)

        assert leaky.status_code == isolated.status_code
        assert _controls(isolated.content.decode()) == _controls(leaky.content.decode())


PANEL = '<c-mvp.page.side label="On this page" id="toc">links</c-mvp.page.side>'


def page_view_region(side=None, title=None):
    """The content region ``page_view.html`` draws, with a body of ``#body``.

    ``side`` fills ``page.side`` with the given markup, and ``title`` replaces
    the whole ``page.title`` block; ``None`` leaves each block alone.
    """
    from django_cotton.compiler_regex import CottonCompiler

    blocks = '{% block page.content %}<p id="body">hi</p>{% endblock %}'
    if side is not None:
        blocks += "{% block page.side %}" + side + "{% endblock %}"
    if title is not None:
        blocks += "{% block page.title %}" + title + "{% endblock %}"
    source = CottonCompiler().process('{% extends "page_view.html" %}' + blocks)
    soup = BeautifulSoup(render_shell(source), "html.parser")
    return soup.select_one("main .container > div")


@pytest.mark.django_db
class TestPageViewSideBlock:
    def test_a_page_without_a_side_panel_draws_the_title_then_the_content(self):
        region = page_view_region()

        assert [
            el.get("id") or el["class"][0] for el in region.find_all(recursive=False)
        ] == [
            "page-title",
            "body",
        ]

    def test_a_page_without_a_side_panel_draws_no_layout_drawer_or_button(self):
        region = page_view_region()

        assert region.select_one(".mvp-page-layout") is None
        assert region.select_one(".drawer") is None
        assert region.select_one(".mvp-page-side-toggle") is None

    def test_a_block_holding_only_whitespace_counts_as_empty(self):
        region = page_view_region(side="  \n\t  ")

        assert region.select_one(".mvp-page-layout") is None
        assert [
            el.get("id") or el["class"][0] for el in region.find_all(recursive=False)
        ] == [
            "page-title",
            "body",
        ]

    def test_a_page_filling_the_block_draws_the_layout_with_its_panel(self):
        region = page_view_region(side=PANEL)

        layout = region.select_one(".mvp-page-layout")
        assert layout.select_one(".mvp-page-header .page-title") is not None
        assert layout.select_one(".mvp-page-main #body") is not None
        assert layout.select_one("#toc") is not None

    def test_a_page_that_empties_the_title_still_lays_out_the_panel(self):
        region = page_view_region(side=PANEL, title="")

        layout = region.select_one(".mvp-page-layout")
        assert layout.select_one(".mvp-page-header") is None
        assert layout.select_one(".mvp-page-main #body") is not None
        assert layout.select_one("#toc") is not None


UNIQUE_TITLE_ARGUMENTS = {
    "page_title": "Unique title",
    "page_eyebrow": "Unique eyebrow",
    "page_lead": "Unique lead",
    "page_actions": [{"text": "Unique action", "href": "/unique-action/"}],
    "page_info": "Unique info",
}

TITLE_PAGE_KINDS = ["page", "form", "detail", "delete", "list", "table"]


@pytest.fixture
def render_title_page(rf, superuser, product):
    """Render one page of the given kind from a view with ``attrs`` set."""

    def render(kind, **attrs):
        from demo.forms import ProductForm
        from demo.models import Product
        from mvp.views import (
            MVPCreateView,
            MVPDeleteView,
            MVPDetailView,
            MVPListView,
            MVPTemplateView,
        )

        url_kwargs = {}
        if kind == "page":
            base, setup = MVPTemplateView, {"template_name": "page_view.html"}
        elif kind == "form":
            base, setup = MVPCreateView, {"model": Product, "form_class": ProductForm}
        elif kind == "detail":
            base, setup = MVPDetailView, {
                "model": Product,
                "show_update_action": True,
                "show_delete_action": True,
            }
            url_kwargs = {"pk": product.pk}
        elif kind == "delete":
            base, setup = MVPDeleteView, {"model": Product}
            url_kwargs = {"pk": product.pk}
        elif kind == "list":
            base, setup = MVPListView, {
                "model": Product,
                "list_item_template": "cards/product_card.html",
                "show_create_action": True,
            }
        else:
            pytest.importorskip("django_tables2")
            from demo.tables import ProductTable
            from mvp.integrations.django_tables.views import MVPTableView

            base, setup = MVPTableView, {
                "model": Product,
                "table_class": ProductTable,
                "show_create_action": True,
            }
        if "page_title" in attrs:
            # Detail and delete pages title themselves from their object.
            attrs["get_page_title"] = lambda self: attrs["page_title"]
        view_class = type("TitleTestView", (base,), {**setup, **attrs})
        request = rf.get("/")
        request.user = superuser
        response = view_class.as_view()(request, **url_kwargs)
        response.render()
        return BeautifulSoup(response.content.decode(), "html.parser")

    return render


def _title_area(soup):
    """The element a page draws its title in: the one holding the ``<h1>``."""
    heading = soup.select_one("main h1")
    return heading.find_parent(class_="page-title")


@pytest.mark.django_db
class TestPageTitleArgumentsOnEveryPage:
    @pytest.mark.parametrize("kind", TITLE_PAGE_KINDS)
    def test_the_title_draws_every_argument_the_view_sets(
        self, render_title_page, kind
    ):
        soup = render_title_page(kind, **UNIQUE_TITLE_ARGUMENTS)

        title = _title_area(soup)
        assert [h1.get_text(strip=True) for h1 in title.find_all("h1")] == [
            "Unique title"
        ]
        assert title.select_one(".mvp-page-eyebrow").get_text(strip=True) == (
            "Unique eyebrow"
        )
        assert title.select_one(".mvp-page-lead").get_text(strip=True) == "Unique lead"
        assert "Unique info" in title.find("dialog").get_text()

    @pytest.mark.parametrize("kind", ["page", "form", "detail", "delete"])
    def test_the_actions_are_drawn_in_the_title_on_pages_without_a_toolbar(
        self, render_title_page, kind
    ):
        soup = render_title_page(kind, **UNIQUE_TITLE_ARGUMENTS)

        actions = soup.select('a[href="/unique-action/"]')
        assert len(actions) == 1
        assert actions[0].find_parent(class_="page-title") is not None

    @pytest.mark.parametrize("kind", ["list", "table"])
    def test_the_actions_are_in_the_toolbar_before_add_and_not_in_the_title(
        self, render_title_page, kind
    ):
        soup = render_title_page(kind, **UNIQUE_TITLE_ARGUMENTS)

        toolbar = soup.select_one(".mvp-list-toolbar, .mvp-table-toolbar")
        links = [a["href"] for a in toolbar.find_all("a", href=True)]
        assert links.count("/unique-action/") == 1
        assert links.index("/unique-action/") < links.index("/products/create/")
        assert _title_area(soup).find("a", href="/unique-action/") is None

    @pytest.mark.parametrize("kind", TITLE_PAGE_KINDS)
    def test_overriding_the_group_changes_what_the_page_draws(
        self, render_title_page, kind
    ):
        def get_page_title_args(self):
            return {
                "title": "Computed title",
                "lead": "Computed lead",
                "info": "Computed info",
            }

        soup = render_title_page(
            kind,
            page_title="Ignored title",
            page_lead="Ignored lead",
            page_info="Ignored info",
            get_page_title_args=get_page_title_args,
        )

        title = _title_area(soup)
        assert [h1.get_text(strip=True) for h1 in title.find_all("h1")] == [
            "Computed title"
        ]
        assert title.select_one(".mvp-page-lead").get_text(strip=True) == (
            "Computed lead"
        )
        assert "Computed info" in title.find("dialog").get_text()
        assert "Ignored" not in title.get_text()

    def test_a_detail_pages_actions_are_drawn_with_edit_and_delete(
        self, render_title_page, product
    ):
        soup = render_title_page("detail", **UNIQUE_TITLE_ARGUMENTS)

        links = [a["href"] for a in _title_area(soup).find_all("a", href=True)]
        assert links == [
            "/unique-action/",
            f"/products/{product.pk}/edit/",
            f"/products/{product.pk}/delete/",
        ]

    @pytest.mark.parametrize("kind", TITLE_PAGE_KINDS)
    def test_a_view_setting_nothing_new_draws_one_heading_and_no_eyebrow_or_actions(
        self, render_title_page, kind
    ):
        soup = render_title_page(kind, page_title="Unique title")

        title = _title_area(soup)
        assert len(title.find_all("h1")) == 1
        assert title.select_one(".mvp-page-eyebrow") is None
        assert title.select_one(".mvp-page-lead") is None
        assert title.find("dialog") is None
        links = [a["href"] for a in title.find_all("a", href=True)]
        assert "/unique-action/" not in links
        if kind != "detail":
            assert links == []
        assert title.find("button") is None
        empty = [
            element
            for element in title.find_all(["div", "p"])
            if not element.get_text(strip=True) and not element.find(True)
        ]
        assert empty == []
