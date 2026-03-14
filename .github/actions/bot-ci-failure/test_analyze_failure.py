import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, mock_open, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyze_failure import (  # noqa: E402
    _extract_failed_tests,
    _normalize_for_dedup,
    _remove_geckodriver_lines,
    get_error_logs,
    get_repo_context,
    main,
    process_error_logs,
)


class TestGetErrorLogs(unittest.TestCase):
    """Tests for get_error_logs function."""

    @patch("analyze_failure.os.path.exists")
    def test_returns_default_when_file_missing(self, mock_exists):
        mock_exists.return_value = False
        text, tests_failed = get_error_logs()
        self.assertEqual(text, "No failed logs found.")
        self.assertFalse(tests_failed)

    @patch("analyze_failure.os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="Small error log")
    def test_returns_full_content_when_small(self, mock_file, mock_exists):
        mock_exists.return_value = True
        text, tests_failed = get_error_logs()
        self.assertEqual(text, "Small error log")
        self.assertFalse(tests_failed)

    @patch("analyze_failure.os.path.exists")
    def test_truncates_large_logs(self, mock_exists):
        mock_exists.return_value = True
        large_content = "x" * 35000
        with patch("builtins.open", mock_open(read_data=large_content)):
            text, tests_failed = get_error_logs()
        self.assertIn("[LOGS TRUNCATED:", text)
        self.assertLessEqual(len(text), 30000)

    @patch("analyze_failure.os.path.exists")
    @patch("builtins.open")
    def test_handles_file_read_exception(self, mock_file, mock_exists):
        mock_exists.return_value = True
        mock_file.side_effect = Exception("Permission denied")
        text, tests_failed = get_error_logs()
        self.assertIn("Error reading logs: Permission denied", text)
        self.assertFalse(tests_failed)


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

    def test_lib_exclusion(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with open(os.path.join(temp_dir, "main.py"), "w") as f:
                f.write("print('included')")
            lib_dir = os.path.join(temp_dir, "lib")
            os.makedirs(lib_dir)
            with open(os.path.join(lib_dir, "ignored.py"), "w") as f:
                f.write("print('ignored')")
            deep_lib_dir = os.path.join(
                temp_dir,
                "openwisp_controller",
                "config",
                "static",
                "config",
                "js",
                "lib",
            )
            os.makedirs(deep_lib_dir)
            with open(os.path.join(deep_lib_dir, "jquery.js"), "w") as f:
                f.write("console.log('massive library ignored')")
            result = get_repo_context(temp_dir)
            self.assertIn("main.py", result)
            self.assertNotIn("ignored.py", result)
            self.assertNotIn("jquery.js", result)
            self.assertNotIn("print('ignored')", result)
            self.assertNotIn("massive library ignored", result)


class TestRemoveGeckodriverLines(unittest.TestCase):
    """Tests for _remove_geckodriver_lines."""

    def test_removes_geckodriver_log_lines(self):
        text = (
            "Normal log line\n"
            "geckodriver.log: some trace\n"
            "Another normal line\n"
            "Reading geckodriver.log output\n"
            "Final line"
        )
        result = _remove_geckodriver_lines(text)
        self.assertNotIn("geckodriver.log", result)
        self.assertIn("Normal log line", result)
        self.assertIn("Another normal line", result)
        self.assertIn("Final line", result)

    def test_no_geckodriver_lines(self):
        text = "line1\nline2\nline3"
        result = _remove_geckodriver_lines(text)
        self.assertEqual(result, text)


class TestExtractFailedTests(unittest.TestCase):
    """Tests for _extract_failed_tests."""

    def test_extracts_only_failed_blocks(self):
        body = (
            "setup stuff\n" + "=" * 70 + "\nFAIL: test_one (app.tests)\n"
            "Traceback (most recent call last):\n"
            '  File "test.py", line 5\n'
            "AssertionError: False is not true\n"
            + "=" * 70
            + "\nok test_two (app.tests)\n"
            + "=" * 70
            + "\nRan 2 tests"
        )
        result = _extract_failed_tests(body)
        self.assertIn("FAIL: test_one", result)
        self.assertNotIn("ok test_two", result)

    def test_wraps_body_with_separators_when_no_original_separators(self):
        body = "some plain text with a FAIL: marker"
        result = _extract_failed_tests(body)
        sep = "=" * 70
        self.assertEqual(result, f"\n{sep}\n{body}\n{sep}\n")


class TestProcessErrorLogs(unittest.TestCase):
    """Tests for process_error_logs."""

    def test_deduplicates_identical_job_bodies(self):
        content = (
            "===== JOB 100 =====\n"
            "flake8 error: E501\n"
            "===== JOB 200 =====\n"
            "flake8 error: E501\n"
        )
        text, tests_failed = process_error_logs(content)
        # Only one copy of the body should remain.
        self.assertEqual(text.count("flake8 error: E501"), 1)
        self.assertFalse(tests_failed)

    def test_removes_geckodriver_from_jobs(self):
        content = (
            "===== JOB 300 =====\n"
            "Running tests...\n"
            "geckodriver.log: trace info\n"
            "FAIL: test_x\n"
        )
        text, tests_failed = process_error_logs(content)
        self.assertNotIn("geckodriver.log", text)
        self.assertIn("FAIL: test_x", text)
        self.assertTrue(tests_failed)

    def test_tests_failed_true_on_test_failure(self):
        content = (
            "===== JOB 400 =====\n"
            "Traceback (most recent call last):\n"
            '  File "x.py", line 1\n'
            "AssertionError\n"
        )
        _, tests_failed = process_error_logs(content)
        self.assertTrue(tests_failed)

    def test_tests_failed_false_on_qa_only(self):
        content = "===== JOB 500 =====\n" "checkcommit: bad commit message\n"
        _, tests_failed = process_error_logs(content)
        self.assertFalse(tests_failed)

    def test_single_block_no_job_headers(self):
        content = "just some error output without job headers"
        text, tests_failed = process_error_logs(content)
        self.assertEqual(text, content)
        self.assertFalse(tests_failed)


class TestNormalizeForDedup(unittest.TestCase):
    """Tests for _normalize_for_dedup."""

    def test_strips_python_version(self):
        a = _normalize_for_dedup("platform linux -- Python 3.10.5, pytest-7.2.0")
        b = _normalize_for_dedup("platform linux -- Python 3.11.2, pytest-8.1.0")
        self.assertEqual(a, b)

    def test_strips_timestamps(self):
        a = _normalize_for_dedup("Error at 2024-03-14 10:23:45 in module")
        b = _normalize_for_dedup("Error at 2025-01-01 00:00:00 in module")
        self.assertEqual(a, b)

    def test_strips_elapsed_time(self):
        a = _normalize_for_dedup("Ran 42 tests in 1.234s")
        b = _normalize_for_dedup("Ran 42 tests in 9.876s")
        self.assertEqual(a, b)

    def test_strips_platform_line(self):
        result = _normalize_for_dedup(
            "platform linux -- Python 3.10.5, pytest-7.2.0, py-1.11.0"
        )
        self.assertIn("PLATFORM_LINE", result)
        self.assertNotIn("linux", result)

    def test_preserves_test_names(self):
        result = _normalize_for_dedup("FAIL: test_login (auth.tests.LoginTest)")
        self.assertIn("test_login", result)
        self.assertIn("auth.tests.LoginTest", result)

    def test_preserves_line_numbers_in_tracebacks(self):
        result = _normalize_for_dedup('  File "test.py", line 42, in test_foo')
        self.assertIn("line 42", result)

    def test_dedup_integration_near_identical_jobs(self):
        content = (
            "===== JOB 100 =====\n"
            "platform linux -- Python 3.10.5, pytest-7.2.0\n"
            "FAIL: test_foo\nAssertionError\n"
            "Ran 5 tests in 1.234s\n"
            "===== JOB 200 =====\n"
            "platform linux -- Python 3.11.2, pytest-8.1.0\n"
            "FAIL: test_foo\nAssertionError\n"
            "Ran 5 tests in 2.567s\n"
        )
        text, _ = process_error_logs(content)
        self.assertEqual(text.count("FAIL: test_foo"), 1)

    def test_dedup_keeps_genuinely_different_failures(self):
        content = (
            "===== JOB 100 =====\n"
            "FAIL: test_foo\nAssertionError\n"
            "===== JOB 200 =====\n"
            "FAIL: test_bar\nAssertionError\n"
        )
        text, _ = process_error_logs(content)
        self.assertIn("FAIL: test_foo", text)
        self.assertIn("FAIL: test_bar", text)


class TestMain(unittest.TestCase):
    """Tests for the main execution block."""

    @patch("builtins.print")
    @patch.dict(os.environ, {}, clear=True)
    def test_exits_early_without_api_key(self, mock_print):
        main()
        mock_print.assert_called_once_with(
            "::warning::Skipping: No API Key found.", file=sys.stderr
        )

    @patch("builtins.print")
    @patch("analyze_failure.get_error_logs")
    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"})
    def test_exits_early_without_failed_logs(self, mock_get_logs, mock_print):
        mock_get_logs.return_value = ("No failed logs found.", False)
        main()
        mock_print.assert_called_once_with(
            "::warning::Skipping: No failure logs to analyse.", file=sys.stderr
        )

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
        mock_logs.return_value = ("Fake error log", True)
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
        mock_print.assert_called_once_with(
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
        mock_logs.return_value = ("Fake error log", True)
        mock_repo.return_value = "Code"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Here is how to fix the bug."
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        with self.assertRaises(SystemExit) as context:
            main()
        self.assertEqual(context.exception.code, 0)
        mock_print.assert_called_once_with(
            "::warning::LLM output failed format validation; skipping comment.",
            file=sys.stderr,
        )

    @patch("builtins.print")
    @patch("analyze_failure.genai")
    @patch("analyze_failure.get_error_logs")
    @patch("analyze_failure.get_repo_context")
    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"})
    def test_handles_empty_api_response(
        self, mock_repo, mock_logs, mock_genai, mock_print
    ):
        mock_logs.return_value = ("Error log", True)
        mock_repo.return_value = "Code"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "   \n  "
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        with self.assertRaises(SystemExit):
            main()
        mock_print.assert_called_once_with(
            "::warning::Generation returned an empty response; skipping report.",
            file=sys.stderr,
        )

    @patch("builtins.print")
    @patch("analyze_failure.genai")
    @patch("analyze_failure.get_error_logs")
    @patch("analyze_failure.get_repo_context")
    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"})
    def test_handles_api_exception(self, mock_repo, mock_logs, mock_genai, mock_print):
        mock_logs.return_value = ("Error log", True)
        mock_repo.return_value = "Code"
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("Quota Exceeded")
        mock_genai.Client.return_value = mock_client
        with self.assertRaises(SystemExit):
            main()
        mock_print.assert_called_once_with(
            "::warning::API Error (Max retries reached or fatal error): Quota Exceeded",
            file=sys.stderr,
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
        mock_logs.return_value = ("Fake error log", True)
        mock_repo.return_value = "Code"
        mock_client = MagicMock()
        mock_response = MagicMock()
        long_response = "*(Analysis for commit abc1234)*\n" + ("x" * 10000)
        mock_response.text = long_response
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        main()
        self.assertEqual(mock_print.call_count, 1)
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
