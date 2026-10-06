"""Tests for ``<c-mvp.data-field>``: a label above a read-only value.

Source: mvp/templates/cotton/mvp/data_field.html
"""


class TestDataFieldHelpText:
    def test_the_help_text_reaches_a_tooltip_around_the_label(
        self, cotton_render_string_soup
    ):
        soup = cotton_render_string_soup(
            '<c-mvp.data-field label="Email" value="ada@example.com" '
            'help_text="Primary contact" />'
        )

        tooltip = soup.find(attrs={"role": "tooltip"})
        assert tooltip.get_text(strip=True) == "Primary contact"
        assert tooltip.parent.find("h6") is not None

    def test_a_field_without_help_text_draws_no_tooltip(
        self, cotton_render_string_soup
    ):
        soup = cotton_render_string_soup(
            '<c-mvp.data-field label="Email" value="ada@example.com" />'
        )

        assert soup.find(attrs={"role": "tooltip"}) is None

    def test_the_value_is_drawn_whether_or_not_there_is_help_text(
        self, cotton_render_string_soup
    ):
        for extra in ("", ' help_text="Primary contact"'):
            soup = cotton_render_string_soup(
                f'<c-mvp.data-field label="Email" value="ada@example.com"{extra} />'
            )

            assert "ada@example.com" in soup.get_text()
