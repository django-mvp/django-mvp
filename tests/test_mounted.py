"""Tests for ``mvp.mounted`` — mounting one django-mvp app inside another.

Source: mvp/mounted.py
"""

import asyncio
import inspect
import re

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import AnonymousUser
from django.core.checks import Error, Tags
from django.core.checks.registry import registry
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.template import Context, Template
from django.test import AsyncRequestFactory, override_settings
from django.urls import Resolver404, path, resolve, reverse
from django.views.decorators.csrf import csrf_exempt
from flex_menu import Menu, MenuItem

from demo.urls import urlpatterns as demo_patterns

from mvp.menus import AppMenu
from mvp.mounted import MountedApp, check_mounted_apps, mount
from tests.testapp_mounted.menus import TestappMountedMenu
from tests.testapp_mounted.mounted import (
    MountedFixtureApp,
    testapp_mounted,
    testapp_mounted_staff,
)
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
class TestClassDeclaration:
    """A package declares a class and the host mounts an instance it can adjust
    (FR-014, decision D26)."""

    def test_a_subclass_declared_the_packages_way_mounts_and_serves(self, client):
        with override_settings(ROOT_URLCONF=urlconf_of(mount("m/", MountedFixtureApp()))):
            response = client.get("/m/")

        assert response.status_code == 200

    def test_a_host_instance_changes_the_entry_without_changing_the_class(self):
        host = MountedFixtureApp(icon="journal", name="Journal")

        entry = host.menu_item()

        assert entry.extra_context["icon"] == "journal"
        assert entry.extra_context["label"] == "Journal"
        assert MountedFixtureApp.icon == "book"
        assert MountedFixtureApp.name == "Mounted Fixture"
        assert testapp_mounted.icon == "book"

    def test_a_host_instance_changes_the_page_title(self, client):
        host = MountedFixtureApp(name="Journal")

        with override_settings(ROOT_URLCONF=urlconf_of(mount("j/", host))):
            response = client.get("/j/detail/")

        assert "Detail | Journal | example.com" == normalised_title(response)

    def test_a_host_subclass_overrides_a_name_and_has_permission(self, rf):
        class HostApp(MountedFixtureApp):
            name = "Host's"

            def has_permission(self, request):
                return super().has_permission(request) and request.user.is_staff

        request = rf.get("/")
        request.user = type("U", (), {"is_staff": False})()
        staff = rf.get("/")
        staff.user = type("U", (), {"is_staff": True})()

        assert HostApp().name == "Host's"
        assert HostApp().has_permission(request) is False
        assert HostApp().has_permission(staff) is True

    def test_an_unknown_keyword_raises_a_type_error_naming_it(self):
        with pytest.raises(TypeError, match="colour"):
            MountedFixtureApp(colour="red")

    def test_a_keyword_is_only_taken_when_the_class_defines_it(self):
        with pytest.raises(TypeError, match="main"):
            MountedFixtureApp(main=True)

    def test_an_attribute_a_subclass_declares_can_be_set_by_keyword(self):
        class BadgedApp(MountedFixtureApp):
            badge = "new"

        assert BadgedApp(badge="beta").badge == "beta"

    @pytest.mark.parametrize("method", ["menu_item", "has_permission", "bind", "shell"])
    def test_a_method_cannot_be_replaced_by_keyword(self, method):
        with pytest.raises(TypeError, match=method):
            MountedFixtureApp(**{method: lambda *args: None})


class TestHasPermission:
    """``check`` is a bool, a callable, or a plain function set on the class."""

    def request(self, rf, **user):
        request = rf.get("/")
        request.user = type("U", (), user)()
        return request

    def test_the_default_check_permits_everyone(self, rf):
        assert MountedApp().has_permission(rf.get("/")) is True

    def test_a_true_check_permits(self, rf):
        assert MountedFixtureApp(check=True).has_permission(rf.get("/")) is True

    def test_a_false_check_refuses(self, rf):
        assert MountedFixtureApp(check=False).has_permission(rf.get("/")) is False

    def test_a_callable_check_is_called_with_the_request(self, rf):
        app = MountedFixtureApp(check=lambda request: request.user.is_staff)

        assert app.has_permission(self.request(rf, is_staff=True)) is True
        assert app.has_permission(self.request(rf, is_staff=False)) is False

    def test_a_plain_function_on_the_class_gets_the_request_alone(self, rf):
        class Staff(MountedFixtureApp):
            def check(request):
                return request.user.is_staff

        assert Staff().has_permission(self.request(rf, is_staff=True)) is True
        assert Staff().has_permission(self.request(rf, is_staff=False)) is False

    def test_a_falsy_callable_result_refuses(self, rf):
        app = MountedFixtureApp(check=lambda request: None)

        assert app.has_permission(rf.get("/")) is False


