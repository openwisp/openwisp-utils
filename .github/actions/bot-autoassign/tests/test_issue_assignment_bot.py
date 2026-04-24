import os
import sys
from unittest.mock import Mock, patch

# Add the parent directory to path for importing bot modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from github import GithubException  # noqa: E402

try:
    from issue_assignment_bot import IssueAssignmentBot  # noqa: E402
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
    monkeypatch.setattr("issue_assignment_bot.time.sleep", lambda _seconds: None)
    with patch("base.Github") as mock_github_cls:
        mock_repo = Mock()
        mock_github = mock_github_cls.return_value
        mock_github.get_repo.return_value = mock_repo
        yield {
            "github_cls": mock_github_cls,
            "github": mock_github,
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
            ("Fixes owner/repo#55", []),  # cross-repo refs are ignored
            ("Fixed #999", [999]),
            ("No issue references here", []),
            ("", []),
            (None, []),
        ],
    )
    def test_extract_linked_issues(self, pr_body, expected, bot_env):
        from utils import extract_linked_issues

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


def _make_issue_with_assignment(
    login="testuser", repo_full_name="openwisp/openwisp-utils"
):
    mock_issue = Mock()
    mock_issue.labels = []
    mock_issue.title = "Test issue"
    mock_issue.body = "Test body"
    mock_issue.pull_request = None
    mock_issue.state = "open"
    mock_issue.assignees = []
    mock_issue.repository.full_name = repo_full_name

    def _assign(user):
        assignee = Mock()
        assignee.login = user
        mock_issue.assignees = [*mock_issue.assignees, assignee]

    mock_issue.add_to_assignees.side_effect = _assign
    return mock_issue


def _make_bot_assign_issue(
    state="open",
    pull_request=None,
    assignees=None,
    repo_full_name="openwisp/openwisp-utils",
):
    mock_issue = Mock()
    mock_issue.state = state
    mock_issue.pull_request = pull_request
    mock_issue.assignees = list(assignees or [])
    mock_issue.repository.full_name = repo_full_name
    return mock_issue


def _make_search_result(number, body, user_login="contributor"):
    mock_pr = Mock()
    mock_pr.number = number
    mock_pr.user.login = user_login
    mock_pr.body = body
    mock_issue = Mock()
    mock_issue.body = body
    mock_issue.number = number
    mock_issue.user.login = user_login
    mock_issue.as_pull_request.return_value = mock_pr
    return mock_issue


