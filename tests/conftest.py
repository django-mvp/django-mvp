"""Shared test fixtures for django-mvp test suite.

Standardized per Phase 2: all model fixtures and view factory helpers live here
so individual test files stay focused on assertions, not setup boilerplate.
"""

import importlib
import importlib.util
import os
import re
import time
import types
from pathlib import Path

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.test import RequestFactory, override_settings
from django.urls import URLResolver, clear_url_caches
from django.views.generic import TemplateView

import mvp.urls as mvp_urls
from mvp.config import MVP_CONFIG
from mvp.menus import AccountCenterMenu
from tests.factories import ArticleFactory, CategoryFactory, ProductFactory
from tests.testapp_account.menus import build_entries

User = get_user_model()


def urlconf_of(*patterns, **attributes):
    """A URLconf object holding ``patterns``, for ``ROOT_URLCONF`` or ``urlconf=``.

    Args:
        *patterns: The URL patterns the URLconf serves.
        **attributes: Anything else a URLconf module may define, such as
            ``handler404``.

    Returns:
        A module object with ``urlpatterns`` and the given attributes set on it.
        It is a module, not a class, because ``pytest.mark.urls`` treats a class
        passed to it as the test class being decorated.
    """
    urlconf = types.ModuleType("urlconf")
    urlconf.urlpatterns = list(patterns)
    for name, value in attributes.items():
        setattr(urlconf, name, value)
    return urlconf


def _reload_urlconfs(module):
    """Rebuild every resolver in ``module`` against ``mvp.urls``'s current
    ``urlpatterns`` (T011, D17).

    ``include("mvp.urls")`` hands a ``URLResolver`` the module object, and
    the resolver's ``url_patterns`` is a ``cached_property`` frozen to the
    list it first read. Reloading ``mvp.urls`` alone rebinds
    ``mvp.urls.urlpatterns`` but leaves any resolver that already read the
    old list stale, so ``module`` — the test module that built its own
    urlconf by calling ``include("mvp.urls")`` at import time, the way
    ``tests/test_urls.py`` and ``tests/test_views/test_account.py`` both do
    — is reloaded too, rebuilding it with a resolver whose cached property
    has not been read yet. ``clear_url_caches()`` drops ``get_resolver()``'s
    cache, which is keyed by urlconf identity.
    """
    importlib.reload(mvp_urls)
    importlib.reload(module)
    clear_url_caches()


@pytest.fixture
def allauth_installed(request):
    middleware = override_settings(
        MIDDLEWARE=[
            *settings.MIDDLEWARE,
            "allauth.account.middleware.AccountMiddleware",
        ]
    )
    installed_apps = override_settings(
        INSTALLED_APPS=[*settings.INSTALLED_APPS, "allauth", "allauth.account"]
    )
    middleware.enable()
    installed_apps.enable()
    _reload_urlconfs(request.module)
    try:
        yield
    finally:
        installed_apps.disable()
        middleware.disable()
        _reload_urlconfs(request.module)


PWA_URLCONF_MODULES = (
    "demo.urls",
    "tests.urls_pwa",
)


def reload_pwa_urlconfs():
    """Rebuild ``mvp.urls`` and swap a fresh include of it into every URLconf
    that mounts it, so the manifest and worker routes follow ``MVP_CONFIG["pwa"]``.

    ``mvp.urls`` reads the setting once, at import. A resolver built from an
    earlier import caches the old ``urlpatterns``, so each include of it is
    replaced in place. The URLconf modules themselves are not reloaded:
    ``demo.urls`` adds routes at import that depend on ``DEBUG``, and reloading
    it inside a test, where ``DEBUG`` is off, would drop them for every later
    test in the process.
    """
    importlib.reload(mvp_urls)
    for name in PWA_URLCONF_MODULES:
        patterns = importlib.import_module(name).urlpatterns
        for index, pattern in enumerate(patterns):
            if getattr(pattern, "urlconf_name", None) is mvp_urls:
                patterns[index] = URLResolver(
                    pattern.pattern,
                    mvp_urls,
                    pattern.default_kwargs,
                    pattern.app_name,
                    pattern.namespace,
                )
    clear_url_caches()


@pytest.fixture
def mobile_navbar_toggle(monkeypatch):
    monkeypatch.setitem(
        MVP_CONFIG["layout"]["navbar"]["mobile"], "sidebar_toggle", True
    )


