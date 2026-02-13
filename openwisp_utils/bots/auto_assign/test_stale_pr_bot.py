import os
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from django.test import TestCase

try:
    from .stale_pr_bot import StalePRBot
except ImportError:
    StalePRBot = None


class TestStalePRBot(TestCase):
    def setUp(self):
        if StalePRBot is None:
            self.skipTest("Stale PR bot script not available")

        self.env_vars = {
            "GITHUB_TOKEN": "test_token",
            "REPOSITORY": "openwisp/openwisp-utils",
        }

        self.env_patcher = patch.dict(os.environ, self.env_vars)
        self.env_patcher.start()

        self.github_patcher = patch(
            "openwisp_utils.bots.auto_assign.stale_pr_bot.Github"
        )
        self.mock_github = self.github_patcher.start()

        self.mock_repo = Mock()
        self.mock_github.return_value.get_repo.return_value = self.mock_repo

    def tearDown(self):
        if hasattr(self, "env_patcher"):
            self.env_patcher.stop()
        if hasattr(self, "github_patcher"):
            self.github_patcher.stop()

    def test_init_success(self):
        bot = StalePRBot()
        self.assertEqual(bot.github_token, "test_token")
        self.assertEqual(bot.repository_name, "openwisp/openwisp-utils")
        self.mock_github.assert_called_once_with("test_token")

    def test_extract_linked_issues(self):
        bot = StalePRBot()

        test_cases = [
            ("Fixes #123", [123]),
            ("Closes #456 and resolves #789", [456, 789]),
            ("fix #100, close #200, resolve #300", [100, 200, 300]),
            ("This PR fixes #123 and closes #123", [123]),  # duplicates removed
            ("No issue references here", []),
            ("", []),
            (None, []),
        ]

        for pr_body, expected in test_cases:
            with self.subTest(pr_body=pr_body):
                result = bot.extract_linked_issues(pr_body)
                self.assertEqual(sorted(result), sorted(expected))

    def test_get_last_changes_requested(self):
        bot = StalePRBot()
        mock_pr = Mock()
        mock_review1 = Mock()
        mock_review1.state = "APPROVED"
        mock_review1.submitted_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        mock_review2 = Mock()
        mock_review2.state = "CHANGES_REQUESTED"
        mock_review2.submitted_at = datetime(2024, 1, 2, tzinfo=timezone.utc)
        mock_review3 = Mock()
        mock_review3.state = "CHANGES_REQUESTED"
        mock_review3.submitted_at = datetime(2024, 1, 3, tzinfo=timezone.utc)
        mock_pr.get_reviews.return_value = [mock_review1, mock_review2, mock_review3]
        result = bot.get_last_changes_requested(mock_pr)
        self.assertEqual(result, datetime(2024, 1, 3, tzinfo=timezone.utc))

    def test_get_last_changes_requested_none(self):
        bot = StalePRBot()

        mock_pr = Mock()
        mock_review = Mock()
        mock_review.state = "APPROVED"
        mock_pr.get_reviews.return_value = [mock_review]

        result = bot.get_last_changes_requested(mock_pr)
        self.assertIsNone(result)

    @patch("openwisp_utils.bots.auto_assign.stale_pr_bot.datetime")
    def test_get_days_since_activity(self, mock_datetime):
        bot = StalePRBot()

        mock_now = datetime(2024, 1, 10, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now

        mock_pr = Mock()
        mock_pr.user.login = "testuser"
        mock_pr.head.sha = "abc123"

        mock_pr.get_issue_comments.return_value = []

        # Mock commits
        mock_commit = Mock()
        mock_commit.commit.author.date = datetime(2024, 1, 5, tzinfo=timezone.utc)
        mock_commit.author.login = "testuser"
        self.mock_repo.get_commits.return_value = [mock_commit]

        last_changes_requested = datetime(2024, 1, 1, tzinfo=timezone.utc)

        result = bot.get_days_since_activity(mock_pr, last_changes_requested)
        self.assertEqual(result, 5)

    def test_unassign_linked_issues(self):
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.body = "Fixes #123"
        mock_pr.user.login = "testuser"
        mock_assignee = Mock()
        mock_assignee.login = "testuser"
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.assignees = [mock_assignee]
        self.mock_repo.get_issue.return_value = mock_issue
        result = bot.unassign_linked_issues(mock_pr)
        self.assertEqual(result, 1)
        mock_issue.remove_from_assignees.assert_called_once_with("testuser")

    def test_has_bot_comment(self):
        bot = StalePRBot()

        mock_pr = Mock()
        mock_comment = Mock()
        mock_comment.user.type = "Bot"
        mock_comment.body = "<!-- bot:stale --> This is a stale warning"
        mock_pr.get_issue_comments.return_value = [mock_comment]

        result = bot.has_bot_comment(mock_pr, "stale")
        self.assertTrue(result)

        result = bot.has_bot_comment(mock_pr, "closed")
        self.assertFalse(result)

    def test_send_stale_warning(self):
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.user.login = "testuser"
        result = bot.send_stale_warning(mock_pr, 7)
        self.assertTrue(result)
        mock_pr.create_issue_comment.assert_called_once()
        call_args = mock_pr.create_issue_comment.call_args[0][0]
        self.assertIn("@testuser", call_args)
        self.assertIn("7 days", call_args)

    def test_mark_pr_stale(self):
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.body = "Fixes #123"
        mock_pr.user.login = "testuser"
        mock_assignee = Mock()
        mock_assignee.login = "testuser"
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.assignees = [mock_assignee]
        self.mock_repo.get_issue.return_value = mock_issue
        result = bot.mark_pr_stale(mock_pr, 14)
        self.assertTrue(result)
        mock_pr.create_issue_comment.assert_called_once()
        mock_pr.add_to_labels.assert_called_once_with("stale")
        mock_issue.remove_from_assignees.assert_called_once_with("testuser")

    def test_close_stale_pr(self):
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.body = "Fixes #123"
        mock_pr.user.login = "testuser"
        mock_assignee = Mock()
        mock_assignee.login = "testuser"
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.assignees = [mock_assignee]
        self.mock_repo.get_issue.return_value = mock_issue
        result = bot.close_stale_pr(mock_pr, 60)
        self.assertTrue(result)
        mock_pr.create_issue_comment.assert_called_once()
        mock_pr.edit.assert_called_once_with(state="closed")
        mock_issue.remove_from_assignees.assert_called_once_with("testuser")