class TestAutoAssignIssuesFromPR:
    def test_success(self, bot_env):
        bot = IssueAssignmentBot()
        issues_by_number = {
            123: _make_issue_with_assignment("testuser"),
            456: _make_issue_with_assignment("testuser"),
        }
        bot_env["repo"].get_issue.side_effect = lambda n: issues_by_number[n]
        assigned = bot.auto_assign_issues_from_pr(
            100, "testuser", "This PR fixes #123 and closes #456"
        )
        assert sorted(assigned) == [123, 456]
        for issue in issues_by_number.values():
            issue.add_to_assignees.assert_called_once_with("testuser")
            issue.create_comment.assert_called_once()
            assert "automatically assigned" in issue.create_comment.call_args[0][0]

    def test_silent_failure_posts_fallback_message(self, bot_env):
        bot = IssueAssignmentBot()
        mock_issue = Mock()
        mock_issue.labels = []
        mock_issue.pull_request = None
        mock_issue.assignees = []
        mock_issue.repository.full_name = "openwisp/openwisp-utils"
        bot_env["repo"].get_issue.return_value = mock_issue
        assigned = bot.auto_assign_issues_from_pr(100, "nonmember", "Fixes #123")
        assert assigned == []
        mock_issue.add_to_assignees.assert_called_once_with("nonmember")
        mock_issue.create_comment.assert_called_once()
        fallback = mock_issue.create_comment.call_args[0][0]
        assert "@nonmember" in fallback
        assert "openwisp-companion assign" in fallback
        assert "automatically assigned" not in fallback

    def test_verification_error_stays_silent(self, bot_env):
        bot = IssueAssignmentBot()
        initial_issue = Mock()
        initial_issue.labels = []
        initial_issue.pull_request = None
        initial_issue.assignees = []
        initial_issue.repository.full_name = "openwisp/openwisp-utils"
        transient = GithubException(500, "transient", headers=None)
        bot_env["repo"].get_issue.side_effect = [
            initial_issue,
            transient,
            transient,
        ]
        assigned = bot.auto_assign_issues_from_pr(100, "someuser", "Fixes #123")
        assert assigned == []
        initial_issue.add_to_assignees.assert_called_once_with("someuser")
        initial_issue.create_comment.assert_not_called()

    def test_verification_retries_on_transient_lag(self, bot_env):
        bot = IssueAssignmentBot()
        initial_issue = Mock()
        initial_issue.labels = []
        initial_issue.pull_request = None
        initial_issue.assignees = []
        initial_issue.repository.full_name = "openwisp/openwisp-utils"
        stale_issue = Mock()
        stale_issue.assignees = []
        fresh_assignee = Mock()
        fresh_assignee.login = "someuser"
        fresh_issue = Mock()
        fresh_issue.assignees = [fresh_assignee]
        bot_env["repo"].get_issue.side_effect = [
            initial_issue,
            stale_issue,
            fresh_issue,
        ]
        assigned = bot.auto_assign_issues_from_pr(100, "someuser", "Fixes #123")
        assert assigned == [123]
        initial_issue.create_comment.assert_called_once()
        assert "automatically assigned" in initial_issue.create_comment.call_args[0][0]

    def test_skip_closed_issue_in_pr_flow(self, bot_env):
        bot = IssueAssignmentBot()
        mock_issue = Mock()
        mock_issue.labels = []
        mock_issue.pull_request = None
        mock_issue.state = "closed"
        mock_issue.assignees = []
        mock_issue.repository.full_name = "openwisp/openwisp-utils"
        bot_env["repo"].get_issue.return_value = mock_issue
        assigned = bot.auto_assign_issues_from_pr(100, "someuser", "Fixes #123")
        assert assigned == []
        mock_issue.add_to_assignees.assert_not_called()
        mock_issue.create_comment.assert_not_called()

    def test_verification_recovers_then_reports_failure(self, bot_env):
        bot = IssueAssignmentBot()
        initial_issue = Mock()
        initial_issue.labels = []
        initial_issue.pull_request = None
        initial_issue.assignees = []
        initial_issue.repository.full_name = "openwisp/openwisp-utils"
        stale_issue = Mock()
        stale_issue.assignees = []
        bot_env["repo"].get_issue.side_effect = [
            initial_issue,
            GithubException(500, "transient", headers=None),
            stale_issue,
        ]
        assigned = bot.auto_assign_issues_from_pr(100, "someuser", "Fixes #123")
        assert assigned == []
        initial_issue.create_comment.assert_called_once()
        fallback = initial_issue.create_comment.call_args[0][0]
        assert "openwisp-companion assign" in fallback

    def test_verification_catches_non_github_exception(self, bot_env):
        bot = IssueAssignmentBot()
        initial_issue = Mock()
        initial_issue.labels = []
        initial_issue.pull_request = None
        initial_issue.assignees = []
        initial_issue.repository.full_name = "openwisp/openwisp-utils"
        bot_env["repo"].get_issue.side_effect = [
            initial_issue,
            RuntimeError("network dropped"),
            RuntimeError("network dropped"),
        ]
        assigned = bot.auto_assign_issues_from_pr(100, "someuser", "Fixes #123")
        assert assigned == []
        initial_issue.create_comment.assert_not_called()

    def test_verification_first_fetch_authoritative(self, bot_env):
        bot = IssueAssignmentBot()
        initial_issue = Mock()
        initial_issue.labels = []
        initial_issue.pull_request = None
        initial_issue.assignees = []
        initial_issue.repository.full_name = "openwisp/openwisp-utils"
        stale_issue = Mock()
        stale_issue.assignees = []
        bot_env["repo"].get_issue.side_effect = [
            initial_issue,
            stale_issue,
            RuntimeError("network dropped"),
        ]
        assigned = bot.auto_assign_issues_from_pr(100, "someuser", "Fixes #123")
        assert assigned == []
        initial_issue.create_comment.assert_called_once()
        fallback = initial_issue.create_comment.call_args[0][0]
        assert "openwisp-companion assign" in fallback

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
        mock_issue.repository.full_name = "openwisp/openwisp-utils"
        bot_env["repo"].get_issue.return_value = mock_issue
        assigned = bot.auto_assign_issues_from_pr(100, "testuser", "Fixes #123")
        assert len(assigned) == 0
        mock_issue.add_to_assignees.assert_not_called()

    def test_rate_limiting(self, bot_env):
        bot = IssueAssignmentBot()
        issue_refs = " ".join([f"fixes #{i}" for i in range(1, 16)])
        issues_by_number = {
            n: _make_issue_with_assignment("testuser") for n in range(1, 16)
        }
        bot_env["repo"].get_issue.side_effect = lambda n: issues_by_number[n]
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

    def test_unassign_matches_case_insensitively(self, bot_env):
        bot = IssueAssignmentBot()
        mock_assignee = Mock()
        mock_assignee.login = "TestUser"
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.assignees = [mock_assignee]
        mock_issue.repository.full_name = "openwisp/openwisp-utils"
        bot_env["repo"].get_issue.return_value = mock_issue
        unassigned = bot.unassign_issues_from_pr("Fixes #123", "testuser")
        assert 123 in unassigned
        mock_issue.remove_from_assignees.assert_called_once_with("testuser")