@pytest.fixture
def pwa_enabled():
    patch = pytest.MonkeyPatch()
    patch.setitem(MVP_CONFIG, "pwa", {"theme_color": "#123456"})
    reload_pwa_urlconfs()
    try:
        yield
    finally:
        patch.undo()
        reload_pwa_urlconfs()


@pytest.fixture
def testapp_account_entries():
    entries = build_entries()
    AccountCenterMenu.extend(entries)
    try:
        yield {entry.name: entry for entry in entries}
    finally:
        for entry in entries:
            entry.parent = None


@pytest.fixture
def make_user(django_user_model):
    """Build a user; a test overrides only the fields its assertions need."""

    def make(username="user", password="pw", **fields):
        return django_user_model.objects.create_user(
            username=username, password=password, **fields
        )

    return make


@pytest.fixture
def user(make_user):
    return make_user()


@pytest.fixture
def staff_user(make_user):
    return make_user("staff", is_staff=True)


@pytest.fixture
def superuser(django_user_model):
    return django_user_model.objects.create_superuser(
        username="superuser", password="pw"
    )


@pytest.fixture
def category(db):
    return CategoryFactory()


@pytest.fixture
def product(db):
    return ProductFactory()


@pytest.fixture
def article(db):
    return ArticleFactory()


def make_stub_view(mixin_class, extra_attrs=None, kwargs=None, user=None):
    """Build a concrete mixin + TemplateView stub with a fake GET request.

    Replaces the common pattern of:
        view_cls = type("StubView", (Mixin, TemplateView), attrs)
        view = view_cls()
        view.request = request; view.kwargs = {}; view.args = []

    Parameters
    ----------
    mixin_class : type
        The mixin to compose with TemplateView.
    extra_attrs : dict, optional
        Additional class-level attributes merged into the stub.
    kwargs : dict, optional
        URL kwargs passed to the view instance.
    user : User, optional
        Request user; defaults to anonymous User().

    Returns
    -------
    view instance with request, kwargs, and args set.
    """
    rf = RequestFactory()
    request = rf.get("/")
    request.user = user or User()

    attrs = {"template_name": "base.html", **(extra_attrs or {})}
    view_cls = type("StubView", (mixin_class, TemplateView), attrs)
    view = view_cls()
    view.request = request
    view.kwargs = kwargs or {}
    view.args = []
    return view


def _browser_is_installed():
    """True when Playwright is importable *and* its browser is downloaded.

    Testing the import alone is not enough. Installing the package is one
    step and downloading the browser is another, so a CI runner that has the
    dependency but has never run ``playwright install`` errors at launch
    instead of skipping. That gap is why the end-to-end formset tests had
    never run anywhere (specs/024-formset-pages/decisions.md D42).
    """
    if importlib.util.find_spec("playwright") is None:
        return False

    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as p:
            return Path(p.chromium.executable_path).exists()
    except Exception:
        return False


def _should_skip_browser_tests(has_browser, env):
    """Decide whether browser-marked tests skip, given the browser and the environment.

    Locally a missing browser is ordinary: a contributor who has not run
    ``playwright install`` should see skips, not a wall of errors.

    In CI it is a failure. ``.github/workflows/tests.yml`` passes
    ``install-playwright: true``, so a browser is always expected there, and
    skipping would hide exactly the thing this guard exists to surface —
    nineteen silent skips reading as nineteen passes (issue #171).
    """
    if has_browser:
        return False
    return env.get("CI", "").lower() not in {"1", "true"}


HAS_BROWSER = _browser_is_installed()

requires_browser = pytest.mark.skipif(
    _should_skip_browser_tests(HAS_BROWSER, os.environ),
    reason="playwright browser not installed (run: playwright install chromium)",
)


@pytest.fixture
def project_components(settings):
    """Put the fixture project's template directory ahead of the apps'."""
    templates = Path(__file__).resolve().parent / "fixtures" / "override_templates"
    engine = settings.TEMPLATES[0]
    settings.TEMPLATES = [{**engine, "DIRS": [str(templates), *engine.get("DIRS", [])]}]


# Browser tests -------------------------------------------------------------------

#: How long a browser action, a navigation or an ``expect`` waits. The 5 s that
#: individual tests used to set failed one run in six on a loaded CI runner.
BROWSER_TIMEOUT_MS = 20_000

