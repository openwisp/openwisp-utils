from unittest.mock import mock_open, patch

from openwisp_utils.releaser.release import update_changelog_file

SAMPLE_CHANGELOG = """Changelog
=========

Version 1.2.0 [Unreleased]
--------------------------

Work in progress.

Version 1.1.2 [2025-06-18]
--------------------------

- A previous fix.
"""

NEW_RELEASE_BLOCK = """Version 1.1.3  [2025-08-11]
---------------------------

Bugfixes
~~~~~~~~

- A critical bugfix.
"""


@patch("builtins.open", new_callable=mock_open, read_data=SAMPLE_CHANGELOG)
def test_update_changelog_bugfix_flow(mock_file):
    """Test that a bugfix release inserts content correctly."""
    update_changelog_file("CHANGES.rst", NEW_RELEASE_BLOCK, "1.1.3", is_bugfix=True)

    written_content = mock_file().write.call_args[0][0]

    assert NEW_RELEASE_BLOCK in written_content
    assert "Version 1.2.0 [Unreleased]" in written_content
    assert written_content.find("Version 1.1.3") > written_content.find(
        "Version 1.2.0 [Unreleased]"
    )
    assert written_content.find("Version 1.1.3") < written_content.find("Version 1.1.2")


@patch("builtins.open", new_callable=mock_open, read_data=SAMPLE_CHANGELOG)
def test_update_changelog_feature_flow(mock_file):
    """Test that a feature release REPLACES the unreleased block."""
    feature_release_block = NEW_RELEASE_BLOCK.replace("1.1.3", "1.2.0")
    update_changelog_file(
        "CHANGES.rst", feature_release_block, "1.2.0", is_bugfix=False
    )

    written_content = mock_file().write.call_args[0][0]

    assert "Version 1.2.0  [2025-08-11]" in written_content
    assert "Version 1.2.0 [Unreleased]" not in written_content
    assert "Version 1.3.0 [Unreleased]" in written_content
    assert "Version 1.1.2 [2025-06-18]" in written_content
