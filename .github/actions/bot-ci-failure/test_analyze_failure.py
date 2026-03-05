import os
import sys
import unittest
from unittest.mock import MagicMock, mock_open, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyze_failure import get_error_logs, get_repo_context, main  # noqa: E402


class TestGetErrorLogs(unittest.TestCase):
    """Tests for get_error_logs function."""

    @patch("analyze_failure.os.path.exists")
    def test_returns_default_when_file_missing(self, mock_exists):
        mock_exists.return_value = False
        result = get_error_logs()
        self.assertEqual(result, "No failed logs found.")

    @patch("analyze_failure.os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="Small error log")
    def test_returns_full_content_when_small(self, mock_file, mock_exists):
        mock_exists.return_value = True
        result = get_error_logs()
        self.assertEqual(result, "Small error log")

    @patch("analyze_failure.os.path.exists")
    def test_truncates_large_logs(self, mock_exists):
        mock_exists.return_value = True
        large_content = "x" * 35000
        with patch("builtins.open", mock_open(read_data=large_content)):
            result = get_error_logs()
        self.assertIn("[LOGS TRUNCATED:", result)
        self.assertLessEqual(len(result), 30000)
        self.assertTrue(result.startswith("x" * 5980))

    @patch("analyze_failure.os.path.exists")
    @patch("builtins.open")
    def test_handles_file_read_exception(self, mock_file, mock_exists):
        mock_exists.return_value = True
        mock_file.side_effect = Exception("Permission denied")
        result = get_error_logs()
        self.assertIn("Error reading logs: Permission denied", result)


class TestGetRepoContext(unittest.TestCase):
    """Tests for get_repo_context function."""

    @patch("analyze_failure.os.path.exists")
    def test_returns_default_when_dir_missing(self, mock_exists):
        mock_exists.return_value = False
        result = get_repo_context("fake_dir")
        self.assertEqual(result, "No repository context available.")

    @patch("analyze_failure.os.path.exists")
    @patch("analyze_failure.os.walk")
    @patch("builtins.open", new_callable=mock_open, read_data="print('hello')")
    def test_reads_allowed_files_and_ignores_blocklist(
        self, mock_file, mock_walk, mock_exists
    ):
        mock_exists.return_value = True
        mock_walk.return_value = [
            ("pr_code", ["docs"], ["main.py", "style.css", "Dockerfile"]),
        ]
        result = get_repo_context("pr_code")
        self.assertIn('<file path="main.py">', result)
        self.assertIn('<file path="Dockerfile">', result)
        self.assertIn("print('hello')", result)
        self.assertNotIn('<file path="style.css">', result)

    @patch("analyze_failure.os.path.exists")
    @patch("analyze_failure.os.walk")
    @patch("builtins.open", new_callable=mock_open, read_data="a" * 1000)
    def test_truncates_when_max_chars_exceeded(self, mock_file, mock_walk, mock_exists):
        mock_exists.return_value = True
        mock_walk.return_value = [("pr_code", [], ["file1.py", "file2.py"])]
        result = get_repo_context("pr_code", max_chars=100)
        self.assertIn("SYSTEM WARNING: REPO CONTEXT TRUNCATED", result)
        self.assertLessEqual(len(result), 300)

    @patch("analyze_failure.os.path.exists")
    @patch("analyze_failure.os.walk")
    def test_skips_files_with_unicode_errors(self, mock_walk, mock_exists):
        mock_exists.return_value = True
        mock_walk.return_value = [("pr_code", [], ["binary.py"])]
        with patch("builtins.open") as mock_file:
            mock_file.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")
            result = get_repo_context("pr_code")
        self.assertEqual(result, "No relevant source files found in repository.")

    @patch("analyze_failure.os.path.exists")
    @patch("analyze_failure.os.walk")
    def test_returns_default_when_no_relevant_files(self, mock_walk, mock_exists):
        mock_exists.return_value = True
        mock_walk.return_value = [
            ("pr_code", [], ["image.png", "style.css", "readme.md"])
        ]
        result = get_repo_context("pr_code")
        self.assertEqual(result, "No relevant source files found in repository.")


class TestMain(unittest.TestCase):
    """Tests for the main execution block."""

    @patch("builtins.print")
    @patch.dict(os.environ, {}, clear=True)
    def test_exits_early_without_api_key(self, mock_print):
        main()
        mock_print.assert_any_call("::warning::Skipping: No API Key found.")

    @patch("builtins.print")
    @patch("analyze_failure.get_error_logs")
    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"})
    def test_exits_early_without_failed_logs(self, mock_get_logs, mock_print):
        mock_get_logs.return_value = "No failed logs found."
        main()
        mock_print.assert_any_call("::warning::Skipping: No failure logs to analyse.")

    @patch("builtins.print")
    @patch("analyze_failure.genai")
    @patch("analyze_failure.get_error_logs")
    @patch("analyze_failure.get_repo_context")
    @patch.dict(
        os.environ,
        {"GEMINI_API_KEY": "fake_key", "PR_AUTHOR": "test", "COMMIT_SHA": "abc"},
    )
    def test_successful_api_call_prints_response(
        self, mock_repo, mock_logs, mock_genai, mock_print
    ):
        mock_logs.return_value = "Fake error log"
        mock_repo.return_value = "<file path='test.py'>code</file>"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = (
            "### Test Failed\n"
            "Hello @testuser\n"
            "*(Analysis for commit abc1234)*\n"
            "Here is the fix."
        )
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        main()
        mock_print.assert_any_call(
            "### Test Failed\n"
            "Hello @testuser\n"
            "*(Analysis for commit abc1234)*\n"
            "Here is the fix."
        )

    @patch("builtins.print")
    @patch("analyze_failure.genai")
    @patch("analyze_failure.get_error_logs")
    @patch("analyze_failure.get_repo_context")
    @patch.dict(
        os.environ,
        {"GEMINI_API_KEY": "fake_key", "PR_AUTHOR": "test", "COMMIT_SHA": "abc"},
    )
    def test_fails_format_validation(
        self, mock_repo, mock_logs, mock_genai, mock_print
    ):
        mock_logs.return_value = "Fake error log"
        mock_repo.return_value = "Code"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Here is how to fix the bug."
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        with self.assertRaises(SystemExit) as context:
            main()
        self.assertEqual(context.exception.code, 0)
        mock_print.assert_any_call(
            "::warning::LLM output failed format validation; skipping comment."
        )

    @patch("builtins.print")
    @patch("analyze_failure.genai")
    @patch("analyze_failure.get_error_logs")
    @patch("analyze_failure.get_repo_context")
    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"})
    def test_handles_empty_api_response(
        self, mock_repo, mock_logs, mock_genai, mock_print
    ):
        mock_logs.return_value = "Error log"
        mock_repo.return_value = "Code"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "   \n  "
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        with self.assertRaises(SystemExit):
            main()
        mock_print.assert_any_call(
            "::warning::Generation returned an empty response; skipping report."
        )

    @patch("builtins.print")
    @patch("analyze_failure.genai")
    @patch("analyze_failure.get_error_logs")
    @patch("analyze_failure.get_repo_context")
    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"})
    def test_handles_api_exception(self, mock_repo, mock_logs, mock_genai, mock_print):
        mock_logs.return_value = "Error log"
        mock_repo.return_value = "Code"
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("Quota Exceeded")
        mock_genai.Client.return_value = mock_client
        with self.assertRaises(SystemExit):
            main()
        mock_print.assert_any_call(
            "::warning::API Error (Max retries reached or fatal error): Quota Exceeded"
        )

    @patch("builtins.print")
    @patch("analyze_failure.genai")
    @patch("analyze_failure.get_error_logs")
    @patch("analyze_failure.get_repo_context")
    @patch.dict(
        os.environ,
        {"GEMINI_API_KEY": "fake_key", "PR_AUTHOR": "test", "COMMIT_SHA": "abc"},
    )
    def test_truncates_large_api_response(
        self, mock_repo, mock_logs, mock_genai, mock_print
    ):
        mock_logs.return_value = "Fake error log"
        mock_repo.return_value = "Code"
        mock_client = MagicMock()
        mock_response = MagicMock()
        long_response = "*(Analysis for commit abc1234)*\n" + ("x" * 10000)
        mock_response.text = long_response
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        main()
        printed_text = mock_print.call_args[0][0]
        self.assertIn(
            "*(Warning: Output truncated due to length limits)*", printed_text
        )
        expected_length = 10000 + len(
            "\n\n*(Warning: Output truncated due to length limits)*"
        )
        self.assertEqual(len(printed_text), expected_length)


if __name__ == "__main__":
    unittest.main()
