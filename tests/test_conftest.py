"""Tests for tests/conftest.py's browser-test skip decision.

This mirrors ``tests/conftest.py`` directly (Article X: a test whose subject
*is* a Python module has something to mirror, and conftest.py is one), so no
``non-mirror-paths`` declaration is needed.

The behaviour under test is why #171 was filed: the ``requires_browser``
marker used to skip silently everywhere a browser was missing, including in
CI where a browser is always expected once the workflow installs it. A
silent skip in CI is indistinguishable from the test never having existed.
"""

from tests.conftest import _should_skip_browser_tests


class TestShouldSkipBrowserTests:
    """Skip only for a contributor without a browser installed locally;
    never skip in CI, so a broken install step fails loudly instead."""

    def test_skips_locally_without_a_browser(self):
        assert _should_skip_browser_tests(has_browser=False, in_ci=False) is True

    def test_runs_locally_with_a_browser(self):
        assert _should_skip_browser_tests(has_browser=True, in_ci=False) is False

    def test_runs_in_ci_with_a_browser(self):
        assert _should_skip_browser_tests(has_browser=True, in_ci=True) is False

    def test_never_skips_in_ci_even_without_a_browser(self):
        # A missing browser in CI means the install step didn't run or
        # failed. That must surface as a loud failure from Playwright's own
        # launch error, not a silent skip — see #171.
        assert _should_skip_browser_tests(has_browser=False, in_ci=True) is False
