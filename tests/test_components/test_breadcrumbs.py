"""Tests for the ``c-mvp.breadcrumbs`` trail as the server draws it.

The folding itself is decided in the browser and is tested in
``test_breadcrumbs_e2e.py``. What the server promises is the markup that works
with no script at all: every step, in order, in a labelled landmark, with the
last step marked as the current page and an optional icon on any step.

Source: mvp/templates/cotton/mvp/breadcrumbs/
"""

import pytest

STEPS = [
    {"text": "Docs", "href": "/docs/", "icon": "home"},
    {"text": "Guides", "href": "/docs/guides/"},
    {"text": "Install"},
]

IN_A_CARD = (
    "<c-mvp.card title='Box'>"
    "<c-mvp.breadcrumbs :items='steps' /></c-mvp.card>"
)

FROM_A_TEMPLATE = """
<c-mvp.breadcrumbs>
  <c-mvp.breadcrumbs.item text="Docs" href="/docs/" />
  <c-mvp.breadcrumbs.item text="Install" />
</c-mvp.breadcrumbs>
"""


@pytest.fixture
def trail(cotton_render_string_soup):
    soup = cotton_render_string_soup(
        "<c-mvp.breadcrumbs :items='steps' />", context={"steps": STEPS}
    )
    return soup.find("nav")


def steps_of(trail):
    return trail.select("li[data-mvp-crumb]")


class TestTheTrailWithNoScript:
    def test_it_is_a_labelled_navigation_landmark(self, trail):
        assert trail["aria-label"] == "Breadcrumbs"

    def test_every_step_is_drawn_in_order(self, trail):
        assert [step.get_text(strip=True) for step in steps_of(trail)] == [
            "Docs",
            "Guides",
            "Install",
        ]

    def test_the_steps_sit_in_an_ordered_list(self, trail):
        assert trail.find("ol") is not None
        assert len(steps_of(trail)) == len(trail.select("ol > li[data-mvp-crumb]"))

    def test_the_fold_is_hidden_until_the_script_needs_it(self, trail):
        fold = trail.select_one("[data-mvp-crumbs-fold]")

        assert fold.has_attr("hidden")

    def test_the_script_is_not_yet_in_charge(self, trail):
        assert "is-enhanced" not in trail["class"]

    def test_a_step_with_an_address_is_a_link(self, trail):
        links = trail.select("li[data-mvp-crumb] > a")

        assert [link["href"] for link in links] == ["/docs/", "/docs/guides/"]

    def test_the_label_can_be_replaced(self, cotton_render_string_soup):
        soup = cotton_render_string_soup(
            "<c-mvp.breadcrumbs :items='steps' aria-label='You are here' />",
            context={"steps": STEPS},
        )

        assert soup.find("nav")["aria-label"] == "You are here"


class TestTheLastStep:
    def test_it_is_the_current_page_and_not_a_link(self, trail):
        last = steps_of(trail)[-1]

        assert last.find("a") is None
        assert last.select_one("span[aria-current='page']") is not None

    def test_no_other_step_is_the_current_page(self, trail):
        marked = trail.select("[aria-current]")

        assert len(marked) == 1


class TestAStepWithAnIcon:
    def test_it_draws_the_icon_before_the_label(self, trail):
        first = steps_of(trail)[0].find("a")
        children = [child.name for child in first.find_all(recursive=False)]

        assert children[-1] == "span"
        assert first.select_one(".mvp-crumb-icon") is not None

    def test_the_icon_is_hidden_from_a_screen_reader(self, trail):
        icon = steps_of(trail)[0].select_one(".mvp-crumb-icon")

        assert icon["aria-hidden"] == "true"

    def test_a_step_with_no_icon_draws_none(self, trail):
        assert steps_of(trail)[1].select_one(".mvp-crumb-icon") is None


class TestTheLabelsTheScriptReads:
    def test_the_fold_button_labels_are_on_the_trail(self, trail):
        assert trail["data-label-one"] == "Show 1 more level"
        assert trail["data-label-many"] == "Show {count} more levels"

    def test_the_menu_heading_is_in_the_markup(self, trail):
        heading = trail.select_one(".mvp-crumbs-fold-heading")

        assert heading.get_text(strip=True) == "Further up"


class TestTheTrailFromATemplate:
    def test_steps_written_in_the_template_are_drawn(self, cotton_render_string_soup):
        trail = cotton_render_string_soup(FROM_A_TEMPLATE).find("nav")

        assert [step.get_text(strip=True) for step in steps_of(trail)] == [
            "Docs",
            "Install",
        ]


class TestTheTrailInABox:
    def test_it_can_be_placed_inside_a_card(self, cotton_render_string_soup):
        soup = cotton_render_string_soup(IN_A_CARD, context={"steps": STEPS})
        trail = soup.find("nav", class_="mvp-crumbs")

        assert trail is not None
        assert len(steps_of(trail)) == 3
