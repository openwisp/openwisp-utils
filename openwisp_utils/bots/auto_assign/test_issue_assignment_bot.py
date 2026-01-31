import os
from unittest.mock import Mock, patch

import pytest

try:
    from .issue_assignment_bot import IssueAssignmentBot
except ImportError:
    IssueAssignmentBot = None

pytestmark = pytest.mark.skipif(
    IssueAssignmentBot is None,
    reason="Issue assignment bot script not available",
)


@pytest.fixture(autouse=True)
def bot_env(monkeypatch):
    """Set up environment and mock GitHub client for all tests."""
    monkeypatch.setenv("GITHUB_TOKEN", "test_token")
    monkeypatch.setenv("REPOSITORY", "openwisp/openwisp-utils")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "issue_comment")

    with patch("openwisp_utils.bots.auto_assign.base.Github") as mock_github_cls:
        mock_repo = Mock()
        mock_github_cls.return_value.get_repo.return_value = mock_repo
        yield {
            "github_cls": mock_github_cls,
            "repo": mock_repo,
        }


class TestInit:
    def test_init_success(self, bot_env):
        bot = IssueAssignmentBot()
        assert bot.github_token == "test_token"
        assert bot.repository_name == "openwisp/openwisp-utils"
        assert bot.event_name == "issue_comment"
        bot_env["github_cls"].assert_called_once_with("test_token")

    def test_init_missing_env_vars(self):
        with patch.dict(os.environ, {}, clear=True):
            bot = IssueAssignmentBot()
            assert bot.github is None
            assert bot.repo is None


class TestAssignmentRequest:
    @pytest.mark.parametrize(
        "comment",
        [
            "assign this issue to me",
            "Assign me please",
            "Can I work on this?",
            "I would like to work on this issue",
            "I want to work on this",
            "Please assign this to me",
            "Can you assign this to me?",
        ],
    )
    def test_positive_cases(self, comment, bot_env):
        bot = IssueAssignmentBot()
        assert bot.is_assignment_request(comment)

    @pytest.mark.parametrize(
        "comment",
        [
            "This is a great idea!",
            "How do I solve this?",
            "The assignment looks wrong",
            "",
            None,
        ],
    )
    def test_negative_cases(self, comment, bot_env):
        bot = IssueAssignmentBot()
        assert not bot.is_assignment_request(comment)


class TestExtractLinkedIssues:
    @pytest.mark.parametrize(
        "pr_body,expected",
        [
            ("Fixes #123", [123]),
            ("Closes #456 and resolves #789", [456, 789]),
            ("fix #100, close #200, resolve #300", [100, 200, 300]),
            ("This PR fixes #123 and closes #123", [123]),  # dedup
            ("Fixes: #42", [42]),  # colon syntax
            ("Related to #99", [99]),  # relates-to
            ("Fixes owner/repo#55", [55]),  # cross-repo
            ("No issue references here", []),
            ("", []),
            (None, []),
        ],
    )
    def test_extract_linked_issues(self, pr_body, expected, bot_env):
        from .utils import extract_linked_issues

        result = extract_linked_issues(pr_body)
        assert sorted(result) == sorted(expected)


class TestRespondToAssignment:
    def test_success_no_type_detected(self, bot_env):
        bot = IssueAssignmentBot()
        mock_issue = Mock()
        mock_issue.labels = []
        mock_issue.title = "Test issue title"
        mock_issue.body = "Test issue body"
        bot_env["repo"].get_issue.return_value = mock_issue

        assert bot.respond_to_assignment_request(123, "testuser")
        bot_env["repo"].get_issue.assert_called_once_with(123)
        mock_issue.create_comment.assert_called_once()

        comment_text = mock_issue.create_comment.call_args[0][0]
        assert "@testuser" in comment_text
        assert "contributing guidelines" in comment_text
        # When type is None, generic instructions listing all keywords
        assert f"`Closes #{123}`" in comment_text
        assert f"`Fixes #{123}`" in comment_text

    def test_success_bug_detected(self, bot_env):
        bot = IssueAssignmentBot()
        mock_label = Mock()
        mock_label.name = "bug"
        mock_issue = Mock()
        mock_issue.labels = [mock_label]
        mock_issue.title = "Something is broken"
        mock_issue.body = "There is a regression"
        bot_env["repo"].get_issue.return_value = mock_issue

        assert bot.respond_to_assignment_request(42, "dev")
        comment_text = mock_issue.create_comment.call_args[0][0]
        assert "`Fixes #42`" in comment_text

    def test_success_feature_detected(self, bot_env):
        bot = IssueAssignmentBot()
        mock_label = Mock()
        mock_label.name = "enhancement"
        mock_issue = Mock()
        mock_issue.labels = [mock_label]
        mock_issue.title = "Add new feature"
        mock_issue.body = "Please add this"
        bot_env["repo"].get_issue.return_value = mock_issue

        assert bot.respond_to_assignment_request(99, "dev")
        comment_text = mock_issue.create_comment.call_args[0][0]
        assert "`Closes #99`" in comment_text

    def test_github_error(self, bot_env):
        bot = IssueAssignmentBot()
        bot_env["repo"].get_issue.side_effect = Exception("API Error")
        assert not bot.respond_to_assignment_request(123, "testuser")


