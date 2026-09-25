"""Tests for ``mvp.mounted`` — mounting one django-mvp app inside another.

Source: mvp/mounted.py
"""

import inspect

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.urls import Resolver404, path, resolve, reverse
from django.views.decorators.csrf import csrf_exempt

from mvp.menus import AppMenu
from mvp.mounted import MountedApp, mount
from tests.testapp_mounted.menus import TestappMountedMenu
from tests.testapp_mounted.mounted import testapp_mounted
from tests.testapp_mounted.views import IndexView

PLAIN_URLCONF = "tests.urls_mounted_plain"


@pytest.mark.django_db
@pytest.mark.urls(PLAIN_URLCONF)
class TestFixtureApp:
    """The fixture app's two pages render through a plain ``include()``."""

    def test_index_page_renders(self, client):
        response = client.get("/mounted/")

        assert response.status_code == 200
        assert b'id="testapp-mounted-index"' in response.content

    def test_detail_page_renders(self, client):
        response = client.get("/mounted/detail/")

        assert response.status_code == 200
        assert b'id="testapp-mounted-detail"' in response.content


def normalised_title(response):
    """The ``<title>`` text with the template's whitespace collapsed."""
    soup = BeautifulSoup(response.content, "html.parser")
    return " ".join(soup.title.get_text().split())


def sidebar_links(response):
    """Every ``(text, href)`` link inside the sidebar, header brand included."""
    soup = BeautifulSoup(response.content, "html.parser")
    sidebar = soup.select_one("aside.mvp-sidebar")
    return [(a.get_text(" ", strip=True), a["href"]) for a in sidebar.select("a")]


def app_menu_links(rf):
    """The ``(label, url)`` of every visible leaf ``AppMenu`` resolves to."""
    request = rf.get("/")
    request.user = AnonymousUser()
    links = []

    def walk(item):
        for child in item.visible_children:
            if child.has_url:
                links.append((child.extra_context["label"], child.url))
            walk(child)

    walk(AppMenu.process(request))
    return links


@pytest.mark.django_db
@pytest.mark.urls(PLAIN_URLCONF)
class TestPageBelongingToNoApp:
    """A project that mounts nothing renders as it always has (FR-010, SC-004).

    Pinned before the shell learns about mounted apps, and green at every
    commit after.
    """

    def test_sidebar_carries_the_app_menu_entries_and_nothing_else(self, client, rf):
        response = client.get("/layout/")

        links = sidebar_links(response)

        brand, *rest = links
        assert brand == ("", "/")
        menu_links = [link for link in rest if link in app_menu_links(rf)]
        assert menu_links == app_menu_links(rf)
        assert links[1:4] == [
            ("Home", "/"),
            ("Layout", "/layout/"),
            ("Theme Customization", "/theme/"),
        ]

    def test_sidebar_draws_no_mounted_app_entries(self, client):
        response = client.get("/mounted/")

        texts = [text for text, _href in sidebar_links(response)]

        assert "Mounted Index" not in texts
        assert "Mounted Detail" not in texts

    def test_sidebar_has_no_back_link(self, client):
        response = client.get("/layout/")

        assert "Back to" not in response.content.decode()

    def test_titled_page_title_is_the_page_then_the_site(self, client):
        response = client.get("/layout/")

        assert normalised_title(response) == "Layout Demo | example.com"

    def test_titled_fixture_page_title_is_the_page_then_the_site(self, client):
        response = client.get("/mounted/detail/")

        assert normalised_title(response) == "Detail | example.com"

    def test_untitled_page_title_is_the_site_alone_after_a_bar(self, client):
        response = client.get("/mounted/")

        assert normalised_title(response) == "| example.com"


def for_path(client, path):
    """The mounted app ``path`` was served through, per the request it got."""
    response = client.get(path)
    assert response.status_code == 200
    return MountedApp.for_request(response.wsgi_request)


def urlconf_of(*patterns):
    """A URLconf object holding ``patterns``, for ``resolve(urlconf=...)``."""
    return type("URLConf", (), {"urlpatterns": list(patterns)})


def ok_view(request):
    """A synchronous function view."""
    return HttpResponse("ok")


async def async_ok_view(request):
    """An asynchronous function view."""
    return HttpResponse("ok")


exempt_view = csrf_exempt(ok_view)


def throwaway_app(*patterns):
    """A mounted app whose URLs are ``patterns``, with no namespace."""
    return MountedApp(
        name="Throwaway",
        icon="box",
        menu=TestappMountedMenu,
        urls=list(patterns),
        landing="throwaway",
    )


