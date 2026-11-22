"""Tests for the link a ``<c-mvp.card>`` can take (issue #685).

A card given an ``href`` makes its title the one link, stretched over the whole
card. The stretch is a stylesheet effect, so the browser test in
``test_card_e2e.py`` proves a click lands and a control inside still works.

Source: mvp/templates/cotton/mvp/card/index.html
"""

import pytest

CARD = """
<c-mvp.card {attrs}>
  <p id="body">The body</p>
  <c-slot name="actions"><button id="menu" type="button">Menu</button></c-slot>
  <c-slot name="footer"><a id="inner" href="/other/">Other</a></c-slot>
</c-mvp.card>
"""


@pytest.fixture
def render_card(cotton_render_string_soup):
    """Render a card with the given attributes."""

    def render(attrs=""):
        return cotton_render_string_soup(CARD.format(attrs=attrs))

    return render


class TestCardLink:
    def test_the_title_is_the_cards_one_link(self, render_card):
        soup = render_card('title="Orders" href="/orders/"')

        links = soup.select(".card-title a")
        assert len(links) == 1
        assert links[0]["href"] == "/orders/"
        assert links[0].get_text(strip=True) == "Orders"

    def test_the_icon_is_not_part_of_the_links_name(self, render_card):
        soup = render_card('title="Orders" icon="info" href="/orders/"')

        link = soup.select_one(".card-title a")
        assert link.find("i") is None

    def test_other_links_and_buttons_stay_outside_the_card_link(self, render_card):
        soup = render_card('title="Orders" href="/orders/"')

        card_link = soup.select_one(".card-title a")
        assert card_link.find(id="menu") is None
        assert card_link.find(id="inner") is None
        assert soup.select_one(".card #menu") is not None
        assert soup.select_one(".card #inner")["href"] == "/other/"

    def test_a_card_with_no_href_draws_its_title_as_plain_text(self, render_card):
        soup = render_card('title="Orders"')

        assert soup.select_one(".card-title a") is None
        assert "Orders" in soup.select_one(".card-title").get_text()

    def test_a_card_with_an_href_and_no_title_draws_no_link(self, render_card):
        soup = render_card('href="/orders/"')

        assert soup.select_one(".card-title a") is None
