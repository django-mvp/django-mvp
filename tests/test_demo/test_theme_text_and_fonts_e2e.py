"""A theme's text values and fonts, read back as computed styles in a real browser.

Source: mvp/tailwind/base.css, specs/026-ship-prebuilt-daisyui/spec.md US-6 and US-7

Each test puts a plain, unlayered theme on a demo page the way a project's own
stylesheet does, draws the elements it asks about, and reads what the browser
resolved. Class names and stylesheet text cannot answer these questions: the
rules work through custom properties, cascade layers and var() fallbacks, and
only the browser resolves those.
"""

import pytest
from playwright.sync_api import expect

from tests.conftest import requires_browser

pytestmark = [pytest.mark.e2e, requires_browser]

PAGE = "/theme/preview/"

FILLS = {"primary": "#d9922f", "secondary": "#b0509a", "accent": "#2fa89a"}
TEXTS = {"primary": "#96550f", "secondary": "#7a2f69", "accent": "#14665d"}
SLOTS = tuple(FILLS)

PALETTE = """
  color-scheme: light;
  --color-base-100: #fffaf2;
  --color-base-content: #2b2118;
  --color-primary: #d9922f;
  --color-primary-content: #2b2118;
  --color-secondary: #b0509a;
  --color-secondary-content: #ffffff;
  --color-accent: #2fa89a;
  --color-accent-content: #0d2422;
  --color-neutral: #33302c;
  --color-error: #c81e1e;
"""

TEXT_VALUES = """
  --color-primary-text: #96550f;
  --color-secondary-text: #7a2f69;
  --color-accent-text: #14665d;
"""

# Every use of a brand colour as text, with {slot} standing for the colour.
TEXT_USES = (
    "text-{slot}",
    "link link-{slot}",
    "btn btn-{slot} btn-outline",
    "btn btn-{slot} btn-dash",
    "btn btn-{slot} btn-soft",
    "btn btn-{slot} btn-ghost",
    "btn btn-{slot} btn-link",
    "badge badge-{slot} badge-outline",
    "badge badge-{slot} badge-dash",
    "badge badge-{slot} badge-soft",
)

HEADINGS = (
    "<h1>",
    "<h2>",
    "<h3>",
    "<h4>",
    "<h5>",
    "<h6>",
    '<div class="card-title">',
    '<div class="collapse-title">',
    '<div class="footer-title">',
    '<li class="menu-title">',
    '<div class="stat-title">',
    '<legend class="fieldset-legend">',
    '<span class="mvp-sidebar-title">',
)


class ThemedPage:
    """A demo page with a project's theme applied to the document."""

    def __init__(self, page, url, declarations):
        self.page = page
        page.goto(url + PAGE)
        page.add_style_tag(content=f'[data-theme="probe"] {{{declarations}}}')
        page.evaluate(
            "document.documentElement.setAttribute('data-theme', 'probe')",
        )

    def draw(self, markup, within=None):
        """Add ``markup`` to the page and return a locator for its first element."""
        marker = f"probe-{self.page.evaluate('document.querySelectorAll("*").length')}"
        self.page.evaluate(
            """([markup, marker, within]) => {
                const box = document.createElement('div');
                box.id = marker;
                box.innerHTML = markup;
                (within ? document.querySelector(within) : document.body).append(box);
            }""",
            [markup, marker, within],
        )
        return self.page.locator(f"#{marker} > *").first

    def computed(self, locator, prop):
        return locator.evaluate("(el, p) => getComputedStyle(el)[p]", prop)

    def resolve(self, colour):
        """The browser's own serialisation of ``colour``, to compare against."""
        return self.computed(
            self.draw(f'<span style="color: {colour}">x</span>'), "color"
        )

    def resolve_slot(self, slot):
        return self.computed(
            self.draw(f'<span style="color: var(--color-{slot})">x</span>'), "color"
        )


@pytest.fixture
def themed(page, live_server):
    def open_page(declarations):
        return ThemedPage(page, live_server.url, declarations)

    return open_page