@pytest.mark.django_db
class TestHostEntryFromInstance:
    """The host's entry, built from the mounted instance, is current on its pages."""

    def test_entry_is_current_on_the_apps_pages(self, client):
        host = MountedFixtureApp(name="Journal")
        urlconf = urlconf_of(*demo_patterns, mount("j/", host))
        template = Template(
            "{% load flex_menu %}{% render_menu menu renderer='sidebar' %}"
        )

        with override_settings(ROOT_URLCONF=urlconf):
            request = client.get("/j/detail/").wsgi_request
            menu = Menu("JournalHostMenu", children=[host.menu_item()])
            html = template.render(Context({"request": request, "menu": menu}))

        link = BeautifulSoup(html, "html.parser").select_one("a")
        assert "Journal" in link.get_text()
        assert "menu-active" in link["class"]


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


def named_app(name, *patterns):
    """A mounted app called ``name`` serving ``patterns``."""
    return MountedApp(
        name=name,
        icon="box",
        menu=TestappMountedMenu,
        urls=list(patterns) or [path("", ok_view, name="index")],
        landing="index",
    )


class TestMountedRegistry:
    """The mounted apps are read back from the URL tree, and bad trees refused."""

    def test_clean_urlconf_lists_its_mounts_in_order(self):
        one, two = named_app("One"), named_app("Two")
        urlconf = urlconf_of(mount("one/", one), mount("two/", two))

        with override_settings(ROOT_URLCONF=urlconf):
            mounts = MountedApp.mounts()

        assert [resolver.app for resolver in mounts] == [one, two]

    def test_clean_urlconf_passes_the_check(self):
        urlconf = urlconf_of(mount("one/", named_app("One")))

        with override_settings(ROOT_URLCONF=urlconf):
            assert check_mounted_apps(None) == []

    def test_urlconf_with_no_mounts_passes_the_check(self):
        with override_settings(ROOT_URLCONF=urlconf_of(path("", ok_view))):
            assert check_mounted_apps(None) == []
            assert MountedApp.mounts() == []

    def test_same_app_mounted_twice_passes_the_check(self):
        app = named_app("Twice")
        urlconf = urlconf_of(mount("a/", app), mount("b/", app))

        with override_settings(ROOT_URLCONF=urlconf):
            assert check_mounted_apps(None) == []
            assert [resolver.app for resolver in MountedApp.mounts()] == [app, app]

    def test_app_mounted_inside_another_is_one_error_naming_both(self):
        inner = named_app("Inner")
        outer = named_app("Outer", mount("inner/", inner))
        urlconf = urlconf_of(mount("outer/", outer))

        with override_settings(ROOT_URLCONF=urlconf):
            errors = check_mounted_apps(None)

        assert len(errors) == 1
        assert "Inner" in errors[0].msg
        assert "Outer" in errors[0].msg
        assert "inside" in errors[0].msg

    def test_server_started_without_checks_raises_the_same_message(self):
        inner = named_app("Inner")
        outer = named_app("Outer", mount("inner/", inner))
        urlconf = urlconf_of(mount("outer/", outer))

        with override_settings(ROOT_URLCONF=urlconf):
            message = check_mounted_apps(None)[0].msg
            with pytest.raises(ImproperlyConfigured) as raised:
                MountedApp.mounts()

        assert str(raised.value) == message

    def test_overriding_root_urlconf_switches_the_registry(self):
        one, two = named_app("One"), named_app("Two")

        with override_settings(ROOT_URLCONF=urlconf_of(mount("one/", one))):
            first = [resolver.app for resolver in MountedApp.mounts()]
        with override_settings(ROOT_URLCONF=urlconf_of(mount("two/", two))):
            second = [resolver.app for resolver in MountedApp.mounts()]

        assert first == [one]
        assert second == [two]

    def test_a_bad_urlconf_leaves_no_stale_error_behind(self):
        inner = named_app("Inner")
        bad = urlconf_of(mount("o/", named_app("Outer", mount("i/", inner))))
        good = urlconf_of(mount("i/", inner))

        with override_settings(ROOT_URLCONF=bad):
            assert len(check_mounted_apps(None)) == 1
        with override_settings(ROOT_URLCONF=good):
            assert check_mounted_apps(None) == []

    def test_the_error_hint_does_not_tell_a_project_to_include_mvp_urls_once(self):
        urlconf = urlconf_of(
            mount("o/", named_app("Outer", mount("i/", named_app("Inner"))))
        )

        with override_settings(ROOT_URLCONF=urlconf):
            hint = check_mounted_apps(None)[0].hint

        assert "mvp.urls" not in hint

    def test_a_per_request_urlconf_gets_its_own_mounts(self, rf):
        one, two = named_app("One"), named_app("Two")
        request = rf.get("/")
        request.urlconf = urlconf_of(mount("two/", two))

        with override_settings(ROOT_URLCONF=urlconf_of(mount("one/", one))):
            mounts = MountedApp.mounts(request)

        assert [resolver.app for resolver in mounts] == [two]

    def test_check_is_registered_for_the_urls_tag(self):
        assert check_mounted_apps in registry.registered_checks
        assert Tags.urls in check_mounted_apps.tags


