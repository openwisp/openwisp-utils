from datetime import datetime
from unittest.mock import ANY, MagicMock, call

import pytest
from openwisp_utils.releaser.release import main as run_release


@pytest.fixture
def mock_all(mocker):
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
            "openwisp_utils.releaser.release.subprocess.run",
            side_effect=subprocess_side_effect,
        ),
        "questionary": mocker.patch("openwisp_utils.releaser.release.questionary"),
        "GitHub": mocker.patch("openwisp_utils.releaser.release.GitHub"),
        "time": mocker.patch("openwisp_utils.releaser.release.time.sleep"),
        "datetime": mocker.patch("openwisp_utils.releaser.release.datetime"),
        "print": mocker.patch("builtins.print"),
        "load_config": mocker.patch("openwisp_utils.releaser.release.load_config"),
        "update_changelog": mocker.patch(
            "openwisp_utils.releaser.release.update_changelog_file"
        ),
        "format_block": mocker.patch(
            "openwisp_utils.releaser.release.format_rst_block", side_effect=lambda x: x
        ),
        "format_file": mocker.patch(
            "openwisp_utils.releaser.release.format_file_with_docstrfmt"
        ),
        "_git_command_map": git_command_results,
    }

    mocks["questionary"].confirm.return_value.ask.return_value = True
    mocks["questionary"].text.return_value.ask.return_value = "1.2.1"
    mocks["questionary"].select.return_value.ask.return_value = "main"

    mock_dt = MagicMock()
    mock_dt.now.return_value = datetime(2025, 8, 11)
    mocks["datetime"] = mocker.patch(
        "openwisp_utils.releaser.release.datetime", mock_dt
    )

    mock_gh_instance = mocks["GitHub"].return_value
    mock_gh_instance.create_pr.side_effect = ["http://pr.url/1", "http://pr.url/2"]
    mock_gh_instance.is_pr_merged.return_value = True

    return mocks


def test_feature_release_flow(mock_all, mocker):
    mock_all["load_config"].return_value = {
        "repo": "test/repo",
        "version_path": "src/__init__.py",
        "changelog_path": "CHANGES.rst",
    }

    mocker.patch("openwisp_utils.releaser.version.os.path.exists", return_value=True)
    mock_version_file = mocker.patch(
        "openwisp_utils.releaser.version.open",
        mocker.mock_open(read_data='VERSION = (1, 2, 0, "alpha")'),
    )

    run_release()

    mock_version_file.assert_any_call("src/__init__.py", "r")
    mock_version_file().write.assert_called_once_with('VERSION = (1, 2, 1, "final")')

    all_print_calls = " ".join(str(c) for c in mock_all["print"].call_args_list)
    assert "✅ Version bumped to 1.2.1 and set to 'final'." in all_print_calls
    assert (
        "⚠️ The version number could not be bumped automatically." not in all_print_calls
    )

    git_calls = mock_all["subprocess"].call_args_list
    assert call(["git", "add", "."], check=True, capture_output=True) in git_calls
    assert (
        call(["git", "commit", "-m", "1.2.1 release"], check=True, capture_output=True)
        in git_calls
    )


def test_release_flow_manual_bump(mock_all, mocker):
    mock_all["load_config"].return_value = {
        "repo": "test/repo",
        "changelog_path": "CHANGES.rst",
    }

    run_release()

    all_print_calls = " ".join(str(c) for c in mock_all["print"].call_args_list)
    assert "⚠️ The version number could not be bumped automatically." in all_print_calls
    assert "✅ Version bumped to 1.2.1 and set to 'final'." not in all_print_calls
    mock_all["questionary"].confirm.assert_any_call(
        "Press Enter when you have bumped the version number..."
    )


def test_bugfix_release_flow_with_porting(mock_all, mocker):
    mock_all["_git_command_map"][("git", "rev-parse", "--abbrev-ref", "HEAD")] = (
        MagicMock(stdout="1.1.x", check_returncode=True)
    )

    mock_all["load_config"].return_value = {
        "repo": "test/repo",
        "version_path": "src/__init__.py",
        "changelog_path": "CHANGES.rst",
    }
    mocker.patch("openwisp_utils.releaser.version.os.path.exists", return_value=True)
    mocker.patch(
        "openwisp_utils.releaser.version.open",
        mocker.mock_open(read_data='VERSION = (1, 2, 0, "alpha")'),
    )

    run_release()

    all_print_calls = " ".join(str(c) for c in mock_all["print"].call_args_list)
    assert "✅ Version bumped to 1.2.1 and set to 'final'." in all_print_calls

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
