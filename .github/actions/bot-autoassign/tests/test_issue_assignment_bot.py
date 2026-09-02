import os
import sys
from unittest.mock import MagicMock, Mock, patch

# Add the parent directory to path for importing bot modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from github import GithubException  # noqa: E402

try:
    from issue_assignment_bot import IssueAssignmentBot  # noqa: E402
    from utils import extract_all_linked_issues  # noqa: E402
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
    monkeypatch.setenv("VALIDATION_GITHUB_TOKEN", "test_validation_token")
    monkeypatch.setenv("REPOSITORY", "openwisp/openwisp-utils")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "issue_comment")
    monkeypatch.setattr("utils.time.sleep", lambda _seconds: None)
    mock_github = Mock()
    mock_repo = Mock()
    mock_github.get_repo.return_value = mock_repo

    mock_github_validation = Mock()
    mock_repo_validation = Mock()
    mock_github_validation.get_repo.return_value = mock_repo_validation

    def github_side_effect(token):
        if token == "test_token":
            return mock_github
        if token == "test_validation_token":
            return mock_github_validation
        return Mock()

    with patch("base.Github") as mock_github_cls:
        mock_github_cls.side_effect = github_side_effect
        yield {
            "github_cls": mock_github_cls,
            "github": mock_github,
            "repo": mock_repo,
            "github_validation": mock_github_validation,
            "repo_validation": mock_repo_validation,
        }


class TestInit:
    def test_init_success(self, bot_env):
        bot = IssueAssignmentBot()
        assert bot.github_token == "test_token"
        assert bot.github_validation_token == "test_validation_token"
        assert bot.repository_name == "openwisp/openwisp-utils"
        assert bot.event_name == "issue_comment"
        bot_env["github_cls"].assert_any_call("test_token")
        bot_env["github_cls"].assert_any_call("test_validation_token")

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
        bot.validate_issue = Mock(return_value=True)
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

    def test_replies_to_unvalidated_issue(self, bot_env):
        bot = IssueAssignmentBot()
        bot.validate_issue = Mock(return_value=False)
        mock_issue = Mock()
        mock_issue.labels = []
        mock_issue.title = "Test issue"
        mock_issue.body = "Test body"
        bot_env["repo"].get_issue.return_value = mock_issue
        assert bot.respond_to_assignment_request(123, "testuser")
        comment_text = mock_issue.create_comment.call_args[0][0]
        assert "not been validated" in comment_text
        assert "OpenWISP Contributor's Board" in comment_text
        assert "closed automatically" in comment_text
        assert "Please refer to the [OpenWISP Contributing Guidelines]" in comment_text

    def test_unvalidated_messages_share_requirements(self, bot_env):
        bot = IssueAssignmentBot()
        issue_comment = bot.get_unvalidated_issue_assignment_request_comment("testuser")
        pr_comment = bot.get_invalid_unvalidated_issue_comment("testuser")
        assert "This pull request has been flagged as invalid" in pr_comment
        for comment in (issue_comment, pr_comment):
            assert "An issue is considered validated" in comment
            assert "OpenWISP Contributor's Board" in comment
            assert "Please refer to the [OpenWISP Contributing Guidelines]" in comment
            assert "OpenWISP Anti AI Spam Policy" in comment
            assert "OpenWISP dev chatroom" in comment
            assert "Pull requests from external contributors" in comment

    def test_stays_silent_when_issue_validation_fails(self, bot_env):
        bot = IssueAssignmentBot()
        bot.validate_issue = Mock(side_effect=GithubException(500, "error", None))
        mock_issue = Mock()
        mock_issue.labels = []
        mock_issue.title = "Test issue"
        mock_issue.body = "Test body"
        bot_env["repo"].get_issue.return_value = mock_issue
        assert not bot.respond_to_assignment_request(123, "testuser")
        mock_issue.create_comment.assert_not_called()

    def test_success_bug_detected(self, bot_env):
        bot = IssueAssignmentBot()
        bot.validate_issue = Mock(return_value=True)
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
        bot.validate_issue = Mock(return_value=True)
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
        mock_issue.state = "open"
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
        bot.validate_pr_issues = MagicMock(return_value=True)
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
        bot.validate_pr_issues = MagicMock(return_value=True)
        assert bot.handle_pull_request()

    def test_skips_auto_assign_if_invalid(self, bot_env):
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
        bot.validate_pr_issues = MagicMock(return_value=False)
        assert bot.handle_pull_request()
        mock_issue.add_to_assignees.assert_not_called()

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

    def test_respects_custom_bot_username(self, monkeypatch, bot_env):
        monkeypatch.setenv("BOT_USERNAME", "custom-bot")
        bot = IssueAssignmentBot()
        assert bot.is_bot_assign_command("@custom-bot assign")
        assert not bot.is_bot_assign_command("@openwisp-companion assign")