class TestThemeTextValue:
    @pytest.mark.parametrize("slot", SLOTS)
    @pytest.mark.parametrize("use", TEXT_USES)
    def test_text_reads_the_text_value(self, themed, use, slot):
        theme = themed(PALETTE + TEXT_VALUES)
        element = theme.draw(f'<a href="#x" class="{use.format(slot=slot)}">x</a>')

        assert theme.computed(element, "color") == theme.resolve(TEXTS[slot])

    @pytest.mark.parametrize("slot", SLOTS)
    @pytest.mark.parametrize("use", TEXT_USES)
    def test_without_a_text_value_text_reads_the_fill(self, themed, use, slot):
        theme = themed(PALETTE)
        element = theme.draw(f'<a href="#x" class="{use.format(slot=slot)}">x</a>')

        assert theme.computed(element, "color") == theme.resolve(FILLS[slot])

    @pytest.mark.parametrize(
        ("classes", "prop"),
        [
            ("bg-primary", "backgroundColor"),
            ("btn btn-primary", "backgroundColor"),
            ("badge badge-primary", "backgroundColor"),
            ("btn btn-primary btn-outline", "borderTopColor"),
            ("border border-primary", "borderTopColor"),
        ],
    )
    def test_fills_keep_the_fill(self, themed, classes, prop):
        theme = themed(PALETTE + TEXT_VALUES)
        element = theme.draw(f'<a href="#x" class="{classes}">x</a>')

        assert theme.computed(element, prop) == theme.resolve(FILLS["primary"])

    def test_a_solid_button_keeps_its_content_colour(self, themed):
        theme = themed(PALETTE + TEXT_VALUES)
        element = theme.draw('<a href="#x" class="btn btn-primary">x</a>')

        assert theme.computed(element, "color") == theme.resolve_slot("primary-content")

    def test_a_hovered_outline_button_is_drawn_as_a_fill(self, themed):
        theme = themed(PALETTE + TEXT_VALUES)
        element = theme.draw('<a href="#x" class="btn btn-primary btn-outline">x</a>')
        element.scroll_into_view_if_needed()
        element.hover()

        expect(element).to_have_css("color", theme.resolve_slot("primary-content"))

    def test_a_hovered_link_darkens_the_text_value(self, themed):
        theme = themed(PALETTE + TEXT_VALUES)
        element = theme.draw('<a href="#x" class="link link-primary">x</a>')
        expected = theme.computed(
            theme.draw('<span style="color: color-mix(in oklab, #96550f 80%, #000)">'),
            "color",
        )
        element.scroll_into_view_if_needed()
        element.hover()

        expect(element).to_have_css("color", expected)

    def test_a_hover_utility_reads_the_text_value(self, themed):
        theme = themed(PALETTE + TEXT_VALUES)
        element = theme.draw('<a href="#x" class="hover:text-primary">x</a>')
        element.scroll_into_view_if_needed()
        element.hover()

        expect(element).to_have_css("color", theme.resolve(TEXTS["primary"]))

    def test_a_link_button_with_no_colour_uses_the_primary_text_value(self, themed):
        theme = themed(PALETTE + TEXT_VALUES)
        element = theme.draw('<a href="#x" class="btn btn-link">x</a>')

        assert theme.computed(element, "color") == theme.resolve(TEXTS["primary"])

    def test_a_link_button_in_another_colour_keeps_that_colour(self, themed):
        theme = themed(PALETTE + TEXT_VALUES)
        element = theme.draw('<a href="#x" class="btn btn-link btn-neutral">x</a>')

        assert theme.computed(element, "color") == theme.resolve_slot("neutral")

    @pytest.mark.parametrize(
        "markup",
        [
            '<button class="btn btn-link" disabled>x</button>',
            '<button class="btn btn-link btn-primary" disabled>x</button>',
            '<a class="btn btn-link btn-disabled">x</a>',
            '<button class="btn btn-primary btn-outline" disabled>x</button>',
            '<a class="btn btn-primary btn-ghost btn-disabled">x</a>',
        ],
    )
    def test_a_disabled_button_stays_muted(self, themed, markup):
        theme = themed(PALETTE + TEXT_VALUES)
        element = theme.draw(markup)

        assert theme.computed(element, "color") != theme.resolve(TEXTS["primary"])

    def test_a_text_utility_on_the_element_still_wins(self, themed):
        theme = themed(PALETTE + TEXT_VALUES)
        element = theme.draw('<a href="#x" class="link link-primary text-error">x</a>')

        assert theme.computed(element, "color") == theme.resolve_slot("error")

    def test_a_region_can_set_its_own_text_value(self, themed):
        theme = themed(PALETTE + TEXT_VALUES)
        theme.page.add_style_tag(
            content='[data-theme="probe"] .mvp-header { --color-primary-text: #123456; }'
        )
        element = theme.draw(
            '<a href="#x" class="link link-primary">x</a>', ".mvp-header"
        )

        assert theme.computed(element, "color") == theme.resolve("#123456")

    def test_a_nested_theme_does_not_inherit_the_page_text_value(self, themed):
        theme = themed(PALETTE + TEXT_VALUES)
        nested = theme.draw(
            '<div data-theme="dracula"><a class="link-primary">x</a></div>'
        )
        element = nested.locator("a")

        assert theme.computed(element, "color") == nested.evaluate(
            """box => {
                const swatch = document.createElement('span');
                swatch.style.color = 'var(--color-primary)';
                box.append(swatch);
                return getComputedStyle(swatch).color;
            }"""
        )


