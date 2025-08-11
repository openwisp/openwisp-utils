from unittest.mock import mock_open, patch

import pytest

from releaser.version import bump_version, get_current_version

SAMPLE_INIT_FILE = """
VERSION = (1, 2, 0, "alpha", 0)
"""


@pytest.fixture
def mock_config():
    """Provides a mock config dictionary."""
    return {"version_path": "path/__init__.py"}


@patch("os.path.exists", return_value=True)
def test_get_current_version(_, mock_config):
    """Verify it correctly parses the version from the tuple."""
    with patch("builtins.open", mock_open(read_data=SAMPLE_INIT_FILE)):
        version = get_current_version(mock_config)
        assert version == "1.2.0"


@patch("os.path.exists", return_value=True)
def test_bump_version_to_final(_, mock_config):
    """Verify it correctly bumps the version and sets the status to 'final'."""
    m_open = mock_open(read_data=SAMPLE_INIT_FILE)
    with patch("builtins.open", m_open):
        bump_version(mock_config, "1.2.1")

    m_open().write.assert_called_once()
    written_content = m_open().write.call_args[0][0]

    assert 'VERSION = (1, 2, 1, "final")' in written_content
