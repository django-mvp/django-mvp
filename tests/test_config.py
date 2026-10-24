"""Tests for ``mvp.config`` — the merged ``MVP_CONFIG`` dict.

Mirrors ``mvp/config.py`` (the testing standard). Covers the ``theme`` block FS-026 US1
adds: the package defaults, and the deep-merge behaviour a project override
gets. The merge itself is exercised directly against ``mergedeep.merge`` —
the same function ``mvp/config.py`` calls to build ``MVP_CONFIG`` at import
time — because ``MVP_CONFIG`` is a process-wide singleton merged once at
import, and this suite's own ``tests/settings.py`` carries no ``theme``
override to exercise that path against.
"""

import copy
import warnings

import pytest
from mergedeep import merge  # type: ignore[import-untyped]

from mvp.config import (
    MVP_CONFIG,
    _warn_on_removed_navbar_lists,
    _warn_on_removed_sidebar_footer_setting,
)
from mvp.warnings import MVPDeprecationWarning


class TestRemovedSidebarFooterSetting:
    @staticmethod
    def _config_with_footer_override():
        config = copy.deepcopy(MVP_CONFIG)
        config["layout"]["sidebar"]["footer"] = ["mvp.actions.theme-controller"]
        return config

    def test_warns_when_the_setting_is_present(self):
        config = self._config_with_footer_override()
        with pytest.warns(MVPDeprecationWarning, match="layout.*sidebar.*footer"):
            _warn_on_removed_sidebar_footer_setting(config)

    def test_pops_the_setting_so_no_template_can_read_it(self):
        config = self._config_with_footer_override()
        with pytest.warns(MVPDeprecationWarning, match="layout.*sidebar.*footer"):
            _warn_on_removed_sidebar_footer_setting(config)
        assert "footer" not in config["layout"]["sidebar"]

    def test_does_not_warn_when_the_setting_is_absent(self):
        config = copy.deepcopy(MVP_CONFIG)
        with warnings.catch_warnings():
            warnings.simplefilter("error", MVPDeprecationWarning)
            _warn_on_removed_sidebar_footer_setting(config)


class TestRemovedNavbarWidthLists:
    @staticmethod
    def config_with(width):
        config = copy.deepcopy(MVP_CONFIG)
        config["layout"]["navbar"].setdefault(width, {})["end"] = [
            "mvp.actions.theme-controller"
        ]
        return config

    @pytest.mark.parametrize("width", ["desktop", "mobile"])
    def test_warns_when_a_width_list_is_present(self, width):
        config = self.config_with(width)
        with pytest.warns(MVPDeprecationWarning, match=f"navbar.*{width}.*end"):
            _warn_on_removed_navbar_lists(config)

    @pytest.mark.parametrize("width", ["desktop", "mobile"])
    def test_pops_the_list_so_no_template_can_read_it(self, width):
        config = self.config_with(width)
        with pytest.warns(MVPDeprecationWarning):
            _warn_on_removed_navbar_lists(config)
        assert "end" not in config["layout"]["navbar"].get(width, {})

    def test_keeps_the_mobile_sidebar_toggle(self):
        config = self.config_with("mobile")
        config["layout"]["navbar"]["mobile"]["sidebar_toggle"] = True
        with pytest.warns(MVPDeprecationWarning):
            _warn_on_removed_navbar_lists(config)
        assert config["layout"]["navbar"]["mobile"]["sidebar_toggle"] is True

    def test_does_not_warn_when_neither_list_is_set(self):
        config = copy.deepcopy(MVP_CONFIG)
        with warnings.catch_warnings():
            warnings.simplefilter("error", MVPDeprecationWarning)
            _warn_on_removed_navbar_lists(config)


class TestPageTitleSetting:
    @staticmethod
    def merged(override):
        """``MVP_CONFIG["page_title"]`` as a project's settings leave it."""
        config = copy.deepcopy(MVP_CONFIG)
        merge(config, {"page_title": override})
        return config["page_title"]["layout"]

    def test_the_default_gives_each_page_type_the_layout_it_always_drew(self):
        assert MVP_CONFIG["page_title"]["layout"] == {
            "page": "default",
            "form": "default",
            "detail": "default",
            "delete": "default",
            "list": "inline",
            "table": "compact",
        }

    def test_a_string_replaces_the_default_for_every_page_type(self):
        assert self.merged({"layout": "centred"}) == "centred"

    def test_a_dict_changes_the_types_it_names_and_keeps_the_rest(self):
        layout = self.merged({"layout": {"list": "centred"}})

        assert layout["list"] == "centred"
        assert layout["table"] == "compact"
        assert layout["page"] == "default"
