"""Tests for ``<c-mvp.messages>``: one alert per Django message.

Each message is drawn as a daisy-cotton alert whose variant follows the message's
level tag. ``debug`` takes the ``info`` variant, since daisy-cotton has no debug
alert. A level tag daisy-cotton has no variant for, such as one a project adds
through ``MESSAGE_TAGS``, draws its message in a plain alert.

A message can carry one action, a link or a button, written into its
``extra_tags`` by ``mvp.utils.action_tags``. A message with an action stays until
it is used or dismissed, and the list can be drawn as an htmx out-of-band swap.

Source: mvp/templates/cotton/mvp/messages.html
"""

import pytest
from django.contrib import messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory

from mvp.utils import action_tags

LEVEL_VARIANTS = {
    messages.DEBUG: "info",
    messages.INFO: "info",
    messages.SUCCESS: "success",
    messages.WARNING: "warning",
    messages.ERROR: "error",
}
VARIANTS = frozenset(LEVEL_VARIANTS.values())
# A level no tag is registered for: its level tag is empty, so the alert gets no
# variant and no icon.
UNTAGGED_LEVEL = 35
# A level a project registers a tag of its own for.
PROJECT_LEVEL = 45
PROJECT_TAGS = ("notice", "in")


@pytest.fixture
def render_messages(cotton_render_string_soup):
    """Render the component over messages added at the given levels."""

    def render(*levels, extra_tags="", attrs=""):
        request = RequestFactory().get("/")
        request.session = {}
        request._messages = FallbackStorage(request)
        messages.set_level(request, messages.DEBUG)
        for level in levels:
            messages.add_message(
                request, level, f"message at level {level}", extra_tags=extra_tags
            )
        return cotton_render_string_soup(
            f"<c-mvp.messages :messages='messages' {attrs} />",
            context={
                "messages": messages.get_messages(request),
                "request": request,
                "csrf_token": "token",
            },
        )

    return render


class TestMessageLevels:
    @pytest.mark.parametrize(("level", "variant"), LEVEL_VARIANTS.items())
    def test_a_message_draws_one_alert_holding_it(
        self, render_messages, level, variant
    ):
        soup = render_messages(level)

        alerts = soup.select(".toast > [role='alert']")
        assert len(alerts) == 1
        assert f"message at level {level}" in alerts[0].get_text()
        assert f"alert-{variant}" in alerts[0]["class"]

    def test_each_message_in_a_list_draws_its_own_alert(self, render_messages):
        soup = render_messages(*LEVEL_VARIANTS)

        alerts = soup.select(".toast > [role='alert']")
        assert len(alerts) == len(LEVEL_VARIANTS)

    def test_a_level_tag_outside_the_four_draws_its_message_and_no_variant(
        self, render_messages
    ):
        soup = render_messages(UNTAGGED_LEVEL)

        alerts = soup.select(".toast > [role='alert']")
        assert len(alerts) == 1
        assert f"message at level {UNTAGGED_LEVEL}" in alerts[0].get_text()
        assert not {f"alert-{variant}" for variant in VARIANTS} & set(
            alerts[0]["class"]
        )


class TestAProjectsOwnLevelTag:
    @pytest.mark.parametrize("tag", PROJECT_TAGS)
    def test_a_message_at_a_tag_a_project_added_draws_its_message(
        self, render_messages, settings, tag
    ):
        settings.MESSAGE_TAGS = {PROJECT_LEVEL: tag}

        soup = render_messages(PROJECT_LEVEL)

        alerts = soup.select(".toast > [role='alert']")
        assert len(alerts) == 1
        assert f"message at level {PROJECT_LEVEL}" in alerts[0].get_text()
        assert not {f"alert-{variant}" for variant in VARIANTS} & set(
            alerts[0]["class"]
        )


class TestMessageIcons:
    @pytest.mark.parametrize("level", LEVEL_VARIANTS)
    def test_a_message_alert_carries_an_icon(self, render_messages, level):
        soup = render_messages(level)

        alert = soup.select_one(".toast > [role='alert']")
        assert alert.find("i") is not None


class TestMessageAction:
    def test_a_link_action_draws_a_link_inside_the_alert(self, render_messages):
        tags = action_tags("View", "/things/7/")

        soup = render_messages(messages.SUCCESS, extra_tags=tags)

        link = soup.select_one(".toast > [role='alert'] a")
        assert link["href"] == "/things/7/"
        assert link.get_text(strip=True) == "View"

    def test_a_post_action_draws_a_form_that_posts_to_the_address(
        self, render_messages
    ):
        tags = action_tags("Undo", "/things/7/undo/", method="post")

        soup = render_messages(messages.SUCCESS, extra_tags=tags)

        form = soup.select_one(".toast > [role='alert'] form")
        assert form["method"] == "post"
        assert form["action"] == "/things/7/undo/"
        assert form.select_one("button[type='submit']").get_text(strip=True) == "Undo"
        assert form.get("hx-post") is None
        assert form.select_one("input[name='csrfmiddlewaretoken']")["value"] == "token"

    def test_a_post_action_with_a_target_is_sent_with_htmx(self, render_messages):
        tags = action_tags(
            "Undo", "/things/7/undo/", method="post", target="#things", swap="outerHTML"
        )

        soup = render_messages(messages.SUCCESS, extra_tags=tags)

        form = soup.select_one(".toast > [role='alert'] form")
        assert form["hx-post"] == "/things/7/undo/"
        assert form["hx-target"] == "#things"
        assert form["hx-swap"] == "outerHTML"

    def test_a_message_without_an_action_draws_none(self, render_messages):
        soup = render_messages(messages.SUCCESS, extra_tags="sticky")

        alert = soup.select_one(".toast > [role='alert']")
        assert alert.find("form") is None
        assert alert.find("a") is None

    def test_a_message_with_an_action_does_not_hide_itself(self, render_messages):
        tags = action_tags("Undo", "/undo/", method="post")

        soup = render_messages(messages.SUCCESS, extra_tags=tags, attrs="dismissible")

        alert = soup.select_one(".toast > [role='alert']")
        assert alert.get("x-init") is None

    def test_a_message_with_an_action_can_be_dismissed_when_the_list_is_not(
        self, render_messages
    ):
        tags = action_tags("Undo", "/undo/", method="post")

        soup = render_messages(messages.SUCCESS, extra_tags=tags)

        assert soup.select_one(".toast > [role='alert'] button[aria-label]")

    def test_a_message_without_an_action_keeps_its_auto_dismiss(
        self, render_messages
    ):
        soup = render_messages(messages.SUCCESS, attrs="dismissible :delay=3000")

        alert = soup.select_one(".toast > [role='alert']")
        assert "3000" in alert["x-init"]


class TestOutOfBandSwap:
    def test_the_list_is_found_by_an_id_in_the_page(self, render_messages):
        soup = render_messages(messages.SUCCESS)

        assert soup.select_one(".toast")["id"]

    def test_oob_has_htmx_swap_the_list_in_place_by_its_id(self, render_messages):
        soup = render_messages(messages.SUCCESS, attrs='oob="true"')

        assert soup.select_one(".toast")["hx-swap-oob"] == "true"

    def test_without_oob_the_list_is_not_an_out_of_band_swap(self, render_messages):
        soup = render_messages(messages.SUCCESS)

        assert soup.select_one(".toast").get("hx-swap-oob") is None
