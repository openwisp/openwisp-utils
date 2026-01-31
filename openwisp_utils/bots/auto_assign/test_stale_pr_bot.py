from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

try:
    from .stale_pr_bot import StalePRBot
except ImportError:
    StalePRBot = None

pytestmark = pytest.mark.skipif(
    StalePRBot is None,
    reason="Stale PR bot script not available",
)


@pytest.fixture(autouse=True)
def bot_env(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test_token")
    monkeypatch.setenv("REPOSITORY", "openwisp/openwisp-utils")

    with patch("openwisp_utils.bots.auto_assign.base.Github") as mock_github_cls:
        mock_repo = Mock()
        mock_github_cls.return_value.get_repo.return_value = mock_repo
        yield {
            "github_cls": mock_github_cls,
            "repo": mock_repo,
        }


class TestInit:
    def test_success(self, bot_env):
        bot = StalePRBot()
        assert bot.github_token == "test_token"
        assert bot.repository_name == "openwisp/openwisp-utils"
        bot_env["github_cls"].assert_called_once_with("test_token")

    def test_thresholds(self, bot_env):
        bot = StalePRBot()
        assert bot.DAYS_BEFORE_STALE_WARNING == 7
        assert bot.DAYS_BEFORE_UNASSIGN == 14
        assert bot.DAYS_BEFORE_CLOSE == 60


class TestExtractLinkedIssues:
    @pytest.mark.parametrize(
        "pr_body,expected",
        [
            ("Fixes #123", [123]),
            ("Closes #456 and resolves #789", [456, 789]),
            ("fix #100, close #200, resolve #300", [100, 200, 300]),
            ("This PR fixes #123 and closes #123", [123]),
            ("No issue references here", []),
            ("", []),
            (None, []),
        ],
    )
    def test_extract_linked_issues(self, pr_body, expected, bot_env):
        from .utils import extract_linked_issues

        result = extract_linked_issues(pr_body)
        assert sorted(result) == sorted(expected)


class TestGetLastChangesRequested:
    def test_returns_latest(self, bot_env):
        bot = StalePRBot()
        mock_pr = Mock()
        reviews = [
            Mock(
                state="APPROVED", submitted_at=datetime(2024, 1, 1, tzinfo=timezone.utc)
            ),
            Mock(
                state="CHANGES_REQUESTED",
                submitted_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
            ),
            Mock(
                state="CHANGES_REQUESTED",
                submitted_at=datetime(2024, 1, 3, tzinfo=timezone.utc),
            ),
        ]
        mock_pr.get_reviews.return_value = reviews
        assert bot.get_last_changes_requested(mock_pr) == datetime(
            2024, 1, 3, tzinfo=timezone.utc
        )

    def test_no_changes_requested(self, bot_env):
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.get_reviews.return_value = [
            Mock(state="APPROVED"),
        ]
        assert bot.get_last_changes_requested(mock_pr) is None


class TestGetDaysSinceActivity:
    @patch("openwisp_utils.bots.auto_assign.stale_pr_bot.datetime")
    def test_with_author_commit(self, mock_datetime, bot_env):
        mock_datetime.now.return_value = datetime(2024, 1, 10, tzinfo=timezone.utc)
        # Keep timezone constructor working
        mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)

        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.user.login = "testuser"
        mock_pr.get_issue_comments.return_value = []

        mock_commit = Mock()
        mock_commit.commit.author.date = datetime(2024, 1, 5, tzinfo=timezone.utc)
        mock_commit.author.login = "testuser"
        mock_pr.get_commits.return_value = [mock_commit]

        last_cr = datetime(2024, 1, 1, tzinfo=timezone.utc)
        result = bot.get_days_since_activity(mock_pr, last_cr)
        assert result == 5

    def test_no_last_changes(self, bot_env):
        bot = StalePRBot()
        mock_pr = Mock()
        assert bot.get_days_since_activity(mock_pr, None) == 0


class TestUnassignLinkedIssues:
    def test_success(self, bot_env):
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.body = "Fixes #123"
        mock_pr.user.login = "testuser"

        mock_assignee = Mock()
        mock_assignee.login = "testuser"
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.assignees = [mock_assignee]
        mock_issue.repository.full_name = "openwisp/openwisp-utils"
        bot_env["repo"].get_issue.return_value = mock_issue

        assert bot.unassign_linked_issues(mock_pr) == 1
        mock_issue.remove_from_assignees.assert_called_once_with("testuser")

    def test_skip_cross_repo(self, bot_env):
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.body = "Fixes #123"
        mock_pr.user.login = "testuser"

        mock_assignee = Mock()
        mock_assignee.login = "testuser"
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.assignees = [mock_assignee]
        mock_issue.repository.full_name = "other-org/other-repo"
        bot_env["repo"].get_issue.return_value = mock_issue

        assert bot.unassign_linked_issues(mock_pr) == 0


