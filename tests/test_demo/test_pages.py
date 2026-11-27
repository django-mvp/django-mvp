"""Tests for demo pages that have no module of their own.

They are the complex form page and the side panel page.

Source: demo/views.py, demo/urls.py
"""

import pytest
from bs4 import BeautifulSoup


class TestComplexFormDemoPage:
    @pytest.mark.django_db
    def test_page_wraps_its_fields_in_one_form(self, client):
        response = client.get("/forms/complex/")

        assert response.status_code == 200
        content = response.content.decode()
        # <c-mvp.form> (form_view.html) is the only real <form> wrapping the
        # fields — form_tag=False must stop crispy nesting a second one
        # inside it. x-data="{form: {}}" is <c-mvp.form>'s own signature
        # attribute; the page also carries unrelated chrome forms (the
        # language switcher, a couple of dialogs), so counting every <form>
        # on the page would not isolate this.
        assert content.count('<form x-data="{form: {}}"') == 1


class TestPageSideDemoPage:
    URL = "/layout/side/"

    def panel(self, client, query=""):
        response = client.get(f"{self.URL}{query}")

        assert response.status_code == 200
        soup = BeautifulSoup(response.content, "html.parser")
        return soup.select_one("#page-side")

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        ("option", "value"),
        [("collapse", "stack"), ("breakpoint", "2xl")],
    )
    def test_an_option_is_switchable_from_the_query_string(self, client, option, value):
        panel = self.panel(client, f"?{option}={value}")

        assert panel[f"data-mvp-side-{option}"] == value

    @pytest.mark.django_db
    def test_a_breakpoint_of_off_writes_no_breakpoint(self, client):
        panel = self.panel(client, "?breakpoint=off")

        assert not panel.has_attr("data-mvp-side-breakpoint")

    @pytest.mark.django_db
    def test_sticky_can_be_switched_off(self, client):
        assert self.panel(client).has_attr("data-mvp-side-sticky")
        assert not self.panel(client, "?sticky=off").has_attr("data-mvp-side-sticky")

    @pytest.mark.django_db
    def test_an_unknown_value_falls_back_to_the_default(self, client):
        panel = self.panel(client, "?position=sideways")

        assert panel["data-mvp-side-position"] == "end"

    @pytest.mark.django_db
    def test_long_contents_add_a_heading_per_step(self, client):
        short = client.get(self.URL).content.decode()
        long = client.get(f"{self.URL}?long=on").content.decode()

        assert 'id="step-30"' not in short
        assert 'id="step-30"' in long