class TestHandleBotAssignRequest:
    @pytest.fixture(autouse=True)
    def valid_pr(self, monkeypatch):
        monkeypatch.setattr(
            IssueAssignmentBot, "is_pr_author_exempt", Mock(return_value=False)
        )
        monkeypatch.setattr(
            IssueAssignmentBot, "validate_issue", Mock(return_value=True)
        )

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

    def test_ignores_invalid_pr(self, bot_env):
        bot = IssueAssignmentBot()
        bot.is_pr_author_exempt = Mock(return_value=False)
        bot.validate_issue = Mock(return_value=False)
        mock_issue = _make_issue_with_assignment("contributor")
        bot_env["repo"].get_issue.return_value = mock_issue
        mock_pr = _make_search_result(200, "Fixes #123")
        bot_env["github"].search_issues.return_value = [mock_pr]
        assert bot.handle_bot_assign_request(123, "contributor")
        bot.validate_issue.assert_called_once_with("openwisp", "openwisp-utils", 123)
        mock_issue.add_to_assignees.assert_not_called()
        mock_issue.create_comment.assert_not_called()

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
        bot.is_pr_author_exempt = Mock(return_value=False)
        bot.validate_issue = Mock(return_value=True)
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


class TestExtractAllLinkedIssues:
    @pytest.mark.parametrize(
        "pr_body,expected",
        [
            ("Fixes #123", [("openwisp", "openwisp-utils", 123)]),
            (
                "Fixes openwisp/openwisp-utils#709",
                [("openwisp", "openwisp-utils", 709)],
            ),
            (
                "Fixes https://github.com/openwisp/openwisp-utils/issues/709",
                [("openwisp", "openwisp-utils", 709)],
            ),
            ("Related to #99", [("openwisp", "openwisp-utils", 99)]),
            (
                "Closes #456 and resolves #789",
                [
                    ("openwisp", "openwisp-utils", 456),
                    ("openwisp", "openwisp-utils", 789),
                ],
            ),
            ("Closes openwisp-utils#42", []),
            ("", []),
            (None, []),
        ],
    )
    def test_extract_all_linked_issues(self, pr_body, expected, bot_env):
        assert extract_all_linked_issues(pr_body, "openwisp/openwisp-utils") == expected


