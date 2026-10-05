"""Tests for ``<c-mvp.messages>``: one alert per Django message.

Each message is drawn as a daisy-cotton alert whose variant follows the message's
level tag. ``debug`` takes the ``info`` variant, since daisy-cotton has no debug
alert. A level tag daisy-cotton has no variant for, such as one a project adds
through ``MESSAGE_TAGS``, draws its message in a plain alert.

Source: mvp/templates/cotton/mvp/messages.html
"""

import pytest
from django.contrib import messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory

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

    def render(*levels):
        request = RequestFactory().get("/")
        request.session = {}
        request._messages = FallbackStorage(request)
        messages.set_level(request, messages.DEBUG)
        for level in levels:
            messages.add_message(request, level, f"message at level {level}")
        return cotton_render_string_soup(
            "<c-mvp.messages :messages='messages' />",
            context={"messages": messages.get_messages(request), "request": request},
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
