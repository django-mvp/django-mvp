"""Tests for demo pages that have no module of their own: the formset
component doc page and the complex form page.

Source: demo/views.py, demo/urls.py
"""

import pytest


class TestFormsetComponentDocPage:
    @pytest.mark.django_db
    def test_page_renders_a_bound_orderline_formset(self, client):
        response = client.get("/components/formset/")

        assert response.status_code == 200
        content = response.content.decode()
        assert 'name="form-TOTAL_FORMS"' in content


class TestComplexFormDemoPage:
    @pytest.mark.django_db
    def test_page_renders_every_fieldset_and_the_layout(self, client):
        response = client.get("/forms/complex/")

        assert response.status_code == 200
        content = response.content.decode()
        # One legend per Fieldset in the helper's layout.
        assert content.count("<legend") == 3
        # <c-mvp.form> (form_view.html) is the only real <form> wrapping the
        # fields — form_tag=False must stop crispy nesting a second one
        # inside it. x-data="{form: {}}" is <c-mvp.form>'s own signature
        # attribute; the page also carries unrelated chrome forms (the
        # language switcher, a couple of dialogs), so counting every <form>
        # on the page would not isolate this.
        assert content.count('<form x-data="{form: {}}"') == 1

    @pytest.mark.django_db
    def test_valid_submission_redirects_and_flashes_success(self, client):
        response = client.post(
            "/forms/complex/",
            {
                "name": "Jane Doe",
                "email": "jane@example.com",
                "address": "1 Example Street",
                "city": "Springfield",
                "postal_code": "12345",
                "shipping_method": "standard",
            },
        )

        assert response.status_code == 302
        assert response.url == "/forms/complex/"


class TestPageSideDemoPage:
    URL = "/layout/side/"

    def panel(self, client, query=""):
        from bs4 import BeautifulSoup

        response = client.get(f"{self.URL}{query}")

        assert response.status_code == 200
        soup = BeautifulSoup(response.content, "html.parser")
        return soup.select_one("#page-side")

    @pytest.mark.django_db
    def test_renders_with_its_panel_beside_the_content(self, client):
        panel = self.panel(client)

        assert panel.select_one("aside#page-side-panel") is not None
        assert panel.find_parent(class_="mvp-page-layout") is not None

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        ("option", "value"),
        [
            ("collapse", "stack"),
            ("align", "content"),
            ("position", "start"),
            ("width", "lg"),
            ("width", "sm"),
            ("breakpoint", "lg"),
            ("breakpoint", "2xl"),
        ],
    )
    def test_each_option_is_switchable_from_the_query_string(
        self, client, option, value
    ):
        panel = self.panel(client, f"?{option}={value}")

        key = f"data-mvp-side-{option}"
        assert panel[key] == value

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
