#!/usr/bin/env python3
"""Tests for the changelog generator GitHub action."""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the directory to path for importing
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_changelog import (
    build_prompt,
    call_gemini,
    get_env_or_exit,
    get_linked_issues,
    get_pr_commits,
    get_pr_details,
    get_pr_diff,
    post_github_comment,
)


class TestGetEnvOrExit(unittest.TestCase):
    """Tests for get_env_or_exit function."""

    def test_returns_value_when_env_var_exists(self):
        with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
            result = get_env_or_exit("TEST_VAR")
            self.assertEqual(result, "test_value")

    def test_exits_when_env_var_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit) as context:
                get_env_or_exit("MISSING_VAR")
            self.assertEqual(context.exception.code, 1)

    def test_exits_when_env_var_empty(self):
        with patch.dict(os.environ, {"EMPTY_VAR": ""}):
            with self.assertRaises(SystemExit) as context:
                get_env_or_exit("EMPTY_VAR")
            self.assertEqual(context.exception.code, 1)


class TestGetPrDetails(unittest.TestCase):
    """Tests for get_pr_details function."""

    @patch("generate_changelog.github_api_request")
    def test_returns_pr_details(self, mock_api):
        mock_api.return_value = {
            "title": "Test PR",
            "body": "Test body",
            "labels": [{"name": "bug"}, {"name": "enhancement"}],
            "base": {"ref": "main"},
            "head": {"ref": "feature-branch"},
            "user": {"login": "testuser"},
            "html_url": "https://github.com/org/repo/pull/123",
        }

        result = get_pr_details("org/repo", 123, "token")

        self.assertEqual(result["title"], "Test PR")
        self.assertEqual(result["body"], "Test body")
        self.assertEqual(result["labels"], ["bug", "enhancement"])
        self.assertEqual(result["base_branch"], "main")
        self.assertEqual(result["head_branch"], "feature-branch")
        self.assertEqual(result["user"], "testuser")
        self.assertEqual(result["number"], 123)

    @patch("generate_changelog.github_api_request")
    def test_handles_missing_fields(self, mock_api):
        mock_api.return_value = {}

        result = get_pr_details("org/repo", 123, "token")

        self.assertEqual(result["title"], "")
        self.assertEqual(result["body"], "")
        self.assertEqual(result["labels"], [])
        self.assertEqual(result["number"], 123)


class TestGetPrDiff(unittest.TestCase):
    """Tests for get_pr_diff function."""

    @patch("generate_changelog.urlopen")
    def test_returns_diff(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b"diff --git a/file.py"
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = get_pr_diff("org/repo", 123, "token")

        self.assertEqual(result, "diff --git a/file.py")

    @patch("generate_changelog.urlopen")
    def test_truncates_large_diff(self, mock_urlopen):
        large_diff = "x" * 20000
        mock_response = MagicMock()
        mock_response.read.return_value = large_diff.encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = get_pr_diff("org/repo", 123, "token")

        self.assertEqual(len(result), 15000 + len("\n\n... [diff truncated for brevity] ..."))
        self.assertIn("[diff truncated for brevity]", result)


class TestGetPrCommits(unittest.TestCase):
    """Tests for get_pr_commits function."""

    @patch("generate_changelog.github_api_request")
    def test_returns_commits(self, mock_api):
        mock_api.return_value = [
            {"sha": "abc1234567890", "commit": {"message": "First commit\n\nDetails"}},
            {"sha": "def1234567890", "commit": {"message": "Second commit"}},
        ]

        result = get_pr_commits("org/repo", 123, "token")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["sha"], "abc1234")
        self.assertEqual(result[0]["message"], "First commit")
        self.assertEqual(result[1]["sha"], "def1234")

    @patch("generate_changelog.github_api_request")
    def test_limits_to_10_commits(self, mock_api):
        mock_api.return_value = [
            {"sha": f"sha{i}1234567890", "commit": {"message": f"Commit {i}"}}
            for i in range(15)
        ]

        result = get_pr_commits("org/repo", 123, "token")

        self.assertEqual(len(result), 10)


class TestGetLinkedIssues(unittest.TestCase):
    """Tests for get_linked_issues function."""

    @patch("generate_changelog.github_api_request")
    def test_extracts_closes_pattern(self, mock_api):
        mock_api.return_value = {
            "title": "Issue title",
            "body": "Issue description",
        }

        result = get_linked_issues("org/repo", "Closes #123", "token")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["number"], "123")

    @patch("generate_changelog.github_api_request")
    def test_extracts_fixes_pattern(self, mock_api):
        mock_api.return_value = {
            "title": "Bug fix",
            "body": "Fixed the bug",
        }

        result = get_linked_issues("org/repo", "Fixes #456", "token")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["number"], "456")

    @patch("generate_changelog.github_api_request")
    def test_limits_to_3_issues(self, mock_api):
        mock_api.return_value = {"title": "Issue", "body": ""}

        result = get_linked_issues(
            "org/repo", "Closes #1, fixes #2, resolves #3, #4, #5", "token"
        )

        self.assertLessEqual(len(result), 3)

    def test_handles_empty_body(self):
        result = get_linked_issues("org/repo", "", "token")
        self.assertEqual(result, [])