#: axe-core, vendored so the accessibility tests need no network.
AXE_SCRIPT = Path(__file__).resolve().parent / "fixtures" / "axe.min.js"
AXE_CDN_URL = re.compile(
    r"https://cdnjs\.cloudflare\.com/ajax/libs/axe-core/.+/axe\.min\.js"
)

#: Tests that take over a second or start a subprocess, by node id prefix. The
#: fast selection ``-m "not e2e and not slow"`` skips them. Browser tests carry
#: ``e2e`` instead, so they are not listed here.
SLOW_TESTS = (
    "tests/test_email/test_brand.py",
    "tests/test_checks.py::TestEmailBrandCheck::test_an_unreadable_colour_is_a_warning_naming_the_theme_and_property",
    "tests/test_checks.py::TestEmailLogoCheck::test_a_project_png_means_no_warning",
    "tests/test_components/test_app_header.py::TestTheSiteNameBesideTheIcon::test_the_header_shows_the_sidebar_title_beside_the_icon_when_asked",
    "tests/test_components/test_email_pieces.py::TestEmailButton::test_the_colour_holds_where_cotton_hides_the_templates_variables_from_a_component",
    "tests/test_components/test_email_pieces.py::TestEmailButton::test_the_link_carries_the_address_and_the_text",
    "tests/test_components/test_email_pieces.py::TestEmailDivider::test_it_renders_a_rule_in_the_border_colour",
    "tests/test_components/test_email_pieces.py::TestEmailText::test_each_option_changes_the_paragraphs_style",
    "tests/test_components/test_form_formset.py::TestFormsetCountersAreNotLocalized::test_total_forms_input_carries_no_grouped_number",
    "tests/test_demo/test_email_templates.py::TestDemoEmailTemplates::test_the_html_message_renders_in_the_brand",
    "tests/test_demo/test_seed_accounts.py::TestSeedAccounts::",
    "tests/test_demo/test_seed_accounts.py::TestSeedAccountsPreferences::",
    "tests/test_email/test_base_template.py::TestBaseTemplate::test_a_filled_footer_replaces_the_default",
    "tests/test_email/test_base_template.py::TestBaseTemplate::test_plain_markup_in_the_body_is_styled_inline",
    "tests/test_email/test_base_template.py::TestBaseTemplate::test_the_style_block_holds_only_the_rules_that_could_not_be_inlined",
    "tests/test_email/test_base_template.py::TestThirdPartySender::test_the_text_body_is_the_apps_own_template",
    "tests/test_email/test_mvp_email.py::TestEmailBrandTag::test_no_dark_logo_stays_none",
    "tests/test_email/test_mvp_email.py::TestEmailBrandTag::test_the_palettes_are_put_in_the_context",
    "tests/test_models.py::TestDemoUserModel::test_makemigrations_has_nothing_to_write_for_any_app",
    "tests/test_mounted.py::TestAppMountedWithoutMain::test_host_page_draws_the_host_menu",
    "tests/test_preferences.py::TestFieldUnderAnotherName::",
    "tests/test_preferences.py::TestUserModelCheck::",
)


def wait_for_alpine(page):
    """Wait until Alpine has started and initialised every ``x-data`` element.

    Args:
        page: The Playwright page.

    ``window.Alpine`` exists as soon as the script has run, but a trigger is not
    wired until Alpine initialises it. A click before that follows the trigger's
    link and the page navigates away from under the test.
    """
    page.wait_for_function(
        "() => window.Alpine && Alpine.version"
        " && [...document.querySelectorAll('[x-data]')].every(el => el._x_dataStack)"
    )


def wait_for_transitions(page):
    """Wait until no CSS transition runs, a frame after the change that starts one.

    The browser cancels a transition it replaces, and a cancelled transition's
    ``finished`` promise rejects, so each pass waits on whatever is running and
    looks again. After ten rounds it stops waiting and returns.

    Args:
        page: The Playwright page.
    """
    page.evaluate(
        """async () => {
          const frame = () => new Promise(done => requestAnimationFrame(done));
          await frame();
          await frame();
          for (let round = 0; round < 10; round++) {
            const running = document.getAnimations()
              .filter(a => a instanceof CSSTransition);
            if (!running.length) return;
            await Promise.allSettled(running.map(a => a.finished));
          }
        }"""
    )


