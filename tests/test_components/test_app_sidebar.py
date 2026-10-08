"""Tests for ``<c-app.sidebar>``'s choice of menu and its back link.

Source: mvp/templates/cotton/app/sidebar/index.html and back.html
"""

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.models import Site
from django.template import engines
from django.test import RequestFactory, override_settings
from django.urls import resolve
from django_cotton.compiler_regex import CottonCompiler
from flex_menu import Menu, MenuItem

from mvp.mounted import MountedApp
from tests.testapp_mounted.menus import TestappMountedMenu

SITE_NAME = "example.com"


def render_sidebar(markup, path="/mounted/", **context):
    """Render Cotton ``markup`` on a request served for ``path``."""
    request = RequestFactory().get(path)
    request.user = AnonymousUser()
    request.resolver_match = resolve(path, urlconf="tests.urls_mounted")
    request.site = Site.objects.get_current()
    template = engines["django"].from_string(CottonCompiler().process(markup))
    html = template.render(context, request=request)
    return BeautifulSoup(html, "html.parser")


def sidebar_labels(soup):
    """The text of the brand link, then every link in a menu, in order.

    The footer's buttons are left out: they are not navigation.
    """
    links = soup.select("aside.mvp-sidebar a.mvp-sidebar-brand, aside.mvp-sidebar ul a")
    return [a.get_text(" ", strip=True) for a in links]


def menu_hrefs(soup):
    """Where every link in a menu goes. Under Cotton's context isolation the
    menu renderer's own item labels are empty, so this is what proves which
    menu was drawn."""
    return [a["href"] for a in soup.select("aside.mvp-sidebar ul a")]


def back_link(soup):
    """The sidebar's back link, or ``None``."""
    return soup.select_one("aside.mvp-sidebar a[data-back-link]")


@pytest.mark.django_db
@pytest.mark.urls("tests.urls_mounted")
class TestSidebarMenuChoice:
    def test_no_menu_and_no_app_draws_app_menu(self):
        soup = render_sidebar("<c-app.sidebar />", path="/layout/")

        labels = sidebar_labels(soup)

        assert "Home" in labels
        assert "Theme Customization" in labels
        assert back_link(soup) is None

    def test_explicit_menu_draws_that_menu_and_no_back_link_on_an_app_page(self):
        soup = render_sidebar('<c-app.sidebar menu="TestappMountedMenu" />')

        labels = sidebar_labels(soup)

        assert "Mounted Index" in labels
        assert "Home" not in labels
        assert back_link(soup) is None

    def test_resolved_menu_and_app_draw_the_menu_under_a_back_link(self):
        soup = render_sidebar("<c-app.sidebar />")

        labels = sidebar_labels(soup)

        assert SITE_NAME in labels[1]
        assert labels[2:] == ["Mounted Index", "Mounted Detail"]
        assert "Home" not in labels

    def test_explicit_menu_beats_the_resolved_pair(self):
        soup = render_sidebar('<c-app.sidebar menu="AppMenu" />')

        assert "Home" in sidebar_labels(soup)
        assert "Mounted Index" not in sidebar_labels(soup)

    def test_menu_with_nothing_visible_draws_the_back_link_alone(self):
        hidden = Menu(
            "HiddenMenu",
            children=[
                MenuItem(name="hidden", view_name="testapp_mounted:index", check=False)
            ],
        )
        app = MountedApp(name="Hidden", icon="box", menu=hidden, urls=[], landing="x")

        soup = render_sidebar(
            "<c-app.sidebar />", mounted_menu=hidden, mounted_app=app
        )

        labels = sidebar_labels(soup)
        assert len(labels) == 2
        assert SITE_NAME in labels[1]
        assert back_link(soup) is not None

    def test_sidebar_still_draws_one_navigation_landmark_beside_a_back_link(self):
        soup = render_sidebar("<c-app.sidebar />")

        landmarks = soup.find_all(
            lambda tag: tag.name == "nav" or tag.get("role") == "navigation"
        )
        named = soup.find_all("nav", attrs={"aria-label": TestappMountedMenu.name})

        assert len(landmarks) == 1
        assert landmarks == named


