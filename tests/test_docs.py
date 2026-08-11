"""Guards live guidance against describing the removed ``inline_*``
attribute surface as supported configuration.

FS-025 rewrote the declaration surface `mvp/views/inline.py` exposes
(``InlineFormSet``/``InlinesMixin``) and removed the six ``inline_*`` view
attributes FS-024 shipped, plus the ``get_formset_factory_kwargs()`` method
they were assembled by. Nothing prevents a stale sentence surviving the
rewrite by accident — this is that check.

Source: mvp/views/inline.py
Spec: specs/025-multiple-related-sets/spec.md — FR-025, User Story 5
scenario 4; specs/025-multiple-related-sets/tasks.md — T053
"""

import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# The exact identifiers FS-024 shipped and FS-025 removed outright, read
# from the last commit that still had them (`git show
# 1038b3e:mvp/views/inline.py`): six class attributes plus the method that
# assembled them into `inlineformset_factory`'s kwargs.
REMOVED_IDENTIFIERS = [
    "inline_model",
    "inline_form_class",
    "inline_fields",
    "inline_extra",
    "inline_can_delete",
    "inline_max_num",
    "inline_title",
    "inline_description",
    "get_formset_factory_kwargs",
]

REMOVED_PATTERN = re.compile(
    r"\b(?:" + "|".join(re.escape(name) for name in REMOVED_IDENTIFIERS) + r")\b"
)

# "Live" guidance: what a developer reads today to configure a page —
# docs/ (excluding docs/adr/), README.md, demo/, mvp/, and the CHANGELOG's
# own Unreleased section. Deliberately excluded, because rewriting it would
# erase a decision rather than supersede it:
#   - docs/adr/                    — accepted decisions, standing record
#   - every released CHANGELOG.md section — what a shipped version did
#   - specs/                       — feature specs and their working notes,
#                                     in their entirety
LIVE_TEXT_EXTENSIONS = {".py", ".md", ".html"}
LIVE_ROOT_NAMES = ("docs", "demo", "mvp")


def _iter_live_files():
    """Yield every path FS-025 US5 T053 treats as live guidance."""
    for root_name in LIVE_ROOT_NAMES:
        root = BASE_DIR / root_name
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix not in LIVE_TEXT_EXTENSIONS:
                continue
            relative_parts = path.relative_to(root).parts
            if root_name == "docs" and relative_parts[0] == "adr":
                continue
            yield path
    yield BASE_DIR / "README.md"


def _changelog_unreleased_section():
    """Return only the CHANGELOG's ``## [Unreleased]`` section text.

    Every other section documents a version that has already shipped with
    those attributes described in it; only Unreleased describes what the
    next release supports.
    """
    text = (BASE_DIR / "CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(r"## \[Unreleased\](.*?)(?=\n## \[|\Z)", text, flags=re.DOTALL)
    assert match is not None, "CHANGELOG.md has no '## [Unreleased]' heading"
    return match.group(1)


class TestLiveGuidanceHasNoRemovedInlineAttributes:
    """No file a developer reads to configure a page today still describes
    a removed ``inline_*`` attribute, or ``get_formset_factory_kwargs``, as
    supported configuration."""

    def test_no_live_file_mentions_a_removed_identifier(self):
        offenders = {}
        for path in _iter_live_files():
            text = path.read_text(encoding="utf-8")
            found = sorted(set(REMOVED_PATTERN.findall(text)))
            if found:
                offenders[str(path.relative_to(BASE_DIR))] = found
        assert offenders == {}, (
            f"Live guidance still describes removed inline_* attributes: {offenders}"
        )

    def test_changelog_unreleased_section_mentions_no_removed_identifier(self):
        found = sorted(set(REMOVED_PATTERN.findall(_changelog_unreleased_section())))
        assert found == [], f"CHANGELOG.md's Unreleased section still names: {found}"