@pytest.mark.django_db
@pytest.mark.urls("tests.urls_mounted")
class TestMountedPageTitle:
    """A page in a mounted app names the app in its title (FR-008)."""

    def test_titled_page_reads_page_then_app_then_site(self, client):
        response = client.get("/mounted/detail/")

        assert normalised_title(response) == "Detail | Mounted Fixture | example.com"

    def test_untitled_page_reads_a_bar_then_app_then_site(self, client):
        response = client.get("/mounted/")

        assert normalised_title(response) == "| Mounted Fixture | example.com"

    def test_app_name_is_escaped_in_the_title(self, client):
        host = MountedFixtureApp(name="<b>Lib</b> & co")

        with override_settings(ROOT_URLCONF=urlconf_of(mount("j/", host))):
            response = client.get("/j/detail/")

        title = re.search(r"<title>(.*?)</title>", response.content.decode(), re.S)
        assert " ".join(title.group(1).split()) == (
            "Detail | &lt;b&gt;Lib&lt;/b&gt; &amp; co | example.com"
        )

    def test_host_page_title_is_unchanged(self, client):
        response = client.get("/layout/")

        assert normalised_title(response) == "Layout Demo | example.com"

    def test_404_raised_inside_a_mounted_view_names_no_app(self, client):
        response = client.get("/mounted/missing/")

        assert response.status_code == 404
        assert "Mounted Fixture" not in normalised_title(response)
        assert normalised_title(response) == "404 — Page Not Found | example.com"


def menu_labels(response):
    """The brand link, then every link in a sidebar menu, by text."""
    soup = BeautifulSoup(response.content, "html.parser")
    links = soup.select("aside.mvp-sidebar a.mvp-sidebar-brand, aside.mvp-sidebar ul a")
    return [a.get_text(" ", strip=True) for a in links]


def dock_links(response):
    """Every ``(text, href)`` in the mobile dock."""
    soup = BeautifulSoup(response.content, "html.parser")
    return [
        (a.get_text(" ", strip=True), a["href"]) for a in soup.select(".dock a[href]")
    ]


@pytest.mark.django_db
@pytest.mark.urls("tests.urls_mounted")
class TestMountedPageSidebar:
    """The sidebar swaps to the app's menu under a back link (FR-005, FR-007)."""

    def test_app_page_draws_the_app_menu_and_none_of_the_host_menu(self, client):
        labels = menu_labels(client.get("/mounted/"))

        assert labels[2:] == ["Mounted Index", "Mounted Detail"]
        assert "Home" not in labels
        assert "Layout" not in labels

    def test_every_page_of_the_app_draws_the_app_menu(self, client):
        labels = menu_labels(client.get("/mounted/detail/"))

        assert labels[2:] == ["Mounted Index", "Mounted Detail"]

    def test_back_link_reads_back_to_the_site_name_and_goes_to_the_brand_url(
        self, client
    ):
        soup = BeautifulSoup(client.get("/mounted/").content, "html.parser")
        back = soup.select_one("aside.mvp-sidebar a[data-back-link]")
        brand = soup.select_one("aside.mvp-sidebar a.mvp-sidebar-brand")

        assert back.get_text(" ", strip=True) == "Back to example.com"
        assert back["href"] == brand["href"] == "/"

    def test_back_link_comes_first_in_the_menu_area(self, client):
        assert menu_labels(client.get("/mounted/"))[1] == "Back to example.com"

    def test_host_page_draws_the_host_menu_and_no_back_link(self, client):
        response = client.get("/layout/")

        assert "Layout" in menu_labels(response)
        assert b"data-back-link" not in response.content
        assert "Mounted Index" not in menu_labels(response)

    def test_dock_is_the_same_on_an_app_page_as_on_a_host_page(self, client):
        assert dock_links(client.get("/mounted/")) == dock_links(client.get("/layout/"))

    def test_error_page_inside_the_app_draws_no_back_link(self, client):
        response = client.get("/mounted/missing/")

        assert response.status_code == 404
        assert b"data-back-link" not in response.content


