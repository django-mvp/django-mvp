"""Tests for ``mvp.config`` — the merged ``MVP_CONFIG`` dict.

Mirrors ``mvp/config.py`` (Article X). Covers the ``theme`` block FS-026 US1
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

from mvp.config import MVP_CONFIG, _warn_on_removed_sidebar_footer_setting
from mvp.warnings import MVPDeprecationWarning


class TestThemeConfigDefaults:
    """No project override: the shipped defaults ``MVP_CONFIG`` exposes."""

    def test_theme_default_is_a_prebuilt_theme(self):
        """The package ships no palette of its own, so the applied theme is one
        of DaisyUI's (docs/adr/0016)."""
        assert MVP_CONFIG["theme"]["default"] == "light"

    def test_theme_dark_is_a_prebuilt_theme(self):
        assert MVP_CONFIG["theme"]["dark"] == "dark"

    def test_theme_choices_is_empty(self):
        assert MVP_CONFIG["theme"]["choices"] == []

    def test_theme_is_a_top_level_sibling_of_brand_not_nested_in_layout(self):
        """A theme is appearance, not a structural layout concern (plan.md
        Design: 'The configuration block')."""
        assert "theme" in MVP_CONFIG
        assert "theme" not in MVP_CONFIG["layout"]
        assert set(MVP_CONFIG["theme"]) == {"default", "dark", "choices"}


class TestThemeConfigOverrideMerge:
    """A project override of one ``theme`` key merges without disturbing the
    other ``theme`` key or any sibling top-level block — the same deep merge
    ``mvp/config.py`` performs at import time via ``mergedeep.merge``.
    """

    @staticmethod
    def _defaults():
        """A deep copy of the real package defaults, so merging into it can't
        mutate the process-wide ``MVP_CONFIG`` other tests read."""
        return copy.deepcopy(MVP_CONFIG)

    def test_overriding_default_leaves_choices_and_siblings_untouched(self):
        config = self._defaults()
        merge(config, {"theme": {"default": "dracula"}})
        assert config["theme"]["default"] == "dracula"
        assert config["theme"]["choices"] == []
        assert config["brand"] == MVP_CONFIG["brand"]
        assert config["layout"] == MVP_CONFIG["layout"]

    def test_overriding_choices_leaves_default_and_siblings_untouched(self):
        config = self._defaults()
        merge(config, {"theme": {"choices": ["light", "dark", "dracula"]}})
        assert config["theme"]["choices"] == ["light", "dark", "dracula"]
        assert config["theme"]["default"] == "light"
        assert config["theme"]["dark"] == "dark"
        assert config["brand"] == MVP_CONFIG["brand"]
        assert config["layout"] == MVP_CONFIG["layout"]


class TestTableConfigDefaults:
    """No project override: the table section's shipped default (issue #255)."""

    def test_wrap_default_is_off(self):
        assert MVP_CONFIG["table"]["wrap"] is False


class TestTableConfigOverrideMerge:
    """A project override of ``table.wrap`` merges without disturbing any
    sibling top-level block — the same deep merge ``mvp/config.py`` performs
    at import time via ``mergedeep.merge``."""

    @staticmethod
    def _defaults():
        """A deep copy of the real package defaults, so merging into it can't
        mutate the process-wide ``MVP_CONFIG`` other tests read."""
        return copy.deepcopy(MVP_CONFIG)

    def test_overriding_wrap_leaves_siblings_untouched(self):
        config = self._defaults()
        merge(config, {"table": {"wrap": True}})
        assert config["table"]["wrap"] is True
        assert config["theme"] == MVP_CONFIG["theme"]
        assert config["layout"] == MVP_CONFIG["layout"]


class TestRemovedSidebarFooterSetting:
    """``layout.sidebar.footer`` (docs/adr/0023): a project that still sets
    it gets a deprecation warning and the key is popped, so no template can
    read a value that no longer has any effect."""

    @staticmethod
    def _config_with_footer_override():
        config = copy.deepcopy(MVP_CONFIG)
        config["layout"]["sidebar"]["footer"] = ["actions.theme-controller"]
        return config

    def test_warns_when_the_setting_is_present(self):
        config = self._config_with_footer_override()
        with pytest.warns(MVPDeprecationWarning, match="layout.*sidebar.*footer"):
            _warn_on_removed_sidebar_footer_setting(config)

    def test_pops_the_setting_so_no_template_can_read_it(self):
        config = self._config_with_footer_override()
        with pytest.warns(MVPDeprecationWarning):
            _warn_on_removed_sidebar_footer_setting(config)
        assert "footer" not in config["layout"]["sidebar"]

    def test_does_not_warn_when_the_setting_is_absent(self):
        config = copy.deepcopy(MVP_CONFIG)
        with warnings.catch_warnings():
            warnings.simplefilter("error", MVPDeprecationWarning)
            _warn_on_removed_sidebar_footer_setting(config)


class TestPwaConfigDefaults:
    """The ``pwa`` block: off by default, every other key unset."""

    def test_the_feature_is_off(self):
        assert MVP_CONFIG["pwa"]["enabled"] is False

    def test_names_and_colours_are_unset(self):
        pwa = MVP_CONFIG["pwa"]

        assert pwa["name"] is None
        assert pwa["short_name"] is None
        assert pwa["start_url"] is None
        assert pwa["theme_color"] is None
        assert pwa["background_color"] is None
        assert pwa["service_worker"] is None

    def test_display_is_standalone(self):
        assert MVP_CONFIG["pwa"]["display"] == "standalone"
