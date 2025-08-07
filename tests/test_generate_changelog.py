import os
import shutil
import subprocess
import tempfile
import unittest
from textwrap import dedent

from generate_changelog import (
    format_with_docstrfmt_file,
    process_changelog,
    run_git_cliff,
)


class TestChangelogGeneration(unittest.TestCase):
    """Test suite for the changelog generator script."""

    def setUp(self):
        """It creates a temporary directory and sets up a clean Git repository inside it."""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()

        # Copy the cliff.toml to the test directory so git-cliff can find it
        shutil.copy(os.path.join(self.original_dir, "cliff.toml"), self.test_dir)

        os.chdir(self.test_dir)

        self._run_command(["git", "init", "--initial-branch=main"])
        self._run_command(["git", "config", "user.name", "Test User"])
        self._run_command(["git", "config", "user.email", "test@example.com"])
        self.commit_count = 0

    def tearDown(self):
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)

    def _run_command(self, command, check=True):
        """Helper to run shell commands."""
        subprocess.run(command, check=check, capture_output=True, text=True)

    def _git_commit(self, message):
        """Helper to create a file and commit it."""
        with open(f"file_{self.commit_count}.txt", "w") as f:
            f.write(message)
        self._run_command(["git", "add", "."])
        self._run_command(["git", "commit", "-m", message])
        self.commit_count += 1

    def test_full_changelog(self):
        # Create a series of commits with various messages
        self._git_commit("[change] Update README with new instructions")
        self._git_commit("[feature] Add amazing new feature")
        self._git_commit("[fix] Correct a critical bug #123")
        self._git_commit("[change!] Drop support for old API")
        self._git_commit("[deps] Update django requirement from ~=4.0 to ~=4.1")
        self._git_commit("[deps] Update requests requirement from <2.25 to <2.30")
        self._git_commit("[test] Add tests for the new feature")
        self._git_commit("[deps] Update django requirement from ~=3.2 to ~=4.0")

        # Expected output
        expected_unformatted_output = dedent(
            """
            Changelog
            =========

            [unreleased]

            Features
            ~~~~~~~~
            - Add amazing new feature

            Changes
            ~~~~~~~

            Backward-incompatible changes
            +++++++++++++++++++++++++++++

            - Drop support for old API

            Other changes
            +++++++++++++

            - Update README with new instructions

            Dependencies
            ++++++++++++

            - Bumped ``django~=4.1``
            - Bumped ``requests<2.30``

            Bugfixes
            ~~~~~~~~~

            - Correct a critical bug #123
        """
        ).strip()

        processed_output = format_with_docstrfmt_file(
            process_changelog(run_git_cliff())
        )
        formatted_expected = format_with_docstrfmt_file(expected_unformatted_output)

        self.assertEqual(processed_output, formatted_expected)
