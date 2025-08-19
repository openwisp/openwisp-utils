from unittest.mock import mock_open, patch

from openwisp_utils.releaser.release import (
    adjust_markdown_headings,
    demote_markdown_headings,
    get_release_block_from_file,
    rst_to_markdown,
)
from openwisp_utils.releaser.utils import format_file_with_docstrfmt

RST_SAMPLE = """
Features
~~~~~~~~

- A new feature.

Changes
~~~~~~~

Backward-incompatible changes
+++++++++++++++++++++++++++++

- A breaking change.
"""

MD_EXPECTED = """
### Features

- A new feature.

### Changes

#### Backward-incompatible changes

- A breaking change.
"""


def test_rst_to_markdown_conversion():
    """Test basic reStructuredText to Markdown conversion."""
    # Test that the function calls it correctly.
    with patch("pypandoc.convert_text", return_value="Converted") as mock_convert:
        result = rst_to_markdown(RST_SAMPLE)
        assert result == "Converted"
        mock_convert.assert_called_once()


def test_adjust_markdown_headings():
    """Test that markdown headings are correctly adjusted for the CHANGES.md file."""
    raw_md = """
## Features

- A feature.

## Changes

### Backward-incompatible changes

- A change.
"""
    expected_md = """
### Features

- A feature.

### Changes

#### Backward-incompatible changes

- A change.
"""
    result = adjust_markdown_headings(raw_md)
    assert result.strip() == expected_md.strip()


def test_demote_markdown_headings():
    """Test that markdown headings are correctly demoted for the GitHub release body."""
    input_md = """
### Features

- A feature.

#### Dependencies

- A dependency.
"""
    expected_md = """
# Features

- A feature.

## Dependencies

- A dependency.
"""
    result = demote_markdown_headings(input_md)
    assert result.strip() == expected_md.strip()


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data="""
Changelog
=========

Version 1.2.0 [Unreleased]
--------------------------
- In progress.

Version 1.1.0
-------------
- A feature.

Version 1.0.0
-------------
- Initial release.
""",
)
def test_get_release_block_from_rst_file(mock_file):
    """Test extracting a release block from a CHANGES.rst file."""
    expected_block = "Version 1.1.0\n-------------\n- A feature."
    result = get_release_block_from_file("CHANGES.rst", "1.1.0")
    assert result == expected_block


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data="""
# Changelog

## Version 1.2.0 [Unreleased]
- In progress.

## Version 1.1.0
- A feature.

## Version 1.0.0
- Initial release.
""",
)
def test_get_release_block_from_md_file(mock_file):
    """Test extracting a release block from a CHANGES.md file."""
    expected_block = "## Version 1.1.0\n- A feature."
    result = get_release_block_from_file("CHANGES.md", "1.1.0")
    assert result == expected_block


@patch("openwisp_utils.releaser.utils.subprocess.run")
@patch("builtins.print")
def test_format_file_with_docstrfmt(mock_print, mock_subprocess):
    """Tests the `format_file_with_docstrfmt` function."""
    file_path = "CHANGES.rst"
    format_file_with_docstrfmt(file_path)

    expected_command = [
        "docstrfmt",
        "--ignore-cache",
        "--line-length",
        "74",
        file_path,
    ]
    mock_subprocess.assert_called_once_with(
        expected_command,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    mock_print.assert_called_once_with(f"✅ Formatted {file_path} successfully.")
