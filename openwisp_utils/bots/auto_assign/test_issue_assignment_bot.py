import os
from unittest.mock import Mock, patch

from django.test import TestCase

try:
    from .issue_assignment_bot import IssueAssignmentBot
except ImportError:
    IssueAssignmentBot = None


class TestIssueAssignmentBot(TestCase):
    def setUp(self):
        if IssueAssignmentBot is None:
            self.skipTest("Issue assignment bot script not available")
        self.env_vars = {
            "GITHUB_TOKEN": "test_token",
            "REPOSITORY": "openwisp/openwisp-utils",
            "GITHUB_EVENT_NAME": "issue_comment",
        }

        self.env_patcher = patch.dict(os.environ, self.env_vars)
        self.env_patcher.start()
        self.github_patcher = patch(
            "openwisp_utils.bots.auto_assign.issue_assignment_bot.Github"
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
        bot = IssueAssignmentBot()
        self.assertEqual(bot.github_token, "test_token")
        self.assertEqual(bot.repository_name, "openwisp/openwisp-utils")
        self.assertEqual(bot.event_name, "issue_comment")
        self.mock_github.assert_called_once_with("test_token")

    def test_init_missing_env_vars(self):
        with patch.dict(os.environ, {}, clear=True):
            bot = IssueAssignmentBot()
            self.assertIsNone(bot.github)
            self.assertIsNone(bot.repo)

    def test_is_assignment_request_positive_cases(self):
        bot = IssueAssignmentBot()

        test_cases = [
            "assign this issue to me",
            "Assign me please",
            "Can I work on this?",
            "I would like to work on this issue",
            "I want to work on this",
            "Please assign this to me",
            "Can you assign this to me?",
        ]

        for comment in test_cases:
            with self.subTest(comment=comment):
                self.assertTrue(bot.is_assignment_request(comment))

    def test_is_assignment_request_negative_cases(self):
        bot = IssueAssignmentBot()
        test_cases = [
            "This is a great idea!",
            "How do I solve this?",
            "The assignment looks wrong",
            "",
            None,
        ]
        for comment in test_cases:
            with self.subTest(comment=comment):
                self.assertFalse(bot.is_assignment_request(comment))

    def test_extract_linked_issues(self):
        bot = IssueAssignmentBot()

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

    def test_respond_to_assignment_request_success(self):
        bot = IssueAssignmentBot()
        mock_issue = Mock()
        mock_issue.labels = []
        mock_issue.title = "Test issue title"
        mock_issue.body = "Test issue body"
        self.mock_repo.get_issue.return_value = mock_issue
        result = bot.respond_to_assignment_request(123, "testuser")
        self.assertTrue(result)
        self.mock_repo.get_issue.assert_called_once_with(123)
        mock_issue.create_comment.assert_called_once()
        call_args = mock_issue.create_comment.call_args[0][0]
        self.assertIn("@testuser", call_args)
        self.assertIn("contributing guidelines", call_args)
        self.assertTrue("Fixes `#123`" in call_args or "Closes `#123`" in call_args)

    def test_respond_to_assignment_request_github_error(self):
        bot = IssueAssignmentBot()
        self.mock_repo.get_issue.side_effect = Exception("API Error")
        result = bot.respond_to_assignment_request(123, "testuser")
        self.assertFalse(result)

    def test_auto_assign_issues_from_pr_success(self):
        bot = IssueAssignmentBot()
        mock_issue = Mock()
        mock_issue.labels = []
        mock_issue.title = "Test issue"
        mock_issue.body = "Test body"
        mock_issue.pull_request = None
        mock_issue.assignees = []
        self.mock_repo.get_issue.return_value = mock_issue
        pr_body = "This PR fixes #123 and closes #456"
        assigned = bot.auto_assign_issues_from_pr(100, "testuser", pr_body)
        self.assertEqual(len(assigned), 2)
        self.assertIn(123, assigned)
        self.assertIn(456, assigned)
        self.assertEqual(mock_issue.add_to_assignees.call_count, 2)
        mock_issue.add_to_assignees.assert_any_call("testuser")

    def test_auto_assign_issues_skip_already_assigned(self):
        bot = IssueAssignmentBot()
        mock_assignee = Mock()
        mock_assignee.login = "otheruser"
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.assignees = [mock_assignee]
        self.mock_repo.get_issue.return_value = mock_issue

        pr_body = "Fixes #123"
        assigned = bot.auto_assign_issues_from_pr(100, "testuser", pr_body)

        self.assertEqual(len(assigned), 0)
        mock_issue.add_to_assignees.assert_not_called()

    def test_auto_assign_issues_skip_pr_references(self):
        bot = IssueAssignmentBot()
        mock_issue = Mock()
        mock_issue.pull_request = {"url": "https://api.github.com/repos/test/pulls/123"}
        self.mock_repo.get_issue.return_value = mock_issue
        pr_body = "Fixes #123"
        assigned = bot.auto_assign_issues_from_pr(100, "testuser", pr_body)
        self.assertEqual(len(assigned), 0)
        mock_issue.add_to_assignees.assert_not_called()

    def test_auto_assign_issues_rate_limiting(self):
        bot = IssueAssignmentBot()
        issue_refs = " ".join([f"fixes #{i}" for i in range(1, 16)])
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.assignees = []
        self.mock_repo.get_issue.return_value = mock_issue
        assigned = bot.auto_assign_issues_from_pr(
            100, "testuser", issue_refs, max_issues=10
        )
        self.assertEqual(len(assigned), 10)

    def test_unassign_issues_from_pr(self):
        bot = IssueAssignmentBot()

        mock_assignee = Mock()
        mock_assignee.login = "testuser"
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.assignees = [mock_assignee]
        self.mock_repo.get_issue.return_value = mock_issue

        pr_body = "Fixes #123"
        unassigned = bot.unassign_issues_from_pr(pr_body, "testuser")

        self.assertEqual(len(unassigned), 1)
        self.assertIn(123, unassigned)
        mock_issue.remove_from_assignees.assert_called_once_with("testuser")

    def test_handle_issue_comment_assignment_request(self):
        bot = IssueAssignmentBot()
        event_payload = {
            "issue": {"number": 123, "pull_request": None},
            "comment": {"body": "assign me please", "user": {"login": "testuser"}},
        }
        bot.load_event_payload(event_payload)
        mock_issue = Mock()
        mock_issue.labels = []
        mock_issue.title = "Test issue"
        mock_issue.body = "Test body"
        self.mock_repo.get_issue.return_value = mock_issue
        result = bot.handle_issue_comment()
        self.assertTrue(result)
        mock_issue.create_comment.assert_called_once()

    def test_handle_issue_comment_skip_pr_comment(self):
        bot = IssueAssignmentBot()

        event_payload = {
            "issue": {
                "number": 123,
                "pull_request": {"url": "https://api.github.com/repos/test/pulls/123"},
            },
            "comment": {"body": "assign me please", "user": {"login": "testuser"}},
        }

        bot.load_event_payload(event_payload)

        result = bot.handle_issue_comment()

        self.assertFalse(result)

    def test_handle_pull_request_opened(self):
        bot = IssueAssignmentBot()
        event_payload = {
            "action": "opened",
            "pull_request": {
                "number": 100,
                "user": {"login": "testuser"},
                "body": "Fixes #123",
            },
        }
        bot.load_event_payload(event_payload)
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.assignees = []
        self.mock_repo.get_issue.return_value = mock_issue
        result = bot.handle_pull_request()
        self.assertTrue(result)
        mock_issue.add_to_assignees.assert_called_once_with("testuser")

    def test_handle_pull_request_reopened(self):
        bot = IssueAssignmentBot()
        event_payload = {
            "action": "reopened",
            "pull_request": {
                "number": 100,
                "user": {"login": "testuser"},
                "body": "Fixes #123",
            },
        }
        bot.load_event_payload(event_payload)
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.assignees = []
        self.mock_repo.get_issue.return_value = mock_issue
        result = bot.handle_pull_request()
        self.assertTrue(result)

    def test_handle_pull_request_unsupported_action(self):
        bot = IssueAssignmentBot()
        event_payload = {
            "action": "synchronize",
            "pull_request": {
                "number": 100,
                "user": {"login": "testuser"},
                "body": "Fixes #123",
            },
        }
        bot.load_event_payload(event_payload)
        result = bot.handle_pull_request()
        self.assertFalse(result)

    def test_run_issue_comment_event(self):
        bot = IssueAssignmentBot()
        bot.event_name = "issue_comment"
        event_payload = {
            "issue": {"number": 123, "pull_request": None},
            "comment": {"body": "assign me", "user": {"login": "testuser"}},
        }
        bot.load_event_payload(event_payload)
        mock_issue = Mock()
        mock_issue.labels = []
        mock_issue.title = "Test issue"
        mock_issue.body = "Test body"
        self.mock_repo.get_issue.return_value = mock_issue
        result = bot.run()
        self.assertTrue(result)

    def test_run_pull_request_event(self):
        bot = IssueAssignmentBot()
        bot.event_name = "pull_request_target"
        event_payload = {
            "action": "opened",
            "pull_request": {
                "number": 100,
                "user": {"login": "testuser"},
                "body": "Fixes #123",
            },
        }
        bot.load_event_payload(event_payload)
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.assignees = []
        self.mock_repo.get_issue.return_value = mock_issue
        result = bot.run()
        self.assertTrue(result)

    def test_run_unsupported_event(self):
        bot = IssueAssignmentBot()
        bot.event_name = "push"
        result = bot.run()
        self.assertFalse(result)

    def test_run_no_github_client(self):
        bot = IssueAssignmentBot()
        bot.github = None
        bot.repo = None
        result = bot.run()
        self.assertFalse(result)
