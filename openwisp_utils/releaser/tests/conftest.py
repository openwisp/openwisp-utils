import subprocess
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def project_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def mock_config():
    return {"version_path": "path/__init__.py"}


def _create_setup_py(path: Path, name="my-test-package"):
    (path / "setup.py").write_text(
        f'from setuptools import setup\nsetup(name="{name}")'
    )


@pytest.fixture
def create_setup_py():
    return _create_setup_py


def _create_package_dir_with_version(
    path: Path, name="my-test-package", version_str="VERSION = (1, 2, 3, 'final')"
):
    pkg_dir = path / name.replace("-", "_")
    pkg_dir.mkdir(exist_ok=True)
    (pkg_dir / "__init__.py").write_text(version_str)


@pytest.fixture
def create_package_dir_with_version():
    return _create_package_dir_with_version


def _create_changelog(path: Path, ext="rst"):
    (path / f"CHANGES.{ext}").write_text("Changelog")


@pytest.fixture
def create_changelog():
    return _create_changelog


def _init_git_repo(
    path: Path, remote_url="https://github.com/my-org/my-test-package.git"
):
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=path, check=True)


@pytest.fixture
def init_git_repo():
    return _init_git_repo


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

    mock_q_confirm = mocker.patch("openwisp_utils.releaser.release.questionary.confirm")
    mock_q_confirm.return_value.ask.return_value = True
    mocker.patch(
        "openwisp_utils.releaser.version.questionary.confirm", new=mock_q_confirm
    )

    mock_q_text = mocker.patch("openwisp_utils.releaser.release.questionary.text")
    mock_q_text.return_value.ask.return_value = "1.2.1"
    mocker.patch("openwisp_utils.releaser.version.questionary.text", new=mock_q_text)

    mock_q_select = mocker.patch("openwisp_utils.releaser.release.questionary.select")
    mock_q_select.return_value.ask.return_value = "main"
    mocker.patch(
        "openwisp_utils.releaser.version.questionary.select", new=mock_q_select
    )

    mocks = {
        "subprocess": mocker.patch(
            "openwisp_utils.releaser.release.subprocess.run",
            side_effect=subprocess_side_effect,
        ),
        "GitHub": mocker.patch("openwisp_utils.releaser.release.GitHub"),
        "time": mocker.patch("openwisp_utils.releaser.release.time.sleep"),
        "print": mocker.patch("builtins.print"),
        "load_config": mocker.patch("openwisp_utils.releaser.release.load_config"),
        "get_current_version": mocker.patch(
            "openwisp_utils.releaser.release.get_current_version",
            return_value=("1.2.0", "final"),
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
        "questionary_confirm": mock_q_confirm,
        "questionary_text": mock_q_text,
        "questionary_select": mock_q_select,
    }

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
        "changelog_uses_version_prefix": True,
    }
    mocks["check_prerequisites"].return_value = (mock_config, mock_gh_instance)
    mocks["load_config"].return_value = mock_config

    return mocks
