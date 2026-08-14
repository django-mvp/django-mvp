"""Tests for mvp.utils — the helpers and the bundled icon pack."""

from mvp.utils import BS5_ICONS


def resolve(name):
    """The Bootstrap Icons class ``name`` maps to in the bundled pack.

    Keys may declare comma-separated aliases, so a plain dict lookup is not
    enough — django-easy-icons expands them when it loads the pack.
    """
    for key, value in BS5_ICONS.items():
        if name in [alias.strip() for alias in key.split(",")]:
            return value
    raise KeyError(name)


class TestSortIcons:
    """Sorting glyphs have to point the way they sort.

    A table header renders both directional icons and shows one at a time
    (``mvp/templates/django_tables2/bootstrap5-mvp.html``), so a pair that
    points the same way — or points the wrong way — is invisible until someone
    clicks a column and reads the arrow.
    """

    def test_ascending_points_up(self):
        assert resolve("sort-asc") == "bi bi-arrow-up-short"

    def test_descending_points_down(self):
        assert resolve("sort-desc") == "bi bi-arrow-down-short"

    def test_the_two_directions_differ(self):
        assert resolve("sort-asc") != resolve("sort-desc")

    def test_the_plain_name_is_direction_free(self):
        """``sort`` labels a sort control, so it must not claim a direction."""
        assert resolve("sort") not in {resolve("sort-asc"), resolve("sort-desc")}
