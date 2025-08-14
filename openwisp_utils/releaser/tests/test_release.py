from datetime import datetime
from unittest.mock import MagicMock

import pytest
from openwisp_utils.releaser.release import main as run_release


@pytest.fixture
def mock_all(mocker):
    """A master fixture to mock all external dependencies of the release script."""
    git_command_results = {
        ("git", "rev-parse", "--abbrev-ref", "HEAD"): MagicMock(
            stdout="main", check_returncode=True
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
        "print": mocker.patch("builtins.print"),
        "load_config": mocker.patch("openwisp_utils.releaser.release.load_config"),
        "get_current_version": mocker.patch(
            "openwisp_utils.releaser.release.get_current_version",
            return_value=("1.2.0", "alpha"),
        ),
        "bump_version": mocker.patch(
            "openwisp_utils.releaser.release.bump_version", return_value=True
        ),
        "update_changelog": mocker.patch(
            "openwisp_utils.releaser.release.update_changelog_file"
        ),
        "format_rst_block": mocker.patch(
            "openwisp_utils.releaser.release.format_rst_block", side_effect=lambda x: x
        ),
        "format_file": mocker.patch(
            "openwisp_utils.releaser.release.format_file_with_docstrfmt"
        ),
        "check_prerequisites": mocker.patch(
            "openwisp_utils.releaser.release.check_prerequisites"
        ),
        "run_git_cliff": mocker.patch(
            "openwisp_utils.releaser.release.run_git_cliff",
            return_value="[unreleased]\n----\n- A new feature.",
        ),
        "get_release_block_from_file": mocker.patch(
            "openwisp_utils.releaser.release.get_release_block_from_file"
        ),
        "_git_command_map": git_command_results,
    }

    mocks["questionary"].confirm.return_value.ask.return_value = True
    mocks["questionary"].text.return_value.ask.return_value = "1.2.1"
    mocks["questionary"].select.return_value.ask.return_value = "main"

    mock_dt = MagicMock()
    mock_dt.now.return_value = datetime(2025, 8, 11)
    mocker.patch("openwisp_utils.releaser.release.datetime", mock_dt)

    mock_gh_instance = mocks["GitHub"].return_value
    mock_gh_instance.create_pr.side_effect = ["http://pr.url/1", "http://pr.url/2"]
    mock_gh_instance.is_pr_merged.return_value = True

    mock_config = {
        "repo": "test/repo",
        "changelog_path": "CHANGES.rst",
        "changelog_format": "rst",
    }
    mocks["check_prerequisites"].return_value = (mock_config, mock_gh_instance)
    mocks["load_config"].return_value = mock_config

    return mocks


def test_feature_release_flow_markdown(mock_all, mocker):
    """Tests the full release flow for a project using a Markdown changelog."""
    mock_config, mock_gh = mock_all["check_prerequisites"].return_value
    mock_config["changelog_path"] = "CHANGES.md"
    mock_config["changelog_format"] = "md"

    mock_all["get_release_block_from_file"].return_value = None

    mocker.patch(
        "openwisp_utils.releaser.release.rst_to_markdown",
        return_value="## Version 1.2.1\n## Markdown Changelog",
    )

    run_release()

    mock_all["update_changelog"].assert_called_once()
    mock_all["format_file"].assert_not_called()

    release_call_args = mock_gh.create_release.call_args.args
    assert "## Markdown Changelog" in release_call_args[2]


def test_release_flow_manual_bump(mock_all):
    """Tests the flow where automatic version bumping fails and the user is prompted to do it manually."""
    mock_all["bump_version"].return_value = False
    run_release()
    all_print_calls = "".join(str(c) for c in mock_all["print"].call_args_list)
    assert "The version number could not be bumped automatically" in all_print_calls
    mock_all["questionary"].confirm.assert_any_call(
        "Press Enter when you have bumped the version number..."
    )


def test_prerequisite_check_failure(mocker):
    """Tests that the script exits if the prerequisite check fails."""
    mocker.patch("openwisp_utils.releaser.release.shutil.which", return_value=None)
    mocker.patch(
        "openwisp_utils.releaser.release.load_config",
        return_value={"repo": "test/repo"},
    )
    mocker.patch(
        "openwisp_utils.releaser.release.GitHub.check_pr_creation_permission",
        return_value=True,
    )

    with pytest.raises(SystemExit):
        from openwisp_utils.releaser.release import check_prerequisites

        check_prerequisites()


def test_main_flow_user_cancels_version(mock_all):
    """Tests the flow where the user cancels when asked for a version."""
    mock_all["get_current_version"].return_value = (None, None)
    mock_all["questionary"].text.return_value.ask.return_value = (
        ""  # User presses enter
    )
    with pytest.raises(SystemExit):
        run_release()


def test_main_flow_user_rejects_changelog(mock_all):
    """Tests the flow where the user rejects the generated changelog."""
    mock_all["questionary"].confirm.return_value.ask.side_effect = [
        True,  # Use AI
        True,  # Use suggested version
        False,  # Reject changelog block
    ]
    with pytest.raises(SystemExit):
        run_release()


def test_bugfix_flow_skip_porting(mock_all):
    """Tests a full bugfix release but declines the final changelog porting step."""
    mock_all["_git_command_map"][
        ("git", "rev-parse", "--abbrev-ref", "HEAD")
    ].stdout = "1.1.x"
    mock_all["questionary"].confirm.return_value.ask.side_effect = [
        True,
        True,
        True,
        True,
        False,  # Decline porting
    ]
    run_release()
    mock_gh = mock_all["GitHub"].return_value
    assert mock_gh.create_pr.call_count == 1