class TestPRValidation:
    def assert_label(self, pr):
        pr.add_to_labels.assert_called_once_with("ai-review")
        pr.create_issue_comment.assert_not_called()

    def test_get_issue_projects_success(self, bot_env):
        bot = IssueAssignmentBot()
        bot.github_validation.requester.graphql_query.return_value = (
            {},
            {
                "data": {
                    "repository": {
                        "issue": {
                            "projectItems": {
                                "nodes": [
                                    {"project": {"id": "PVT_kwDOABGNI84Amkl7"}},
                                    {"project": {"id": "SOME_OTHER_ID"}},
                                ]
                            }
                        }
                    }
                }
            },
        )
        projects = bot.get_issue_projects("openwisp", "openwisp-utils", 123)
        assert projects == ["PVT_kwDOABGNI84Amkl7", "SOME_OTHER_ID"]
        bot.github_validation.requester.graphql_query.assert_called_once()

    def test_get_issue_projects_single_project(self, bot_env):
        bot = IssueAssignmentBot()
        bot.github_validation.requester.graphql_query.return_value = (
            {},
            {
                "data": {
                    "repository": {
                        "issue": {
                            "projectItems": {
                                "nodes": [
                                    {"project": {"id": "CLASSIC_PROJECT_ID"}},
                                ]
                            }
                        }
                    }
                }
            },
        )
        projects = bot.get_issue_projects("openwisp", "openwisp-utils", 123)
        assert projects == ["CLASSIC_PROJECT_ID"]

    def test_get_issue_projects_graphql_error(self, bot_env):
        bot = IssueAssignmentBot()
        bot.github_validation.requester.graphql_query.side_effect = GithubException(
            400, {"errors": [{"message": "Some error"}]}, {}
        )
        with pytest.raises(GithubException):
            bot.get_issue_projects("openwisp", "openwisp-utils", 123)

    def test_get_issue_projects_graphql_payload_error(self, bot_env):
        bot = IssueAssignmentBot()
        bot.github_validation.requester.graphql_query.return_value = (
            {},
            {"errors": [{"message": "Insufficient scopes"}]},
        )
        with pytest.raises(ValueError, match="GraphQL API Permission Error"):
            bot.get_issue_projects("openwisp", "openwisp-utils", 123)

    def test_get_issue_projects_pagination(self, bot_env):
        bot = IssueAssignmentBot()
        bot.github_validation.requester.graphql_query.side_effect = [
            (
                {},
                {
                    "data": {
                        "repository": {
                            "issue": {
                                "projectItems": {
                                    "nodes": [{"project": {"id": "PAGE1_ID"}}],
                                    "pageInfo": {
                                        "hasNextPage": True,
                                        "endCursor": "cursor123",
                                    },
                                }
                            }
                        }
                    }
                },
            ),
            (
                {},
                {
                    "data": {
                        "repository": {
                            "issue": {
                                "projectItems": {
                                    "nodes": [{"project": {"id": "PAGE2_ID"}}],
                                    "pageInfo": {
                                        "hasNextPage": False,
                                        "endCursor": None,
                                    },
                                }
                            }
                        }
                    }
                },
            ),
        ]
        projects = bot.get_issue_projects("openwisp", "openwisp-utils", 123)
        assert projects == ["PAGE1_ID", "PAGE2_ID"]
        assert bot.github_validation.requester.graphql_query.call_count == 2

    def test_get_issue_projects_null_project_items(self, bot_env):
        bot = IssueAssignmentBot()
        bot.github_validation.requester.graphql_query.return_value = (
            {},
            {
                "data": {
                    "repository": {
                        "issue": {
                            "projectItems": None,
                        }
                    }
                }
            },
        )
        with pytest.raises(ValueError, match="could not read project assignments"):
            bot.get_issue_projects("openwisp", "openwisp-utils", 123)

    def test_get_issue_projects_null_issue(self, bot_env):
        bot = IssueAssignmentBot()
        bot.github_validation.requester.graphql_query.return_value = (
            {},
            {"data": {"repository": {"issue": None}}},
        )
        with pytest.raises(ValueError, match="could not access issue"):
            bot.get_issue_projects("openwisp", "openwisp-utils", 123)

    def test_validate_pr_issues_excluded_author(self, bot_env):
        bot = IssueAssignmentBot()
        mock_pr = Mock()
        mock_pr.user.login = "dependabot[bot]"
        assert bot.validate_pr_issues(mock_pr)

    def test_validate_pr_issues_exempt_association(self, bot_env):
        bot = IssueAssignmentBot()
        mock_pr = Mock()
        mock_pr.user.login = "some-member"
        mock_pr.author_association = "MEMBER"
        assert bot.validate_pr_issues(mock_pr)

    def test_validate_pr_issues_exempt_bot_author(self, bot_env):
        bot = IssueAssignmentBot()
        mock_pr = Mock()
        mock_pr.user.login = "openwisp-companion[bot]"
        mock_pr.author_association = "NONE"
        mock_pr.body = "Backport of #504 to `1.2`."
        assert bot.validate_pr_issues(mock_pr)
        bot_env["github_validation"].get_repo.assert_not_called()
        bot.github_validation.requester.graphql_query.assert_not_called()
        bot_env["repo_validation"].get_issue.assert_not_called()

    def test_validate_pr_issues_no_issues(self, bot_env):
        bot = IssueAssignmentBot()
        mock_pr = Mock()
        mock_pr.user.login = "external-contributor"
        mock_pr.author_association = "NONE"
        mock_pr.body = "No references here"
        assert not bot.validate_pr_issues(mock_pr)

    def test_validate_pr_issues_limits_linked_issues(self, bot_env):
        bot = IssueAssignmentBot()
        mock_pr = Mock()
        mock_pr.user.login = "external-contributor"
        mock_pr.author_association = "NONE"
        mock_pr.body = " ".join(f"Fixes #{number}" for number in range(1, 12))
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.state = "open"
        mock_issue.labels = []
        bot_env["repo_validation"].get_issue.return_value = mock_issue
        assert not bot.validate_pr_issues(mock_pr)
        assert bot_env["repo_validation"].get_issue.call_count == 10

    def test_validate_pr_issues_cross_org_issue(self, bot_env):
        bot = IssueAssignmentBot()
        mock_pr = Mock()
        mock_pr.user.login = "external-contributor"
        mock_pr.author_association = "NONE"
        mock_pr.body = "Fixes otherorg/repo#12"
        assert not bot.validate_pr_issues(mock_pr)

    def test_validate_pr_issues_is_pr(self, bot_env):
        bot = IssueAssignmentBot()
        mock_pr = Mock()
        mock_pr.user.login = "external-contributor"
        mock_pr.author_association = "NONE"
        mock_pr.body = "Fixes #12"
        mock_issue = Mock()
        mock_issue.pull_request = {"url": "..."}
        bot_env["repo_validation"].get_issue.return_value = mock_issue
        assert not bot.validate_pr_issues(mock_pr)

    def test_validate_pr_issues_closed(self, bot_env):
        bot = IssueAssignmentBot()
        mock_pr = Mock()
        mock_pr.user.login = "external-contributor"
        mock_pr.author_association = "NONE"
        mock_pr.body = "Fixes #12"
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.state = "closed"
        bot_env["repo_validation"].get_issue.return_value = mock_issue
        assert not bot.validate_pr_issues(mock_pr)

    def test_validate_pr_issues_invalid_labels(self, bot_env):
        bot = IssueAssignmentBot()
        mock_pr = Mock()
        mock_pr.user.login = "external-contributor"
        mock_pr.author_association = "NONE"
        mock_pr.body = "Fixes #12"
        # Test case 1: No labels
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.state = "open"
        mock_issue.labels = []
        bot_env["repo_validation"].get_issue.return_value = mock_issue
        assert not bot.validate_pr_issues(mock_pr)
        # Test case 2: Has wontfix/invalid labels
        label_wontfix = Mock()
        label_wontfix.name = "wontfix"
        mock_issue.labels = [label_wontfix]
        assert not bot.validate_pr_issues(mock_pr)
        # Test case 3: Has a mix of valid and invalid/wontfix labels
        label_bug = Mock()
        label_bug.name = "bug"
        mock_issue.labels = [label_bug, label_wontfix]
        assert not bot.validate_pr_issues(mock_pr)

    def test_validate_pr_issues_not_in_project(self, bot_env):
        bot = IssueAssignmentBot()
        mock_pr = Mock()
        mock_pr.user.login = "external-contributor"
        mock_pr.author_association = "NONE"
        mock_pr.body = "Fixes #12"
        label_bug = Mock()
        label_bug.name = "bug"
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.state = "open"
        mock_issue.labels = [label_bug]
        bot_env["repo_validation"].get_issue.return_value = mock_issue
        with patch.object(
            bot, "get_issue_projects", return_value=["Some Other Project"]
        ):
            assert not bot.validate_pr_issues(mock_pr)

    def test_validate_pr_issues_fully_valid(self, bot_env):
        bot = IssueAssignmentBot()
        mock_pr = Mock()
        mock_pr.user.login = "external-contributor"
        mock_pr.author_association = "NONE"
        mock_pr.body = "Fixes #12"
        label_bug = Mock()
        label_bug.name = "bug"
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.state = "open"
        mock_issue.labels = [label_bug]
        bot_env["repo_validation"].get_issue.return_value = mock_issue
        with patch.object(
            bot, "get_issue_projects", return_value=["PVT_kwDOABGNI84Amkl7"]
        ):
            assert bot.validate_pr_issues(mock_pr)

    def test_client_segregation_mutations_vs_validation(self, bot_env):
        """Proves cross-repository validation uses the read-only validation client,
        while all mutations use the repository-scoped write client.
        """
        bot = IssueAssignmentBot()
        bot.event_name = "pull_request_target"
        # Mocks for validation (reads)
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.state = "open"
        label_bug = Mock()
        label_bug.name = "bug"
        mock_issue.labels = [label_bug]
        bot_env["repo_validation"].get_issue.return_value = mock_issue
        bot.github_validation.requester.graphql_query.return_value = (
            {},
            {
                "data": {
                    "repository": {
                        "issue": {
                            "projectItems": {
                                "nodes": [{"project": {"id": "PVT_kwDOABGNI84Amkl7"}}]
                            }
                        }
                    }
                }
            },
        )
        # Mocks for mutations (writes)
        mock_pr = Mock()
        mock_pr.number = 12
        mock_pr.user.login = "external-contributor"
        mock_pr.author_association = "NONE"
        mock_pr.body = "Fixes #123"
        invalid_label = Mock()
        invalid_label.name = "invalid"
        mock_pr.labels = [invalid_label]
        bot_env["repo"].get_pull.return_value = mock_pr
        # Execute handler
        bot.load_event_payload(
            {
                "action": "opened",
                "pull_request": {
                    "number": 12,
                    "merged": False,
                    "user": {"login": "external-contributor"},
                    "body": "Fixes #123",
                },
            }
        )
        bot.handle_pull_request()
        # Assert Reads used VALIDATION client
        bot_env["github_validation"].get_repo.assert_any_call("openwisp/openwisp-utils")
        bot_env["repo_validation"].get_issue.assert_called_once_with(123)
        bot.github_validation.requester.graphql_query.assert_called_once()

        # Assert Writes used WRITE client (bot_env["repo"] / bot_env["github"])
        bot_env["repo"].get_pull.assert_called_once_with(12)
        mock_pr.remove_from_labels.assert_called_once_with("invalid")
        # Ensure validation client is strictly read-only in this flow (no label/edit calls)
        assert (
            not hasattr(bot_env["repo_validation"], "remove_from_labels")
            or not bot_env["repo_validation"].remove_from_labels.called
        )

    def test_handle_pull_request_invalid_label_and_comment(self, bot_env):
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
        mock_pr_obj = Mock()
        mock_pr_obj.labels = []
        bot_env["repo"].get_pull.return_value = mock_pr_obj
        with patch.object(bot, "validate_pr_issues", return_value=False), patch.object(
            bot, "has_bot_comment", return_value=False
        ):
            assert bot.handle_pull_request()
            mock_pr_obj.add_to_labels.assert_called_once_with("invalid")
            mock_pr_obj.create_issue_comment.assert_called_once()
            assert (
                "invalid_unvalidated_issue"
                in mock_pr_obj.create_issue_comment.call_args[0][0].lower()
            )

    def test_handle_pull_request_valid_removes_label(self, bot_env):
        bot = IssueAssignmentBot()
        bot.event_name = "pull_request_target"
        bot.load_event_payload(
            {
                "action": "edited",
                "pull_request": {
                    "number": 100,
                    "user": {"login": "testuser"},
                    "body": "Fixes #123",
                },
            }
        )
        mock_label = Mock()
        mock_label.name = "invalid"
        mock_pr_obj = Mock()
        mock_pr_obj.labels = [mock_label]
        bot_env["repo"].get_pull.return_value = mock_pr_obj
        with patch.object(bot, "validate_pr_issues", return_value=True):
            assert bot.handle_pull_request()
            mock_pr_obj.remove_from_labels.assert_called_once_with("invalid")
            self.assert_label(mock_pr_obj)

    def test_adds_label(self, bot_env):
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
        mock_pr_obj = Mock()
        mock_pr_obj.labels = []
        bot_env["repo"].get_pull.return_value = mock_pr_obj
        with patch.object(bot, "validate_pr_issues", return_value=True):
            assert bot.handle_pull_request()
            self.assert_label(mock_pr_obj)

    @pytest.mark.parametrize(
        "author,title",
        [
            ("dependabot[bot]", "Bump a dependency"),
            ("testuser", "[release] Version 1.3.1"),
            ("testuser", "[backport] Fixed regression"),
        ],
    )
    def test_skips_excluded_prs(self, author, title, bot_env):
        bot = IssueAssignmentBot()
        bot.event_name = "pull_request_target"
        bot.load_event_payload(
            {
                "action": "opened",
                "pull_request": {
                    "number": 100,
                    "title": title,
                    "user": {"login": author},
                    "body": "Fixes #123",
                },
            }
        )
        mock_pr_obj = Mock()
        mock_pr_obj.labels = []
        bot_env["repo"].get_pull.return_value = mock_pr_obj
        with patch.object(bot, "validate_pr_issues", return_value=True):
            assert bot.handle_pull_request()
            mock_pr_obj.add_to_labels.assert_not_called()

    def test_skips_label_when_labeled(self, bot_env):
        bot = IssueAssignmentBot()
        bot.event_name = "pull_request_target"
        bot.load_event_payload(
            {
                "action": "edited",
                "pull_request": {
                    "number": 100,
                    "user": {"login": "testuser"},
                    "body": "Fixes #123",
                },
            }
        )
        mock_label = Mock()
        mock_label.name = "ai-review"
        mock_pr_obj = Mock()
        mock_pr_obj.labels = [mock_label]
        bot_env["repo"].get_pull.return_value = mock_pr_obj
        with patch.object(bot, "validate_pr_issues", return_value=True):
            assert bot.handle_pull_request()
            mock_pr_obj.create_issue_comment.assert_not_called()
            mock_pr_obj.add_to_labels.assert_not_called()

    def test_workflow_has_members_read_permission(self):
        """Verify that the reusable workflow requests permission-members: read."""
        workflow_path = os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
            ),
            "workflows",
            "reusable-bot-autoassign.yml",
        )
        assert os.path.exists(
            workflow_path
        ), f"Workflow file not found at {workflow_path}"
        in_write_token_step = False
        with_indent = None
        with open(workflow_path, "r") as f:
            for raw_line in f:
                stripped = raw_line.strip()
                if stripped == "- name: Generate repository write token":
                    in_write_token_step = True
                    with_indent = None
                elif in_write_token_step and stripped.startswith("- name:"):
                    in_write_token_step = False
                    with_indent = None
                elif in_write_token_step and stripped == "with:":
                    with_indent = len(raw_line) - len(raw_line.lstrip())
                elif with_indent is not None:
                    current_indent = len(raw_line) - len(raw_line.lstrip())
                    if current_indent <= with_indent:
                        with_indent = None
                    elif stripped == "permission-members: read":
                        return
        pytest.fail("permission-members: read is not requested in write-token step")