HostMenu = Menu("MountedHostTestMenu", children=[testapp_mounted.menu_item()])


def render_host_menu(request, renderer):
    """Draw ``HostMenu`` the way a host's sidebar or dock draws its own menu."""
    template = Template("{% load flex_menu %}{% render_menu menu renderer=renderer %}")
    context = Context({"request": request, "menu": HostMenu, "renderer": renderer})
    return BeautifulSoup(template.render(context), "html.parser")


@pytest.mark.django_db
@pytest.mark.urls("tests.urls_mounted")
class TestMountedAppMenuItem:
    """The host's own entry for a mounted app (FR-004, FR-009)."""

    def test_entry_shows_the_apps_name_icon_and_landing_address(self, client):
        request = client.get("/layout/").wsgi_request

        link = render_host_menu(request, "sidebar").select_one("a")

        assert link["href"] == "/mounted/"
        assert link.get_text(" ", strip=True) == "Mounted Fixture"
        assert link.select_one("i.bi-book") is not None

    def test_entry_is_current_on_the_apps_landing_page(self, client):
        request = client.get("/mounted/").wsgi_request

        link = render_host_menu(request, "sidebar").select_one("a")

        assert "menu-active" in link["class"]

    def test_entry_is_current_on_every_page_of_the_app_not_just_the_landing(
        self, client
    ):
        request = client.get("/mounted/detail/").wsgi_request

        link = render_host_menu(request, "sidebar").select_one("a")

        assert "menu-active" in link["class"]

    def test_dock_entry_is_current_on_a_detail_page(self, client):
        request = client.get("/mounted/detail/").wsgi_request

        link = render_host_menu(request, "dock").select_one("a")

        assert "dock-active" in link["class"]
        assert link["aria-current"] == "page"

    def test_entry_is_not_current_on_a_host_page(self, client):
        request = client.get("/layout/").wsgi_request

        sidebar = render_host_menu(request, "sidebar").select_one("a")
        dock = render_host_menu(request, "dock").select_one("a")

        assert "menu-active" not in sidebar["class"]
        assert "dock-active" not in dock["class"]

    def test_entry_is_not_current_for_another_apps_page(self, client):
        other = named_app("Other")
        entry = other.menu_item()
        request = client.get("/mounted/detail/").wsgi_request

        assert entry.process(request).selected is False

    def test_entry_takes_a_name_and_extra_context(self):
        entry = testapp_mounted.menu_item(name="library", badge="3")

        assert entry.name == "library"
        assert entry.extra_context["badge"] == "3"
        assert entry.extra_context["label"] == "Mounted Fixture"
        assert entry.extra_context["icon"] == "book"

    def test_entry_defaults_its_name_from_the_landing(self):
        assert testapp_mounted.menu_item().name == "testapp_mounted-index"

    def test_entry_without_a_request_is_not_current(self):
        entry = testapp_mounted.menu_item()

        assert entry.process(None).selected is False


def host_linking_app(name, *entries):
    """A mounted app whose menu links ``entries``, each a ``(name, view_name)``.

    The app serves one page of its own and is mounted at ``own/``; the menu
    entries may point anywhere in the URLconf, host pages included.
    """
    menu = Menu(
        f"{name}Menu",
        children=[
            MenuItem(name=entry, view_name=view_name, extra_context={"label": entry})
            for entry, view_name in entries
        ],
    )
    return MountedApp(
        name=name,
        icon="book",
        menu=menu,
        urls=[path("", ok_view, name="index")],
        landing="index",
    )


def host_urlconf(*mounts):
    """The demo's URLs with ``mounts`` added, as a URLconf ``override_settings`` takes."""
    return urlconf_of(*demo_patterns, *mounts)


