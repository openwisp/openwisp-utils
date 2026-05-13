import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

# Add the parent directory to path for importing bot modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

try:
    from stale_pr_bot import StalePRBot  # noqa: E402
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
    with patch("base.Github") as mock_github_cls:
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
        assert bot.DAYS_BEFORE_FINAL_FOLLOWUP == 60


class TestGetLastChangesRequested:
    def test_returns_latest(self, bot_env):
        bot = StalePRBot()
        mock_pr = Mock()
        reviews = [
            Mock(
                state="APPROVED",
                submitted_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
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

    def _make_review(self, state, submitted_at, login="alice", user_type="User"):
        review = Mock()
        review.state = state
        review.submitted_at = submitted_at
        review.user.login = login
        review.user.type = user_type
        return review

    def test_bot_changes_requested_ignored(self, bot_env):
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.get_reviews.return_value = [
            self._make_review(
                "CHANGES_REQUESTED",
                datetime(2024, 1, 2, tzinfo=timezone.utc),
                login="coderabbitai[bot]",
                user_type="Bot",
            ),
        ]
        assert bot.get_last_changes_requested(mock_pr) is None

    def test_bot_changes_requested_then_bot_approved(self, bot_env):
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.get_reviews.return_value = [
            self._make_review(
                "CHANGES_REQUESTED",
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                login="coderabbitai[bot]",
                user_type="Bot",
            ),
            self._make_review(
                "APPROVED",
                datetime(2024, 1, 2, tzinfo=timezone.utc),
                login="coderabbitai[bot]",
                user_type="Bot",
            ),
        ]
        assert bot.get_last_changes_requested(mock_pr) is None

    def test_human_changes_requested_then_same_human_approved(self, bot_env):
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.get_reviews.return_value = [
            self._make_review(
                "CHANGES_REQUESTED",
                datetime(2024, 1, 1, tzinfo=timezone.utc),
            ),
            self._make_review(
                "APPROVED",
                datetime(2024, 1, 2, tzinfo=timezone.utc),
            ),
        ]
        assert bot.get_last_changes_requested(mock_pr) is None

    def test_human_changes_requested_then_dismissed(self, bot_env):
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.get_reviews.return_value = [
            self._make_review(
                "CHANGES_REQUESTED",
                datetime(2024, 1, 1, tzinfo=timezone.utc),
            ),
            self._make_review(
                "DISMISSED",
                datetime(2024, 1, 3, tzinfo=timezone.utc),
            ),
        ]
        assert bot.get_last_changes_requested(mock_pr) is None

    def test_commented_does_not_supersede_changes_requested(self, bot_env):
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.get_reviews.return_value = [
            self._make_review(
                "CHANGES_REQUESTED",
                datetime(2024, 1, 1, tzinfo=timezone.utc),
            ),
            self._make_review(
                "COMMENTED",
                datetime(2024, 1, 5, tzinfo=timezone.utc),
            ),
        ]
        assert bot.get_last_changes_requested(mock_pr) == datetime(
            2024, 1, 1, tzinfo=timezone.utc
        )

    def test_bot_review_after_human_block_does_not_dominate(self, bot_env):
        bot = StalePRBot()
        mock_pr = Mock()
        human_block = datetime(2024, 1, 1, tzinfo=timezone.utc)
        mock_pr.get_reviews.return_value = [
            self._make_review("CHANGES_REQUESTED", human_block, login="alice"),
            self._make_review(
                "CHANGES_REQUESTED",
                datetime(2024, 2, 1, tzinfo=timezone.utc),
                login="coderabbitai[bot]",
                user_type="Bot",
            ),
        ]
        assert bot.get_last_changes_requested(mock_pr) == human_block

    def test_one_human_blocks_other_approves(self, bot_env):
        bot = StalePRBot()
        mock_pr = Mock()
        block_time = datetime(2024, 1, 5, tzinfo=timezone.utc)
        mock_pr.get_reviews.return_value = [
            self._make_review(
                "APPROVED",
                datetime(2024, 1, 4, tzinfo=timezone.utc),
                login="alice",
            ),
            self._make_review(
                "CHANGES_REQUESTED",
                block_time,
                login="bob",
            ),
        ]
        assert bot.get_last_changes_requested(mock_pr) == block_time

    def test_review_without_user_skipped(self, bot_env):
        bot = StalePRBot()
        mock_pr = Mock()
        bad_review = Mock(
            state="CHANGES_REQUESTED",
            submitted_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        bad_review.user = None
        mock_pr.get_reviews.return_value = [bad_review]
        assert bot.get_last_changes_requested(mock_pr) is None

    def test_review_without_submitted_at_skipped(self, bot_env):
        bot = StalePRBot()
        mock_pr = Mock()
        pending = self._make_review("CHANGES_REQUESTED", None)
        mock_pr.get_reviews.return_value = [pending]
        assert bot.get_last_changes_requested(mock_pr) is None


class TestGetDaysSinceActivity:
    @patch("stale_pr_bot.datetime")
    def test_with_author_commit(self, mock_datetime, bot_env):
        mock_datetime.now.return_value = datetime(2024, 1, 10, tzinfo=timezone.utc)
        # Keep timezone constructor working
        mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.user.login = "testuser"
        mock_pr.get_issue_comments.return_value = []
        mock_pr.get_review_comments.return_value = []
        mock_pr.get_reviews.return_value = []
        mock_commit = Mock()
        mock_commit.commit.author.date = datetime(2024, 1, 5, tzinfo=timezone.utc)
        mock_commit.commit.committer.date = datetime(2024, 1, 5, tzinfo=timezone.utc)
        mock_commit.author.login = "testuser"
        mock_commit.committer.login = "testuser"
        mock_pr.get_commits.return_value = [mock_commit]
        last_cr = datetime(2024, 1, 1, tzinfo=timezone.utc)
        result = bot.get_days_since_activity(mock_pr, last_cr)
        assert result == 5

    def test_no_last_changes(self, bot_env):
        bot = StalePRBot()
        mock_pr = Mock()
        assert bot.get_days_since_activity(mock_pr, None) == 0

    @patch("stale_pr_bot.datetime")
    def test_force_push_uses_committer_date(self, mock_datetime, bot_env):
        mock_datetime.now.return_value = datetime(2024, 1, 20, tzinfo=timezone.utc)
        mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.user.login = "testuser"
        mock_pr.get_issue_comments.return_value = []
        mock_pr.get_review_comments.return_value = []
        mock_pr.get_reviews.return_value = []
        mock_commit = Mock()
        mock_commit.commit.author.date = datetime(2023, 12, 1, tzinfo=timezone.utc)
        mock_commit.commit.committer.date = datetime(2024, 1, 15, tzinfo=timezone.utc)
        mock_commit.author.login = "testuser"
        mock_commit.committer.login = "testuser"
        mock_pr.get_commits.return_value = [mock_commit]
        last_cr = datetime(2024, 1, 1, tzinfo=timezone.utc)
        assert bot.get_days_since_activity(mock_pr, last_cr) == 5

    @patch("stale_pr_bot.datetime")
    def test_unlinked_author_falls_back_to_committer(self, mock_datetime, bot_env):
        mock_datetime.now.return_value = datetime(2024, 1, 10, tzinfo=timezone.utc)
        mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.user.login = "testuser"
        mock_pr.get_issue_comments.return_value = []
        mock_pr.get_review_comments.return_value = []
        mock_pr.get_reviews.return_value = []
        mock_commit = Mock()
        mock_commit.commit.author.date = datetime(2024, 1, 5, tzinfo=timezone.utc)
        mock_commit.commit.committer.date = datetime(2024, 1, 5, tzinfo=timezone.utc)
        mock_commit.author = None
        mock_commit.committer.login = "testuser"
        mock_pr.get_commits.return_value = [mock_commit]
        last_cr = datetime(2024, 1, 1, tzinfo=timezone.utc)
        assert bot.get_days_since_activity(mock_pr, last_cr) == 5

    @patch("stale_pr_bot.datetime")
    def test_both_unlinked_commit_skipped(self, mock_datetime, bot_env):
        mock_datetime.now.return_value = datetime(2024, 1, 10, tzinfo=timezone.utc)
        mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.user.login = "testuser"
        mock_pr.get_issue_comments.return_value = []
        mock_pr.get_review_comments.return_value = []
        mock_pr.get_reviews.return_value = []
        mock_commit = Mock()
        mock_commit.commit.author.date = datetime(2024, 1, 5, tzinfo=timezone.utc)
        mock_commit.commit.committer.date = datetime(2024, 1, 5, tzinfo=timezone.utc)
        mock_commit.author = None
        mock_commit.committer = None
        mock_pr.get_commits.return_value = [mock_commit]
        last_cr = datetime(2024, 1, 1, tzinfo=timezone.utc)
        assert bot.get_days_since_activity(mock_pr, last_cr) == 9

    @patch("stale_pr_bot.datetime")
    def test_maintainer_rebase_does_not_count_as_author_activity(
        self, mock_datetime, bot_env
    ):
        mock_datetime.now.return_value = datetime(2024, 3, 1, tzinfo=timezone.utc)
        mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.user.login = "contributor"
        mock_pr.get_issue_comments.return_value = []
        mock_pr.get_review_comments.return_value = []
        mock_pr.get_reviews.return_value = []
        mock_commit = Mock()
        mock_commit.commit.author.date = datetime(2023, 12, 1, tzinfo=timezone.utc)
        mock_commit.commit.committer.date = datetime(2024, 2, 25, tzinfo=timezone.utc)
        mock_commit.author.login = "contributor"
        mock_commit.committer.login = "maintainer"
        mock_pr.get_commits.return_value = [mock_commit]
        last_cr = datetime(2024, 1, 1, tzinfo=timezone.utc)
        assert bot.get_days_since_activity(mock_pr, last_cr) == 60


class TestIsWaitingForMaintainer:
    def _make_pr(self, author="contributor"):
        mock_pr = Mock()
        mock_pr.number = 1
        mock_pr.user.login = author
        mock_pr.get_commits.return_value = []
        mock_pr.get_issue_comments.return_value = []
        mock_pr.get_review_comments.return_value = []
        mock_pr.get_reviews.return_value = []
        return mock_pr

    def test_contributor_responded_no_maintainer_since(self, bot_env):
        """Contributor pushed after changes requested, no maintainer response."""
        bot = StalePRBot()
        pr = self._make_pr()
        last_cr = datetime(2024, 1, 1, tzinfo=timezone.utc)
        # Contributor pushed a commit after changes were requested
        commit = Mock()
        commit.commit.author.date = datetime(2024, 1, 5, tzinfo=timezone.utc)
        commit.commit.committer.date = datetime(2024, 1, 5, tzinfo=timezone.utc)
        commit.author.login = "contributor"
        commit.committer.login = "contributor"
        pr.get_commits.return_value = [commit]
        assert bot.is_waiting_for_maintainer(pr, last_cr) is True

    def test_contributor_responded_maintainer_reviewed(self, bot_env):
        """Contributor pushed, then maintainer submitted a review."""
        bot = StalePRBot()
        pr = self._make_pr()
        last_cr = datetime(2024, 1, 1, tzinfo=timezone.utc)
        commit = Mock()
        commit.commit.author.date = datetime(2024, 1, 5, tzinfo=timezone.utc)
        commit.commit.committer.date = datetime(2024, 1, 5, tzinfo=timezone.utc)
        commit.author.login = "contributor"
        commit.committer.login = "contributor"
        pr.get_commits.return_value = [commit]
        # Maintainer reviewed after contributor's commit
        review = Mock()
        review.user.login = "maintainer"
        review.user.type = "User"
        review.author_association = "MEMBER"
        review.submitted_at = datetime(2024, 1, 7, tzinfo=timezone.utc)
        pr.get_reviews.return_value = [review]
        assert bot.is_waiting_for_maintainer(pr, last_cr) is False

    def test_maintainer_comment_does_not_count_as_review(self, bot_env):
        """A maintainer comment is not a review; the PR is still waiting."""
        bot = StalePRBot()
        pr = self._make_pr()
        last_cr = datetime(2024, 1, 1, tzinfo=timezone.utc)
        commit = Mock()
        commit.commit.author.date = datetime(2024, 1, 5, tzinfo=timezone.utc)
        commit.commit.committer.date = datetime(2024, 1, 5, tzinfo=timezone.utc)
        commit.author.login = "contributor"
        commit.committer.login = "contributor"
        pr.get_commits.return_value = [commit]
        comment = Mock()
        comment.user.login = "maintainer"
        comment.user.type = "User"
        comment.author_association = "COLLABORATOR"
        comment.created_at = datetime(2024, 1, 7, tzinfo=timezone.utc)
        pr.get_issue_comments.return_value = [comment]
        assert bot.is_waiting_for_maintainer(pr, last_cr) is True

    def test_contributor_never_responded(self, bot_env):
        """No contributor activity after changes requested → not waiting."""
        bot = StalePRBot()
        pr = self._make_pr()
        last_cr = datetime(2024, 1, 1, tzinfo=timezone.utc)
        assert bot.is_waiting_for_maintainer(pr, last_cr) is False

    def test_bot_comments_are_ignored(self, bot_env):
        """Bot comments should not count as maintainer activity."""
        bot = StalePRBot()
        pr = self._make_pr()
        last_cr = datetime(2024, 1, 1, tzinfo=timezone.utc)
        commit = Mock()
        commit.commit.author.date = datetime(2024, 1, 5, tzinfo=timezone.utc)
        commit.commit.committer.date = datetime(2024, 1, 5, tzinfo=timezone.utc)
        commit.author.login = "contributor"
        commit.committer.login = "contributor"
        pr.get_commits.return_value = [commit]
        # Only a bot comment exists after contributor's activity
        bot_comment = Mock()
        bot_comment.user.login = "github-actions[bot]"
        bot_comment.user.type = "Bot"
        bot_comment.author_association = "NONE"
        bot_comment.created_at = datetime(2024, 1, 6, tzinfo=timezone.utc)
        pr.get_issue_comments.return_value = [bot_comment]
        assert bot.is_waiting_for_maintainer(pr, last_cr) is True

    def test_non_maintainer_comment_ignored(self, bot_env):
        """A random community member commenting should not count as maintainer."""
        bot = StalePRBot()
        pr = self._make_pr()
        last_cr = datetime(2024, 1, 1, tzinfo=timezone.utc)
        commit = Mock()
        commit.commit.author.date = datetime(2024, 1, 5, tzinfo=timezone.utc)
        commit.commit.committer.date = datetime(2024, 1, 5, tzinfo=timezone.utc)
        commit.author.login = "contributor"
        commit.committer.login = "contributor"
        pr.get_commits.return_value = [commit]
        comment = Mock()
        comment.user.login = "random_user"
        comment.user.type = "User"
        comment.author_association = "NONE"
        comment.created_at = datetime(2024, 1, 7, tzinfo=timezone.utc)
        pr.get_issue_comments.return_value = [comment]
        assert bot.is_waiting_for_maintainer(pr, last_cr) is True

    def test_many_events_does_not_miss_contributor_activity(self, bot_env):
        """Contributor activity must be found even with many subsequent events."""
        bot = StalePRBot()
        pr = self._make_pr()
        last_cr = datetime(2024, 1, 1, tzinfo=timezone.utc)
        # Contributor pushed a commit early on
        contributor_commit = Mock()
        contributor_commit.commit.author.date = datetime(
            2024, 1, 2, tzinfo=timezone.utc
        )
        contributor_commit.commit.committer.date = datetime(
            2024, 1, 2, tzinfo=timezone.utc
        )
        contributor_commit.author.login = "contributor"
        contributor_commit.committer.login = "contributor"
        # 60 subsequent commits from CI/other (not from contributor)
        base = datetime(2024, 1, 3, tzinfo=timezone.utc)
        other_commits = []
        for i in range(60):
            c = Mock()
            c.commit.author.date = base + timedelta(days=i)
            c.commit.committer.date = base + timedelta(days=i)
            c.author.login = "ci-bot"
            c.committer.login = "ci-bot"
            other_commits.append(c)
        pr.get_commits.return_value = [contributor_commit] + other_commits
        assert bot.is_waiting_for_maintainer(pr, last_cr) is True

    def test_fails_closed_on_exception(self, bot_env):
        bot = StalePRBot()
        pr = self._make_pr()
        pr.get_commits.side_effect = RuntimeError("transient API error")
        last_cr = datetime(2024, 1, 1, tzinfo=timezone.utc)
        assert bot.is_waiting_for_maintainer(pr, last_cr) is True


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
        mock_comment.user.login = bot.bot_login
        mock_comment.body = "<!-- bot:stale --> This is a stale warning"
        mock_comment.created_at = datetime(2024, 1, 10, tzinfo=timezone.utc)
        mock_pr.get_issue_comments.return_value = [mock_comment]
        assert bot.has_bot_comment(mock_pr, "stale")
        assert not bot.has_bot_comment(mock_pr, "closed")

    def test_ignores_marker_from_other_bot(self, bot_env):
        bot = StalePRBot()
        mock_pr = Mock()
        mock_comment = Mock()
        mock_comment.user.login = "some-other-bot[bot]"
        mock_comment.body = "<!-- bot:stale --> quoted from elsewhere"
        mock_comment.created_at = datetime(2024, 1, 10, tzinfo=timezone.utc)
        mock_pr.get_issue_comments.return_value = [mock_comment]
        assert not bot.has_bot_comment(mock_pr, "stale")

    def test_ignores_old_marker_before_after_date(self, bot_env):
        bot = StalePRBot()
        mock_pr = Mock()
        mock_comment = Mock()
        mock_comment.user.login = bot.bot_login
        mock_comment.body = "<!-- bot:stale_warning --> old warning"
        mock_comment.created_at = datetime(2024, 1, 5, tzinfo=timezone.utc)
        mock_pr.get_issue_comments.return_value = [mock_comment]
        after_date = datetime(2024, 1, 8, tzinfo=timezone.utc)
        assert not bot.has_bot_comment(mock_pr, "stale_warning", after_date=after_date)

    def test_finds_recent_marker_after_date(self, bot_env):
        bot = StalePRBot()
        mock_pr = Mock()
        mock_comment = Mock()
        mock_comment.user.login = bot.bot_login
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

    def test_no_comment_when_unassign_raises(self, bot_env):
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.user.login = "testuser"
        mock_pr.number = 1
        bot.unassign_linked_issues = Mock(side_effect=RuntimeError("transient"))
        assert bot.mark_pr_stale(mock_pr, 14) is False
        mock_pr.create_issue_comment.assert_not_called()
        mock_pr.add_to_labels.assert_not_called()


class TestSendFinalFollowup:
    def test_success(self, bot_env):
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.user.login = "testuser"
        assert bot.send_final_followup(mock_pr, 60)
        mock_pr.create_issue_comment.assert_called_once()
        comment = mock_pr.create_issue_comment.call_args[0][0]
        assert "<!-- bot:final_followup -->" in comment
        mock_pr.edit.assert_not_called()


class TestProcessStalePrs:
    @patch("stale_pr_bot.datetime")
    def test_skips_pr_waiting_for_maintainer(self, mock_datetime, bot_env):
        mock_datetime.now.return_value = datetime(2024, 2, 1, tzinfo=timezone.utc)
        mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.number = 42
        mock_pr.user.login = "contributor"
        # Maintainer requested changes on Jan 1
        review = Mock()
        review.state = "CHANGES_REQUESTED"
        review.submitted_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        review.user.login = "maintainer"
        review.user.type = "User"
        mock_pr.get_reviews.return_value = [review]
        # Contributor pushed on Jan 5
        commit = Mock()
        commit.commit.author.date = datetime(2024, 1, 5, tzinfo=timezone.utc)
        commit.commit.committer.date = datetime(2024, 1, 5, tzinfo=timezone.utc)
        commit.author.login = "contributor"
        commit.committer.login = "contributor"
        mock_pr.get_commits.return_value = [commit]
        # No maintainer activity
        mock_pr.get_issue_comments.return_value = []
        mock_pr.get_review_comments.return_value = []
        bot_env["repo"].get_pulls.return_value = [mock_pr]
        bot.process_stale_prs()
        # PR should not be warned, staled, or closed
        mock_pr.create_issue_comment.assert_not_called()
        mock_pr.edit.assert_not_called()

    @patch("stale_pr_bot.datetime")
    def test_skips_pr_with_only_bot_changes_requested(self, mock_datetime, bot_env):
        mock_datetime.now.return_value = datetime(2024, 5, 10, tzinfo=timezone.utc)
        mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.number = 1235
        mock_pr.user.login = "contributor"
        bot_review = Mock()
        bot_review.state = "CHANGES_REQUESTED"
        bot_review.submitted_at = datetime(2024, 2, 1, tzinfo=timezone.utc)
        bot_review.user.login = "coderabbitai[bot]"
        bot_review.user.type = "Bot"
        mock_pr.get_reviews.return_value = [bot_review]
        mock_pr.get_commits.return_value = []
        mock_pr.get_issue_comments.return_value = []
        mock_pr.get_review_comments.return_value = []
        bot_env["repo"].get_pulls.return_value = [mock_pr]
        bot.process_stale_prs()
        mock_pr.create_issue_comment.assert_not_called()
        mock_pr.edit.assert_not_called()

    @patch("stale_pr_bot.datetime")
    def test_skips_pr_with_superseded_changes_requested(self, mock_datetime, bot_env):
        mock_datetime.now.return_value = datetime(2024, 5, 10, tzinfo=timezone.utc)
        mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.number = 99
        mock_pr.user.login = "contributor"
        cr_review = Mock()
        cr_review.state = "CHANGES_REQUESTED"
        cr_review.submitted_at = datetime(2024, 2, 1, tzinfo=timezone.utc)
        cr_review.user.login = "maintainer"
        cr_review.user.type = "User"
        approve_review = Mock()
        approve_review.state = "APPROVED"
        approve_review.submitted_at = datetime(2024, 2, 5, tzinfo=timezone.utc)
        approve_review.user.login = "maintainer"
        approve_review.user.type = "User"
        mock_pr.get_reviews.return_value = [cr_review, approve_review]
        mock_pr.get_commits.return_value = []
        mock_pr.get_issue_comments.return_value = []
        mock_pr.get_review_comments.return_value = []
        bot_env["repo"].get_pulls.return_value = [mock_pr]
        bot.process_stale_prs()
        mock_pr.create_issue_comment.assert_not_called()
        mock_pr.edit.assert_not_called()

    @patch("stale_pr_bot.datetime")
    def test_pr_first_processed_past_60_days_marks_stale_only(
        self, mock_datetime, bot_env
    ):
        mock_datetime.now.return_value = datetime(2024, 5, 10, tzinfo=timezone.utc)
        mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.body = ""
        mock_pr.number = 7
        mock_pr.user.login = "contributor"
        cr_review = Mock()
        cr_review.state = "CHANGES_REQUESTED"
        cr_review.submitted_at = datetime(2024, 2, 1, tzinfo=timezone.utc)
        cr_review.user.login = "maintainer"
        cr_review.user.type = "User"
        mock_pr.get_reviews.return_value = [cr_review]
        mock_pr.get_commits.return_value = []
        mock_pr.get_issue_comments.return_value = []
        mock_pr.get_review_comments.return_value = []
        mock_pr.get_labels.return_value = []
        bot_env["repo"].get_pulls.return_value = [mock_pr]
        bot.process_stale_prs()
        bodies = [c[0][0] for c in mock_pr.create_issue_comment.call_args_list]
        assert any("<!-- bot:stale -->" in b for b in bodies)
        assert not any("<!-- bot:final_followup -->" in b for b in bodies)
        assert not any("<!-- bot:stale_warning -->" in b for b in bodies)
        mock_pr.add_to_labels.assert_called_once_with("stale")
        mock_pr.edit.assert_not_called()

    @patch("stale_pr_bot.datetime")
    def test_final_followup_fires_after_prior_stale_run(self, mock_datetime, bot_env):
        mock_datetime.now.return_value = datetime(2024, 5, 10, tzinfo=timezone.utc)
        mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.body = ""
        mock_pr.number = 7
        mock_pr.user.login = "contributor"
        cr_review = Mock()
        cr_review.state = "CHANGES_REQUESTED"
        cr_review.submitted_at = datetime(2024, 2, 1, tzinfo=timezone.utc)
        cr_review.user.login = "maintainer"
        cr_review.user.type = "User"
        mock_pr.get_reviews.return_value = [cr_review]
        mock_pr.get_commits.return_value = []
        mock_pr.get_review_comments.return_value = []
        stale_label = Mock()
        stale_label.name = "stale"
        mock_pr.get_labels.return_value = [stale_label]
        prior_stale = Mock()
        prior_stale.user.login = bot.bot_login
        prior_stale.body = "<!-- bot:stale --> previous run"
        prior_stale.created_at = datetime(2024, 5, 1, tzinfo=timezone.utc)
        mock_pr.get_issue_comments.return_value = [prior_stale]
        bot_env["repo"].get_pulls.return_value = [mock_pr]
        bot.process_stale_prs()
        bodies = [c[0][0] for c in mock_pr.create_issue_comment.call_args_list]
        assert any("<!-- bot:final_followup -->" in b for b in bodies)
        assert not any(
            "<!-- bot:stale -->" in b and "previous run" not in b for b in bodies
        )
        mock_pr.edit.assert_not_called()

    @patch("stale_pr_bot.datetime")
    def test_clears_stale_label_when_contributor_responds(self, mock_datetime, bot_env):
        mock_datetime.now.return_value = datetime(2024, 2, 1, tzinfo=timezone.utc)
        mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.body = "Fixes #42"
        mock_pr.number = 1
        mock_pr.user.login = "contributor"
        cr_review = Mock()
        cr_review.state = "CHANGES_REQUESTED"
        cr_review.submitted_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        cr_review.user.login = "maintainer"
        cr_review.user.type = "User"
        mock_pr.get_reviews.return_value = [cr_review]
        commit = Mock()
        commit.commit.author.date = datetime(2024, 1, 20, tzinfo=timezone.utc)
        commit.commit.committer.date = datetime(2024, 1, 20, tzinfo=timezone.utc)
        commit.author.login = "contributor"
        commit.committer.login = "contributor"
        mock_pr.get_commits.return_value = [commit]
        stale_label = Mock()
        stale_label.name = "stale"
        mock_pr.get_labels.return_value = [stale_label]
        mock_pr.get_issue_comments.return_value = []
        mock_pr.get_review_comments.return_value = []
        mock_issue = Mock()
        mock_issue.number = 42
        mock_issue.pull_request = None
        mock_issue.assignees = []
        mock_issue.repository.full_name = "openwisp/openwisp-utils"
        bot_env["repo"].get_issue.return_value = mock_issue
        bot_env["repo"].get_pulls.return_value = [mock_pr]
        bot.process_stale_prs()
        mock_pr.remove_from_labels.assert_called_once_with("stale")
        mock_issue.add_to_assignees.assert_called_once_with("contributor")
        mock_pr.create_issue_comment.assert_not_called()

    @patch("stale_pr_bot.datetime")
    def test_clears_stale_label_when_no_active_block(self, mock_datetime, bot_env):
        mock_datetime.now.return_value = datetime(2024, 2, 1, tzinfo=timezone.utc)
        mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)
        bot = StalePRBot()
        mock_pr = Mock()
        mock_pr.body = "Fixes #42"
        mock_pr.number = 1
        mock_pr.user.login = "contributor"
        # Reviewer approved after their CR → no active CHANGES_REQUESTED.
        approve = Mock()
        approve.state = "APPROVED"
        approve.submitted_at = datetime(2024, 1, 20, tzinfo=timezone.utc)
        approve.user.login = "maintainer"
        approve.user.type = "User"
        mock_pr.get_reviews.return_value = [approve]
        stale_label = Mock()
        stale_label.name = "stale"
        mock_pr.get_labels.return_value = [stale_label]
        mock_issue = Mock()
        mock_issue.number = 42
        mock_issue.pull_request = None
        mock_issue.assignees = []
        mock_issue.repository.full_name = "openwisp/openwisp-utils"
        bot_env["repo"].get_issue.return_value = mock_issue
        bot_env["repo"].get_pulls.return_value = [mock_pr]
        bot.process_stale_prs()
        mock_pr.remove_from_labels.assert_called_once_with("stale")
        mock_issue.add_to_assignees.assert_called_once_with("contributor")
        mock_pr.create_issue_comment.assert_not_called()


class TestRun:
    def test_no_github_client(self, bot_env):
        bot = StalePRBot()
        bot.github = None
        bot.repo = None
        assert not bot.run()
