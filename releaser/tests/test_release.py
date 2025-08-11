from datetime import datetime
from unittest.mock import ANY, MagicMock, call

import pytest

from releaser.release import main as run_release


@pytest.fixture
def mock_all(mocker):
    """A master fixture to mock all external dependencies."""

    git_command_results = {
        ("git", "rev-parse", "--abbrev-ref", "HEAD"): MagicMock(
            stdout="main", check_returncode=True
        ),
        ("git", "cliff", "--unreleased"): MagicMock(
            stdout="[unreleased]\n----\n- A new feature.", check_returncode=True
        ),
    }

    default_mock = MagicMock(stdout="", stderr="", check_returncode=True)

    def subprocess_side_effect(command, *args, **kwargs):
        return git_command_results.get(tuple(command), default_mock)

    mocks = {
        "subprocess": mocker.patch(
            "releaser.release.subprocess.run", side_effect=subprocess_side_effect
        ),
        "questionary": mocker.patch("releaser.release.questionary"),
        "GitHub": mocker.patch("releaser.release.GitHub"),
        "time": mocker.patch("releaser.release.time.sleep"),
        "datetime": mocker.patch("releaser.release.datetime"),
        "open": mocker.patch("builtins.open", mocker.mock_open(read_data="")),
        "load_config": mocker.patch(
            "releaser.release.load_config",
            return_value={
                "repo": "test/repo",
                "version_path": "src/__init__.py",
                "changelog_path": "CHANGES.rst",
            },
        ),
        "get_current_version": mocker.patch(
            "releaser.release.get_current_version", return_value="1.2.0"
        ),
        "bump_version": mocker.patch("releaser.release.bump_version"),
        "update_changelog": mocker.patch("releaser.release.update_changelog_file"),
        "format_block": mocker.patch(
            "releaser.release.format_rst_block", side_effect=lambda x: x
        ),
        "format_file": mocker.patch("releaser.release.format_file_with_docstrfmt"),
        "_git_command_map": git_command_results,
    }

    mocks["questionary"].confirm.return_value.ask.return_value = True
    mocks["questionary"].text.return_value.ask.return_value = "1.2.1"
    mocks["questionary"].select.return_value.ask.return_value = "main"

    mock_dt = MagicMock()
    mock_dt.now.return_value = datetime(2025, 8, 11)
    mocks["datetime"] = mocker.patch("releaser.release.datetime", mock_dt)

    mock_gh_instance = mocks["GitHub"].return_value
    mock_gh_instance.create_pr.side_effect = ["http://pr.url/1", "http://pr.url/2"]
    mock_gh_instance.is_pr_merged.return_value = True

    return mocks


def test_feature_release_flow(mock_all, mocker):
    """Test the entire flow for a feature release on the 'main' branch."""
    run_release()

    mock_all["get_current_version"].assert_called_once()
    mock_all["bump_version"].assert_called_once_with(ANY, "1.2.1")

    mock_all["update_changelog"].assert_called_once_with(
        "CHANGES.rst", ANY, "1.2.1", False
    )
    mock_all["format_file"].assert_called_once_with("CHANGES.rst")

    git_calls = mock_all["subprocess"].call_args_list
    assert (
        call(
            ["git", "checkout", "-b", "release/1.2.1"], check=True, capture_output=True
        )
        in git_calls
    )
    assert (
        call(
            ["git", "commit", "-m", "[release] Prepare for release 1.2.1"],
            check=True,
            capture_output=True,
        )
        in git_calls
    )
    assert (
        call(
            ["git", "push", "origin", "release/1.2.1"], check=True, capture_output=True
        )
        in git_calls
    )

    mock_gh_instance = mock_all["GitHub"].return_value

    expected_pr_title = "[release] Version 1.2.1"
    mock_gh_instance.create_pr.assert_called_once_with(
        "release/1.2.1", "main", expected_pr_title
    )

    assert (
        call(
            ["git", "tag", "-s", "1.2.1", "-m", "Version 1.2.1 [11-08-2025]"],
            check=True,
        )
        in git_calls
    )
    assert call(["git", "push", "origin", "1.2.1"], check=True) in git_calls

    mock_gh_instance.create_release.assert_called_once()

    assert "port the changelog" not in str(
        mock_all["questionary"].confirm.call_args_list
    )


def test_bugfix_release_flow_with_porting(mock_all, mocker):
    """Test the entire flow for a bugfix release, including the final PR port."""
    mock_all["_git_command_map"][("git", "rev-parse", "--abbrev-ref", "HEAD")] = (
        MagicMock(stdout="1.1.x", check_returncode=True)
    )

    run_release()

    mock_all["update_changelog"].assert_any_call("CHANGES.rst", ANY, "1.2.1", True)
    assert mock_all["update_changelog"].call_count == 2

    assert "port the changelog" in str(mock_all["questionary"].confirm.call_args_list)

    mock_gh_instance = mock_all["GitHub"].return_value
    assert mock_gh_instance.create_pr.call_count == 2

    port_pr_call_args = mock_gh_instance.create_pr.call_args_list[1].args
    expected_port_pr_args = (
        "chore/port-changelog-1.2.1",
        "main",
        "[docs] Port changelog for release 1.2.1",
    )
    assert port_pr_call_args == expected_port_pr_args

    git_calls = mock_all["subprocess"].call_args_list
    assert (
        call(["git", "checkout", "main"], check=True, capture_output=True) in git_calls
    )
    assert (
        call(
            ["git", "checkout", "-b", "chore/port-changelog-1.2.1"],
            check=True,
            capture_output=True,
        )
        in git_calls
    )
    assert (
        call(
            ["git", "commit", "-m", "[docs] Port changelog for 1.2.1"],
            check=True,
            capture_output=True,
        )
        in git_calls
    )
    assert (
        call(
            ["git", "push", "origin", "chore/port-changelog-1.2.1"],
            check=True,
            capture_output=True,
        )
        in git_calls
    )

    assert (
        call(["git", "checkout", "1.1.x"], check=True, capture_output=True) in git_calls
    )