@pytest.mark.django_db
class TestPageClaimedByAMenu:
    """A page no mount served belongs to the first app whose menu marks it current
    (FR-019, decision D13)."""

    def test_host_page_linked_from_the_apps_menu_is_the_app(self, client, settings):
        app = host_linking_app("Linker", ("layout", "layout"))
        settings.ROOT_URLCONF = host_urlconf(mount("own/", app))

        assert for_path(client, "/layout/") is app

    def test_host_page_no_menu_links_is_no_app(self, client, settings):
        app = host_linking_app("Linker", ("layout", "layout"))
        settings.ROOT_URLCONF = host_urlconf(mount("own/", app))

        assert for_path(client, "/theme/") is None

    def test_page_served_through_a_mount_beats_a_menu_that_claims_it(
        self, client, settings
    ):
        claimer = host_linking_app("Claimer", ("own", "index"))
        owner = host_linking_app("Owner")
        settings.ROOT_URLCONF = host_urlconf(
            mount("claimer/", claimer), mount("owner/", owner)
        )

        assert for_path(client, "/owner/") is owner

    def test_first_mount_in_url_order_wins_when_two_menus_link_the_page(
        self, client, settings
    ):
        first = host_linking_app("First", ("layout", "layout"))
        second = host_linking_app("Second", ("layout", "layout"))
        settings.ROOT_URLCONF = host_urlconf(
            mount("first/", first), mount("second/", second)
        )

        assert for_path(client, "/layout/") is first

    def test_menu_holding_another_apps_entry_resolves_without_recursion(
        self, client, settings
    ):
        other = host_linking_app("Other")
        holder = host_linking_app("Holder", ("layout", "layout"))
        holder.menu.append(other.menu_item())
        settings.ROOT_URLCONF = host_urlconf(
            mount("holder/", holder), mount("other/", other)
        )

        assert for_path(client, "/layout/") is holder

    def test_menu_holding_another_apps_entry_alone_claims_nothing(
        self, client, settings
    ):
        other = host_linking_app("Other")
        holder = host_linking_app("Holder")
        holder.menu.append(other.menu_item())
        settings.ROOT_URLCONF = host_urlconf(
            mount("holder/", holder), mount("other/", other)
        )

        assert for_path(client, "/theme/") is None

    def test_the_answer_is_kept_on_the_request(self, client, settings):
        app = host_linking_app("Linker", ("layout", "layout"))
        settings.ROOT_URLCONF = host_urlconf(mount("own/", app))
        request = client.get("/layout/").wsgi_request

        first = MountedApp.for_request(request)
        app.menu.children[0].parent = None

        assert MountedApp.for_request(request) is first


MAIN_URLCONF = "tests.urls_mounted_main"


@pytest.mark.django_db
@pytest.mark.urls(MAIN_URLCONF)
class TestMainApp:
    """An app mounted with ``main=True`` is the site's own menu (FR-016, FR-017)."""

    def test_host_page_draws_the_main_apps_menu_and_none_of_the_app_menu(self, client):
        labels = menu_labels(client.get("/layout/"))

        assert "Mounted Index" in labels
        assert "Mounted Detail" in labels
        assert "Layout" not in labels

    def test_host_page_has_no_back_link(self, client):
        response = client.get("/layout/")

        assert b"data-back-link" not in response.content

    def test_host_page_title_is_the_same_as_without_a_main_app(self, client, settings):
        with_main = normalised_title(client.get("/layout/"))
        settings.ROOT_URLCONF = PLAIN_URLCONF
        without_main = normalised_title(client.get("/layout/"))

        assert with_main == without_main
        assert "Mounted Fixture" not in with_main

    def test_main_apps_own_page_draws_its_menu_without_a_back_link(self, client):
        response = client.get("/detail/")

        assert response.status_code == 200
        assert b'id="testapp-mounted-detail"' in response.content
        assert "Mounted Index" in menu_labels(response)
        assert b"data-back-link" not in response.content

    def test_main_apps_own_page_title_carries_no_app_name(self, client):
        assert "Mounted Fixture" not in normalised_title(client.get("/detail/"))

    def test_account_center_swaps_to_its_own_menu_with_a_back_link(
        self, admin_client
    ):
        response = admin_client.get("/account/")
        labels = menu_labels(response)

        assert response.status_code == 200

        assert b"data-back-link" in response.content
        assert "Overview" in labels
        assert "Mounted Index" not in labels
        assert "Mounted Detail" not in labels

    def test_app_menu_is_not_drawn_on_any_page(self, client):
        assert "Layout" not in menu_labels(client.get("/detail/"))

    def test_main_app_refusing_the_request_falls_back_to_the_app_menu(
        self, client, monkeypatch
    ):
        monkeypatch.setattr(testapp_mounted, "check", lambda request: False)

        labels = menu_labels(client.get("/layout/"))

        assert "Layout" in labels
        assert "Mounted Index" not in labels

    def test_main_app_menu_linking_a_host_page_does_not_claim_it(self, client):
        response = client.get("/layout/")

        assert MountedApp.for_request(response.wsgi_request) is None


