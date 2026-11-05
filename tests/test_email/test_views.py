"""Tests for mvp.email.views and the routes ``mvp.urls`` adds while ``DEBUG`` is on (FS-044)."""

from urllib.parse import parse_qs, urlparse

import pytest
from bs4 import BeautifulSoup
from django.conf import settings as django_settings
from django.test import override_settings
from django.urls import NoReverseMatch, reverse

from mvp.email.previews import EmailPreview, register
from tests.conftest import reload_pwa_urlconfs

CONFIRM = "testapp_email/email/confirm_message.html"
LANGUAGE = "testapp_email/email/language_message.html"
BROKEN = "testapp_email/email/does-not-exist_message.html"
PAGE = "mvp-email-preview"
FRAME = "mvp-email-preview-frame"


def routes_with_debug(debug):
    """Rebuild ``mvp.urls`` as it is when it is imported with ``DEBUG`` set to ``debug``."""
    with override_settings(DEBUG=debug):
        reload_pwa_urlconfs()


@pytest.fixture
def debug_on():
    """The email routes as they are while ``DEBUG`` is on."""
    routes_with_debug(True)
    yield
    # The process starts with the demo's DEBUG on, so that is the state to hand on.
    routes_with_debug(True)


@pytest.fixture
def debug_off():
    """The email routes as they are while ``DEBUG`` is off."""
    routes_with_debug(False)
    yield
    routes_with_debug(True)


@pytest.fixture(autouse=True)
def previews(monkeypatch):
    """A registry holding a plain email, a two-language one and a broken one."""
    monkeypatch.setattr(EmailPreview, "registry", {})
    register(
        CONFIRM,
        "Confirm your address",
        {"name": "Ada", "url": "https://example.org/confirm/abc/"},
        subject="testapp_email/email/confirm_subject.txt",
        text="testapp_email/email/confirm_message.txt",
        group="Accounts",
    )
    register(
        LANGUAGE,
        "Language",
        {},
        subject="testapp_email/email/language_subject.txt",
        text="testapp_email/email/language_message.txt",
        group="Accounts",
    )
    register(BROKEN, "Broken", {}, group="Other")


@pytest.fixture
def staff_client(client, staff_user):
    client.force_login(staff_user)
    return client


def page(client, **query):
    return client.get(reverse(PAGE), query)


def frame(client, template=CONFIRM, **query):
    return client.get(reverse(FRAME, args=[template]), query)


def soup(response):
    return BeautifulSoup(response.content, "html.parser")


@pytest.mark.django_db
@pytest.mark.usefixtures("debug_on")
class TestAccess:
    def test_an_anonymous_visitor_is_sent_to_sign_in(self, client):
        response = page(client)

        assert response.status_code == 302
        assert response["Location"].startswith(reverse(django_settings.LOGIN_URL))

    def test_a_signed_in_user_who_is_not_staff_gets_403(self, client, user):
        client.force_login(user)

        assert page(client).status_code == 403

    def test_the_frame_is_closed_to_anonymous_and_non_staff_visitors_too(self, client, user):
        assert frame(client).status_code == 302

        client.force_login(user)

        assert frame(client).status_code == 403

    def test_a_staff_member_gets_the_page_and_the_frame(self, staff_client):
        assert page(staff_client).status_code == 200
        assert frame(staff_client).status_code == 200


@pytest.mark.django_db
class TestRoutes:
    def test_while_debug_is_on_the_page_and_the_frame_have_routes(self, debug_on):
        assert reverse(PAGE) == "/emails/"
        assert reverse(FRAME, args=[CONFIRM]) == f"/emails/frame/{CONFIRM}"

    def test_while_debug_is_off_neither_route_exists(self, debug_off, staff_client):
        with pytest.raises(NoReverseMatch):
            reverse(PAGE)
        with pytest.raises(NoReverseMatch):
            reverse(FRAME, args=[CONFIRM])

        assert staff_client.get("/emails/").status_code == 404
        assert staff_client.get(f"/emails/frame/{CONFIRM}").status_code == 404


