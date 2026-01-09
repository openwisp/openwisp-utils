import os
import subprocess
from unittest.mock import Mock, patch

from django.test import TestCase

try:
    from openwisp_utils.ci_failure_bot import CIFailureBot
except ImportError:
    CIFailureBot = None


class TestCIFailureBot(TestCase):
    def setUp(self):
        if CIFailureBot is None:
            self.skipTest("CI failure bot script not available")
        self.env_vars = {
            "GITHUB_TOKEN": "test_token",
            "GEMINI_API_KEY": "test_gemini_key",
            "WORKFLOW_RUN_ID": "12345",
            "REPOSITORY": "openwisp/openwisp-utils",
            "PR_NUMBER": "1",
        }
        self.env_patcher = patch.dict(os.environ, self.env_vars)
        self.env_patcher.start()
        self.github_patcher = patch("openwisp_utils.ci_failure_bot.Github")
        self.genai_patcher = patch("openwisp_utils.ci_failure_bot.genai")
        self.mock_github = self.github_patcher.start()
        self.mock_genai = self.genai_patcher.start()
        self.mock_repo = Mock()
        self.mock_github.return_value.get_repo.return_value = self.mock_repo
        self.mock_model = Mock()
        self.mock_genai.GenerativeModel.return_value = self.mock_model

    def tearDown(self):
        if hasattr(self, "env_patcher"):
            self.env_patcher.stop()
        if hasattr(self, "github_patcher"):
            self.github_patcher.stop()
        if hasattr(self, "genai_patcher"):
            self.genai_patcher.stop()

    def test_init_success(self):
        bot = CIFailureBot()
        self.assertEqual(bot.github_token, "test_token")
        self.assertEqual(bot.gemini_api_key, "test_gemini_key")
        self.assertEqual(bot.workflow_run_id, 12345)
        self.assertEqual(bot.repository_name, "openwisp/openwisp-utils")
        self.assertEqual(bot.pr_number, "1")
        self.mock_github.assert_called_once_with("test_token")
        self.mock_genai.configure.assert_called_once_with(api_key="test_gemini_key")

    def test_init_missing_env_vars(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit):
                CIFailureBot()

    def test_init_without_gemini_key(self):
        env_vars_no_gemini = {
            "GITHUB_TOKEN": "test_token",
            "WORKFLOW_RUN_ID": "12345",
            "REPOSITORY": "openwisp/openwisp-utils",
            "PR_NUMBER": "1",
        }
        with patch.dict(os.environ, env_vars_no_gemini, clear=True):
            bot = CIFailureBot()
            self.assertIsNone(bot.model)
            self.mock_genai.configure.assert_not_called()

    def test_init_invalid_workflow_run_id(self):
        with patch.dict(os.environ, {"WORKFLOW_RUN_ID": "invalid"}):
            with self.assertRaises(SystemExit):
                CIFailureBot()

    def test_init_custom_gemini_model(self):
        with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-pro"}):
            bot = CIFailureBot()
            if bot.model:
                self.mock_genai.GenerativeModel.assert_called_with("gemini-pro")

    @patch("openwisp_utils.ci_failure_bot.requests.get")
    def test_get_build_logs_success(self, mock_requests):
        bot = CIFailureBot()
        mock_workflow_run = Mock()
        mock_job = Mock()
        mock_job.conclusion = "failure"
        mock_job.name = "test-job"
        mock_job.logs_url = "https://api.github.com/logs/123"
        mock_step = Mock()
        mock_step.conclusion = "failure"
        mock_step.name = "Run tests"
        mock_step.number = 1
        mock_job.steps = [mock_step]
        mock_workflow_run.jobs.return_value = [mock_job]
        self.mock_repo.get_workflow_run.return_value = mock_workflow_run
        mock_response = Mock()
        mock_response.content = b"Error: Test failed at line 42\n" * 1000
        mock_response.raise_for_status = Mock()
        mock_requests.return_value = mock_response
        logs = bot.get_build_logs()
        self.assertEqual(len(logs), 2)
        self.assertIn("job_name", logs[0])
        self.assertIn("logs", logs[0])
        self.assertEqual(logs[1]["step_name"], "Run tests")

    def test_get_build_logs_no_failures(self):
        bot = CIFailureBot()
        mock_workflow_run = Mock()
        mock_job = Mock()
        mock_job.conclusion = "success"
        mock_workflow_run.jobs.return_value = [mock_job]
        self.mock_repo.get_workflow_run.return_value = mock_workflow_run
        logs = bot.get_build_logs()
        self.assertEqual(logs, [])

    @patch("openwisp_utils.ci_failure_bot.subprocess.run")
    @patch("openwisp_utils.ci_failure_bot.requests.get")
    def test_get_pr_diff_success(self, mock_requests, mock_subprocess):
        bot = CIFailureBot()
        mock_pr = Mock()
        mock_pr.title = "Test PR"
        mock_pr.body = "Test description"
        mock_pr.diff_url = "https://github.com/test/diff"
        self.mock_repo.get_pull.return_value = mock_pr
        # Mock successful git diff
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = (
            "diff --git a/test.py b/test.py\n" + "line\n" * 1000
        )
        diff_data = bot.get_pr_diff()
        self.assertEqual(diff_data["title"], "Test PR")
        self.assertEqual(diff_data["body"], "Test description")
        self.assertIn("[...middle truncated...]", diff_data["diff"])
        mock_subprocess.assert_called_once()

    def test_get_pr_diff_no_pr_number(self):
        bot = CIFailureBot()
        bot.pr_number = None
        diff_data = bot.get_pr_diff()
        self.assertIsNone(diff_data)

    def test_get_workflow_yaml_success(self):
        bot = CIFailureBot()
        mock_workflow_run = Mock()
        mock_workflow_run.path = ".github/workflows/ci.yml"
        self.mock_repo.get_workflow_run.return_value = mock_workflow_run
        mock_file = Mock()
        mock_file.decoded_content = b"name: CI\non: [push]"
        self.mock_repo.get_contents.return_value = mock_file
        yaml_content = bot.get_workflow_yaml()
        self.assertEqual(yaml_content, "name: CI\non: [push]")

    def test_analyze_with_gemini_success(self):
        bot = CIFailureBot()
        mock_response = Mock()
        mock_response.text = "The build failed because of a syntax error."
        self.mock_model.generate_content.return_value = mock_response
        build_logs = [{"job_name": "test", "logs": "Error: syntax error"}]
        pr_diff = {"title": "Test", "diff": "diff content"}
        workflow_yaml = "name: CI"
        result = bot.analyze_with_gemini(build_logs, pr_diff, workflow_yaml)
        if bot.model:
            self.assertEqual(result, "The build failed because of a syntax error.")
            self.mock_model.generate_content.assert_called_once()
        else:
            self.assertIn("CI Build Failed", result)

    def test_analyze_with_gemini_api_error(self):
        bot = CIFailureBot()
        if bot.model:
            self.mock_model.generate_content.side_effect = Exception("API Error")
        result = bot.analyze_with_gemini([], None, None)
        self.assertIn("CI Build Failed", result)
        self.assertIn("temporarily unavailable", result)

    def test_post_comment_success(self):
        bot = CIFailureBot()
        mock_pr = Mock()
        mock_user = Mock()
        mock_user.login = "github-actions[bot]"
        self.mock_github.return_value.get_user.return_value = mock_user
        self.mock_repo.get_pull.return_value = mock_pr
        mock_pr.get_issue_comments.return_value = []
        bot.post_comment("Test message")
        mock_pr.create_issue_comment.assert_called_once()
        call_args = mock_pr.create_issue_comment.call_args[0][0]
        self.assertIn("<!-- ci-failure-bot-comment -->", call_args)
        self.assertIn("Test message", call_args)

    def test_post_comment_update_existing(self):
        bot = CIFailureBot()
        mock_pr = Mock()
        mock_user = Mock()
        mock_user.login = "github-actions[bot]"
        self.mock_github.return_value.get_user.return_value = mock_user
        self.mock_repo.get_pull.return_value = mock_pr
        mock_comment = Mock()
        mock_comment.user.login = "github-actions[bot]"
        mock_comment.body = "<!-- ci-failure-bot-comment -->\nOld message"
        mock_pr.get_issue_comments.return_value = [mock_comment]
        bot.post_comment("New message")
        mock_comment.edit.assert_called_once()
        mock_pr.create_issue_comment.assert_not_called()

    def test_post_comment_no_pr_number(self):
        bot = CIFailureBot()
        bot.pr_number = None
        with patch("builtins.print") as mock_print:
            bot.post_comment("Test message")
        mock_print.assert_any_call("No PR number, skipping comment")

    def test_run_skips_dependabot(self):
        bot = CIFailureBot()
        mock_workflow_run = Mock()
        mock_actor = Mock()
        mock_actor.login = "dependabot[bot]"
        mock_workflow_run.actor = mock_actor
        self.mock_repo.get_workflow_run.return_value = mock_workflow_run
        with patch("builtins.print") as mock_print:
            bot.run()
        mock_print.assert_any_call("Skipping dependabot PR from dependabot[bot]")

    @patch("openwisp_utils.ci_failure_bot.requests.get")
    def test_run_full_workflow(self, mock_requests):
        bot = CIFailureBot()
        mock_workflow_run = Mock()
        mock_actor = Mock()
        mock_actor.login = "user"
        mock_workflow_run.actor = mock_actor
        mock_job = Mock()
        mock_job.conclusion = "failure"
        mock_job.name = "test-job"
        mock_job.logs_url = "https://api.github.com/logs/123"
        mock_job.steps = []
        mock_workflow_run.jobs.return_value = [mock_job]
        self.mock_repo.get_workflow_run.return_value = mock_workflow_run
        mock_response = Mock()
        mock_response.content = b"Build failed"
        mock_response.raise_for_status = Mock()
        mock_requests.return_value = mock_response
        mock_gemini_response = Mock()
        mock_gemini_response.text = "Analysis: Build failed due to syntax error"
        self.mock_model.generate_content.return_value = mock_gemini_response
        mock_pr = Mock()
        mock_pr.head = Mock()
        mock_pr.head.repo = Mock()
        mock_pr.head.repo.full_name = "openwisp/openwisp-utils"
        mock_user = Mock()
        mock_user.login = "github-actions[bot]"
        self.mock_github.return_value.get_user.return_value = mock_user
        self.mock_repo.get_pull.return_value = mock_pr
        mock_pr.get_issue_comments.return_value = []
        bot.run()
        if bot.model:
            self.mock_model.generate_content.assert_called_once()
        mock_pr.create_issue_comment.assert_called_once()

    def test_run_no_build_logs(self):
        bot = CIFailureBot()
        mock_workflow_run = Mock()
        mock_actor = Mock()
        mock_actor.login = "user"
        mock_workflow_run.actor = mock_actor
        mock_workflow_run.jobs.return_value = []
        self.mock_repo.get_workflow_run.return_value = mock_workflow_run
        with patch("builtins.print") as mock_print:
            bot.run()
        mock_print.assert_any_call("No build logs found")
        if bot.model:
            self.mock_model.generate_content.assert_not_called()

    @patch("openwisp_utils.ci_failure_bot.requests.get")
    def test_get_build_logs_zip_format(self, mock_requests):
        """Test ZIP-encoded log extraction in get_build_logs()"""
        import io
        import zipfile

        bot = CIFailureBot()
        # Create in-memory ZIP file with log content
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("failed_job.txt", "Error: test failed\nstack trace here")
        zip_content = zip_buffer.getvalue()
        # Mock workflow and job
        mock_workflow_run = Mock()
        mock_job = Mock()
        mock_job.name = "test-job"
        mock_job.conclusion = "failure"
        mock_job.logs_url = "https://api.github.com/logs/123"
        step = Mock()
        step.name = "failing-step"
        step.conclusion = "failure"
        step.number = 1
        mock_job.steps = [step]
        mock_workflow_run.jobs.return_value = [mock_job]
        self.mock_repo.get_workflow_run.return_value = mock_workflow_run
        # Mock requests to return ZIP content
        mock_response = Mock()
        mock_response.content = zip_content
        mock_response.raise_for_status = Mock()
        mock_requests.return_value = mock_response
        logs = bot.get_build_logs()
        self.assertEqual(len(logs), 2)  # job log + step info
        self.assertIn("Error: test failed", logs[0]["logs"])
        self.assertEqual(logs[0]["job_name"], "test-job")

    @patch("openwisp_utils.ci_failure_bot.subprocess.run")
    @patch("openwisp_utils.ci_failure_bot.requests.get")
    def test_get_pr_diff_git_failure_http_fallback(
        self, mock_requests, mock_subprocess
    ):
        """Test git diff fallback to HTTP when subprocess fails"""
        bot = CIFailureBot()
        mock_pr = Mock()
        mock_pr.title = "Test PR"
        mock_pr.body = "Test description"
        mock_pr.diff_url = "https://github.com/test/diff"
        self.mock_repo.get_pull.return_value = mock_pr
        self.mock_repo.default_branch = "main"
        # Mock subprocess to fail (git not available or timeout)
        mock_subprocess.side_effect = subprocess.SubprocessError("git command failed")
        # Mock HTTP fallback to succeed
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "diff --git a/file.py b/file.py\n+new line"
        mock_requests.return_value = mock_response
        diff = bot.get_pr_diff()
        # Verify subprocess was attempted
        mock_subprocess.assert_called_once()
        # Verify HTTP fallback was used
        mock_requests.assert_called_once()
        self.assertIn("+new line", diff["diff"])
        self.assertEqual(diff["title"], "Test PR")

    def test_run_skips_deleted_fork_pr(self):
        """Test that run() skips PRs from deleted fork repositories"""
        bot = CIFailureBot()
        mock_workflow_run = Mock()
        mock_actor = Mock()
        mock_actor.login = "user"
        mock_workflow_run.actor = mock_actor
        self.mock_repo.get_workflow_run.return_value = mock_workflow_run
        # Mock PR with deleted fork (head.repo is None)
        mock_pr = Mock()
        mock_pr.head.repo = None  # Simulates deleted fork
        self.mock_repo.get_pull.return_value = mock_pr
        # Should exit early without exception
        with patch("builtins.print") as mock_print:
            bot.run()
            # Verify skip message was printed
            mock_print.assert_any_call("Skipping PR with deleted head repository")

    def test_main_handles_init_exception(self):
        """Test that main() handles initialization exceptions gracefully"""
        from openwisp_utils.ci_failure_bot import main

        # Missing WORKFLOW_RUN_ID should cause SystemExit during init
        with patch.dict(
            os.environ,
            {"GITHUB_TOKEN": "test-token", "REPOSITORY": "test/repo"},
            clear=True,
        ):
            with self.assertRaises(SystemExit) as cm:
                main()
            # Verify it exits with error code 1
            self.assertEqual(cm.exception.code, 1)