class TestHandleIssueComment:
    def test_assignment_request(self, bot_env):
        bot = IssueAssignmentBot()
        bot.load_event_payload(
            {
                "issue": {"number": 123, "pull_request": None},
                "comment": {
                    "body": "assign me please",
                    "user": {"login": "testuser"},
                },
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
                        "url": ("https://api.github.com" "/repos/test/pulls/123")
                    },
                },
                "comment": {
                    "body": "assign me please",
                    "user": {"login": "testuser"},
                },
            }
        )
        assert bot.handle_issue_comment()

    def test_non_assignment_comment(self, bot_env):
        bot = IssueAssignmentBot()
        bot.load_event_payload(
            {
                "issue": {"number": 123, "pull_request": None},
                "comment": {
                    "body": "looks good!",
                    "user": {"login": "testuser"},
                },
            }
        )
        assert bot.handle_issue_comment()

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
        mock_issue = _make_issue_with_assignment("testuser")
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
        mock_issue = _make_issue_with_assignment("testuser")
        bot_env["repo"].get_issue.return_value = mock_issue
        assert bot.handle_pull_request()

    def test_closed(self, bot_env):
        bot = IssueAssignmentBot()
        bot.load_event_payload(
            {
                "action": "closed",
                "pull_request": {
                    "number": 100,
                    "user": {"login": "testuser"},
                    "body": "Fixes #123",
                },
            }
        )
        mock_assignee = Mock()
        mock_assignee.login = "testuser"
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.assignees = [mock_assignee]
        mock_issue.repository.full_name = "openwisp/openwisp-utils"
        bot_env["repo"].get_issue.return_value = mock_issue
        assert bot.handle_pull_request()
        mock_issue.remove_from_assignees.assert_called_once_with("testuser")

    def test_merged_does_not_unassign(self, bot_env):
        bot = IssueAssignmentBot()
        bot.load_event_payload(
            {
                "action": "closed",
                "pull_request": {
                    "number": 100,
                    "user": {"login": "testuser"},
                    "body": "Fixes #123",
                    "merged": True,
                },
            }
        )
        assert bot.handle_pull_request()
        bot_env["repo"].get_issue.assert_not_called()

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
        assert bot.handle_pull_request()