@pytest.mark.django_db
@pytest.mark.usefixtures("debug_on")
class TestPreviewPage:
    def test_every_declared_email_is_listed_under_its_group(self, staff_client):
        response = page(staff_client)

        by_group = {}
        for link in response.context["email_links"]:
            by_group.setdefault(link["preview"].group, []).append(link["preview"].template)
        assert by_group == {"Accounts": [CONFIRM, LANGUAGE], "Other": [BROKEN]}

    def test_the_first_email_is_selected_and_shows_its_rendered_subject(self, staff_client):
        response = page(staff_client)

        assert response.context["selected"].template == CONFIRM
        assert soup(response).find(id="email-subject").get_text(strip=True) == "Confirm your address, Ada"

    def test_the_email_query_selects_another_email(self, staff_client):
        response = page(staff_client, email=LANGUAGE)

        assert response.context["selected"].template == LANGUAGE

    def test_the_email_shows_in_an_iframe_of_the_frame_view(self, staff_client):
        response = page(staff_client, email=LANGUAGE)

        src = soup(response).find("iframe")["src"]
        assert urlparse(src).path == reverse(FRAME, args=[LANGUAGE])
        assert parse_qs(urlparse(src).query)["email"] == [LANGUAGE]

    def test_plain_text_part_shows_the_text_template_and_no_iframe(self, staff_client):
        response = page(staff_client, part="text")

        html = soup(response)
        assert "Hello Ada," in html.find("pre").get_text()
        assert html.find("iframe") is None

    def test_the_plain_text_choice_is_offered_only_for_an_email_with_a_text_template(self, staff_client):
        register("testapp_email/email/confirm_message.html", "No text", {"name": "Ada", "url": "x"}, group="Accounts")

        response = page(staff_client)

        part = next(t for t in response.context["toggles"] if t["key"] == "part")
        assert [c["value"] for c in part["choices"]] == ["html"]

    def test_part_text_falls_back_to_html_when_the_email_has_no_text_template(self, staff_client):
        register(CONFIRM, "No text", {"name": "Ada", "url": "x"})

        response = page(staff_client, part="text")

        assert response.context["opts"]["part"] == "html"

    def test_lang_renders_the_email_in_that_language(self, staff_client):
        response = page(staff_client, email=LANGUAGE, lang="de", part="text")

        assert "Plain text in de" in soup(response).find("pre").get_text()
        assert soup(response).find(id="email-subject").get_text(strip=True) == "Subject in de"

    def test_the_language_choice_is_offered_only_with_more_than_one_language(self, staff_client, settings):
        settings.LANGUAGES = [("en", "English")]
        assert "lang" not in [t["key"] for t in page(staff_client).context["toggles"]]

        settings.LANGUAGES = [("en", "English"), ("de", "German")]
        toggles = {t["key"]: t for t in page(staff_client).context["toggles"]}
        assert [c["value"] for c in toggles["lang"]["choices"]] == ["en", "de"]

    def test_an_unknown_language_is_ignored(self, staff_client):
        response = page(staff_client, email=LANGUAGE, lang="xx", part="text")

        assert "Plain text in en" in soup(response).find("pre").get_text()

    def test_a_broken_email_shows_its_error_and_the_list_still_loads(self, staff_client):
        response = page(staff_client, email=BROKEN)

        assert response.status_code == 200
        assert "TemplateDoesNotExist" in response.context["error"]
        assert soup(response).find("iframe") is None
        assert len(response.context["email_links"]) == 3

    def test_with_no_declared_email_the_page_still_loads(self, staff_client, monkeypatch):
        monkeypatch.setattr(EmailPreview, "registry", {})

        response = page(staff_client)

        assert response.status_code == 200
        assert response.context["selected"] is None

    def test_the_controls_keep_the_current_choices_in_their_links(self, staff_client):
        response = page(staff_client, scheme="dark", width="phone")

        toggles = {t["key"]: t for t in response.context["toggles"]}
        images_off = next(c for c in toggles["images"]["choices"] if c["value"] == "off")
        query = parse_qs(images_off["url"].lstrip("?"))
        assert (query["scheme"], query["width"], query["images"]) == (["dark"], ["phone"], ["off"])


@pytest.mark.django_db
@pytest.mark.usefixtures("debug_on")
class TestFrame:
    def test_it_is_the_email_html_exactly_as_rendered(self, staff_client):
        from django.template.loader import render_to_string

        expected = render_to_string(CONFIRM, {"name": "Ada", "url": "https://example.org/confirm/abc/"})

        assert frame(staff_client).content.decode() == expected

    def test_an_unregistered_template_is_a_404(self, staff_client):
        assert frame(staff_client, "testapp_email/email/confirm_message.txt").status_code == 404

    def test_dark_scheme_turns_the_dark_rules_on_for_every_width(self, staff_client):
        register("mvp/email/base.html", "Base", {}, group="Accounts")

        light = frame(staff_client, "mvp/email/base.html").content.decode()
        dark = frame(staff_client, "mvp/email/base.html", scheme="dark").content.decode()

        assert "@media (prefers-color-scheme: dark)" in light
        assert "@media (prefers-color-scheme: dark)" not in dark

    def test_blocked_images_have_an_empty_src(self, staff_client):
        register("mvp/email/base.html", "Base", {}, group="Accounts")

        shown = frame(staff_client, "mvp/email/base.html").content.decode()
        blocked = frame(staff_client, "mvp/email/base.html", images="off").content.decode()

        assert 'src="' in shown
        assert 'src=""' in blocked
        assert BeautifulSoup(shown, "html.parser").find("img")["src"] not in blocked

    def test_lang_renders_the_frame_in_that_language(self, staff_client):
        assert "Written in de" in frame(staff_client, LANGUAGE, lang="de").content.decode()

    @override_settings(X_FRAME_OPTIONS="DENY")
    def test_the_page_can_frame_it_under_the_default_clickjacking_setting(self, staff_client):
        assert frame(staff_client)["X-Frame-Options"] == "SAMEORIGIN"


@pytest.mark.django_db
@pytest.mark.usefixtures("debug_on")
class TestDemoMenu:
    def emails_item(self, rf, staff_user):
        from mvp.menus import AppMenu

        request = rf.get("/")
        request.user = staff_user
        return AppMenu.process(request).get("emails")

    def test_the_emails_entry_is_shown_while_debug_is_on(self, rf, staff_user, settings):
        settings.DEBUG = True

        item = self.emails_item(rf, staff_user)

        assert item.url == reverse(PAGE)

    def test_the_emails_entry_is_left_out_while_debug_is_off(self, rf, staff_user, settings):
        settings.DEBUG = False

        assert self.emails_item(rf, staff_user) is None
