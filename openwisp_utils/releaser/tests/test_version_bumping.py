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
        version = get_current_version(mock_config)
        assert version == "1.2.0"


def test_get_current_version_no_path_in_config(mock_config_no_path):
    version = get_current_version(mock_config_no_path)
    assert version is None


@patch("os.path.exists", return_value=False)
def test_get_current_version_file_not_found(_, mock_config):
    version = get_current_version(mock_config)
    assert version is None


def test_bump_version_success(mock_config):
    m_open = mock_open(read_data=SAMPLE_INIT_FILE)
    with patch("os.path.exists", return_value=True), patch("builtins.open", m_open):
        result = bump_version(mock_config, "1.2.0")

    assert result is True
    m_open().write.assert_called_once_with(EXPECTED_BUMPED_CONTENT)


def test_bump_version_no_path_in_config(mock_config_no_path):
    result = bump_version(mock_config_no_path, "1.2.0")
    assert result is False


def test_bump_version_file_not_found(mock_config):
    with pytest.raises(FileNotFoundError):
        bump_version(mock_config, "1.2.0")
