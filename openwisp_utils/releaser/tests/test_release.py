from unittest.mock import MagicMock, call, patch

import pytest
from openwisp_utils.releaser.release import bump_to_next_alpha, check_prerequisites
from openwisp_utils.releaser.release import main as run_release
from openwisp_utils.releaser.release import port_changelog_to_main
from openwisp_utils.releaser.utils import SkipSignal


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
    mock_all["questionary_confirm"].assert_any_call(
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
        return_value=(True, "Permissions OK"),
    )

    with pytest.raises(SystemExit):
        from openwisp_utils.releaser.release import check_prerequisites

        check_prerequisites()


def test_main_flow_user_cancels_version(mock_all):
    """Tests the flow where the user cancels when asked for a version."""
    mock_all["get_current_version"].return_value = (None, None)
    mock_all["questionary_text"].return_value.ask.return_value = (
        ""  # User presses enter
    )
    with pytest.raises(SystemExit):
        run_release()


def test_main_flow_user_rejects_changelog(mock_all):
    """Tests the flow where the user rejects the generated changelog."""
    mock_all["questionary_confirm"].return_value.ask.side_effect = [
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
    mock_all["questionary_confirm"].return_value.ask.side_effect = [
        True,  # Use suggested version
        True,  # Accept changelog block
        True,  # Finished editing
        False,  # Decline porting
    ]
    run_release()
    mock_gh = mock_all["GitHub"].return_value
    assert mock_gh.create_pr.call_count == 1


def test_check_prerequisites_config_load_error(mocker):
    """Tests the FileNotFoundError when loading config."""
    mocker.patch("openwisp_utils.releaser.release.shutil.which", return_value=True)
    mocker.patch("os.environ.get", return_value="fake-token")
    mocker.patch(
        "openwisp_utils.releaser.release.load_config", side_effect=FileNotFoundError
    )
    with pytest.raises(SystemExit):
        check_prerequisites()


def test_check_prerequisites_github_permission_error(mocker):
    """Tests when the GitHub token does not have PR creation permissions."""
    mocker.patch("openwisp_utils.releaser.release.shutil.which", return_value=True)
    mocker.patch("os.environ.get", return_value="fake-token")
    mocker.patch(
        "openwisp_utils.releaser.release.load_config",
        return_value={"repo": "owner/repo"},
    )
    mock_gh = MagicMock()
    mock_gh.check_pr_creation_permission.return_value = (
        False,
        "Permission denied.",
    )
    mocker.patch("openwisp_utils.releaser.release.GitHub", return_value=mock_gh)
    with pytest.raises(SystemExit):
        check_prerequisites()


def test_check_prerequisites_success(mocker):
    """Tests the successful execution path of `check_prerequisites`."""
    mocker.patch("openwisp_utils.releaser.release.shutil.which", return_value=True)
    mocker.patch("os.environ.get", return_value="fake-token")
    mocker.patch(
        "openwisp_utils.releaser.release.load_config",
        return_value={"repo": "owner/repo"},
    )
    mock_gh = MagicMock()
    mock_gh.check_pr_creation_permission.return_value = (
        True,
        "Permissions verified.",
    )
    mocker.patch("openwisp_utils.releaser.release.GitHub", return_value=mock_gh)
    config, gh = check_prerequisites()
    assert config is not None and gh is not None


def test_main_flow_pr_merge_wait(mock_all):
    """Tests the `while` loop that waits for a PR to be merged."""
    mock_gh_instance = mock_all["GitHub"].return_value
    mock_gh_instance.is_pr_merged.side_effect = [False, True]
    run_release()
    mock_all["time"].assert_called_once_with(20)
    assert mock_gh_instance.is_pr_merged.call_count == 2


@patch("openwisp_utils.releaser.release.update_changelog_file")
@patch("openwisp_utils.releaser.release.format_file_with_docstrfmt")
@patch("openwisp_utils.releaser.release.subprocess.run")
@patch("openwisp_utils.releaser.release.branch_exists")
@patch("openwisp_utils.releaser.release.questionary")
def test_port_changelog_to_main_flow(
    mock_questionary,
    mock_branch_exists,
    mock_subprocess,
    mock_format_file,
    mock_update_changelog,
):
    """Tests the changelog porting process for RST files."""
    mock_gh = MagicMock()
    mock_config_rst = {"changelog_path": "CHANGES.rst"}
    # Both branches exist: user is asked
    mock_branch_exists.return_value = True
    mock_questionary.select.return_value.ask.return_value = "main"
    port_changelog_to_main(mock_gh, mock_config_rst, "1.1.1", "- fix", "1.1.x")
    mock_gh.create_pr.assert_called_once()
    mock_format_file.assert_called_once_with("CHANGES.rst")


@patch("openwisp_utils.releaser.release.update_changelog_file")
@patch("openwisp_utils.releaser.release.format_file_with_docstrfmt")
@patch("openwisp_utils.releaser.release.subprocess.run")
@patch("openwisp_utils.releaser.release.branch_exists")
def test_port_changelog_only_master_exists(
    mock_branch_exists, mock_subprocess, mock_format_file, mock_update_changelog
):
    """`master` is auto-selected when `main` does not exist locally."""
    mock_gh = MagicMock()
    mock_config = {"changelog_path": "CHANGES.rst"}
    # Simulate: main=False, master=True
    mock_branch_exists.side_effect = lambda name: name == "master"
    port_changelog_to_main(mock_gh, mock_config, "1.1.1", "- fix", "1.1.x")
    mock_gh.create_pr.assert_called_once()
    # Verify PR was opened against master
    assert mock_gh.create_pr.call_args[0][1] == "master"


@patch("openwisp_utils.releaser.release.update_changelog_file")
@patch("openwisp_utils.releaser.release.format_file_with_docstrfmt")
@patch("openwisp_utils.releaser.release.subprocess.run")
@patch("openwisp_utils.releaser.release.branch_exists")
def test_port_changelog_only_main_exists(
    mock_branch_exists, mock_subprocess, mock_format_file, mock_update_changelog
):
    """`main` is auto-selected when it exists and `master` does not."""
    mock_gh = MagicMock()
    mock_config = {"changelog_path": "CHANGES.rst"}
    # Simulate: main=True, master=False
    mock_branch_exists.side_effect = lambda name: name == "main"
    port_changelog_to_main(mock_gh, mock_config, "1.1.1", "- fix", "1.1.x")
    mock_gh.create_pr.assert_called_once()
    # Verify PR was opened against main
    assert mock_gh.create_pr.call_args[0][1] == "main"


@patch("openwisp_utils.releaser.release.update_changelog_file")
@patch("openwisp_utils.releaser.release.format_file_with_docstrfmt")
@patch("openwisp_utils.releaser.release.subprocess.run")
@patch("openwisp_utils.releaser.release.branch_exists")
@patch("openwisp_utils.releaser.release.questionary")
def test_port_changelog_both_branches_prompts_user(
    mock_questionary,
    mock_branch_exists,
    mock_subprocess,
    mock_format_file,
    mock_update_changelog,
):
    """User is prompted to choose when both `main` and `master` exist."""
    mock_gh = MagicMock()
    mock_config = {"changelog_path": "CHANGES.rst"}
    # Both branches exist
    mock_branch_exists.return_value = True
    mock_questionary.select.return_value.ask.return_value = "master"
    port_changelog_to_main(mock_gh, mock_config, "1.1.1", "- fix", "1.1.x")
    mock_questionary.select.assert_called_once()
    mock_gh.create_pr.assert_called_once()
    assert mock_gh.create_pr.call_args[0][1] == "master"


@patch("openwisp_utils.releaser.release.update_changelog_file")
@patch("openwisp_utils.releaser.release.format_file_with_docstrfmt")
@patch("openwisp_utils.releaser.release.subprocess.run")
@patch("openwisp_utils.releaser.release.branch_exists")
def test_port_changelog_neither_branch_exists(
    mock_branch_exists, mock_subprocess, mock_format_file, mock_update_changelog
):
    """Porting is skipped with a message if neither branch exists."""
    mock_gh = MagicMock()
    mock_config = {"changelog_path": "CHANGES.rst"}
    # Neither exists
    mock_branch_exists.return_value = False
    port_changelog_to_main(mock_gh, mock_config, "1.1.1", "- fix", "1.1.x")
    # Verify no PR was created
    mock_gh.create_pr.assert_not_called()
    # Verify no file update was attempted
    mock_update_changelog.assert_not_called()


@patch("openwisp_utils.releaser.release.update_changelog_file")
@patch("openwisp_utils.releaser.release.format_file_with_docstrfmt")
@patch("openwisp_utils.releaser.release.subprocess.run")
@patch("openwisp_utils.releaser.release.branch_exists")
@patch("openwisp_utils.releaser.release.questionary")
def test_port_changelog_cancelled(
    mock_questionary,
    mock_branch_exists,
    mock_subprocess,
    mock_format_file,
    mock_update_changelog,
):
    """Porting is cancelled if user doesn't select a branch."""
    mock_gh = MagicMock()
    mock_config = {"changelog_path": "CHANGES.rst"}
    # Both exist to trigger prompt
    mock_branch_exists.return_value = True
    # User cancels (Ctrl+C or Esc)
    mock_questionary.select.return_value.ask.return_value = None
    port_changelog_to_main(mock_gh, mock_config, "1.1.1", "- fix", "1.1.x")
    # Verify no PR was created
    mock_gh.create_pr.assert_not_called()


def test_main_bugfix_flow_with_porting(mock_all, mocker):
    """Tests the main release flow for a bugfix, including accepting the changelog port."""
    mock_all["_git_command_map"][
        ("git", "rev-parse", "--abbrev-ref", "HEAD")
    ].stdout = "1.1.x"
    mock_all["questionary_confirm"].return_value.ask.return_value = True
    mock_porting_func = mocker.patch(
        "openwisp_utils.releaser.release.port_changelog_to_main"
    )
    run_release()
    mock_porting_func.assert_called_once()


def test_main_flow_no_version_prefix_style(mock_all):
    """Tests the release flow for a changelog that does NOT use the 'Version ' prefix."""
    # Config where the "Version" prefix is not used
    mock_config, _ = mock_all["check_prerequisites"].return_value
    mock_config["changelog_uses_version_prefix"] = False
    mock_all["get_release_block_from_file"].return_value = None

    run_release()

    # Check that the block written to the file does NOT have the "Version" prefix
    update_call_args = mock_all["update_changelog"].call_args[0]
    written_block = update_call_args[1]
    assert written_block.startswith("1.3.0")
    assert not written_block.startswith("Version 1.3.0")

    # Check that the user is shown the FULL block for approval
    full_print_output = "".join(str(call) for call in mock_all["print"].call_args_list)
    assert "The following block will be added to the changelog" in full_print_output
    # Verify the header shown to the user is also in the correct style
    assert "1.3.0 [2025-08-11]" in full_print_output
    assert "Version 1.3.0" not in full_print_output


def test_main_flow_skip_pr_creation(mock_all):
    """Tests the flow where user skips PR creation."""
    mock_gh = mock_all["GitHub"].return_value
    mock_gh.create_pr.side_effect = SkipSignal

    run_release()

    # Ensure the user is prompted to complete the step manually
    mock_all["questionary_confirm"].assert_any_call(
        "Press Enter when you have merged the PR manually."
    )
    # The rest of the flow should continue, so release creation should be attempted
    mock_gh.create_release.assert_called_once()


def test_main_flow_skip_release_creation(mock_all):
    """Tests the flow where user skips GitHub release creation."""
    mock_gh = mock_all["GitHub"].return_value
    mock_gh.create_release.side_effect = SkipSignal

    run_release()

    mock_gh.create_pr.assert_called_once()
    mock_all["questionary_confirm"].assert_any_call(
        "Press Enter when you have created the release manually."
    )


@patch("openwisp_utils.releaser.release.branch_exists")
@patch("openwisp_utils.releaser.release.subprocess.run")
def test_port_changelog_to_main_flow_markdown(
    mock_subprocess, mock_branch_exists, mock_all
):
    """Tests the changelog porting process for a Markdown file."""
    mock_gh = MagicMock()
    mock_config_md = {"changelog_path": "CHANGES.md"}
    mock_branch_exists.return_value = True
    mock_all["questionary_select"].return_value.ask.return_value = "main"

    with patch("openwisp_utils.releaser.release.update_changelog_file") as mock_update:
        port_changelog_to_main(mock_gh, mock_config_md, "1.1.1", "- fix", "1.1.x")
        # Check that the header for markdown is correctly formatted
        called_with_content = mock_update.call_args[0][1]
        assert "## Version 1.1.1" in called_with_content


@patch("openwisp_utils.releaser.release.branch_exists")
@patch("openwisp_utils.releaser.release.subprocess.run")
def test_port_changelog_skip_pr_creation(mock_subprocess, mock_branch_exists, mock_all):
    """Tests skipping PR creation during changelog porting."""
    mock_gh = MagicMock()
    mock_gh.create_pr.side_effect = SkipSignal
    mock_config = {"changelog_path": "CHANGES.rst"}
    mock_branch_exists.return_value = True
    mock_all["questionary_select"].return_value.ask.return_value = "main"

    with patch("openwisp_utils.releaser.release.update_changelog_file"):
        port_changelog_to_main(mock_gh, mock_config, "1.1.1", "- fix", "1.1.x")
        mock_all["questionary_confirm"].assert_any_call(
            "Press Enter when you have created the PR manually."
        )


@pytest.fixture
def bump_mocks(mocker):
    """Mocks the external dependencies of ``bump_to_next_alpha``."""
    mocks = {
        "run_git": mocker.patch("openwisp_utils.releaser.release.run_git"),
        "subprocess": mocker.patch("openwisp_utils.releaser.release.subprocess.run"),
        "branch_exists": mocker.patch(
            "openwisp_utils.releaser.release.branch_exists",
            side_effect=lambda name: name == "master",
        ),
        "get_remote_branch_commit": mocker.patch(
            "openwisp_utils.releaser.release.get_remote_branch_commit",
            return_value=None,
        ),
        "determine_new_version": mocker.patch(
            "openwisp_utils.releaser.release.determine_new_version",
            return_value="1.3.0",
        ),
        "bump_version": mocker.patch(
            "openwisp_utils.releaser.release.bump_version", return_value=True
        ),
        "update_changelog": mocker.patch(
            "openwisp_utils.releaser.release.update_changelog_file"
        ),
        "format_file": mocker.patch(
            "openwisp_utils.releaser.release.format_file_with_docstrfmt"
        ),
        "questionary": mocker.patch("openwisp_utils.releaser.release.questionary"),
        "print": mocker.patch("builtins.print"),
    }
    return mocks


def _git_commands(mock_run_git):
    return [call.args[0] for call in mock_run_git.call_args_list]


def test_bump_to_next_alpha_flow(bump_mocks):
    mock_gh = MagicMock()
    mock_gh.create_pr.return_value = "http://pr.url/3"
    config = {
        "package_type": "python",
        "changelog_path": "CHANGES.rst",
        "changelog_format": "rst",
        "changelog_uses_version_prefix": True,
    }
    bump_to_next_alpha(mock_gh, config, "1.2.0", "master")
    bump_mocks["bump_version"].assert_called_once_with(
        config, "1.3.0", version_type="alpha"
    )
    bump_mocks["update_changelog"].assert_called_once_with(
        "CHANGES.rst",
        "Version 1.3.0 [unreleased]\n--------------------------\n\nWork in progress.",
    )
    bump_mocks["format_file"].assert_called_once_with("CHANGES.rst")
    assert _git_commands(bump_mocks["run_git"]) == [
        ["checkout", "master"],
        ["pull", "origin", "master"],
        ["checkout", "-B", "chore/bump-version-1.3.0"],
        ["add", "-u"],
        ["commit", "-m", "[chores] Bumped version to 1.3.0 alpha"],
        ["push", "-u", "origin", "chore/bump-version-1.3.0"],
    ]
    mock_gh.create_pr.assert_called_once_with(
        "chore/bump-version-1.3.0",
        "master",
        "[chores] Bumped version to 1.3.0 alpha",
    )
    mock_gh.is_pr_merged.assert_not_called()
    bump_mocks["subprocess"].assert_called_once_with(
        ["git", "checkout", "master"], check=True, capture_output=True
    )


def test_bump_to_next_alpha_changelog_block_variants(bump_mocks):
    mock_gh = MagicMock()
    variants = [
        (
            {"changelog_format": "md", "changelog_uses_version_prefix": True},
            "## Version 1.3.0 [unreleased]\n\nWork in progress.",
        ),
        (
            {"changelog_format": "md", "changelog_uses_version_prefix": False},
            "## 1.3.0 [unreleased]\n\nWork in progress.",
        ),
        (
            {"changelog_format": "rst", "changelog_uses_version_prefix": False},
            "1.3.0 [unreleased]\n------------------\n\nWork in progress.",
        ),
    ]
    for changelog_config, expected_block in variants:
        bump_mocks["update_changelog"].reset_mock()
        bump_mocks["format_file"].reset_mock()
        config = {
            "package_type": "python",
            "changelog_path": "CHANGES." + changelog_config["changelog_format"],
            **changelog_config,
        }
        bump_to_next_alpha(mock_gh, config, "1.2.0", "master")
        bump_mocks["update_changelog"].assert_called_once_with(
            config["changelog_path"], expected_block
        )
        if changelog_config["changelog_format"] == "md":
            bump_mocks["format_file"].assert_not_called()


def test_bump_to_next_alpha_existing_branch_reset(bump_mocks):
    mock_gh = MagicMock()
    bump_mocks["branch_exists"].side_effect = lambda name: name in [
        "master",
        "chore/bump-version-1.3.0",
    ]
    bump_mocks["questionary"].select.return_value.ask.return_value = (
        "Reset it to 'master'"
    )
    remote_commit = "a" * 40
    bump_mocks["get_remote_branch_commit"].return_value = remote_commit
    config = {
        "package_type": "python",
        "changelog_path": "CHANGES.rst",
        "changelog_format": "rst",
        "changelog_uses_version_prefix": True,
    }
    bump_to_next_alpha(mock_gh, config, "1.2.0", "master")
    assert [
        "push",
        "--force-with-lease=refs/heads/chore/bump-version-1.3.0:" + remote_commit,
        "-u",
        "origin",
        "chore/bump-version-1.3.0",
    ] in _git_commands(bump_mocks["run_git"])
    mock_gh.create_pr.assert_called_once()


def test_bump_to_next_alpha_existing_remote_branch_reset(bump_mocks):
    mock_gh = MagicMock()
    remote_commit = "a" * 40
    bump_mocks["get_remote_branch_commit"].return_value = remote_commit
    bump_mocks["questionary"].select.return_value.ask.return_value = (
        "Reset it to 'master'"
    )
    config = {
        "package_type": "python",
        "changelog_path": "CHANGES.rst",
        "changelog_format": "rst",
        "changelog_uses_version_prefix": True,
    }
    bump_to_next_alpha(mock_gh, config, "1.2.0", "master")
    assert [
        "push",
        "--force-with-lease=refs/heads/chore/bump-version-1.3.0:" + remote_commit,
        "-u",
        "origin",
        "chore/bump-version-1.3.0",
    ] in _git_commands(bump_mocks["run_git"])


def test_bump_to_next_alpha_existing_branch_abort(bump_mocks):
    mock_gh = MagicMock()
    bump_mocks["branch_exists"].side_effect = lambda name: name in [
        "master",
        "chore/bump-version-1.3.0",
    ]
    bump_mocks["questionary"].select.return_value.ask.return_value = (
        "Abort the version bump"
    )
    config = {
        "package_type": "python",
        "changelog_path": "CHANGES.rst",
        "changelog_format": "rst",
        "changelog_uses_version_prefix": True,
    }
    bump_to_next_alpha(mock_gh, config, "1.2.0", "master")
    bump_mocks["update_changelog"].assert_not_called()
    mock_gh.create_pr.assert_not_called()
    bump_mocks["subprocess"].assert_called_once_with(
        ["git", "checkout", "master"], check=True, capture_output=True
    )


def test_bump_to_next_alpha_package_without_prerelease_support(bump_mocks):
    mock_gh = MagicMock()
    config = {
        "package_type": "generic",
        "changelog_path": "CHANGES.rst",
        "changelog_format": "rst",
        "changelog_uses_version_prefix": True,
    }
    bump_to_next_alpha(mock_gh, config, "1.2.0", "master")
    bump_mocks["bump_version"].assert_not_called()
    bump_mocks["run_git"].assert_not_called()
    bump_mocks["update_changelog"].assert_not_called()
    mock_gh.create_pr.assert_not_called()


def test_bump_to_next_alpha_skip_pr_creation(bump_mocks):
    mock_gh = MagicMock()
    mock_gh.create_pr.side_effect = SkipSignal("User chose to skip this operation.")
    config = {
        "package_type": "python",
        "changelog_path": "CHANGES.rst",
        "changelog_format": "rst",
        "changelog_uses_version_prefix": True,
    }
    bump_to_next_alpha(mock_gh, config, "1.2.0", "master")
    printed_output = "\n".join(
        str(call.args[0]) for call in bump_mocks["print"].call_args_list if call.args
    )
    assert "Please complete the version bump manually." in printed_output
    assert "chore/bump-version-1.3.0" in printed_output
    bump_mocks["subprocess"].assert_called_once_with(
        ["git", "checkout", "master"], check=True, capture_output=True
    )


def test_bump_to_next_alpha_preserves_uncommitted_changes(bump_mocks):
    mock_gh = MagicMock()

    def fail_commit(args, description):
        if args[0] == "commit":
            raise SkipSignal("User chose to skip: commit the version bump.")

    bump_mocks["run_git"].side_effect = fail_commit
    config = {
        "package_type": "python",
        "changelog_path": "CHANGES.rst",
        "changelog_format": "rst",
        "changelog_uses_version_prefix": True,
    }
    bump_to_next_alpha(mock_gh, config, "1.2.0", "master")
    bump_mocks["subprocess"].assert_not_called()
    printed_output = "\n".join(
        str(call.args[0]) for call in bump_mocks["print"].call_args_list if call.args
    )
    assert "Keeping branch 'chore/bump-version-1.3.0' checked out" in printed_output


def test_bump_to_next_alpha_cancelled(bump_mocks):
    mock_gh = MagicMock()
    bump_mocks["determine_new_version"].return_value = None
    config = {
        "package_type": "python",
        "changelog_path": "CHANGES.rst",
        "changelog_format": "rst",
        "changelog_uses_version_prefix": True,
    }
    bump_to_next_alpha(mock_gh, config, "1.2.0", "master")
    bump_mocks["run_git"].assert_not_called()
    mock_gh.create_pr.assert_not_called()


def test_main_feature_flow_offers_alpha_bump(mock_all):
    run_release()
    mock_all["bump_to_next_alpha"].assert_called_once()
    assert mock_all["bump_to_next_alpha"].call_args[0][2] == "1.3.0"


def test_main_bugfix_flow_does_not_offer_alpha_bump(mock_all, mocker):
    mock_all["_git_command_map"][("git", "rev-parse", "--abbrev-ref", "HEAD")] = (
        MagicMock(stdout="1.2.x")
    )
    mocker.patch("openwisp_utils.releaser.release.branch_exists", return_value=True)
    run_release()
    mock_all["bump_to_next_alpha"].assert_not_called()


def test_main_feature_flow_skips_alpha_bump_for_unsupported_package(mock_all):
    mock_config, _ = mock_all["check_prerequisites"].return_value
    mock_config["package_type"] = "generic"
    run_release()
    mock_all["bump_to_next_alpha"].assert_not_called()
    assert (
        call("Do you want to bump the version to the next alpha release now?")
        not in mock_all["questionary_confirm"].call_args_list
    )