class TestAutoAssignIssuesFromPR:
    def test_success(self, bot_env):
        bot = IssueAssignmentBot()
        mock_issue = Mock()
        mock_issue.labels = []
        mock_issue.title = "Test issue"
        mock_issue.body = "Test body"
        mock_issue.pull_request = None
        mock_issue.assignees = []
        bot_env["repo"].get_issue.return_value = mock_issue

        assigned = bot.auto_assign_issues_from_pr(
            100, "testuser", "This PR fixes #123 and closes #456"
        )
        assert len(assigned) == 2
        assert 123 in assigned
        assert 456 in assigned
        assert mock_issue.add_to_assignees.call_count == 2
        mock_issue.add_to_assignees.assert_any_call("testuser")

    def test_skip_already_assigned(self, bot_env):
        bot = IssueAssignmentBot()
        mock_assignee = Mock()
        mock_assignee.login = "otheruser"
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.assignees = [mock_assignee]
        mock_issue.repository.full_name = "openwisp/openwisp-utils"
        bot_env["repo"].get_issue.return_value = mock_issue

        assigned = bot.auto_assign_issues_from_pr(100, "testuser", "Fixes #123")
        assert len(assigned) == 0
        mock_issue.add_to_assignees.assert_not_called()

    def test_skip_pr_references(self, bot_env):
        bot = IssueAssignmentBot()
        mock_issue = Mock()
        mock_issue.pull_request = {"url": "https://api.github.com/repos/test/pulls/123"}
        bot_env["repo"].get_issue.return_value = mock_issue

        assigned = bot.auto_assign_issues_from_pr(100, "testuser", "Fixes #123")
        assert len(assigned) == 0
        mock_issue.add_to_assignees.assert_not_called()

    def test_rate_limiting(self, bot_env):
        bot = IssueAssignmentBot()
        issue_refs = " ".join([f"fixes #{i}" for i in range(1, 16)])
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.assignees = []
        bot_env["repo"].get_issue.return_value = mock_issue

        assigned = bot.auto_assign_issues_from_pr(
            100, "testuser", issue_refs, max_issues=10
        )
        assert len(assigned) == 10

    def test_no_linked_issues(self, bot_env):
        bot = IssueAssignmentBot()
        assigned = bot.auto_assign_issues_from_pr(100, "testuser", "No issues here")
        assert assigned == []

    def test_empty_body(self, bot_env):
        bot = IssueAssignmentBot()
        assigned = bot.auto_assign_issues_from_pr(100, "testuser", "")
        assert assigned == []

    def test_none_body(self, bot_env):
        bot = IssueAssignmentBot()
        assigned = bot.auto_assign_issues_from_pr(100, "testuser", None)
        assert assigned == []


class TestUnassignIssuesFromPR:
    def test_unassign_success(self, bot_env):
        bot = IssueAssignmentBot()
        mock_assignee = Mock()
        mock_assignee.login = "testuser"
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.assignees = [mock_assignee]
        mock_issue.repository.full_name = "openwisp/openwisp-utils"
        bot_env["repo"].get_issue.return_value = mock_issue

        unassigned = bot.unassign_issues_from_pr("Fixes #123", "testuser")
        assert len(unassigned) == 1
        assert 123 in unassigned
        mock_issue.remove_from_assignees.assert_called_once_with("testuser")

    def test_skip_cross_repo_issues(self, bot_env):
        bot = IssueAssignmentBot()
        mock_assignee = Mock()
        mock_assignee.login = "testuser"
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.assignees = [mock_assignee]
        mock_issue.repository.full_name = "other-org/other-repo"
        bot_env["repo"].get_issue.return_value = mock_issue

        unassigned = bot.unassign_issues_from_pr("Fixes #123", "testuser")
        assert len(unassigned) == 0
        mock_issue.remove_from_assignees.assert_not_called()


