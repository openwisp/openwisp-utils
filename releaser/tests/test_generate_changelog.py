import os
import shutil
import subprocess
import tempfile

import pytest

from releaser.generate_changelog import (
    format_rst_block,
    process_changelog,
    run_git_cliff,
)


def find_changelog_test_cases():
    # Scans the samples directory to find matching pairs of commit
    # and changelog files to be used as test cases
    SAMPLES_DIR = "releaser/tests/samples"
    COMMIT_SAMPLES_DIR = os.path.join(SAMPLES_DIR, "commits")
    CHANGELOG_SAMPLES_DIR = os.path.join(SAMPLES_DIR, "changelogs")

    test_cases = []

    if not os.path.isdir(COMMIT_SAMPLES_DIR):
        return []

    for commit_filename in os.listdir(COMMIT_SAMPLES_DIR):
        if not commit_filename.endswith(".txt"):
            continue

        base_name = os.path.splitext(commit_filename)[0]
        changelog_filename = f"{base_name}.rst"

        commit_filepath = os.path.join(COMMIT_SAMPLES_DIR, commit_filename)
        changelog_filepath = os.path.join(CHANGELOG_SAMPLES_DIR, changelog_filename)

        if os.path.exists(changelog_filepath):
            # The 'id' gives a nice name to the test case when it runs
            test_cases.append(
                pytest.param(commit_filepath, changelog_filepath, id=base_name)
            )

    return test_cases


@pytest.fixture
def git_repo():
    # Sets up a temporary directory with a clean Git repository
    # and copies the cliff.toml file into it. It changes the current
    # working directory to the temp directory and cleans up everything
    # after the test is done.
    original_dir = os.getcwd()
    test_dir = tempfile.mkdtemp()

    # Copy the cliff.toml to the test directory
    cliff_toml_path = os.path.join(original_dir, "cliff.toml")
    if os.path.exists(cliff_toml_path):
        shutil.copy(cliff_toml_path, test_dir)

    os.chdir(test_dir)

    # Initialize Git repository
    subprocess.run(
        ["git", "init", "--initial-branch=main"], check=True, capture_output=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)

    # Yield control to the test function
    yield original_dir

    # Teardown: clean up after the test
    os.chdir(original_dir)
    shutil.rmtree(test_dir)


@pytest.mark.parametrize(
    "commit_file, expected_changelog_file", find_changelog_test_cases()
)
def test_changelog_generation(git_repo, commit_file, expected_changelog_file):
    """Tests changelog generation for all discovered sample files"""
    original_dir = git_repo
    commit_count = 0

    # Helper to create a file and commit it
    def _git_commit(message):
        nonlocal commit_count
        with open(f"file_{commit_count}.txt", "w") as f:
            f.write(message)
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", message], check=True, capture_output=True
        )
        commit_count += 1

    # Construct full paths to sample files from the original directory
    commit_file_path = os.path.join(original_dir, commit_file)
    expected_changelog_path = os.path.join(original_dir, expected_changelog_file)

    # Create commits from the provided sample file
    with open(commit_file_path, "r") as f:
        for line in f:
            if line.strip():
                _git_commit(line.strip())

    # Read the expected output from the sample file
    with open(expected_changelog_path, "r") as f:
        expected_output = f.read().strip()

    # Generate the changelog and get the actual output
    raw_changelog = run_git_cliff()
    processed_changelog = process_changelog(raw_changelog)
    processed_changelog = "Changelog\n=========\n\n" + processed_changelog
    actual_output = format_rst_block(processed_changelog)

    assert actual_output == expected_output
