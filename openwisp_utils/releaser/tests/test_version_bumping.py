from unittest.mock import mock_open, patch

import pytest
from openwisp_utils.releaser.version import bump_version, get_current_version

SAMPLE_INIT_FILE = """
# Some comments
VERSION = (1, 2, 0, "alpha")
# More comments
"""

EXPECTED_BUMPED_CONTENT = """
# Some comments
VERSION = (1, 2, 0, "final")
# More comments
"""


@pytest.fixture
def mock_config():
    return {"version_path": "path/__init__.py"}


@pytest.fixture
def mock_config_no_path():
    return {}


@patch("os.path.exists", return_value=True)
def test_get_current_version_success(_, mock_config):
    with patch("builtins.open", mock_open(read_data=SAMPLE_INIT_FILE)):
        version, version_type = get_current_version(mock_config)
        assert version == "1.2.0"
        assert version_type == "alpha"


def test_get_current_version_no_path_in_config(mock_config_no_path):
    version, version_type = get_current_version(mock_config_no_path)
    assert version is None
    assert version_type is None


@patch("os.path.exists", return_value=False)
def test_get_current_version_file_not_found(_, mock_config):
    version, version_type = get_current_version(mock_config)
    assert version is None
    assert version_type is None


def test_bump_version_success(mock_config):
    m_open = mock_open(read_data=SAMPLE_INIT_FILE)
    with patch("os.path.exists", return_value=True), patch("builtins.open", m_open):
        result = bump_version(mock_config, "1.2.0")

    assert result is True
    written_content = m_open().write.call_args[0][0]
    expected_content = 'VERSION = (1, 2, 0, "final")'
    assert expected_content in written_content


def test_bump_version_no_path_in_config(mock_config_no_path):
    result = bump_version(mock_config_no_path, "1.2.0")
    assert result is False


def test_bump_version_file_not_found(mock_config):
    with patch("os.path.exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            bump_version(mock_config, "1.2.0")


def test_get_current_version_no_tuple(mock_config):
    """Tests that get_current_version raises RuntimeError if VERSION is not found."""
    with patch("os.path.exists", return_value=True), patch(
        "builtins.open", mock_open(read_data="NO_VERSION_HERE")
    ):
        with pytest.raises(RuntimeError, match="Could not find the VERSION tuple"):
            get_current_version(mock_config)


def test_get_current_version_short_tuple(mock_config):
    """Tests RuntimeError if VERSION tuple has fewer than four elements."""
    with patch("os.path.exists", return_value=True), patch(
        "builtins.open", mock_open(read_data="VERSION = (1, 2)")
    ):
        with pytest.raises(
            RuntimeError, match="does not appear to have at least three"
        ):
            get_current_version(mock_config)


def test_bump_version_no_tuple_found(mock_config):
    """Tests RuntimeError during version bumping if VERSION is not found."""
    with patch("os.path.exists", return_value=True), patch(
        "builtins.open", mock_open(read_data="NO_VERSION_HERE")
    ):
        with pytest.raises(RuntimeError, match="Failed to find and bump VERSION"):
            bump_version(mock_config, "1.2.1")
