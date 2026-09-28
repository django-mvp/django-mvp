"""Tests for the browser-test skip decision in ``tests/conftest.py``.

The decision is worth pinning because getting it wrong is invisible. A guard
that skips in CI turns nineteen browser tests into nineteen green skips, which
reads exactly like nineteen passes on the checks page (issue #171).
"""

from tests.conftest import _should_skip_browser_tests


class TestShouldSkipBrowserTests:
    def test_runs_when_the_browser_is_present(self):
        assert _should_skip_browser_tests(has_browser=True, env={}) is False

    def test_runs_in_ci_when_the_browser_is_present(self):
        assert _should_skip_browser_tests(has_browser=True, env={"CI": "true"}) is False

    def test_skips_locally_without_a_browser(self):
        assert _should_skip_browser_tests(has_browser=False, env={}) is True

    def test_does_not_skip_in_ci_without_a_browser(self):
        assert (
            _should_skip_browser_tests(has_browser=False, env={"CI": "true"}) is False
        )

    def test_accepts_the_other_spelling_of_ci(self):
        assert _should_skip_browser_tests(has_browser=False, env={"CI": "1"}) is False

    def test_treats_an_empty_ci_variable_as_not_ci(self):
        assert _should_skip_browser_tests(has_browser=False, env={"CI": ""}) is True
