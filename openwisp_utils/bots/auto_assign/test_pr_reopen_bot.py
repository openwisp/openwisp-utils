import os
from unittest.mock import Mock, patch

from django.test import TestCase

try:
    from .pr_reopen_bot import PRActivityBot, PRReopenBot
except ImportError:
    PRReopenBot = None
    PRActivityBot = None


class TestPRReopenBot(TestCase):
    def setUp(self):
        if PRReopenBot is None:
            self.skipTest("PR reopen bot script not available")

        self.env_vars = {
            "GITHUB_TOKEN": "test_token",
            "REPOSITORY": "openwisp/openwisp-utils",
            "GITHUB_EVENT_NAME": "pull_request_target",
        }

        self.env_patcher = patch.dict(os.environ, self.env_vars)
        self.env_patcher.start()

        self.github_patcher = patch(
            "openwisp_utils.bots.auto_assign.pr_reopen_bot.Github"
        )
        self.mock_github = self.github_patcher.start()

        self.mock_repo = Mock()
        self.mock_github.return_value.get_repo.return_value = self.mock_repo

    def tearDown(self):
        if hasattr(self, "env_patcher"):
            self.env_patcher.stop()
        if hasattr(self, "github_patcher"):
            self.github_patcher.stop()

    def test_reassign_issues_to_author(self):
        bot = PRReopenBot()
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.assignees = []
        self.mock_repo.get_issue.return_value = mock_issue
        pr_body = "Fixes #123"
        assigned = bot.reassign_issues_to_author(100, "testuser", pr_body)
        self.assertEqual(len(assigned), 1)
        self.assertIn(123, assigned)
        mock_issue.add_to_assignees.assert_called_once_with("testuser")
        mock_issue.create_comment.assert_called_once()

    def test_remove_stale_label(self):
        bot = PRReopenBot()
        mock_pr = Mock()
        mock_label = Mock()
        mock_label.name = "stale"
        mock_pr.get_labels.return_value = [mock_label]
        self.mock_repo.get_pull.return_value = mock_pr
        result = bot.remove_stale_label(100)
        self.assertTrue(result)
        mock_pr.remove_from_labels.assert_called_once_with("stale")

    def test_handle_pr_reopen(self):
        bot = PRReopenBot()
        event_payload = {
            "pull_request": {
                "number": 100,
                "user": {"login": "testuser"},
                "body": "Fixes #123",
            }
        }
        bot.load_event_payload(event_payload)
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.assignees = []
        self.mock_repo.get_issue.return_value = mock_issue
        mock_pr = Mock()
        mock_pr.get_labels.return_value = []
        self.mock_repo.get_pull.return_value = mock_pr
        result = bot.handle_pr_reopen()
        self.assertTrue(result)
        mock_issue.add_to_assignees.assert_called_once_with("testuser")


class TestPRActivityBot(TestCase):
    def setUp(self):
        if PRActivityBot is None:
            self.skipTest("PR activity bot script not available")

        self.env_vars = {
            "GITHUB_TOKEN": "test_token",
            "REPOSITORY": "openwisp/openwisp-utils",
            "GITHUB_EVENT_NAME": "issue_comment",
        }

        self.env_patcher = patch.dict(os.environ, self.env_vars)
        self.env_patcher.start()

        self.github_patcher = patch(
            "openwisp_utils.bots.auto_assign.pr_reopen_bot.Github"
        )
        self.mock_github = self.github_patcher.start()

        self.mock_repo = Mock()
        self.mock_github.return_value.get_repo.return_value = self.mock_repo

    def tearDown(self):
        if hasattr(self, "env_patcher"):
            self.env_patcher.stop()
        if hasattr(self, "github_patcher"):
            self.github_patcher.stop()

    def test_handle_contributor_activity(self):
        bot = PRActivityBot()
        event_payload = {
            "issue": {
                "number": 100,
                "pull_request": {
                    "url": "https://api.github.com/repos/owner/repo/pulls/100"
                },
            },
            "comment": {"user": {"login": "testuser"}},
        }
        bot.load_event_payload(event_payload)
        mock_pr = Mock()
        mock_pr.user.login = "testuser"
        mock_pr.body = "Fixes #123"
        mock_label = Mock()
        mock_label.name = "stale"
        mock_pr.get_labels.return_value = [mock_label]
        self.mock_repo.get_pull.return_value = mock_pr
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.assignees = []
        self.mock_repo.get_issue.return_value = mock_issue
        result = bot.handle_contributor_activity()
        self.assertTrue(result)
        mock_pr.remove_from_labels.assert_called_once_with("stale")
        mock_issue.add_to_assignees.assert_called_once_with("testuser")
        mock_pr.create_issue_comment.assert_called_once()

    def test_handle_contributor_activity_not_author(self):
        bot = PRActivityBot()
        event_payload = {
            "issue": {
                "number": 100,
                "pull_request": {
                    "url": "https://api.github.com/repos/owner/repo/pulls/100"
                },
            },
            "comment": {"user": {"login": "otheruser"}},
        }
        bot.load_event_payload(event_payload)
        mock_pr = Mock()
        mock_pr.user.login = "testuser"
        self.mock_repo.get_pull.return_value = mock_pr
        result = bot.handle_contributor_activity()
        self.assertFalse(result)