class TestThemeFonts:
    @pytest.mark.parametrize(
        ("variable", "markup"),
        [
            ("--font-sans", "<p>x</p>"),
            ("--font-serif", '<p class="font-serif">x</p>'),
            ("--font-mono", "<code>x</code>"),
        ],
    )
    def test_a_font_variable_reaches_the_text_it_names(self, themed, variable, markup):
        theme = themed(f'{variable}: "Probe Face", serif;')
        element = theme.draw(markup)

        assert "Probe Face" in theme.computed(element, "fontFamily")

    @pytest.mark.parametrize("markup", HEADINGS)
    def test_a_heading_reads_the_heading_font(self, themed, markup):
        theme = themed('--font-heading: "Probe Heading", serif;')
        element = theme.draw(f"{markup}x")

        assert "Probe Heading" in theme.computed(element, "fontFamily")

    def test_body_text_keeps_the_body_font(self, themed):
        theme = themed('--font-sans: "Probe Body"; --font-heading: "Probe Heading";')
        element = theme.draw("<p>x</p>")

        assert "Probe Body" in theme.computed(element, "fontFamily")
        assert "Probe Heading" not in theme.computed(element, "fontFamily")

    @pytest.mark.parametrize("markup", HEADINGS)
    def test_without_a_heading_font_a_heading_follows_the_body_font(
        self, themed, markup
    ):
        theme = themed('--font-sans: "Probe Body", serif;')
        element = theme.draw(f"{markup}x")

        assert "Probe Body" in theme.computed(element, "fontFamily")

    def test_without_a_heading_font_a_heading_inherits_from_its_container(self, themed):
        theme = themed("")
        container = theme.draw('<div class="font-mono"><h2>x</h2></div>')

        assert theme.computed(container.locator("h2"), "fontFamily") == theme.computed(
            container, "fontFamily"
        )

    def test_a_font_utility_on_a_heading_still_wins(self, themed):
        theme = themed('--font-heading: "Probe Heading"; --font-mono: "Probe Mono";')
        element = theme.draw('<h2 class="font-mono">x</h2>')

        assert "Probe Mono" in theme.computed(element, "fontFamily")

    def test_the_shell_draws_its_headings_in_the_heading_font(self, themed):
        theme = themed('--font-heading: "Probe Heading", serif;')
        titles = theme.page.locator("h1, .mvp-sidebar-title, .menu-title")

        assert titles.count() > 2
        for family in titles.evaluate_all(
            "els => els.map(el => getComputedStyle(el).fontFamily)"
        ):
            assert "Probe Heading" in family
