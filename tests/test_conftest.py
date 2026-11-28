"""Tests for the browser-test decisions in ``tests/conftest.py``.

The decision is worth pinning because getting it wrong is invisible. A guard
that skips in CI turns nineteen browser tests into nineteen green skips, which
reads exactly like nineteen passes on the checks page (issue #171).
"""

from tests.conftest import (
    OFF_THIS_MACHINE,
    _should_skip_browser_tests,
    answer_request,
)


class TestShouldSkipBrowserTests:
    def test_runs_when_the_browser_is_present(self):
        assert _should_skip_browser_tests(has_browser=True, env={}) is False

    def test_skips_locally_without_a_browser(self):
        assert _should_skip_browser_tests(has_browser=False, env={}) is True

    def test_does_not_skip_in_ci_without_a_browser(self):
        assert (
            _should_skip_browser_tests(has_browser=False, env={"CI": "true"}) is False
        )

    def test_treats_an_empty_ci_variable_as_not_ci(self):
        assert _should_skip_browser_tests(has_browser=False, env={"CI": ""}) is True


class FakeRoute:
    """The answers a Playwright route can give, recorded."""

    def __init__(self):
        self.answer = None
        self.body = None

    def fulfill(self, body, content_type, headers):
        self.answer = "fulfill"
        self.body = body

    def abort(self, reason):
        self.answer = "abort"


class FakeRequest:
    def __init__(self, url, method="GET"):
        self.url = url
        self.method = method


def _answer(url):
    route, external = FakeRoute(), []
    answer_request(route, FakeRequest(url), external)
    return route, external


class TestAnswerRequest:
    def test_a_request_to_a_stood_in_host_is_served_from_the_repository(self):
        route, external = _answer(
            "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png"
        )

        assert (route.answer, external) == ("fulfill", [])
        assert route.body.startswith(b"\x89PNG")

    def test_a_request_to_any_other_host_is_refused_and_recorded(self):
        route, external = _answer("https://example.com/tracker.js")

        assert route.answer == "abort"
        assert external == ["GET https://example.com/tracker.js"]


class TestOffThisMachine:
    def test_only_addresses_on_other_machines_match(self):
        addresses = {
            "http://localhost:8123/components/": False,
            "http://127.0.0.1:41233/": False,
            "http://[::1]:8000/x": False,
            "https://localhost/": False,
            "https://example.com/localhost/": True,
            "http://localhost.example.com/": True,
            "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js": True,
        }

        matched = {url: bool(OFF_THIS_MACHINE.match(url)) for url in addresses}

        assert matched == addresses
