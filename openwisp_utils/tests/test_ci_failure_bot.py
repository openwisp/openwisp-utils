import os
import sys
from unittest.mock import Mock, patch

from django.test import TestCase

# Add the .github/scripts directory to Python path for testing
scripts_path = os.path.join(os.path.dirname(__file__), "../../.github/scripts")
sys.path.insert(0, scripts_path)

try:
    from ci_failure_bot import CIFailureBot
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

        self.github_patcher = patch("ci_failure_bot.Github")
        self.genai_patcher = patch("ci_failure_bot.genai")

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

    def test_init_invalid_workflow_run_id(self):
        with patch.dict(os.environ, {"WORKFLOW_RUN_ID": "invalid"}):
            with self.assertRaises(SystemExit):
                CIFailureBot()

    def test_init_custom_gemini_model(self):
        with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-pro"}):
            CIFailureBot()
            self.mock_genai.GenerativeModel.assert_called_with("gemini-pro")

    @patch("ci_failure_bot.requests.get")
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
        mock_response.status_code = 200
        mock_response.text = "Error: Test failed at line 42\n" * 1000
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

    @patch("ci_failure_bot.requests.get")
    def test_get_pr_diff_success(self, mock_requests):
        bot = CIFailureBot()

        mock_pr = Mock()
        mock_pr.title = "Test PR"
        mock_pr.body = "Test description"
        mock_pr.diff_url = "https://github.com/test/diff"
        self.mock_repo.get_pull.return_value = mock_pr

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "diff --git a/test.py b/test.py\n" + "line\n" * 1000
        mock_requests.return_value = mock_response

        diff_data = bot.get_pr_diff()

        self.assertEqual(diff_data["title"], "Test PR")
        self.assertEqual(diff_data["body"], "Test description")
        self.assertIn("[...middle truncated...]", diff_data["diff"])

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

        self.assertEqual(result, "The build failed because of a syntax error.")
        self.mock_model.generate_content.assert_called_once()

    def test_analyze_with_gemini_api_error(self):
        bot = CIFailureBot()

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

        bot.post_comment("Test message")

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

    @patch("ci_failure_bot.requests.get")
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
        mock_response.status_code = 200
        mock_response.text = "Build failed"
        mock_requests.return_value = mock_response

        mock_gemini_response = Mock()
        mock_gemini_response.text = "Analysis: Build failed due to syntax error"
        self.mock_model.generate_content.return_value = mock_gemini_response

        mock_pr = Mock()
        mock_user = Mock()
        mock_user.login = "github-actions[bot]"
        self.mock_github.return_value.get_user.return_value = mock_user
        self.mock_repo.get_pull.return_value = mock_pr
        mock_pr.get_issue_comments.return_value = []

        bot.run()

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
        self.mock_model.generate_content.assert_not_called()