class TestCallGemini(unittest.TestCase):
    """Tests for call_gemini function using google-genai SDK."""

    @patch("generate_changelog.genai")
    def test_successful_call(self, mock_genai):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Generated changelog"
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        result = call_gemini("Test prompt", "api_key")

        self.assertEqual(result, "Generated changelog")
        mock_genai.Client.assert_called_once_with(api_key="api_key")
        mock_client.models.generate_content.assert_called_once()

    @patch("generate_changelog.genai")
    def test_uses_correct_model(self, mock_genai):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Result"
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        call_gemini("Test prompt", "api_key", model="gemini-1.5-pro")

        call_kwargs = mock_client.models.generate_content.call_args[1]
        self.assertEqual(call_kwargs["model"], "gemini-1.5-pro")

    @patch("generate_changelog.types")
    @patch("generate_changelog.genai")
    def test_uses_system_instruction(self, mock_genai, mock_types):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Result"
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        call_gemini("Test prompt", "api_key")

        mock_types.GenerateContentConfig.assert_called_once()
        call_kwargs = mock_types.GenerateContentConfig.call_args[1]
        self.assertIn("system_instruction", call_kwargs)
        self.assertIn("technical writer", call_kwargs["system_instruction"])

    @patch("generate_changelog.types")
    @patch("generate_changelog.genai")
    def test_uses_correct_generation_config(self, mock_genai, mock_types):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Result"
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        call_gemini("Test prompt", "api_key")

        call_kwargs = mock_types.GenerateContentConfig.call_args[1]
        self.assertEqual(call_kwargs["temperature"], 0.3)
        self.assertEqual(call_kwargs["max_output_tokens"], 1000)

    @patch("generate_changelog.genai")
    def test_exits_on_empty_response(self, mock_genai):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = ""
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        with self.assertRaises(SystemExit) as context:
            call_gemini("Test prompt", "api_key")

        self.assertEqual(context.exception.code, 1)

    @patch("generate_changelog.genai")
    def test_exits_on_api_error(self, mock_genai):
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API Error")
        mock_genai.Client.return_value = mock_client

        with self.assertRaises(SystemExit) as context:
            call_gemini("Test prompt", "api_key")

        self.assertEqual(context.exception.code, 1)

    @patch("generate_changelog.genai")
    def test_passes_prompt_as_contents(self, mock_genai):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Result"
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        call_gemini("Test prompt", "api_key")

        call_kwargs = mock_client.models.generate_content.call_args[1]
        self.assertEqual(call_kwargs["contents"], "Test prompt")


class TestBuildPrompt(unittest.TestCase):
    """Tests for build_prompt function."""

    def test_builds_basic_prompt(self):
        pr_details = {
            "number": 123,
            "title": "Add new feature",
            "body": "This PR adds a new feature",
            "labels": ["enhancement"],
        }

        result = build_prompt(pr_details, "diff content", [], [])

        self.assertIn("PR #123: Add new feature", result)
        self.assertIn("This PR adds a new feature", result)
        self.assertIn("Labels: enhancement", result)
        self.assertIn("diff content", result)

    def test_includes_commits(self):
        pr_details = {"number": 1, "title": "Test", "body": "", "labels": []}
        commits = [
            {"sha": "abc1234", "message": "First commit"},
            {"sha": "def5678", "message": "Second commit"},
        ]

        result = build_prompt(pr_details, "", commits, [])

        self.assertIn("Commits:", result)
        self.assertIn("abc1234: First commit", result)
        self.assertIn("def5678: Second commit", result)

    def test_includes_issues(self):
        pr_details = {"number": 1, "title": "Test", "body": "", "labels": []}
        issues = [
            {"number": "42", "title": "Bug report", "body": "Description of bug"},
        ]

        result = build_prompt(pr_details, "", [], issues)

        self.assertIn("Linked Issues:", result)
        self.assertIn("#42: Bug report", result)

    def test_handles_empty_body(self):
        pr_details = {"number": 1, "title": "Test", "body": "", "labels": []}

        result = build_prompt(pr_details, "", [], [])

        self.assertIn("No description provided", result)

    def test_truncates_long_body(self):
        pr_details = {
            "number": 1,
            "title": "Test",
            "body": "x" * 3000,
            "labels": [],
        }

        result = build_prompt(pr_details, "", [], [])

        # Body should be truncated to 2000 chars
        self.assertNotIn("x" * 3000, result)


class TestPostGithubComment(unittest.TestCase):
    """Tests for post_github_comment function."""

    @patch("generate_changelog.urlopen")
    def test_successful_post(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 201
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        # Should not raise
        post_github_comment("org/repo", 123, "Test comment", "token")

        mock_urlopen.assert_called_once()

    @patch("generate_changelog.urlopen")
    def test_raises_on_non_201_status(self, mock_urlopen):
        from urllib.error import HTTPError

        mock_response = MagicMock()
        mock_response.status = 403
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        with self.assertRaises(HTTPError):
            post_github_comment("org/repo", 123, "Test comment", "token")


if __name__ == "__main__":
    unittest.main()
