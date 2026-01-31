from unittest.mock import Mock, patch

import pytest

try:
    from .pr_reopen_bot import PRActivityBot, PRReopenBot
except ImportError:
    PRReopenBot = None
    PRActivityBot = None

pytestmark = pytest.mark.skipif(
    PRReopenBot is None,
    reason="PR reopen bot script not available",
)


class TestPRReopenBot:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")
        monkeypatch.setenv("REPOSITORY", "openwisp/openwisp-utils")
        monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request_target")

        with patch("openwisp_utils.bots.auto_assign.base.Github") as mock_github_cls:
            mock_repo = Mock()
            mock_github_cls.return_value.get_repo.return_value = mock_repo
            self.mock_github = mock_github_cls
            self.mock_repo = mock_repo
            yield

    def test_reassign_issues_to_author(self):
        bot = PRReopenBot()
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.assignees = []
        self.mock_repo.get_issue.return_value = mock_issue

        assigned = bot.reassign_issues_to_author(100, "testuser", "Fixes #123")
        assert len(assigned) == 1
        assert 123 in assigned
        mock_issue.add_to_assignees.assert_called_once_with("testuser")
        mock_issue.create_comment.assert_called_once()
        comment = mock_issue.create_comment.call_args[0][0]
        assert "@testuser" in comment
        assert "PR #100" in comment

    def test_reassign_skip_already_assigned_by_others(self):
        bot = PRReopenBot()
        mock_assignee = Mock()
        mock_assignee.login = "otheruser"
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.assignees = [mock_assignee]
        self.mock_repo.get_issue.return_value = mock_issue

        assigned = bot.reassign_issues_to_author(100, "testuser", "Fixes #123")
        assert len(assigned) == 0

    def test_remove_stale_label(self):
        bot = PRReopenBot()
        mock_pr = Mock()
        mock_label = Mock()
        mock_label.name = "stale"
        mock_pr.get_labels.return_value = [mock_label]
        self.mock_repo.get_pull.return_value = mock_pr

        assert bot.remove_stale_label(100)
        mock_pr.remove_from_labels.assert_called_once_with("stale")

    def test_remove_stale_label_not_present(self):
        bot = PRReopenBot()
        mock_pr = Mock()
        mock_pr.get_labels.return_value = []
        self.mock_repo.get_pull.return_value = mock_pr

        assert not bot.remove_stale_label(100)

    def test_handle_pr_reopen(self):
        bot = PRReopenBot()
        bot.load_event_payload(
            {
                "pull_request": {
                    "number": 100,
                    "user": {"login": "testuser"},
                    "body": "Fixes #123",
                }
            }
        )
        mock_issue = Mock()
        mock_issue.pull_request = None
        mock_issue.assignees = []
        self.mock_repo.get_issue.return_value = mock_issue
        mock_pr = Mock()
        mock_pr.get_labels.return_value = []
        self.mock_repo.get_pull.return_value = mock_pr

        assert bot.handle_pr_reopen()
        mock_issue.add_to_assignees.assert_called_once_with("testuser")

    def test_handle_pr_reopen_no_payload(self):
        bot = PRReopenBot()
        assert not bot.handle_pr_reopen()

    def test_run_unsupported_event(self):
        bot = PRReopenBot()
        bot.event_name = "push"
        assert not bot.run()


class TestPRActivityBot:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")
        monkeypatch.setenv("REPOSITORY", "openwisp/openwisp-utils")
        monkeypatch.setenv("GITHUB_EVENT_NAME", "issue_comment")

        with patch("openwisp_utils.bots.auto_assign.base.Github") as mock_github_cls:
            mock_repo = Mock()
            mock_github_cls.return_value.get_repo.return_value = mock_repo
            self.mock_github = mock_github_cls
            self.mock_repo = mock_repo
            yield

    def test_handle_contributor_activity(self):
        bot = PRActivityBot()
        bot.load_event_payload(
            {
                "issue": {
                    "number": 100,
                    "pull_request": {
                        "url": "https://api.github.com/repos/owner/repo/pulls/100"
                    },
                },
                "comment": {"user": {"login": "testuser"}},
            }
        )
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

        assert bot.handle_contributor_activity()
        mock_pr.remove_from_labels.assert_called_once_with("stale")
        mock_issue.add_to_assignees.assert_called_once_with("testuser")
        mock_pr.create_issue_comment.assert_called_once()
        comment = mock_pr.create_issue_comment.call_args[0][0]
        assert "@testuser" in comment

    def test_handle_contributor_activity_not_author(self):
        bot = PRActivityBot()
        bot.load_event_payload(
            {
                "issue": {
                    "number": 100,
                    "pull_request": {
                        "url": "https://api.github.com/repos/owner/repo/pulls/100"
                    },
                },
                "comment": {"user": {"login": "otheruser"}},
            }
        )
        mock_pr = Mock()
        mock_pr.user.login = "testuser"
        self.mock_repo.get_pull.return_value = mock_pr

        assert not bot.handle_contributor_activity()

    def test_handle_contributor_activity_pr_not_stale(self):
        bot = PRActivityBot()
        bot.load_event_payload(
            {
                "issue": {
                    "number": 100,
                    "pull_request": {"url": "https://api.github.com/..."},
                },
                "comment": {"user": {"login": "testuser"}},
            }
        )
        mock_pr = Mock()
        mock_pr.user.login = "testuser"
        mock_pr.get_labels.return_value = []
        self.mock_repo.get_pull.return_value = mock_pr

        assert not bot.handle_contributor_activity()

    def test_handle_contributor_activity_not_pr(self):
        bot = PRActivityBot()
        bot.load_event_payload(
            {
                "issue": {"number": 100, "pull_request": None},
                "comment": {"user": {"login": "testuser"}},
            }
        )
        assert not bot.handle_contributor_activity()

    def test_handle_contributor_activity_no_payload(self):
        bot = PRActivityBot()
        assert not bot.handle_contributor_activity()

    def test_run_unsupported_event(self):
        bot = PRActivityBot()
        bot.event_name = "push"
        assert not bot.run()
