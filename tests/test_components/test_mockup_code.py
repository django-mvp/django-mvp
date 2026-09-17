"""``<c-mockup.code.line>``'s prompt character is the ``prefix`` attribute.

The component declared ``prefix`` and then wrote a literal ``data-prefix="$"``,
so a caller asking for a different prompt — ``>`` for a Windows shell, ``#``
for a root prompt, nothing at all for plain output — got a dollar sign and no
indication of why.

``text`` was rendered without being declared, which left the component's
declaration describing an interface narrower than the one the demo uses.
"""


class TestCodeLinePrefix:
    def test_the_prompt_defaults_to_a_shell_dollar(self, cotton_render_string_soup):
        soup = cotton_render_string_soup(
            '<c-mockup.code.line text="pip install django-mvp" />'
        )

        assert soup.find("pre")["data-prefix"] == "$"

    def test_a_caller_chooses_the_prompt(self, cotton_render_string_soup):
        soup = cotton_render_string_soup(
            '<c-mockup.code.line prefix="#" text="apt install python3" />'
        )

        assert soup.find("pre")["data-prefix"] == "#"

    def test_the_prompt_can_be_emptied(self, cotton_render_string_soup):
        """Output lines in a terminal mockup carry no prompt at all."""
        soup = cotton_render_string_soup(
            '<c-mockup.code.line prefix="" text="Successfully installed" />'
        )

        assert soup.find("pre")["data-prefix"] == ""

    def test_the_line_renders_its_text(self, cotton_render_string_soup):
        soup = cotton_render_string_soup(
            '<c-mockup.code.line text="python manage.py runserver" />'
        )

        assert soup.find("code").get_text() == "python manage.py runserver"
