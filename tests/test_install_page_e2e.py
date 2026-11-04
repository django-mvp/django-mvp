"""The install page's script, in a real browser.

``tests/test_pwa/test_views.py`` proves the page carries every platform's steps.
These tests load it in Chromium, under the user agent of each device it tells
apart, and check what the bundled script (assets/js/install.js) shows: the
steps for that device, the browser's own install button when the browser
offers one, and the installed state.

Source: assets/js/install.js, mvp/templates/mvp/pwa/install.html
"""

import pytest
from playwright.sync_api import expect

from tests.conftest import requires_browser

pytestmark = [pytest.mark.e2e, requires_browser]

IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
)
ANDROID = (
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36"
)
MAC_SAFARI = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/18.0 Safari/605.1.15"
)
FIREFOX = "Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0"
DESKTOP_CHROME = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
)

DEVICES = ("ios", "android", "chromium", "safari", "firefox")

# Stands in for Chromium's own event: it can be prompted once, and the visitor's
# answer comes back through ``userChoice``.
OFFER_INSTALL = """(outcome) => {
    const event = new Event("beforeinstallprompt", { cancelable: true });
    window.promptShown = false;
    event.prompt = () => { window.promptShown = true; };
    event.userChoice = Promise.resolve({ outcome });
    window.dispatchEvent(event);
}"""


# Chromium cannot emulate the display-mode media feature, so the script's test
# for it is answered as an installed app would answer it.
OPENED_AS_THE_APP = """
const matchMedia = window.matchMedia.bind(window);
window.matchMedia = (query) =>
    query === "(display-mode: standalone)"
        ? { matches: true, media: query, addEventListener() {}, removeEventListener() {} }
        : matchMedia(query);
"""

# Whether the stylesheet hides the element in the installed app: a rule under
# the display-mode media query that matches it and sets display to none.
HIDDEN_IN_THE_APP = """(element) => {
    // Rules sit inside cascade layers, so every grouping rule is walked.
    const hides = (rules, inApp) => {
        for (const rule of rules) {
            if (rule instanceof CSSStyleRule) {
                if (inApp && element.matches(rule.selectorText) && rule.style.display === "none") {
                    return true;
                }
            } else if (rule.cssRules) {
                const media = rule instanceof CSSMediaRule
                    && rule.conditionText.includes("display-mode: standalone");
                if (hides(rule.cssRules, inApp || media)) {
                    return true;
                }
            }
        }
        return false;
    };
    for (const sheet of document.styleSheets) {
        let rules;
        try { rules = sheet.cssRules; } catch { continue; }
        if (hides(rules, false)) {
            return true;
        }
    }
    return false;
}"""


@pytest.fixture
def install_url(live_server, pwa_enabled):
    return f"{live_server.url}/install/"


@pytest.fixture
def open_as(browser, install_url):
    """Open the install page in a fresh context with the given user agent."""
    contexts = []

    def open_page(user_agent, standalone=False):
        context = browser.new_context(user_agent=user_agent)
        contexts.append(context)
        page = context.new_page()
        if standalone:
            page.add_init_script(OPENED_AS_THE_APP)
        page.goto(install_url)
        return page

    yield open_page
    for context in contexts:
        context.close()


def this_device(page, device):
    return page.locator(f'[data-mvp-install-device="{device}"]')


@pytest.mark.django_db(transaction=True)
class TestThisDevice:
    @pytest.mark.parametrize(
        ("user_agent", "device"),
        [
            (IPHONE, "ios"),
            (ANDROID, "android"),
            (MAC_SAFARI, "safari"),
            (FIREFOX, "firefox"),
            (DESKTOP_CHROME, "chromium"),
        ],
    )
    def test_the_card_shows_the_steps_for_this_device_alone(
        self, open_as, user_agent, device
    ):
        page = open_as(user_agent)

        expect(page.locator('[aria-labelledby="install-this-device"]')).to_be_visible()
        for other in DEVICES:
            if other == device:
                expect(this_device(page, other)).to_be_visible()
            else:
                expect(this_device(page, other)).to_be_hidden()

    @pytest.mark.parametrize(("user_agent", "device"), [(IPHONE, "ios"), (ANDROID, "android")])
    def test_a_phone_leaves_its_own_section_out_of_other_devices(
        self, open_as, user_agent, device
    ):
        page = open_as(user_agent)

        expect(page.locator(f'[data-mvp-install-other="{device}"]')).to_be_hidden()

    def test_a_computer_lists_both_phones_under_other_devices(self, open_as):
        page = open_as(DESKTOP_CHROME)

        expect(page.locator('[data-mvp-install-other="ios"]')).to_be_visible()
        expect(page.locator('[data-mvp-install-other="android"]')).to_be_visible()


@pytest.mark.django_db(transaction=True)
class TestTheBrowsersInstallPrompt:
    def test_an_offered_prompt_replaces_the_steps_with_the_install_button(
        self, open_as
    ):
        page = open_as(DESKTOP_CHROME)

        page.evaluate(OFFER_INSTALL, "accepted")

        expect(page.locator("[data-mvp-install-prompt]")).to_be_visible()
        expect(this_device(page, "chromium")).to_be_hidden()

    def test_accepting_the_prompt_says_the_app_is_installed(self, open_as):
        page = open_as(DESKTOP_CHROME)
        page.evaluate(OFFER_INSTALL, "accepted")

        page.locator("[data-mvp-install-prompt] button").click()

        assert page.evaluate("() => window.promptShown") is True
        expect(page.locator('[data-mvp-install-state="just-installed"]')).to_be_visible()
        expect(page.locator('[aria-labelledby="install-this-device"]')).to_be_hidden()

    def test_dismissing_the_prompt_brings_back_the_steps(self, open_as):
        page = open_as(DESKTOP_CHROME)
        page.evaluate(OFFER_INSTALL, "dismissed")

        page.locator("[data-mvp-install-prompt] button").click()

        expect(page.locator("[data-mvp-install-prompt]")).to_be_hidden()
        expect(this_device(page, "chromium")).to_be_visible()
        expect(page.locator('[data-mvp-install-state="just-installed"]')).to_be_hidden()

    def test_installing_from_the_browsers_own_menu_says_the_app_is_installed(
        self, open_as
    ):
        page = open_as(DESKTOP_CHROME)

        page.evaluate("() => window.dispatchEvent(new Event('appinstalled'))")

        expect(page.locator('[data-mvp-install-state="just-installed"]')).to_be_visible()


@pytest.mark.django_db(transaction=True)
class TestOpenedInTheInstalledApp:
    def test_the_page_says_it_is_installed_and_nothing_else(self, open_as):
        page = open_as(DESKTOP_CHROME, standalone=True)

        expect(page.locator('[data-mvp-install-state="installed"]')).to_be_visible()
        expect(page.locator('[aria-labelledby="install-other-devices"]')).to_be_hidden()
        assert page.locator(".page-title").evaluate(HIDDEN_IN_THE_APP) is True

    def test_in_a_browser_tab_the_title_and_steps_show(self, open_as):
        page = open_as(DESKTOP_CHROME)

        expect(page.locator('[data-mvp-install-state="installed"]')).to_be_hidden()
        expect(page.locator(".page-title")).to_be_visible()
        expect(page.locator('[aria-labelledby="install-other-devices"]')).to_be_visible()

    def test_no_other_page_hides_its_title_in_the_app(self, browser, live_server):
        page = browser.new_page()
        page.goto(f"{live_server.url}/components/")

        assert page.locator(".page-title").first.evaluate(HIDDEN_IN_THE_APP) is False
        page.close()
