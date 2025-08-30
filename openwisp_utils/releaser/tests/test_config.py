import pytest
from openwisp_utils.releaser.config import detect_changelog_style, load_config


@pytest.mark.parametrize(
    "changelog_filename, expected_format",
    [
        ("CHANGES.rst", "rst"),
        ("CHANGELOG.rst", "rst"),
        ("CHANGES.md", "md"),
        ("CHANGELOG.md", "md"),
    ],
)
def test_load_config_flexible_changelog_names(
    project_dir,
    create_setup_py,
    create_package_dir_with_version,
    create_changelog,
    init_git_repo,
    changelog_filename,
    expected_format,
):
    """Tests that various common changelog filenames are detected."""
    create_setup_py(project_dir)
    create_package_dir_with_version(project_dir)
    (project_dir / changelog_filename).write_text("Changelog")
    init_git_repo(project_dir)

    config = load_config()

    assert config["repo"] == "my-org/my-test-package"
    assert config["version_path"] == "my_test_package/__init__.py"
    assert config["CURRENT_VERSION"] == [1, 2, 3, "final"]
    assert config["changelog_path"] == changelog_filename
    assert config["changelog_format"] == expected_format


def test_load_config_raises_specific_error(project_dir, create_setup_py):
    create_setup_py(project_dir)
    with pytest.raises(FileNotFoundError, match="Could not find CHANGES.rst"):
        load_config()


def test_detect_changelog_style_with_prefix(tmp_path):
    """Tests that style is detected as 'True' when 'Version ' is present."""
    p = tmp_path / "CHANGES.rst"
    p.write_text("Version 1.0.0\n---\n- A change.")
    assert detect_changelog_style(str(p)) is True


def test_detect_changelog_style_without_prefix(tmp_path):
    """Tests that style is detected as 'False' when 'Version ' is absent."""
    p = tmp_path / "CHANGES.rst"
    p.write_text("1.0.0\n---\n- A change.")
    assert detect_changelog_style(str(p)) is False


def test_detect_changelog_style_empty_or_no_versions(tmp_path):
    """Tests that the style defaults to 'True' for new or empty files."""
    # File does not exist
    assert detect_changelog_style(str(tmp_path / "new.rst")) is True
    # File is empty
    p = tmp_path / "empty.rst"
    p.touch()
    assert detect_changelog_style(str(p)) is True
    # File has content but no versions
    p_content = tmp_path / "content.rst"
    p_content.write_text("Changelog\n=========")
    assert detect_changelog_style(str(p_content)) is True


def test_load_config_ssh_md(
    project_dir,
    create_setup_py,
    create_package_dir_with_version,
    create_changelog,
    init_git_repo,
):
    """Tests the ideal scenario with an SSH git remote and a .md changelog."""
    create_setup_py(project_dir)
    create_package_dir_with_version(project_dir)
    create_changelog(project_dir, "md")
    init_git_repo(project_dir, remote_url="git@github.com:my-org/my-test-package.git")

    config = load_config()

    assert config["repo"] == "my-org/my-test-package"
    assert config["changelog_path"] == "CHANGES.md"


def test_missing_changelog_raises_error(project_dir, create_setup_py, init_git_repo):
    """Verifies that a FileNotFoundError is raised if no changelog exists."""
    create_setup_py(project_dir)
    init_git_repo(project_dir)

    with pytest.raises(FileNotFoundError, match="Changelog file is required"):
        load_config()


def test_missing_setup_py_is_graceful(project_dir, create_changelog, init_git_repo):
    """Tests that if setup.py is missing, version info is None but other info is found."""
    create_changelog(project_dir)
    init_git_repo(project_dir)

    config = load_config()

    assert config["repo"] == "my-org/my-test-package"
    assert config["changelog_path"] == "CHANGES.rst"
    assert config["version_path"] is None
    assert config["CURRENT_VERSION"] is None


def test_missing_version_file_is_graceful(
    project_dir, create_setup_py, create_changelog
):
    """Tests that if __init__.py is missing, version info is None."""
    create_setup_py(project_dir)
    create_changelog(project_dir)

    config = load_config()

    assert config["version_path"] is None
    assert config["CURRENT_VERSION"] is None
    assert config["changelog_path"] == "CHANGES.rst"
    assert config["repo"] is None


def test_version_tuple_not_in_init_py(
    project_dir, create_setup_py, create_package_dir_with_version, create_changelog
):
    """Tests that if __init__.py exists but has no VERSION tuple, version info is None."""
    create_setup_py(project_dir)
    create_package_dir_with_version(project_dir, version_str="# This file is empty")
    create_changelog(project_dir)

    config = load_config()

    assert config["version_path"] is None
    assert config["CURRENT_VERSION"] is None
    assert config["changelog_path"] == "CHANGES.rst"


def test_get_package_name_no_match(project_dir):
    # Tests that get_package_name_from_setup returns None
    # if setup.py exists but the name attribute cannot be found.
    (project_dir / "setup.py").write_text("from setuptools import setup\nsetup()")
    from openwisp_utils.releaser.config import get_package_name_from_setup

    assert get_package_name_from_setup() is None


def test_config_malformed_version(
    project_dir, create_setup_py, create_package_dir_with_version, create_changelog
):
    """Tests config loading when __init__.py contains a malformed VERSION tuple."""
    create_setup_py(project_dir)
    create_package_dir_with_version(project_dir, version_str="VERSION = (1, 2,,")
    create_changelog(project_dir)
    config = load_config()
    assert config["CURRENT_VERSION"] is None


def test_config_malformed_version_literal_eval_fails(
    project_dir, create_setup_py, create_package_dir_with_version, create_changelog
):
    # Tests config loading when __init__.py contains a malformed VERSION
    # tuple that causes literal_eval to fail.

    create_setup_py(project_dir)
    # This string is valid python syntax but will fail literal_eval
    create_package_dir_with_version(
        project_dir, version_str="VERSION = (1, 2, 'a' + 'b')"
    )
    create_changelog(project_dir)
    config = load_config()
    # Should gracefully handle the error and return None
    assert config["CURRENT_VERSION"] is None