class TestHandleIssueComment:
    def test_assignment_request(self, bot_env):
        bot = IssueAssignmentBot()
        bot.load_event_payload(
            {
                "issue": {"number": 123, "pull_request": None},
                "comment": {"body": "assign me please", "user": {"login": "testuser"}},
            }
        )
        mock_issue = Mock()
        mock_issue.labels = []
        mock_issue.title = "Test issue"
        mock_issue.body = "Test body"
        bot_env["repo"].get_issue.return_value = mock_issue

        assert bot.handle_issue_comment()
        mock_issue.create_comment.assert_called_once()

    def test_skip_pr_comment(self, bot_env):
        bot = IssueAssignmentBot()
        bot.load_event_payload(
            {
                "issue": {
                    "number": 123,
                    "pull_request": {
                        "url": "https://api.github.com/repos/test/pulls/123"
                    },
                },
                "comment": {"body": "assign me please", "user": {"login": "testuser"}},
            }
        )
        assert not bot.handle_issue_comment()

    def test_non_assignment_comment(self, bot_env):
        bot = IssueAssignmentBot()
        bot.load_event_payload(
            {
                "issue": {"number": 123, "pull_request": None},
                "comment": {"body": "looks good!", "user": {"login": "testuser"}},
            }
        )
        assert not bot.handle_issue_comment()

    def test_no_payload(self, bot_env):
        bot = IssueAssignmentBot()
        assert not bot.handle_issue_comment()


class TestHandlePullRequest:
    def test_opened(self, bot_env):
        bot = IssueAssignmentBot()
        bot.load_event_payload(
            {
                "action": "opened",
                "pull_request": {
                    "number": 100,
                    "user": {"login": "testuser"},
                    "body": "Fixes #123",
                },
            }
        )
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.assignees = []
        bot_env["repo"].get_issue.return_value = mock_issue

        assert bot.handle_pull_request()
        mock_issue.add_to_assignees.assert_called_once_with("testuser")

    def test_reopened(self, bot_env):
        bot = IssueAssignmentBot()
        bot.load_event_payload(
            {
                "action": "reopened",
                "pull_request": {
                    "number": 100,
                    "user": {"login": "testuser"},
                    "body": "Fixes #123",
                },
            }
        )
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.assignees = []
        bot_env["repo"].get_issue.return_value = mock_issue

        assert bot.handle_pull_request()

    def test_unsupported_action(self, bot_env):
        bot = IssueAssignmentBot()
        bot.load_event_payload(
            {
                "action": "synchronize",
                "pull_request": {
                    "number": 100,
                    "user": {"login": "testuser"},
                    "body": "Fixes #123",
                },
            }
        )
        assert not bot.handle_pull_request()


class TestRun:
    def test_issue_comment_event(self, bot_env):
        bot = IssueAssignmentBot()
        bot.event_name = "issue_comment"
        bot.load_event_payload(
            {
                "issue": {"number": 123, "pull_request": None},
                "comment": {"body": "assign me", "user": {"login": "testuser"}},
            }
        )
        mock_issue = Mock()
        mock_issue.labels = []
        mock_issue.title = "Test issue"
        mock_issue.body = "Test body"
        bot_env["repo"].get_issue.return_value = mock_issue

        assert bot.run()

    def test_pull_request_event(self, bot_env):
        bot = IssueAssignmentBot()
        bot.event_name = "pull_request_target"
        bot.load_event_payload(
            {
                "action": "opened",
                "pull_request": {
                    "number": 100,
                    "user": {"login": "testuser"},
                    "body": "Fixes #123",
                },
            }
        )
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.assignees = []
        bot_env["repo"].get_issue.return_value = mock_issue

        assert bot.run()

    def test_unsupported_event(self, bot_env):
        bot = IssueAssignmentBot()
        bot.event_name = "push"
        assert not bot.run()

    def test_no_github_client(self, bot_env):
        bot = IssueAssignmentBot()
        bot.github = None
        bot.repo = None
        assert not bot.run()
