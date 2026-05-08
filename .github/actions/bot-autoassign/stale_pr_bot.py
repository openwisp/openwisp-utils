import time
from datetime import datetime, timezone

from base import GitHubBot
from utils import unassign_linked_issues_helper

# GitHub author_association values that represent project maintainers.
MAINTAINER_ROLES = frozenset({"OWNER", "MEMBER", "COLLABORATOR"})


class StalePRBot(GitHubBot):
    def __init__(self):
        super().__init__()
        self.DAYS_BEFORE_STALE_WARNING = 7
        self.DAYS_BEFORE_UNASSIGN = 14
        self.DAYS_BEFORE_CLOSE = 60

    @staticmethod
    def _commit_activity_date_for_author(commit, pr_author):
        dates = []
        if (
            commit.author
            and commit.author.login == pr_author
            and commit.commit.author
            and commit.commit.author.date
        ):
            dates.append(commit.commit.author.date)
        if (
            commit.committer
            and commit.committer.login == pr_author
            and commit.commit.committer
            and commit.commit.committer.date
        ):
            dates.append(commit.commit.committer.date)
        return max(dates, default=None)

    def _get_last_author_activity(
        self,
        pr,
        after_date,
        issue_comments=None,
        all_reviews=None,
        review_comments=None,
    ):
        """Return the datetime of the PR author's latest activity after *after_date*.

        Returns ``None`` when the author has not acted since *after_date*.
        """
        pr_author = pr.user.login if pr.user else None
        if not pr_author:
            return None
        last_activity = None
        for commit in pr.get_commits():
            commit_date = self._commit_activity_date_for_author(commit, pr_author)
            if not commit_date or commit_date <= after_date:
                continue
            if not last_activity or commit_date > last_activity:
                last_activity = commit_date
        if issue_comments is None:
            issue_comments = list(pr.get_issue_comments())
        for comment in issue_comments:
            if comment.user and comment.user.login == pr_author:
                comment_date = comment.created_at
                if comment_date > after_date:
                    if not last_activity or comment_date > last_activity:
                        last_activity = comment_date
        if review_comments is None:
            review_comments = list(pr.get_review_comments())
        for comment in review_comments:
            if comment.user and comment.user.login == pr_author:
                comment_date = comment.created_at
                if comment_date > after_date:
                    if not last_activity or comment_date > last_activity:
                        last_activity = comment_date
        if all_reviews is None:
            all_reviews = list(pr.get_reviews())
        for review in all_reviews:
            if review.user and review.user.login == pr_author:
                review_date = review.submitted_at
                if review_date and review_date > after_date:
                    if not last_activity or review_date > last_activity:
                        last_activity = review_date
        return last_activity

    def get_days_since_activity(
        self,
        pr,
        last_changes_requested,
        issue_comments=None,
        all_reviews=None,
        review_comments=None,
    ):
        if not last_changes_requested:
            return 0
        try:
            last_author_activity = self._get_last_author_activity(
                pr,
                last_changes_requested,
                issue_comments,
                all_reviews,
                review_comments,
            )
            reference_date = last_author_activity or last_changes_requested
            now = datetime.now(timezone.utc)
            return (now - reference_date).days
        except Exception as e:
            print("Error calculating activity" f" for PR #{pr.number}: {e}")
            return 0

    def is_waiting_for_maintainer(
        self,
        pr,
        last_changes_requested,
        issue_comments=None,
        all_reviews=None,
        review_comments=None,
    ):
        """Return True when the contributor has responded but no maintainer has acted since.

        The bot should not warn, mark stale, or close a PR when the ball
        is in the maintainers' court.
        """
        try:
            pr_author = pr.user.login if pr.user else None
            if not pr_author:
                return False
            last_author_activity = self._get_last_author_activity(
                pr,
                last_changes_requested,
                issue_comments,
                all_reviews,
                review_comments,
            )
            if not last_author_activity:
                return False
            # Check for maintainer activity after the contributor's last action.
            # Only OWNER / MEMBER / COLLABORATOR responses count; random
            # community comments and bot messages do not.
            if issue_comments is None:
                issue_comments = list(pr.get_issue_comments())
            for comment in issue_comments:
                if (
                    comment.user
                    and comment.user.login != pr_author
                    and comment.user.type != "Bot"
                    and getattr(comment, "author_association", None) in MAINTAINER_ROLES
                    and comment.created_at > last_author_activity
                ):
                    return False
            if review_comments is None:
                review_comments = list(pr.get_review_comments())
            for comment in review_comments:
                if (
                    comment.user
                    and comment.user.login != pr_author
                    and comment.user.type != "Bot"
                    and getattr(comment, "author_association", None) in MAINTAINER_ROLES
                    and comment.created_at > last_author_activity
                ):
                    return False
            if all_reviews is None:
                all_reviews = list(pr.get_reviews())
            for review in all_reviews:
                if (
                    review.user
                    and review.user.login != pr_author
                    and review.user.type != "Bot"
                    and getattr(review, "author_association", None) in MAINTAINER_ROLES
                    and review.submitted_at
                    and review.submitted_at > last_author_activity
                ):
                    return False
            return True
        except Exception as e:
            print("Error checking maintainer activity" f" for PR #{pr.number}: {e}")
            return False

    def get_last_changes_requested(self, pr, all_reviews=None):
        """Timestamp of the latest CHANGES_REQUESTED that still represents
        a human reviewer's current stance, or ``None``.
        """
        try:
            if all_reviews is None:
                all_reviews = list(pr.get_reviews())
            # Bot reviews are advisory; COMMENTED does not change stance.
            latest_per_reviewer = {}
            for review in all_reviews:
                if (
                    not review.user
                    or not review.submitted_at
                    or review.user.type == "Bot"
                    or review.state == "COMMENTED"
                ):
                    continue
                current = latest_per_reviewer.get(review.user.login)
                if current is None or review.submitted_at > current.submitted_at:
                    latest_per_reviewer[review.user.login] = review
            return max(
                (
                    review.submitted_at
                    for review in latest_per_reviewer.values()
                    if review.state == "CHANGES_REQUESTED"
                ),
                default=None,
            )
        except Exception as e:
            print("Error getting reviews" f" for PR #{pr.number}: {e}")
            return None

    def has_bot_comment(self, pr, comment_type, after_date=None, issue_comments=None):
        """Check if PR already has a specific type of bot comment.

        Uses HTML markers. If ``after_date`` is provided,
        only considers comments posted after that date.
        """
        try:
            if issue_comments is None:
                issue_comments = list(pr.get_issue_comments())
            marker = f"<!-- bot:{comment_type} -->"
            for comment in issue_comments:
                if (
                    comment.user
                    and comment.user.type == "Bot"
                    and marker in comment.body
                ):
                    if after_date and comment.created_at <= after_date:
                        continue
                    return True
            return False
        except Exception as e:
            print("Error checking bot comments" f" for PR #{pr.number}: {e}")
            return False

    def unassign_linked_issues(self, pr):
        try:
            pr_author = pr.user.login if pr.user else None
            if not pr_author:
                return False
            unassigned_issues = unassign_linked_issues_helper(
                self.repo, self.repository_name, pr.body or "", pr_author
            )
            return len(unassigned_issues)
        except Exception as e:
            print(f"Error processing linked issues for PR #{pr.number}: {e}")
            return 0

    def close_stale_pr(self, pr, days_inactive):
        # TEMPORARY: auto-close disabled. The stale-detection heuristic
        # has been closing PRs that are merely blocked by bot reviews
        # (or by reviews the same reviewer later approved). The proper
        # fix lives in PR #668; until it lands, no PR is auto-closed.
        print(f"Auto-close currently disabled, skipping PR #{pr.number}")
        return False
        if pr.state == "closed":
            print(f"PR #{pr.number} is already closed, skipping")
            return True
        try:
            pr_author = pr.user.login if pr.user else None
            if not pr_author:
                return False
            close_lines = [
                "<!-- bot:closed -->",
                f"Hi @{pr_author} 👋,",
                "",
                (
                    "This pull request has been automatically"
                    " closed due to"
                    f" **{days_inactive} days of inactivity**."
                    " After changes were requested,"
                    " the PR remained inactive."
                ),
                "",
                (
                    "We understand that life gets busy,"
                    " and we appreciate your initial"
                    " contribution! 💙"
                ),
                "",
                ("**The door is always open**" " for you to come back:"),
                (
                    "- You can **reopen this PR** at any time"
                    " if you'd like to continue working on it"
                ),
                ("- Feel free to push new commits" " addressing the requested changes"),
                (
                    "- If you reopen the PR, the linked issue"
                    " will be reassigned to you"
                ),
                "",
                (
                    "If you have any questions or need help,"
                    " don't hesitate to reach out."
                    " We're here to support you!"
                ),
                "",
                ("Thank you for your interest in" " contributing to OpenWISP! 🙏"),
            ]
            try:
                pr.create_issue_comment("\n".join(close_lines))
            except Exception as comment_error:
                print(
                    f"Warning: Could not post closing comment"
                    f" on PR #{pr.number}: {comment_error}"
                )
            finally:
                pr.edit(state="closed")
            unassigned_count = self.unassign_linked_issues(pr)
            print(
                f"Closed PR #{pr.number} after"
                f" {days_inactive} days of inactivity,"
                f" unassigned {unassigned_count} issues"
            )
            return True
        except Exception as e:
            print(f"Error closing PR #{pr.number}: {e}")
            return False

    def mark_pr_stale(self, pr, days_inactive):
        try:
            pr_author = pr.user.login if pr.user else None
            if not pr_author:
                return False
            unassign_lines = [
                "<!-- bot:stale -->",
                f"Hi @{pr_author} 👋,",
                "",
                (
                    "This pull request has been marked"
                    " as **stale** due to"
                    f" **{days_inactive} days of inactivity**"
                    " after changes were requested."
                ),
                "",
                (
                    "As a result, **the linked issue(s)"
                    " have been unassigned** from you"
                    " to allow other contributors"
                    " to work on it."
                ),
                "",
                (
                    "However, **you can still continue"
                    " working on this PR**!"
                    " If you push new commits or respond"
                    " to the review feedback:"
                ),
                "- The issue will be reassigned to you",
                "- Your contribution is still very welcome",
                "",
                (
                    "If you need more time or have questions"
                    " about the requested changes, please"
                    " let us know."
                    " We're happy to help! 🤝"
                ),
                "",
                (
                    "If there's no further activity within"
                    f" **{self.DAYS_BEFORE_CLOSE - days_inactive}"
                    " more days**, this PR will be"
                    " automatically closed"
                    " (but can be reopened anytime)."
                ),
            ]
            pr.create_issue_comment("\n".join(unassign_lines))
            unassigned_count = self.unassign_linked_issues(pr)
            try:
                pr.add_to_labels("stale")
            except Exception as e:
                print(f"Could not add stale label: {e}")
            print(
                f"Marked PR #{pr.number} as stale after"
                f" {days_inactive} days,"
                f" unassigned {unassigned_count} issues"
            )
            return True
        except Exception as e:
            print(f"Error marking PR #{pr.number}" f" as stale: {e}")
            return False

    def send_stale_warning(self, pr, days_inactive):
        try:
            pr_author = pr.user.login if pr.user else None
            if not pr_author:
                return False
            remaining = self.DAYS_BEFORE_UNASSIGN - days_inactive
            warning_lines = [
                "<!-- bot:stale_warning -->",
                f"Hi @{pr_author} 👋,",
                "",
                (
                    "This is a friendly reminder that"
                    " this pull request has had"
                    f" **no activity for {days_inactive}"
                    " days** since changes were requested."
                ),
                "",
                (
                    "We'd love to see this contribution"
                    " merged! Please take a moment to:"
                ),
                "- Address the review feedback",
                "- Push your changes",
                ("- Let us know if you have any questions" " or need clarification"),
                "",
                (
                    "If you're busy or need more time,"
                    " no worries! Just leave a comment"
                    " to let us know you're still"
                    " working on it."
                ),
                "",
                (
                    f"**Note:** within"
                    f" **{remaining} more days**,"
                    " the linked issue will be unassigned"
                    " to allow other contributors"
                    " to work on it."
                ),
                "",
                "Thank you for your contribution! 🙏",
            ]
            pr.create_issue_comment("\n".join(warning_lines))
            print(f"Sent stale warning for PR #{pr.number}")
            return True
        except Exception as e:
            print("Error sending warning" f" for PR #{pr.number}: {e}")
            return False

    def process_stale_prs(self):
        if not self.repo:
            print("GitHub repository not initialized")
            return False
        try:
            open_prs = self.repo.get_pulls(state="open")
            processed_count = 0
            pr_count = 0
            for pr in open_prs:
                pr_count += 1
                try:
                    all_reviews = list(pr.get_reviews())
                    last_changes_requested = self.get_last_changes_requested(
                        pr, all_reviews
                    )
                    if not last_changes_requested:
                        continue
                    issue_comments = list(pr.get_issue_comments())
                    review_comments = list(pr.get_review_comments())
                    days_inactive = self.get_days_since_activity(
                        pr,
                        last_changes_requested,
                        issue_comments,
                        all_reviews,
                        review_comments,
                    )
                    print(
                        f"PR #{pr.number}: {days_inactive}"
                        " days since contributor activity"
                    )
                    if self.is_waiting_for_maintainer(
                        pr,
                        last_changes_requested,
                        issue_comments,
                        all_reviews,
                        review_comments,
                    ):
                        print(
                            f"PR #{pr.number}: waiting for"
                            " maintainer review, skipping"
                        )
                        continue
                    if days_inactive >= self.DAYS_BEFORE_CLOSE:
                        if self.close_stale_pr(pr, days_inactive):
                            processed_count += 1
                    elif days_inactive >= self.DAYS_BEFORE_UNASSIGN:
                        if not self.has_bot_comment(
                            pr,
                            "stale",
                            after_date=last_changes_requested,
                            issue_comments=issue_comments,
                        ):
                            if self.mark_pr_stale(pr, days_inactive):
                                processed_count += 1
                    elif days_inactive >= self.DAYS_BEFORE_STALE_WARNING:
                        if not self.has_bot_comment(
                            pr,
                            "stale_warning",
                            after_date=last_changes_requested,
                            issue_comments=issue_comments,
                        ):
                            if self.send_stale_warning(pr, days_inactive):
                                processed_count += 1
                except Exception as e:
                    print(f"Error processing" f" PR #{pr.number}: {e}")
                    continue
                finally:
                    time.sleep(0.5)
            print(
                f"Checked {pr_count} open PRs,"
                f" processed {processed_count} stale PRs"
            )
            return True
        except Exception as e:
            print(f"Error in process_stale_prs: {e}")
            return False

    def run(self):
        if not self.github or not self.repo:
            print("GitHub client not properly initialized," " cannot proceed")
            return False
        print("Stale PR Management Bot starting...")
        try:
            return self.process_stale_prs()
        except Exception as e:
            print(f"Error in main execution: {e}")
            return False
        finally:
            print("Stale PR Management Bot completed")


def main():
    bot = StalePRBot()
    result = bot.run()
    return 0 if result else 1


if __name__ == "__main__":
    main()
