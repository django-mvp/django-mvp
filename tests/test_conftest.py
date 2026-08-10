"""Tests for tests/conftest.py's browser-test skip decision.

Declared as a ``non-mirror-paths`` exemption in pyproject.toml: its subject,
``tests/conftest.py``, is test infrastructure shared by three otherwise
unrelated test modules (test_renderers, test_error, test_form_formset), not
an ``mvp/`` package module for the mirror rule to match.

The behaviour under test is why #171 was filed: the ``requires_browser``
marker used to skip identically everywhere a browser was missing, local
machine or CI. A CI run that never asked for a browser (today's workflow,
``install-playwright: false``) should still skip quietly. A CI run that DID
ask and still has no browser — the install step ran and left it broken, or
regressed away entirely — should fail loudly instead.
"""

from tests.conftest import _should_skip_browser_tests


class TestShouldSkipBrowserTests:
    """Skip locally, and in CI when no install was ever attempted; fail
    loudly only once CI has actually tried to get a browser and still has
    none."""

    def test_runs_with_a_browser_present(self):
        assert (
            _should_skip_browser_tests(
                has_browser=True, in_ci=False, browsers_attempted=False
            )
            is False
        )

    def test_runs_with_a_browser_present_in_ci_too(self):
        assert (
            _should_skip_browser_tests(
                has_browser=True, in_ci=True, browsers_attempted=True
            )
            is False
        )

    def test_skips_locally_without_a_browser(self):
        assert (
            _should_skip_browser_tests(
                has_browser=False, in_ci=False, browsers_attempted=False
            )
            is True
        )

    def test_skips_locally_even_if_some_unrelated_project_left_a_cache(self):
        # A contributor's machine can have ~/.cache/ms-playwright from a
        # different project entirely. Outside CI that must never turn into a
        # loud failure — only the browser actually being missing matters.
        assert (
            _should_skip_browser_tests(
                has_browser=False, in_ci=False, browsers_attempted=True
            )
            is True
        )

    def test_skips_in_ci_when_no_install_was_ever_attempted(self):
        # Today's workflow: install-playwright defaults to false, so the
        # install step never runs and the cache root never appears. That
        # must stay a quiet skip, not a failure — this is the state the
        # suite is in right now, and it must stay green.
        assert (
            _should_skip_browser_tests(
                has_browser=False, in_ci=True, browsers_attempted=False
            )
            is True
        )

    def test_fails_loudly_in_ci_once_an_install_was_attempted_and_still_missing(
        self,
    ):
        # The install step ran (the cache root exists) but the browser this
        # test needs still isn't there — a broken or reverted install,
        # exactly the regression #171 is about. Left unskipped so it fails
        # on Playwright's own launch error.
        assert (
            _should_skip_browser_tests(
                has_browser=False, in_ci=True, browsers_attempted=True
            )
            is False
        )
