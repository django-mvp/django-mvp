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
