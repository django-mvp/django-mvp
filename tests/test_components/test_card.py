"""Tests for ``<c-card>``: daisyUI's card, built from header, body and footer parts.

Each part is written only when wanted, and a card with none holds its content on the
card's surface. A header given an ``href`` makes its title the one link, stretched
over the whole card by a stylesheet effect, so the browser test in
``test_card_e2e.py`` proves a click lands and a control inside still works. How the
parts stack is django-mvp-layout's to test: these tests check that the markup carries
the layout's classes and the parts.

Source: mvp/templates/cotton/card/index.html
"""

import pytest

CARD = """
<c-card {attrs}>
  <c-card.header {header}>
    <c-slot name="badges"><i id="badge">New</i></c-slot>
    <c-slot name="actions"><button id="menu" type="button">Menu</button></c-slot>
  </c-card.header>
  <c-card.body {body}><p id="body">The body</p></c-card.body>
  <c-card.footer>
    <a id="inner" href="/other/">Other</a>
    <c-slot name="end"><b id="end">End</b></c-slot>
  </c-card.footer>
</c-card>
"""


@pytest.fixture
def render_card(cotton_render_string_soup):
    """Render a card with the given attributes on each part."""

    def render(attrs="", header='title="Orders"', body=""):
        return cotton_render_string_soup(
            CARD.format(attrs=attrs, header=header, body=body)
        )

    return render


class TestCardParts:
    def test_the_card_is_daisyuis_card_stacked_by_the_layout(self, render_card):
        soup = render_card()

        assert "hbf" in soup.select_one(".card")["class"]

    def test_each_part_carries_the_layouts_class(self, render_card):
        soup = render_card()

        assert soup.select_one(".card > .mvpl-header") is not None
        assert soup.select_one(".card > .mvpl-body.card-body #body") is not None
        assert soup.select_one(".card > .mvpl-footer") is not None

    def test_the_header_draws_the_title_badges_and_actions(self, render_card):
        soup = render_card(header='title="Orders" icon="info"')

        header = soup.select_one(".mvpl-header")
        assert "Orders" in header.select_one(".card-title").get_text()
        assert header.select_one(".card-title i") is not None
        assert header.select_one("#badge") is not None
        assert header.select_one("#menu") is not None

    def test_the_footer_has_a_start_group_and_an_end_slot(self, render_card):
        soup = render_card()

        footer = soup.select_one(".mvpl-footer")
        assert footer.select_one("#inner") is not None
        assert footer.select_one("#end") is not None

    def test_a_tight_body_is_marked(self, render_card):
        soup = render_card(body="tight")

        assert "mvp-card-body-tight" in soup.select_one("#body").parent["class"]

    def test_a_card_with_no_parts_holds_its_content_on_the_surface(
        self, cotton_render_string_soup
    ):
        soup = cotton_render_string_soup("<c-card><p id='bare'>Bare</p></c-card>")

        assert soup.select_one(".card > #bare") is not None
        assert soup.select_one(".card-body") is None

    def test_a_card_with_a_figure_is_not_stacked(self, cotton_render_string_soup):
        soup = cotton_render_string_soup(
            "<c-card><c-slot name='figure'><img src='/a.png' alt=''></c-slot>"
            "<c-card.body>Text</c-card.body></c-card>"
        )

        assert soup.select_one(".card > figure img") is not None
        assert "hbf" not in soup.select_one(".card")["class"]

    @pytest.mark.parametrize("option", ["border", "dash"])
    def test_a_bordered_card_is_flat(self, render_card, option):
        soup = render_card(attrs=option)

        assert "shadow-sm" not in soup.select_one(".card")["class"]

    def test_a_plain_card_keeps_the_raised_look(self, render_card):
        soup = render_card()

        assert "shadow-sm" in soup.select_one(".card")["class"]


class TestCardLayout:
    def test_a_view_draws_a_layout_with_the_parts_as_its_header_and_footer(
        self, cotton_render_string_soup
    ):
        soup = cotton_render_string_soup(
            "<c-card view='hHh LpR fFf'><c-card.header title='Inbox' />"
            "<c-layout.page>Mail</c-layout.page><c-card.footer>Foot</c-card.footer>"
            "</c-card>"
        )

        layout = soup.select_one(".card .mvpl")
        assert layout is not None
        assert layout.select_one(".mvpl-header") is not None
        assert layout.select_one(".mvpl-footer") is not None
        assert "Mail" in layout.get_text()

    def test_the_header_always_draws_a_toggle_for_each_side(
        self, cotton_render_string_soup
    ):
        soup = cotton_render_string_soup("<c-card><c-card.header title='A' /></c-card>")

        assert len(soup.select(".mvpl-header .mvpl-toggle")) == 2

    def test_height_is_set_on_the_layout(self, cotton_render_string_soup):
        soup = cotton_render_string_soup(
            "<c-card view='hHh LpR fFf' height='20rem'>"
            "<c-layout.page>Mail</c-layout.page></c-card>"
        )

        assert "height: 20rem" in soup.select_one(".card .mvpl")["style"]


class TestCardLink:
    def test_the_title_is_the_cards_one_link(self, render_card):
        soup = render_card(header='title="Orders" href="/orders/"')

        links = soup.select(".card-title a")
        assert len(links) == 1
        assert links[0]["href"] == "/orders/"
        assert links[0].get_text(strip=True) == "Orders"

    def test_the_icon_is_not_part_of_the_links_name(self, render_card):
        soup = render_card(header='title="Orders" icon="info" href="/orders/"')

        link = soup.select_one(".card-title a")
        assert link.find("i") is None

    def test_other_links_and_buttons_stay_outside_the_card_link(self, render_card):
        soup = render_card(header='title="Orders" href="/orders/"')

        card_link = soup.select_one(".card-title a")
        assert card_link.find(id="menu") is None
        assert card_link.find(id="inner") is None
        assert soup.select_one(".card #menu") is not None
        assert soup.select_one(".card #inner")["href"] == "/other/"

    def test_a_card_with_no_href_draws_its_title_as_plain_text(self, render_card):
        soup = render_card(header='title="Orders"')

        assert soup.select_one(".card-title a") is None
        assert "Orders" in soup.select_one(".card-title").get_text()