@pytest.mark.django_db
class TestMountedAppLookup:
    """``MountedApp.for_request`` says which app a page was served through."""

    @pytest.mark.urls("tests.urls_mounted")
    def test_page_served_through_the_mount_is_the_app(self, client):
        assert for_path(client, "/mounted/") is testapp_mounted

    @pytest.mark.urls("tests.urls_mounted")
    def test_every_page_of_the_app_is_the_app(self, client):
        assert for_path(client, "/mounted/detail/") is testapp_mounted

    @pytest.mark.urls("tests.urls_mounted")
    def test_host_page_is_no_app(self, client):
        assert for_path(client, "/layout/") is None

    @pytest.mark.urls("tests.urls_mounted_root")
    def test_app_mounted_at_the_root_claims_only_its_own_pages(self, client):
        assert for_path(client, "/detail/") is testapp_mounted

    @pytest.mark.urls("tests.urls_mounted_root")
    def test_app_mounted_at_the_root_leaves_host_pages_alone(self, client):
        assert for_path(client, "/layout/") is None
        assert for_path(client, "/theme/") is None

    def test_request_with_no_match_is_no_app(self, rf):
        assert MountedApp.for_request(rf.get("/")) is None

    @pytest.mark.urls("tests.urls_mounted")
    def test_lookup_is_kept_on_the_request(self, client):
        request = client.get("/mounted/").wsgi_request

        first = MountedApp.for_request(request)
        request.resolver_match = None

        assert MountedApp.for_request(request) is first


class TestMountedAppResolver:
    """The mount hands each page's view back as it found it (R3)."""

    def test_view_class_is_still_the_apps_view_class(self):
        match = resolve("/mounted/", urlconf="tests.urls_mounted")

        assert match.func.view_class is IndexView

    def test_view_name_keeps_the_namespace(self):
        match = resolve("/mounted/detail/", urlconf="tests.urls_mounted")

        assert match.view_name == "testapp_mounted:detail"

    def test_csrf_exemption_survives(self):
        app = throwaway_app(path("x/", exempt_view, name="x"))
        urlconf = urlconf_of(mount("m/", app))

        match = resolve("/m/x/", urlconf=urlconf)

        assert match.func.csrf_exempt is True

    def test_function_view_keeps_its_name(self):
        app = throwaway_app(path("x/", ok_view, name="x"))
        urlconf = urlconf_of(mount("m/", app))

        match = resolve("/m/x/", urlconf=urlconf)

        assert match.func.__name__ == "ok_view"

    def test_async_view_stays_a_coroutine_function(self):
        app = throwaway_app(path("x/", async_ok_view, name="x"))
        urlconf = urlconf_of(mount("m/", app))

        match = resolve("/m/x/", urlconf=urlconf)

        assert inspect.iscoroutinefunction(match.func)

    def test_wrapper_calls_the_original_view(self, rf):
        app = throwaway_app(path("x/", ok_view, name="x"))
        urlconf = urlconf_of(mount("m/", app))

        match = resolve("/m/x/", urlconf=urlconf)

        assert match.func(rf.get("/m/x/")).content == b"ok"

    def test_same_view_resolves_to_the_same_wrapper(self):
        app = throwaway_app(path("x/", ok_view, name="x"))
        urlconf = urlconf_of(mount("m/", app))

        first = resolve("/m/x/", urlconf=urlconf).func
        second = resolve("/m/x/", urlconf=urlconf).func

        assert first is second

    def test_one_view_in_two_apps_is_wrapped_for_each(self):
        one = throwaway_app(path("x/", ok_view, name="x"))
        two = throwaway_app(path("x/", ok_view, name="x"))
        urlconf = urlconf_of(mount("one/", one), mount("two/", two))

        first = resolve("/one/x/", urlconf=urlconf).func
        second = resolve("/two/x/", urlconf=urlconf).func

        assert first.mounted_app is one
        assert second.mounted_app is two

    def test_unmatched_path_is_still_a_404(self):
        with pytest.raises(Resolver404):
            resolve("/mounted/nope/", urlconf="tests.urls_mounted")

    def test_main_is_accepted_and_stored(self):
        resolver = mount("m/", throwaway_app(path("x/", ok_view)), main=True)

        assert resolver.main is True

    def test_main_defaults_to_false(self):
        resolver = mount("m/", throwaway_app(path("x/", ok_view)))

        assert resolver.main is False


class TestLandingReverse:
    """The landing reverses wherever the host mounts the app (scenario 7)."""

    def test_landing_under_the_first_prefix(self):
        assert reverse(testapp_mounted.landing, urlconf="tests.urls_mounted") == (
            "/mounted/"
        )

    def test_landing_under_a_different_prefix(self):
        assert reverse(
            testapp_mounted.landing, urlconf="tests.urls_mounted_other_prefix"
        ) == ("/elsewhere/nested/")


class TestHostMenusUntouched:
    """Declaring and mounting an app writes into no host menu (FR-003)."""

    def test_declaring_and_mounting_leave_app_menu_children_alone(self):
        before = list(AppMenu.children)

        app = throwaway_app(path("x/", ok_view, name="x"))
        mount("m/", app)

        assert list(AppMenu.children) == before

    def test_the_apps_entries_are_not_in_app_menu(self):
        names = {child.name for child in AppMenu.children}

        assert "testapp_mounted_index" not in names
        assert "testapp_mounted_detail" not in names
