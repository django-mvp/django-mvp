"""Tests for ``<c-mvp.app.footer>``: the shell's footer landmark.

Source: mvp/templates/cotton/mvp/app/footer.html
"""


class TestAppFooter:
    def test_the_slot_content_and_a_callers_class_reach_the_footer(
        self, cotton_render_string_soup
    ):
        soup = cotton_render_string_soup(
            '<c-mvp.app.footer class="project-footer">'
            '<span id="footer-note">note</span></c-mvp.app.footer>'
        )

        footer = soup.find("footer")
        assert "project-footer" in footer["class"]
        assert footer.find(id="footer-note") is not None