@pytest.mark.django_db
@pytest.mark.urls("tests.urls_mounted")
class TestSidebarUnderContextIsolation:
    @override_settings(COTTON_ENABLE_CONTEXT_ISOLATION=True)
    def test_an_app_page_still_draws_the_menu_and_the_back_link(self):
        soup = render_sidebar("<c-app.sidebar />")

        assert menu_hrefs(soup) == ["/", "/mounted/", "/mounted/detail/"]
        assert back_link(soup)["href"] == "/"

    @override_settings(COTTON_ENABLE_CONTEXT_ISOLATION=True)
    def test_a_host_page_still_draws_the_app_menu_with_no_back_link(self):
        soup = render_sidebar("<c-app.sidebar />", path="/layout/")

        assert "/layout/" in menu_hrefs(soup)
        assert "/mounted/" not in menu_hrefs(soup)
        assert back_link(soup) is None

    @override_settings(COTTON_ENABLE_CONTEXT_ISOLATION=True)
    def test_menu_entries_keep_their_labels(self):
        isolated = sidebar_labels(render_sidebar("<c-app.sidebar />"))

        with override_settings(COTTON_ENABLE_CONTEXT_ISOLATION=False):
            shared = sidebar_labels(render_sidebar("<c-app.sidebar />"))

        assert "Mounted Index" in isolated
        assert isolated == shared

    @override_settings(COTTON_ENABLE_CONTEXT_ISOLATION=True)
    def test_the_shell_still_draws_the_sidebar_it_is_given(self):
        soup = render_sidebar(
            '<c-app><c-slot name="sidebar"><c-app.sidebar '
            "/></c-slot></c-app>"
        )

        assert "Mounted Index" in sidebar_labels(soup)


@pytest.mark.django_db
@pytest.mark.urls("tests.urls_mounted")
class TestSidebarBackLink:
    def render(self, **context):
        return render_sidebar(
            "<c-app.sidebar {{ extra }} />".replace(
                "{{ extra }}", context.pop("extra", "")
            ),
            **context,
        )

    def test_label_reads_back_to_the_site_name(self):
        assert SITE_NAME in back_link(self.render()).get_text(" ", strip=True)

    def test_link_goes_to_the_brand_url(self):
        soup = self.render(extra='brand-url="/home-page/"')

        assert back_link(soup)["href"] == "/home-page/"
        assert soup.select_one("a.mvp-sidebar-brand")["href"] == "/home-page/"

    def test_link_goes_to_the_site_root_by_default(self):
        assert back_link(self.render())["href"] == "/"

    def test_link_is_named_by_its_label_when_the_rail_hides_the_text(self):
        link = back_link(self.render())

        assert SITE_NAME in link["aria-label"]
        assert link["aria-label"] == link.get_text(" ", strip=True)

    def test_configured_site_name_wins_over_the_site_record(self, monkeypatch):
        from mvp.config import MVP_CONFIG

        monkeypatch.setitem(MVP_CONFIG, "site_name", "FairDM")

        assert "FairDM" in back_link(self.render())["aria-label"]

    def test_site_name_is_escaped_once(self, monkeypatch):
        from mvp.config import MVP_CONFIG

        monkeypatch.setitem(MVP_CONFIG, "site_name", "R&D <Lab>")
        html = str(self.render())

        assert "R&amp;D &lt;Lab&gt;" in html
        assert "&amp;amp;" not in html

    def test_no_site_name_never_reads_back_to_alone(self, monkeypatch):
        from mvp.config import MVP_CONFIG

        monkeypatch.setitem(MVP_CONFIG, "site_name", "")
        Site.objects.filter(pk=Site.objects.get_current().pk).update(name="")
        Site.objects.clear_cache()

        label = back_link(self.render()).get_text(" ", strip=True)

        assert label
        assert back_link(self.render())["aria-label"] == label
