import os
from unittest.mock import Mock, patch

from django.test import TestCase
from openwisp_utils.bots.ci_failure.bot import CIFailureBot


class TestCIFailureBot(TestCase):
    def setUp(self):
        self.env_vars = {
            "GITHUB_TOKEN": "test_token",
            "GEMINI_API_KEY": "test_gemini_key",
            "WORKFLOW_RUN_ID": "12345",
            "REPOSITORY": "openwisp/openwisp-utils",
            "PR_NUMBER": "1",
        }
        self.env_patcher = patch.dict(os.environ, self.env_vars)
        self.env_patcher.start()
        self.github_patcher = patch("openwisp_utils.bots.ci_failure.bot.Github")
        self.genai_patcher = patch("openwisp_utils.bots.ci_failure.bot.genai")
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

    def _mock_workflow_run(self, actor="user", jobs=None):
        """Helper to create mock workflow run"""
        mock_run = Mock()
        mock_actor = Mock()
        mock_actor.login = actor
        mock_run.actor = mock_actor
        if jobs is not None:
            mock_run.jobs.return_value = jobs
        self.mock_repo.get_workflow_run.return_value = mock_run
        return mock_run

    def _mock_pr(self, full_name="openwisp/openwisp-utils", deleted_fork=False):
        """Helper to create mock PR"""
        mock_pr = Mock()
        if deleted_fork:
            mock_pr.head.repo = None
        else:
            mock_pr.head.repo = Mock()
            mock_pr.head.repo.full_name = full_name
        mock_pr.get_issue_comments.return_value = []
        self.mock_repo.get_pull.return_value = mock_pr
        return mock_pr

    def _mock_failed_job(self, logs_url="https://api.github.com/logs/123", steps=None):
        """Helper to create mock failed job"""
        job = Mock()
        job.name = "test-job"
        job.conclusion = "failure"
        job.logs_url = logs_url
        job.steps = steps or []
        return job

    def test_init_success(self):
        bot = CIFailureBot()
        self.assertEqual(bot.github_token, "test_token")
        self.assertEqual(bot.gemini_api_key, "test_gemini_key")
        self.assertEqual(bot.workflow_run_id, "12345")
        self.assertEqual(bot.repository_name, "openwisp/openwisp-utils")
        self.assertEqual(bot.pr_number, "1")
        self.mock_github.assert_called_once_with("test_token")
        self.mock_genai.configure.assert_called_once_with(api_key="test_gemini_key")

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

    def test_classify_failure_qa(self):
        bot = CIFailureBot()
        logs = [{"job_name": "Build / Python 3.11", "logs": "flake8 error"}]
        self.assertEqual(bot.classify_failure(logs), "qa")

    def test_classify_failure_tests(self):
        bot = CIFailureBot()
        logs = [{"job_name": "unit-tests", "logs": "test failed"}]
        self.assertEqual(bot.classify_failure(logs), "tests")

    def test_classify_failure_setup(self):
        bot = CIFailureBot()
        logs = [
            {"job_name": "build", "logs": "ModuleNotFoundError: No module named 'xyz'"}
        ]
        self.assertEqual(bot.classify_failure(logs), "setup")

    def test_classify_failure_mixed(self):
        bot = CIFailureBot()
        logs = [
            {"job_name": "Build / Python 3.11", "logs": "flake8 error"},
            {"job_name": "Build / Python 3.11", "logs": "test failed"},
        ]
        self.assertEqual(bot.classify_failure(logs), "mixed")

    def test_classify_failure_unknown(self):
        bot = CIFailureBot()
        logs = [{"job_name": "unknown-job", "logs": "some error"}]
        self.assertEqual(bot.classify_failure(logs), "unknown")

    @patch("openwisp_utils.bots.ci_failure.bot.requests.get")
    def test_get_build_logs_success(self, mock_requests):
        bot = CIFailureBot()
        mock_workflow_run = Mock()
        mock_step = Mock()
        mock_step.conclusion = "failure"
        mock_step.name = "Run tests"
        mock_step.number = 1
        mock_job = self._mock_failed_job(steps=[mock_step])
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

    @patch("openwisp_utils.bots.ci_failure.bot.requests.get")
    def test_get_build_logs_zip_format(self, mock_requests):
        """Test ZIP-encoded log extraction"""
        import io
        import zipfile

        bot = CIFailureBot()
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("failed_job.txt", "Error: test failed\nstack trace here")
        zip_content = zip_buffer.getvalue()
        mock_workflow_run = Mock()
        step = Mock()
        step.name = "failing-step"
        step.conclusion = "failure"
        step.number = 1
        mock_job = self._mock_failed_job(steps=[step])
        mock_workflow_run.jobs.return_value = [mock_job]
        self.mock_repo.get_workflow_run.return_value = mock_workflow_run
        mock_response = Mock()
        mock_response.content = zip_content
        mock_response.raise_for_status = Mock()
        mock_requests.return_value = mock_response
        logs = bot.get_build_logs()
        self.assertEqual(len(logs), 2)
        self.assertIn("Error: test failed", logs[0]["logs"])

    @patch("openwisp_utils.bots.ci_failure.bot.requests.get")
    def test_get_build_logs_error(self, mock_requests):
        """Test network error during log fetch"""
        import requests

        bot = CIFailureBot()
        mock_workflow_run = Mock()
        mock_job = self._mock_failed_job()
        mock_workflow_run.jobs.return_value = [mock_job]
        self.mock_repo.get_workflow_run.return_value = mock_workflow_run
        mock_requests.side_effect = requests.RequestException("Network error")
        logs = bot.get_build_logs()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["logs"], "")

    @patch("openwisp_utils.bots.ci_failure.bot.subprocess.run")
    def test_get_pr_diff_success(self, mock_subprocess):
        bot = CIFailureBot()
        mock_pr = Mock()
        mock_pr.title = "Test PR"
        mock_pr.body = "Test description"
        self.mock_repo.get_pull.return_value = mock_pr
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "diff --git a/test.py b/test.py\n" + (
            "line\n" * 2000
        )
        diff_data = bot.get_pr_diff()
        self.assertEqual(diff_data["title"], "Test PR")
        self.assertEqual(diff_data["body"], "Test description")
        self.assertIn("[...middle truncated...]", diff_data["diff"])

    @patch("openwisp_utils.bots.ci_failure.bot.subprocess.run")
    def test_get_pr_diff_error(self, mock_subprocess):
        """Test git subprocess failure"""
        import subprocess

        bot = CIFailureBot()
        mock_pr = Mock()
        mock_pr.title = "Test"
        mock_pr.body = "Desc"
        self.mock_repo.get_pull.return_value = mock_pr
        self.mock_repo.default_branch = "main"
        mock_subprocess.side_effect = subprocess.SubprocessError("git failed")
        diff = bot.get_pr_diff()
        self.assertIsNone(diff)

    def test_analyze_with_gemini_success(self):
        bot = CIFailureBot()
        bot.model = self.mock_model
        mock_response = Mock()
        mock_response.text = """The file bad_format.py contains PEP 8 violations.

Required Actions:
```bash
pip install -e .[qa]
openwisp-qa-format
```"""
        self.mock_model.generate_content.return_value = mock_response
        build_logs = [{"job_name": "Build / Python 3.11", "logs": "flake8 error"}]
        pr_diff = {"title": "Test", "diff": "diff content"}
        result = bot.analyze_with_gemini(build_logs, pr_diff)
        self.assertIn("PEP 8", result)
        self.assertIn("pip install", result)
        self.mock_model.generate_content.assert_called_once()

    def test_analyze_with_gemini_fallback(self):
        bot = CIFailureBot()
        bot.model = self.mock_model
        self.mock_model.generate_content.side_effect = Exception("API Error")
        result = bot.analyze_with_gemini([], None)
        self.assertIn("Automated analysis", result)
        self.assertIn("pip install", result)

    def test_post_comment_create(self):
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

    def test_run_skips_dependabot(self):
        bot = CIFailureBot()
        self._mock_workflow_run(actor="dependabot[bot]")
        with patch("builtins.print") as mock_print:
            bot.run()
        mock_print.assert_any_call("Skipping: dependabot PR from dependabot[bot]")

    @patch("openwisp_utils.bots.ci_failure.bot.subprocess.run")
    @patch("openwisp_utils.bots.ci_failure.bot.requests.get")
    def test_run_full_workflow(self, mock_requests, mock_subprocess):
        bot = CIFailureBot()
        mock_job = self._mock_failed_job()
        self._mock_workflow_run(jobs=[mock_job])
        mock_response = Mock()
        mock_response.content = b"Build failed"
        mock_response.raise_for_status = Mock()
        mock_requests.return_value = mock_response

        # Mock subprocess for PR diff
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "diff --git a/test.py"

        mock_gemini_response = Mock()
        mock_gemini_response.text = "Analysis: Build failed due to syntax error"
        self.mock_model.generate_content.return_value = mock_gemini_response
        mock_pr = self._mock_pr()
        bot.run()
        mock_pr.create_issue_comment.assert_called_once()

    def test_run_skips_fork_pr(self):
        """Test skipping fork PR"""
        bot = CIFailureBot()
        self._mock_workflow_run(actor="contributor")
        self.mock_repo.full_name = "openwisp/openwisp-utils"
        mock_pr = self._mock_pr(full_name="contributor/openwisp-utils")
        with patch("builtins.print") as mock_print:
            bot.run()
            mock_print.assert_any_call(
                "Skipping: fork PR from contributor/openwisp-utils"
            )
        mock_pr.create_issue_comment.assert_not_called()

    def test_run_skips_deleted_fork_pr(self):
        """Test skipping PR from deleted fork"""
        bot = CIFailureBot()
        self._mock_workflow_run()
        mock_pr = self._mock_pr(deleted_fork=True)
        with patch("builtins.print") as mock_print:
            bot.run()
            mock_print.assert_any_call("Skipping: PR with deleted head repository")
        mock_pr.create_issue_comment.assert_not_called()

    def test_run_fork_status_exception(self):
        """Test fork status check exception"""
        from github import GithubException

        bot = CIFailureBot()
        mock_run = Mock()
        mock_actor = Mock()
        mock_actor.login = "user"
        mock_run.actor = mock_actor
        self.mock_repo.get_workflow_run.return_value = mock_run
        self.mock_repo.get_pull.side_effect = GithubException(404, "Not found")
        with patch("builtins.print") as mock_print:
            bot.run()
            mock_print.assert_any_call(
                'Warning: Could not check fork status: 404 "Not found"'
            )

    def test_run_actor_check_exception(self):
        """Test actor check exception"""
        from github import GithubException

        bot = CIFailureBot()
        self.mock_repo.get_workflow_run.side_effect = GithubException(
            401, "Unauthorized"
        )
        mock_pr = Mock()
        mock_pr.get_issue_comments.return_value = []
        self.mock_repo.get_pull.return_value = mock_pr
        with patch("builtins.print") as mock_print:
            bot.run()
            mock_print.assert_any_call(
                'Warning: Could not check actor: 401 "Unauthorized"'
            )

    def test_run_no_pr_context(self):
        """Test run with no PR context"""
        bot = CIFailureBot()
        bot.pr_number = None
        mock_run = Mock()
        mock_actor = Mock()
        mock_actor.login = "user"
        mock_run.actor = mock_actor
        self.mock_repo.get_workflow_run.return_value = mock_run
        with patch("builtins.print") as mock_print:
            bot.run()
            mock_print.assert_any_call(
                "No PR context available - workflow_run without PR"
            )

    def test_run_no_logs_no_diff_fallback(self):
        """Test fallback when no logs or diff available"""
        bot = CIFailureBot()
        mock_run = Mock()
        mock_actor = Mock()
        mock_actor.login = "user"
        mock_run.actor = mock_actor
        mock_run.jobs.return_value = []
        self.mock_repo.get_workflow_run.return_value = mock_run
        mock_pr = Mock()
        mock_pr.head.repo.full_name = "openwisp/openwisp-utils"
        mock_pr.get_issue_comments.return_value = []
        self.mock_repo.get_pull.return_value = mock_pr
        with patch("builtins.print") as mock_print:
            bot.run()
            mock_print.assert_any_call(
                "No build logs or PR diff found, using fallback response"
            )

    def test_run_outer_exception(self):
        """Test outer exception handling in run"""
        bot = CIFailureBot()
        with patch.object(bot, "get_build_logs", side_effect=Exception("boom")):
            mock_run = Mock()
            mock_actor = Mock()
            mock_actor.login = "user"
            mock_run.actor = mock_actor
            self.mock_repo.get_workflow_run.return_value = mock_run
            mock_pr = Mock()
            mock_pr.head.repo.full_name = "openwisp/openwisp-utils"
            mock_pr.get_issue_comments.return_value = []
            self.mock_repo.get_pull.return_value = mock_pr
            with patch("builtins.print") as mock_print:
                bot.run()
                mock_print.assert_any_call("Error in analysis: boom")

    def test_run_no_repo(self):
        """Test run when repo is None"""
        bot = CIFailureBot()
        bot.repo = None
        with patch("builtins.print") as mock_print:
            bot.run()
            mock_print.assert_any_call("GitHub client not initialized, cannot proceed")

    def test_get_build_logs_no_repo(self):
        """Test get_build_logs when repo is None"""
        bot = CIFailureBot()
        bot.repo = None
        logs = bot.get_build_logs()
        self.assertEqual(logs, [])

    def test_get_build_logs_no_workflow_run_id(self):
        """Test get_build_logs when workflow_run_id is None"""
        bot = CIFailureBot()
        bot.workflow_run_id = None
        logs = bot.get_build_logs()
        self.assertEqual(logs, [])

    def test_get_pr_diff_no_repo(self):
        """Test get_pr_diff when repo is None"""
        bot = CIFailureBot()
        bot.repo = None
        diff = bot.get_pr_diff()
        self.assertIsNone(diff)

    def test_get_pr_diff_no_pr_number(self):
        """Test get_pr_diff when pr_number is None"""
        bot = CIFailureBot()
        bot.pr_number = None
        diff = bot.get_pr_diff()
        self.assertIsNone(diff)

    def test_post_comment_no_pr_number(self):
        """Test post_comment when pr_number is None"""
        bot = CIFailureBot()
        bot.pr_number = None
        bot.post_comment("Test message")

    def test_post_comment_no_github_client(self):
        """Test post_comment when GitHub client is None"""
        bot = CIFailureBot()
        bot.github = None
        bot.repo = None
        bot.post_comment("Test message")

    def test_analyze_with_gemini_no_model(self):
        """Test analyze_with_gemini when model is None"""
        bot = CIFailureBot()
        bot.model = None
        result = bot.analyze_with_gemini([], None)
        self.assertIn("Automated analysis", result)

    def test_analyze_with_gemini_no_repository_name(self):
        """Test analyze_with_gemini when repository_name is None"""
        bot = CIFailureBot()
        bot.repository_name = None
        result = bot.analyze_with_gemini([], None)
        self.assertIn("Automated analysis", result)

    def test_classify_failure_qa_formatting(self):
        """Test QA classification with formatting keywords"""
        bot = CIFailureBot()
        logs = [{"job_name": "lint", "logs": "formatting error"}]
        self.assertEqual(bot.classify_failure(logs), "qa")

    def test_classify_failure_tests_pytest(self):
        """Test classification with pytest keyword"""
        bot = CIFailureBot()
        logs = [{"job_name": "pytest", "logs": "test error"}]
        self.assertEqual(bot.classify_failure(logs), "tests")

    def test_get_failed_jobs_summary_with_steps(self):
        """Test get_failed_jobs_summary extracts step info"""
        bot = CIFailureBot()
        build_logs = [
            {"job_name": "test-job", "step_name": "Run tests", "step_number": 1},
            {"job_name": "lint-job", "logs": "error"},
        ]
        summary = bot.get_failed_jobs_summary(build_logs)
        self.assertEqual(len(summary), 2)
        self.assertEqual(summary[0]["name"], "test-job")
        self.assertEqual(summary[0]["step"], "Run tests")

    def test_get_build_logs_no_logs_url(self):
        """Test get_build_logs when job has no logs_url"""
        bot = CIFailureBot()
        mock_workflow_run = Mock()
        mock_job = self._mock_failed_job(logs_url=None)
        mock_workflow_run.jobs.return_value = [mock_job]
        self.mock_repo.get_workflow_run.return_value = mock_workflow_run
        logs = bot.get_build_logs()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["logs"], "")

    @patch("openwisp_utils.bots.ci_failure.bot.subprocess.run")
    def test_get_pr_diff_large_diff_truncation(self, mock_subprocess):
        """Test PR diff truncation for large diffs"""
        bot = CIFailureBot()
        mock_pr = Mock()
        mock_pr.title = "Test"
        mock_pr.body = "Desc"
        self.mock_repo.get_pull.return_value = mock_pr
        mock_subprocess.return_value.returncode = 0
        # Create a diff larger than 8000 chars
        mock_subprocess.return_value.stdout = "line\n" * 2000
        diff = bot.get_pr_diff()
        self.assertIn("[...middle truncated...]", diff["diff"])

    def test_init_missing_github_token(self):
        """Test initialization with missing GITHUB_TOKEN"""
        env_vars = {
            "REPOSITORY": "repo",
            "WORKFLOW_RUN_ID": "12345",
            "PR_NUMBER": "1",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            bot = CIFailureBot()
            self.assertIsNone(bot.github)
            self.assertIsNone(bot.repo)

    def test_init_missing_repository(self):
        """Test initialization with missing REPOSITORY"""
        env_vars = {
            "GITHUB_TOKEN": "token",
            "WORKFLOW_RUN_ID": "12345",
            "PR_NUMBER": "1",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            bot = CIFailureBot()
            self.assertIsNone(bot.github)
            self.assertIsNone(bot.repo)

    @patch("openwisp_utils.bots.ci_failure.bot.Github")
    def test_init_github_exception(self, mock_github_class):
        """Test GitHub initialization exception"""
        from github import GithubException

        mock_github_class.side_effect = GithubException(401, "Unauthorized")
        env_vars = {
            "GITHUB_TOKEN": "token",
            "REPOSITORY": "repo",
            "WORKFLOW_RUN_ID": "12345",
            "PR_NUMBER": "1",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            bot = CIFailureBot()
            self.assertIsNone(bot.github)
            self.assertIsNone(bot.repo)

    @patch("openwisp_utils.bots.ci_failure.bot.genai")
    @patch("openwisp_utils.bots.ci_failure.bot.Github")
    def test_init_gemini_exception(self, mock_github_class, mock_genai):
        """Test Gemini initialization exception"""
        mock_genai.configure.side_effect = Exception("API key invalid")
        env_vars = {
            "GITHUB_TOKEN": "token",
            "GEMINI_API_KEY": "key",
            "REPOSITORY": "repo",
            "WORKFLOW_RUN_ID": "12345",
            "PR_NUMBER": "1",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            bot = CIFailureBot()
            self.assertIsNone(bot.model)

    @patch("openwisp_utils.bots.ci_failure.bot.requests.get")
    def test_get_build_logs_zip_with_txt_extension(self, mock_requests):
        """Test ZIP file with .txt extension"""
        import io
        import zipfile

        bot = CIFailureBot()
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("job.txt", "Error log content")
        zip_content = zip_buffer.getvalue()
        mock_workflow_run = Mock()
        mock_job = self._mock_failed_job()
        mock_workflow_run.jobs.return_value = [mock_job]
        self.mock_repo.get_workflow_run.return_value = mock_workflow_run
        mock_response = Mock()
        mock_response.content = zip_content
        mock_response.raise_for_status = Mock()
        mock_requests.return_value = mock_response
        logs = bot.get_build_logs()
        self.assertGreater(len(logs), 0)

    @patch("openwisp_utils.bots.ci_failure.bot.requests.get")
    def test_get_build_logs_with_failed_steps(self, mock_requests):
        """Test build logs with failed steps"""
        bot = CIFailureBot()
        mock_workflow_run = Mock()
        step = Mock()
        step.name = "failing-step"
        step.conclusion = "failure"
        step.number = 1
        mock_job = self._mock_failed_job(steps=[step])
        mock_workflow_run.jobs.return_value = [mock_job]
        self.mock_repo.get_workflow_run.return_value = mock_workflow_run
        mock_response = Mock()
        mock_response.content = b"Error logs"
        mock_response.raise_for_status = Mock()
        mock_requests.return_value = mock_response
        logs = bot.get_build_logs()
        # Should have job log + step info
        self.assertGreater(len(logs), 1)

    def test_get_pr_diff_invalid_pr_number(self):
        """Test get_pr_diff with invalid PR number"""
        bot = CIFailureBot()
        bot.pr_number = "invalid_string"
        diff = bot.get_pr_diff()
        self.assertIsNone(diff)

    def test_get_pr_diff_github_exception(self):
        """Test get_pr_diff with GithubException"""
        from github import GithubException

        bot = CIFailureBot()
        self.mock_repo.get_pull.side_effect = GithubException(404, "Not found")
        diff = bot.get_pr_diff()
        self.assertIsNone(diff)

    def test_post_comment_invalid_pr_number(self):
        """Test post_comment with invalid PR number"""
        bot = CIFailureBot()
        bot.pr_number = "invalid"
        bot.post_comment("Test message")

    def test_post_comment_github_exception_fetch_pr(self):
        """Test post_comment with GithubException when fetching PR"""
        from github import GithubException

        bot = CIFailureBot()
        self.mock_repo.get_pull.side_effect = GithubException(403, "Forbidden")
        bot.post_comment("Test message")

    def test_post_comment_github_exception_get_comments(self):
        """Test post_comment with GithubException when getting comments"""
        from github import GithubException

        bot = CIFailureBot()
        mock_pr = Mock()
        self.mock_repo.get_pull.return_value = mock_pr
        mock_pr.get_issue_comments.side_effect = GithubException(500, "Server error")
        bot.post_comment("Test message")

    def test_post_comment_github_exception_create_comment(self):
        """Test post_comment with GithubException when creating comment"""
        from github import GithubException

        bot = CIFailureBot()
        mock_pr = Mock()
        self.mock_repo.get_pull.return_value = mock_pr
        mock_pr.get_issue_comments.return_value = []
        mock_pr.create_issue_comment.side_effect = GithubException(403, "Forbidden")
        bot.post_comment("Test message")

    def test_get_failed_jobs_summary_job_name_only(self):
        """Test get_failed_jobs_summary with job_name only"""
        bot = CIFailureBot()
        build_logs = [{"job_name": "test-job", "logs": "error"}]
        summary = bot.get_failed_jobs_summary(build_logs)
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]["name"], "test-job")
        self.assertNotIn("step", summary[0])