def frames(page, count):
    """Wait for ``count`` animation frames, the unit a drag's pace is counted in.

    Args:
        page: The Playwright page.
        count: How many frames to wait for.
    """
    page.evaluate(
        """async count => {
          for (let frame = 0; frame < count; frame++) {
            await new Promise(done => requestAnimationFrame(done));
          }
        }""",
        count,
    )


def wait_until_still(page):
    """Wait until nothing on the page is moving or being requested.

    No htmx request is in flight, no row or panel is held, and no CSS transition is
    running, for two animation frames in a row. This is the state a fixed pause
    after a gesture was standing in for.

    Args:
        page: The Playwright page.

    Raises:
        AssertionError: If the page is still busy after about 600 frames.
    """
    still = page.evaluate(
        """async () => {
          const frame = () => new Promise(done => requestAnimationFrame(done));
          const busy = () => document.querySelector('.htmx-request, .mvp-reorder-held')
            || document.getAnimations().some(a => a instanceof CSSTransition);
          let quiet = 0;
          for (let tries = 0; tries < 600 && quiet < 2; tries++) {
            await frame();
            quiet = busy() ? 0 : quiet + 1;
          }
          return quiet >= 2;
        }"""
    )
    assert still, "the page never came to rest"


def wait_until(condition, timeout=5.0, interval=0.02):
    """Poll ``condition`` until it is true, for state on the server side.

    A browser event, such as a dialog, reaches the test only during a Playwright
    call, so this never sees one. Wait for those with ``page.expect_event``.

    Args:
        condition: A callable returning a truthy value once the state is reached.
        timeout: Seconds to wait before failing.
        interval: Seconds between looks.
    """
    deadline = time.monotonic() + timeout
    while not condition():
        assert time.monotonic() < deadline, "the state was never reached"
        time.sleep(interval)


def pytest_collection_modifyitems(config, items):
    """Mark every browser test ``e2e`` and the listed slow tests ``slow``.

    A test is a browser test when its fixtures reach Playwright's ``browser``.
    Marking here means a new browser test cannot miss the marker, and
    ``pytest -m "not e2e and not slow"`` is the whole suite without them.
    """
    for item in items:
        if "browser" in item.fixturenames:
            item.add_marker(pytest.mark.e2e)
        if item.nodeid.startswith(SLOW_TESTS):
            item.add_marker(pytest.mark.slow)


def _configure_context(context, serve_axe=False):
    """Apply the suite's timeouts to a browser context.

    Args:
        context: The Playwright browser context.
        serve_axe: Answer the axe-core CDN address from the vendored copy. Routing
            turns the browser's HTTP cache off, so only a test module that loads
            axe-core asks for it.
    """
    context.set_default_timeout(BROWSER_TIMEOUT_MS)
    context.set_default_navigation_timeout(BROWSER_TIMEOUT_MS)
    if serve_axe:
        context.route(
            AXE_CDN_URL,
            lambda route: route.fulfill(
                path=str(AXE_SCRIPT), content_type="application/javascript"
            ),
        )


@pytest.fixture(autouse=True)
def _reset_framework_caches():
    """Empty the ``Site`` and ``ContentType`` caches after every test.

    Both cache rows by primary key in the process. A test database that rolls
    back leaves those entries pointing at rows that no longer exist, so the
    next test that looks one up gets a stale object.
    """
    yield
    Site.objects.clear_cache()
    ContentType.objects.clear_cache()


@pytest.fixture(autouse=True)
def _browser_defaults(request, monkeypatch):
    """Give every browser context a timeout that survives a loaded runner, and
    serve axe-core from the repository instead of a CDN.

    The contexts a test opens itself through ``browser.new_context`` or
    ``browser.new_page`` are configured the same way as the ``page`` fixture's.
    """
    if "browser" not in request.fixturenames:
        return
    from playwright.sync_api import expect

    expect.set_options(timeout=BROWSER_TIMEOUT_MS)
    serve_axe = "axe.min.js" in Path(request.module.__file__).read_text()
    browser = request.getfixturevalue("browser")
    new_context, new_page = browser.new_context, browser.new_page

    def configured_context(*args, **kwargs):
        context = new_context(*args, **kwargs)
        _configure_context(context, serve_axe)
        return context

    def configured_page(*args, **kwargs):
        page = new_page(*args, **kwargs)
        _configure_context(page.context, serve_axe)
        return page

    monkeypatch.setattr(browser, "new_context", configured_context)
    monkeypatch.setattr(browser, "new_page", configured_page)