class TestRun:
    def test_issue_comment_event(self, bot_env):
        bot = IssueAssignmentBot()
        bot.event_name = "issue_comment"
        bot.load_event_payload(
            {
                "issue": {"number": 123, "pull_request": None},
                "comment": {
                    "body": "assign me",
                    "user": {"login": "testuser"},
                },
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
        mock_issue = _make_issue_with_assignment("testuser")
        bot_env["repo"].get_issue.return_value = mock_issue
        assert bot.run()

    def test_unsupported_event(self, bot_env):
        bot = IssueAssignmentBot()
        bot.event_name = "push"
        assert bot.run()

    def test_no_github_client(self, bot_env):
        bot = IssueAssignmentBot()
        bot.github = None
        bot.repo = None
        assert not bot.run()


class TestIsBotAssignCommand:
    @pytest.mark.parametrize(
        "comment",
        [
            "@openwisp-companion assign",
            "@openwisp-companion assign me",
            "hey @openwisp-companion assign please",
            "@OpenWISP-Companion ASSIGN",
        ],
    )
    def test_positive_cases(self, comment, bot_env):
        bot = IssueAssignmentBot()
        assert bot.is_bot_assign_command(comment)

    @pytest.mark.parametrize(
        "comment",
        [
            "assign me please",
            "@openwisp-companion hello",
            "@someone-else assign",
            "assign @openwisp-companion",
            "@openwisp-companion assignee",
            "@openwisp-companion assigning",
            "@openwisp-companion assigns",
            "@openwisp-companion assignment",
            "",
            None,
        ],
    )
    def test_negative_cases(self, comment, bot_env):
        bot = IssueAssignmentBot()
        assert not bot.is_bot_assign_command(comment)


class TestHandleBotAssignRequest:
    def test_assigns_when_open_pr_exists(self, bot_env):
        bot = IssueAssignmentBot()
        mock_issue = _make_issue_with_assignment("contributor")
        bot_env["repo"].get_issue.return_value = mock_issue
        bot_env["github"].search_issues.return_value = [
            _make_search_result(200, "Fixes #123")
        ]
        assert bot.handle_bot_assign_request(123, "contributor")
        mock_issue.add_to_assignees.assert_called_once_with("contributor")
        mock_issue.create_comment.assert_called_once()
        comment = mock_issue.create_comment.call_args[0][0]
        assert "assigned to @contributor" in comment
        assert "PR #200" in comment

    def test_replies_when_no_open_pr(self, bot_env):
        bot = IssueAssignmentBot()
        mock_issue = _make_bot_assign_issue()
        bot_env["repo"].get_issue.return_value = mock_issue
        bot_env["github"].search_issues.return_value = []
        assert bot.handle_bot_assign_request(123, "contributor")
        mock_issue.add_to_assignees.assert_not_called()
        mock_issue.create_comment.assert_called_once()
        comment_text = mock_issue.create_comment.call_args[0][0]
        assert "could not find an open PR" in comment_text

    def test_stays_silent_when_search_errors(self, bot_env):
        bot = IssueAssignmentBot()
        mock_issue = _make_bot_assign_issue()
        bot_env["repo"].get_issue.return_value = mock_issue
        bot_env["github"].search_issues.side_effect = GithubException(
            500, "transient", headers=None
        )
        assert bot.handle_bot_assign_request(123, "contributor")
        mock_issue.add_to_assignees.assert_not_called()
        mock_issue.create_comment.assert_not_called()

    def test_skip_if_already_assigned(self, bot_env):
        bot = IssueAssignmentBot()
        existing = Mock()
        existing.login = "contributor"
        mock_issue = _make_bot_assign_issue(assignees=[existing])
        bot_env["repo"].get_issue.return_value = mock_issue
        assert bot.handle_bot_assign_request(123, "contributor")
        mock_issue.add_to_assignees.assert_not_called()
        mock_issue.create_comment.assert_not_called()

    def test_skip_if_already_assigned_case_insensitive(self, bot_env):
        bot = IssueAssignmentBot()
        existing = Mock()
        existing.login = "Contributor"
        mock_issue = _make_bot_assign_issue(assignees=[existing])
        bot_env["repo"].get_issue.return_value = mock_issue
        assert bot.handle_bot_assign_request(123, "contributor")
        mock_issue.add_to_assignees.assert_not_called()

    def test_skip_if_issue_closed(self, bot_env):
        bot = IssueAssignmentBot()
        mock_issue = _make_bot_assign_issue(state="closed")
        bot_env["repo"].get_issue.return_value = mock_issue
        assert bot.handle_bot_assign_request(123, "contributor")
        mock_issue.add_to_assignees.assert_not_called()
        mock_issue.create_comment.assert_not_called()

    def test_skip_if_cross_repo_issue(self, bot_env):
        bot = IssueAssignmentBot()
        mock_issue = _make_bot_assign_issue(repo_full_name="other-org/other-repo")
        bot_env["repo"].get_issue.return_value = mock_issue
        assert bot.handle_bot_assign_request(123, "contributor")
        mock_issue.add_to_assignees.assert_not_called()
        mock_issue.create_comment.assert_not_called()

    def test_matches_pr_author_case_insensitively(self, bot_env):
        bot = IssueAssignmentBot()
        mock_issue = _make_issue_with_assignment("contributor")
        bot_env["repo"].get_issue.return_value = mock_issue
        bot_env["github"].search_issues.return_value = [
            _make_search_result(200, "Fixes #123", user_login="Contributor")
        ]
        assert bot.handle_bot_assign_request(123, "contributor")
        mock_issue.add_to_assignees.assert_called_once_with("contributor")

    def test_skip_if_target_is_pr(self, bot_env):
        bot = IssueAssignmentBot()
        mock_issue = _make_bot_assign_issue(pull_request={"url": "x"})
        bot_env["repo"].get_issue.return_value = mock_issue
        assert bot.handle_bot_assign_request(123, "contributor")
        mock_issue.add_to_assignees.assert_not_called()

    def test_still_silently_rejected(self, bot_env):
        bot = IssueAssignmentBot()
        mock_issue = _make_bot_assign_issue()
        bot_env["repo"].get_issue.return_value = mock_issue
        bot_env["github"].search_issues.return_value = [
            _make_search_result(200, "Fixes #123")
        ]
        assert bot.handle_bot_assign_request(123, "contributor")
        mock_issue.add_to_assignees.assert_called_once_with("contributor")
        comment_text = mock_issue.create_comment.call_args[0][0]
        assert "manually" in comment_text

    def test_accepts_related_to_pr_reference(self, bot_env):
        bot = IssueAssignmentBot()
        mock_issue = _make_issue_with_assignment("contributor")
        bot_env["repo"].get_issue.return_value = mock_issue
        bot_env["github"].search_issues.return_value = [
            _make_search_result(200, "Related to #123")
        ]
        assert bot.handle_bot_assign_request(123, "contributor")
        mock_issue.add_to_assignees.assert_called_once_with("contributor")


class TestHandleIssueCommentBotCommand:
    def test_bot_command_triggers_assign(self, bot_env):
        bot = IssueAssignmentBot()
        bot.load_event_payload(
            {
                "issue": {"number": 123, "pull_request": None},
                "comment": {
                    "body": "@openwisp-companion assign",
                    "user": {"login": "contributor"},
                },
            }
        )
        mock_issue = _make_issue_with_assignment("contributor")
        bot_env["repo"].get_issue.return_value = mock_issue
        bot_env["github"].search_issues.return_value = [
            _make_search_result(200, "Fixes #123")
        ]
        assert bot.handle_issue_comment()
        mock_issue.add_to_assignees.assert_called_once_with("contributor")

    def test_ignores_bot_own_comments(self, bot_env):
        bot = IssueAssignmentBot()
        bot.load_event_payload(
            {
                "issue": {"number": 123, "pull_request": None},
                "comment": {
                    "body": "@openwisp-companion assign",
                    "user": {"login": "openwisp-companion[bot]"},
                },
            }
        )
        assert bot.handle_issue_comment()
        bot_env["repo"].get_issue.assert_not_called()

    def test_ignores_comments_with_bot_type(self, bot_env):
        bot = IssueAssignmentBot()
        bot.load_event_payload(
            {
                "issue": {"number": 123, "pull_request": None},
                "comment": {
                    "body": "@openwisp-companion assign",
                    "user": {"login": "some-other-bot[bot]", "type": "Bot"},
                },
            }
        )
        assert bot.handle_issue_comment()
        bot_env["repo"].get_issue.assert_not_called()

    def test_ignores_comments_from_github_app(self, bot_env):
        bot = IssueAssignmentBot()
        bot.load_event_payload(
            {
                "issue": {"number": 123, "pull_request": None},
                "comment": {
                    "body": "@openwisp-companion assign",
                    "user": {"login": "someuser"},
                    "performed_via_github_app": {"id": 1},
                },
            }
        )
        assert bot.handle_issue_comment()
        bot_env["repo"].get_issue.assert_not_called()

    def test_ignores_edited_comments(self, bot_env):
        bot = IssueAssignmentBot()
        bot.load_event_payload(
            {
                "action": "edited",
                "issue": {"number": 123, "pull_request": None},
                "comment": {
                    "body": "@openwisp-companion assign",
                    "user": {"login": "contributor"},
                },
            }
        )
        assert bot.handle_issue_comment()
        bot_env["repo"].get_issue.assert_not_called()

    def test_bot_fallback_message_does_not_self_trigger(self, bot_env):
        bot = IssueAssignmentBot()
        fallback = bot._cannot_auto_assign_message("contributor", 200)
        bot.load_event_payload(
            {
                "action": "created",
                "issue": {"number": 123, "pull_request": None},
                "comment": {
                    "body": fallback,
                    "user": {
                        "login": "openwisp-companion[bot]",
                        "type": "Bot",
                    },
                },
            }
        )
        assert bot.handle_issue_comment()
        bot_env["repo"].get_issue.assert_not_called()
