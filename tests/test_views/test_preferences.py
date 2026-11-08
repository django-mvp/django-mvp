"""Tests for ``mvp.views.preferences`` — the Account Center's preferences page.

Source: mvp/views/preferences.py, mvp/views/account.py, mvp/menus.py,
mvp/templates/mvp/account/preferences.html
"""

import pytest
from bs4 import BeautifulSoup
from django.contrib.messages import get_messages
from django.urls import reverse
from object_preferences.registry import registry

from tests.test_views.test_account import sidebar_hrefs, sidebar_menu_hrefs

URL_NAME = "account-preferences"


def values(**overrides):
    """A valid submission of the page's one group, with ``overrides`` applied."""
    data = {"locale-timezone": "Asia/Tokyo", "locale-language": "de"}
    return {**data, **overrides}


def stored(person):
    """What ``person``'s locale group reads as after a fresh read from the database."""
    person.refresh_from_db()
    return dict(registry.get_preferences(person)["locale"])


@pytest.fixture
def defaults(settings):
    return {"timezone": settings.TIME_ZONE, "language": ""}


@pytest.fixture(autouse=True)
def three_languages(settings):
    settings.LANGUAGES = [("en", "English"), ("de", "German"), ("fr", "French")]


@pytest.fixture
def signed_in(client, user):
    client.force_login(user)
    return client


@pytest.mark.django_db
class TestOffersThePage:
    def test_the_landing_page_has_a_card_linking_to_it(self, signed_in):
        response = signed_in.get(reverse("account-center"))

        soup = BeautifulSoup(response.content, "html.parser")
        region = soup.find(id="account-center-cards")
        assert region.find("a", href=reverse(URL_NAME)) is not None

    def test_the_menu_lists_it(self, signed_in):
        response = signed_in.get(reverse("account-center"))

        assert reverse(URL_NAME) in sidebar_menu_hrefs(response)

    def test_it_sits_inside_the_account_centers_mount(self, signed_in):
        assert reverse(URL_NAME) == "/account/preferences/"

        response = signed_in.get(reverse(URL_NAME))

        assert response.status_code == 200
        assert reverse("account-center") in sidebar_hrefs(response)
        assert reverse("home") not in sidebar_menu_hrefs(response)


@pytest.mark.django_db
class TestAccess:
    def test_a_visitor_is_sent_to_sign_in(self, client):
        response = client.get(reverse(URL_NAME))

        assert response.status_code == 302
        assert response.url.startswith(reverse("account_login"))

    def test_a_visitors_post_saves_nothing(self, client, user, defaults):
        response = client.post(reverse(URL_NAME), values())

        assert response.status_code == 302
        assert stored(user) == defaults

    def test_it_shows_the_signed_in_person_whatever_the_request_names(
        self, signed_in, user, make_user
    ):
        other = make_user("other")
        other.preferences = {"locale": {"timezone": "Asia/Tokyo"}}
        other.save()

        response = signed_in.get(reverse(URL_NAME), {"pk": other.pk, "id": other.pk})

        assert response.context["object"] == user
        assert response.context["forms"]["locale"].initial["timezone"] != "Asia/Tokyo"

    def test_a_post_naming_another_person_saves_only_the_signed_in_one(
        self, signed_in, user, make_user, defaults
    ):
        other = make_user("other")

        signed_in.post(
            reverse(URL_NAME), values(pk=other.pk, id=other.pk, user=other.pk)
        )

        assert stored(user) == {"timezone": "Asia/Tokyo", "language": "de"}
        assert stored(other) == defaults


@pytest.mark.django_db
class TestSaving:
    def test_one_group_is_one_fieldset_and_there_is_one_save_button(self, signed_in):
        response = signed_in.get(reverse(URL_NAME))

        soup = BeautifulSoup(response.content, "html.parser")
        form = soup.select_one("main form")
        assert len(form.find_all("fieldset", recursive=False)) == len(
            response.context["forms"]
        )
        assert len(form.find_all("button", attrs={"type": "submit"})) == 1

    def test_each_fieldset_is_headed_by_its_groups_translatable_label(self, signed_in):
        from django.contrib.auth import get_user_model
        from django.utils.functional import Promise

        group = registry.get_group(get_user_model(), "locale")
        response = signed_in.get(reverse(URL_NAME))

        legend = BeautifulSoup(response.content, "html.parser").select_one(
            "main form > fieldset legend"
        )
        assert isinstance(group.verbose_name, Promise)
        assert legend.get_text(strip=True) == str(group.verbose_name)
        assert legend.get_text(strip=True) != group.name.capitalize()

    def test_valid_values_redirect_back_with_a_success_message(self, signed_in, user):
        response = signed_in.post(reverse(URL_NAME), values())

        assert response.status_code == 302
        assert response.url == reverse(URL_NAME)
        assert [m.level_tag for m in get_messages(response.wsgi_request)] == [
            "success"
        ]
        assert stored(user) == {"timezone": "Asia/Tokyo", "language": "de"}

    def test_the_next_page_uses_what_was_saved(self, signed_in):
        signed_in.post(reverse(URL_NAME), values())

        response = signed_in.get(reverse("account-center"))

        assert response.headers["Content-Language"] == "de"
        assert response.wsgi_request.LANGUAGE_CODE == "de"

    def test_the_page_shows_what_is_saved_as_selected(self, signed_in):
        signed_in.post(reverse(URL_NAME), values())

        response = signed_in.get(reverse(URL_NAME))

        soup = BeautifulSoup(response.content, "html.parser")
        selected = {
            option["value"] for option in soup.select("option[selected]")
        }
        assert {"Asia/Tokyo", "de"} <= selected

    def test_an_invalid_submission_saves_nothing_and_marks_the_field(
        self, signed_in, user, defaults
    ):
        response = signed_in.post(reverse(URL_NAME), values(**{"locale-timezone": "x"}))

        assert response.status_code == 200
        assert stored(user) == defaults
        assert response.context["forms"]["locale"].has_error("timezone")
        soup = BeautifulSoup(response.content, "html.parser")
        assert soup.select("[aria-invalid='true']")


@pytest.mark.django_db
class TestTimezoneControl:
    def test_the_timezone_is_a_searchable_control_whose_assets_the_page_loads(
        self, signed_in
    ):
        response = signed_in.get(reverse(URL_NAME))

        soup = BeautifulSoup(response.content, "html.parser")
        select = soup.select_one("select[name='locale-timezone']")
        assert select.has_attr("data-tom-select")
        scripts = [tag["src"] for tag in soup.find_all("script", src=True)]
        styles = [tag["href"] for tag in soup.find_all("link", rel="stylesheet")]
        assert any(src.endswith("mvp_forms/tomselect.js") for src in scripts)
        assert any("tom-select" in src for src in scripts)
        assert any("tom-select" in href for href in styles)