class TestHasBotComment:
    def test_finds_marker(self, bot_env):
        bot = StalePRBot()
        mock_pr = Mock()
        mock_comment = Mock()
        mock_comment.user.type = "Bot"
        mock_comment.body = "<!-- bot:stale --> This is a stale warning"
        mock_comment.created_at = datetime(2024, 1, 10, tzinfo=timezone.utc)
        mock_pr.get_issue_comments.return_value = [mock_comment]

        assert bot.has_bot_comment(mock_pr, "stale")
        assert not bot.has_bot_comment(mock_pr, "closed")

    def test_ignores_old_marker_before_after_date(self, bot_env):
        """Old markers from a previous cycle should be ignored."""
        bot = StalePRBot()
        mock_pr = Mock()
        mock_comment = Mock()
        mock_comment.user.type = "Bot"
        mock_comment.body = "<!-- bot:stale_warning --> old warning"
        mock_comment.created_at = datetime(2024, 1, 5, tzinfo=timezone.utc)
        mock_pr.get_issue_comments.return_value = [mock_comment]

        # The marker is from Jan 5, but changes were re-requested on Jan 8
        after_date = datetime(2024, 1, 8, tzinfo=timezone.utc)
        assert not bot.has_bot_comment(mock_pr, "stale_warning", after_date=after_date)

    def test_finds_recent_marker_after_date(self, bot_env):
        bot = StalePRBot()
        mock_pr = Mock()
        mock_comment = Mock()
        mock_comment.user.type = "Bot"
        mock_comment.body = "<!-- bot:stale_warning --> new warning"
        mock_comment.created_at = datetime(2024, 1, 15, tzinfo=timezone.utc)
        mock_pr.get_issue_comments.return_value = [mock_comment]

        after_date = datetime(2024, 1, 8, tzinfo=timezone.utc)
        assert bot.has_bot_comment(mock_pr, "stale_warning", after_date=after_date)


class TestSendStaleWarning:
    def test_success(self, bot_env):
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.user.login = "testuser"

        assert bot.send_stale_warning(mock_pr, 7)
        mock_pr.create_issue_comment.assert_called_once()
        comment = mock_pr.create_issue_comment.call_args[0][0]
        assert "@testuser" in comment
        assert "7 days" in comment
        assert "<!-- bot:stale_warning -->" in comment


class TestMarkPRStale:
    def test_success(self, bot_env):
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.body = "Fixes #123"
        mock_pr.user.login = "testuser"

        mock_assignee = Mock()
        mock_assignee.login = "testuser"
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.assignees = [mock_assignee]
        mock_issue.repository.full_name = "openwisp/openwisp-utils"
        bot_env["repo"].get_issue.return_value = mock_issue

        assert bot.mark_pr_stale(mock_pr, 14)
        mock_pr.create_issue_comment.assert_called_once()
        comment = mock_pr.create_issue_comment.call_args[0][0]
        assert "<!-- bot:stale -->" in comment
        mock_pr.add_to_labels.assert_called_once_with("stale")
        mock_issue.remove_from_assignees.assert_called_once_with("testuser")


class TestCloseStalePR:
    def test_success(self, bot_env):
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.body = "Fixes #123"
        mock_pr.user.login = "testuser"
        mock_pr.state = "open"

        mock_assignee = Mock()
        mock_assignee.login = "testuser"
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.assignees = [mock_assignee]
        mock_issue.repository.full_name = "openwisp/openwisp-utils"
        bot_env["repo"].get_issue.return_value = mock_issue

        assert bot.close_stale_pr(mock_pr, 60)
        mock_pr.create_issue_comment.assert_called_once()
        comment = mock_pr.create_issue_comment.call_args[0][0]
        assert "<!-- bot:closed -->" in comment
        mock_pr.edit.assert_called_once_with(state="closed")
        mock_issue.remove_from_assignees.assert_called_once_with("testuser")

    def test_already_closed(self, bot_env):
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.state = "closed"

        assert not bot.close_stale_pr(mock_pr, 60)
        mock_pr.create_issue_comment.assert_not_called()
        mock_pr.edit.assert_not_called()


class TestRun:
    def test_no_github_client(self, bot_env):
        bot = StalePRBot()
        bot.github = None
        bot.repo = None
        assert not bot.run()