@pytest.mark.django_db
@pytest.mark.urls("tests.urls_mounted_root")
class TestAppMountedWithoutMain:
    """The same app without ``main`` behaves as in US-1 (scenario 4)."""

    def test_host_page_draws_the_host_menu(self, client):
        labels = menu_labels(client.get("/layout/"))

        assert "Layout" in labels
        assert "Mounted Index" not in labels

    def test_apps_own_page_draws_a_back_link(self, client):
        response = client.get("/detail/")

        assert b"data-back-link" in response.content
        assert "Mounted Fixture" in normalised_title(response)


class TestMainAppRegistry:
    """Two main apps are refused, and ``main`` belongs to the mount (FR-018)."""

    def test_the_main_app_is_found_among_the_mounts(self):
        main = named_app("Main")
        urlconf = urlconf_of(
            mount("other/", named_app("Other")), mount("", main, main=True)
        )

        with override_settings(ROOT_URLCONF=urlconf):
            assert MountedApp.main() is main

    def test_no_main_app_is_none(self):
        urlconf = urlconf_of(mount("one/", named_app("One")))

        with override_settings(ROOT_URLCONF=urlconf):
            assert MountedApp.main() is None

    def test_two_main_apps_are_one_error_naming_both(self):
        urlconf = urlconf_of(
            mount("a/", named_app("First"), main=True),
            mount("b/", named_app("Second"), main=True),
        )

        with override_settings(ROOT_URLCONF=urlconf):
            errors = check_mounted_apps(None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert "First" in errors[0].msg
        assert "Second" in errors[0].msg
        assert "main" in errors[0].msg

    def test_two_main_apps_raise_from_the_registry_walk(self):
        urlconf = urlconf_of(
            mount("a/", named_app("First"), main=True),
            mount("b/", named_app("Second"), main=True),
        )

        with override_settings(ROOT_URLCONF=urlconf):
            with pytest.raises(ImproperlyConfigured, match="First.*Second"):
                MountedApp.mounts()

    def test_one_main_app_among_others_passes_the_check(self):
        urlconf = urlconf_of(
            mount("a/", named_app("First"), main=True),
            mount("b/", named_app("Second")),
        )

        with override_settings(ROOT_URLCONF=urlconf):
            assert check_mounted_apps(None) == []

    def test_main_is_a_mount_keyword_and_not_a_mounted_app_one(self):
        with pytest.raises(TypeError):
            MountedApp(  # type: ignore[call-arg]
                name="Main",
                icon="box",
                menu=TestappMountedMenu,
                urls=[],
                landing="index",
                main=True,
            )
        assert "main" in inspect.signature(mount).parameters


CHECKED_URLCONF = "tests.urls_mounted_checked"


@pytest.fixture
def staff_user(django_user_model):
    return django_user_model.objects.create_user(
        "staff", password="pw", is_staff=True
    )


@pytest.fixture
def regular_user(django_user_model):
    return django_user_model.objects.create_user("regular", password="pw")


def entry_visible_to(user, path="/layout/", *, client, app=testapp_mounted_staff):
    """Whether the host's sidebar draws ``app``'s entry for ``user``."""
    if user is not None:
        client.force_login(user)
    request = client.get(path).wsgi_request
    template = Template("{% load flex_menu %}{% render_menu menu renderer='sidebar' %}")
    menu = Menu("CheckedHostMenu", children=[app.menu_item()])
    context = Context({"request": request, "menu": menu})
    return bool(BeautifulSoup(template.render(context), "html.parser").select("a"))


@pytest.mark.django_db
@pytest.mark.urls(CHECKED_URLCONF)
class TestMountedAppCheck:
    """An app's ``check`` hides it from, and refuses, everyone it excludes
    (FR-012, FR-013, decision D4)."""

    def test_host_entry_is_shown_to_staff(self, client, staff_user):
        assert entry_visible_to(staff_user, client=client) is True

    def test_host_entry_is_absent_for_a_regular_user(self, client, regular_user):
        assert entry_visible_to(regular_user, client=client) is False

    def test_host_entry_is_absent_for_an_anonymous_visitor(self, client):
        assert entry_visible_to(None, client=client) is False

    def test_anonymous_visitor_is_sent_to_sign_in_with_next(self, client):
        response = client.get("/mounted/detail/")

        assert response.status_code == 302
        assert response["Location"] == "/account/login/?next=/mounted/detail/"

    def test_signed_in_person_the_check_refuses_is_forbidden(
        self, client, regular_user
    ):
        client.force_login(regular_user)

        response = client.get("/mounted/")

        assert response.status_code == 403

    def test_forbidden_page_title_names_no_app(self, client, regular_user):
        client.force_login(regular_user)

        response = client.get("/mounted/")

        assert "Staff Fixture" not in normalised_title(response)

    def test_a_project_403_page_draws_app_menu_not_the_apps(
        self, client, regular_user
    ):
        client.force_login(regular_user)

        response = client.get("/mounted/")

        assert b'id="testapp-mounted-forbidden"' in response.content
        labels = menu_labels(response)
        assert "Mounted Index" not in labels
        assert "Mounted Detail" not in labels
        assert b"data-back-link" not in response.content

    def test_staff_see_the_page_and_the_apps_sidebar(self, client, staff_user):
        client.force_login(staff_user)

        response = client.get("/mounted/")

        assert response.status_code == 200
        assert "Mounted Index" in menu_labels(response)

    def test_lookup_finds_no_app_for_a_refused_request(self, client, regular_user):
        client.force_login(regular_user)

        response = client.get("/mounted/")

        assert MountedApp.for_request(response.wsgi_request) is None

    @pytest.mark.urls("tests.urls_mounted")
    def test_an_app_with_no_check_is_open_to_everyone(self, client):
        assert client.get("/mounted/").status_code == 200
        assert entry_visible_to(None, client=client, app=testapp_mounted) is True


@pytest.mark.django_db
class TestMountedAppCheckOnOtherPaths:
    """The check also decides menu claims and async views."""

    def test_menu_claim_skips_an_app_whose_check_fails(
        self, client, settings, regular_user
    ):
        app = host_linking_app("Linker", ("layout", "layout"))
        app.check = lambda request: request.user.is_staff
        settings.ROOT_URLCONF = host_urlconf(mount("own/", app))
        client.force_login(regular_user)

        assert for_path(client, "/layout/") is None

    def test_menu_claim_holds_for_a_person_the_check_admits(
        self, client, settings, staff_user
    ):
        app = host_linking_app("Linker", ("layout", "layout"))
        app.check = lambda request: request.user.is_staff
        settings.ROOT_URLCONF = host_urlconf(mount("own/", app))
        client.force_login(staff_user)

        assert for_path(client, "/layout/") is app

    def test_menu_claim_passes_over_a_refusing_app_to_the_next(
        self, client, settings, regular_user
    ):
        first = host_linking_app("First", ("layout", "layout"))
        first.check = lambda request: request.user.is_staff
        second = host_linking_app("Second", ("layout", "layout"))
        settings.ROOT_URLCONF = host_urlconf(
            mount("first/", first), mount("second/", second)
        )
        client.force_login(regular_user)

        assert for_path(client, "/layout/") is second

    def test_async_view_behind_a_failing_check_is_refused(self):
        app = throwaway_app(path("x/", async_ok_view, name="x"))
        app.check = lambda request: False
        match = resolve("/m/x/", urlconf=urlconf_of(mount("m/", app)))
        request = AsyncRequestFactory().get("/m/x/")
        request.user = AnonymousUser()

        response = asyncio.run(match.func(request))

        assert response.status_code == 302

    def test_async_view_behind_a_passing_check_runs(self):
        app = throwaway_app(path("x/", async_ok_view, name="x"))
        app.check = lambda request: True
        match = resolve("/m/x/", urlconf=urlconf_of(mount("m/", app)))
        request = AsyncRequestFactory().get("/m/x/")
        request.user = AnonymousUser()

        response = asyncio.run(match.func(request))

        assert response.content == b"ok"
