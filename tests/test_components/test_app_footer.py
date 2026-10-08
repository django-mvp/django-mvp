"""Tests for ``<c-app.footer>``: the shell's footer landmark.

Source: mvp/templates/cotton/app/footer.html
"""


class TestAppFooter:
    def test_the_slot_content_and_a_callers_class_reach_the_footer(
        self, cotton_render_string_soup
    ):
        soup = cotton_render_string_soup(
            '<c-app.footer class="project-footer">'
            '<span id="footer-note">note</span></c-app.footer>'
        )

        footer = soup.find("footer")
        assert "project-footer" in footer["class"]
        assert footer.find(id="footer-note") is not None
