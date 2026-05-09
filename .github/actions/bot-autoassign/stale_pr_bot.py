import os
import time
from datetime import datetime, timezone

from base import GitHubBot
from utils import (
    extract_linked_issues,
    get_valid_linked_issues,
    unassign_linked_issues_helper,
)

# GitHub author_association values that represent project maintainers.
MAINTAINER_ROLES = frozenset({"OWNER", "MEMBER", "COLLABORATOR"})


class StalePRBot(GitHubBot):
    def __init__(self):
        super().__init__()
        self.DAYS_BEFORE_STALE_WARNING = 7
        self.DAYS_BEFORE_UNASSIGN = 14
        self.DAYS_BEFORE_FINAL_FOLLOWUP = 60
        self.bot_login = os.environ.get("BOT_USERNAME", "openwisp-companion") + "[bot]"

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
        commits=None,
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
        if commits is None:
            commits = pr.get_commits()
        for commit in commits:
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
        commits=None,
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
                commits,
                issue_comments,
                all_reviews,
                review_comments,
            )
            reference_date = last_author_activity or last_changes_requested
            now = datetime.now(timezone.utc)
            return (now - reference_date).days
        except Exception as e:
            print(f"Error calculating activity for PR #{pr.number}: {e}")
            return 0

    def is_waiting_for_maintainer(
        self,
        pr,
        last_changes_requested,
        commits=None,
        issue_comments=None,
        all_reviews=None,
        review_comments=None,
    ):
        """True when the contributor has responded but no maintainer review
        has followed. Comments don't count; errors fail closed (skip).
        """
        try:
            pr_author = pr.user.login if pr.user else None
            if not pr_author:
                return True
            last_author_activity = self._get_last_author_activity(
                pr,
                last_changes_requested,
                commits,
                issue_comments,
                all_reviews,
                review_comments,
            )
            if not last_author_activity:
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
            print(f"Error checking maintainer activity for PR #{pr.number}: {e}")
            return True

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
            print(f"Error getting reviews for PR #{pr.number}: {e}")
            return None

    def has_bot_comment(self, pr, comment_type, after_date=None, issue_comments=None):
        """Check if this bot has already posted a comment with the given
        marker. If ``after_date`` is set, only later comments count.
        """
        try:
            if issue_comments is None:
                issue_comments = list(pr.get_issue_comments())
            marker = f"<!-- bot:{comment_type} -->"
            for comment in issue_comments:
                if (
                    comment.user
                    and comment.user.login == self.bot_login
                    and marker in comment.body
                ):
                    if after_date and comment.created_at <= after_date:
                        continue
                    return True
            return False
        except Exception as e:
            print(f"Error checking bot comments for PR #{pr.number}: {e}")
            return False

    def unassign_linked_issues(self, pr):
        pr_author = pr.user.login if pr.user else None
        if not pr_author:
            return 0
        return len(
            unassign_linked_issues_helper(
                self.repo, self.repository_name, pr.body or "", pr_author
            )
        )

    def _clear_stale_label(self, pr):
        try:
            if "stale" not in {label.name for label in pr.get_labels()}:
                return False
            pr.remove_from_labels("stale")
            return True
        except Exception as e:
            print(f"Could not clear stale label from PR #{pr.number}: {e}")
            return False

    def _reassign_unassigned_linked_issues(self, pr):
        pr_author = pr.user.login if pr.user else None
        if not pr_author:
            return
        try:
            linked = extract_linked_issues(pr.body or "")
            for _, issue in get_valid_linked_issues(
                self.repo, self.repository_name, linked
            ):
                try:
                    if not issue.assignees:
                        issue.add_to_assignees(pr_author)
                except Exception as e:
                    print(f"Error reassigning issue #{issue.number}: {e}")
        except Exception as e:
            print(f"Error iterating linked issues for PR #{pr.number}: {e}")

    def send_final_followup(self, pr, days_inactive):
        try:
            pr_author = pr.user.login if pr.user else None
            if not pr_author:
                return False
            followup_lines = [
                "<!-- bot:final_followup -->",
                f"Hi @{pr_author} 👋,",
                "",
                (
                    f"This PR has been inactive for **{days_inactive} days**"
                    " since changes were requested. Are you still working on it?"
                ),
                "",
                (
                    "If yes, push new commits or reply to let us know."
                    " If you've moved on, please close the PR or comment"
                    " so another contributor can pick it up."
                ),
            ]
            pr.create_issue_comment("\n".join(followup_lines))
            print(f"Sent final follow-up for PR #{pr.number}")
            return True
        except Exception as e:
            print(f"Error sending final follow-up for PR #{pr.number}: {e}")
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
            ]
            unassigned_count = self.unassign_linked_issues(pr)
            pr.create_issue_comment("\n".join(unassign_lines))
            try:
                pr.add_to_labels("stale")
            except Exception as e:
                print(f"Could not add stale label: {e}")
            print(
                f"Marked PR #{pr.number} as stale after {days_inactive} days,"
                f" unassigned {unassigned_count} issues"
            )
            return True
        except Exception as e:
            print(f"Error marking PR #{pr.number} as stale: {e}")
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
            print(f"Error sending warning for PR #{pr.number}: {e}")
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
                    commits = list(pr.get_commits())
                    days_inactive = self.get_days_since_activity(
                        pr,
                        last_changes_requested,
                        commits,
                        issue_comments,
                        all_reviews,
                        review_comments,
                    )
                    print(
                        f"PR #{pr.number}: {days_inactive} days since"
                        " contributor activity"
                    )
                    if self.is_waiting_for_maintainer(
                        pr,
                        last_changes_requested,
                        commits,
                        issue_comments,
                        all_reviews,
                        review_comments,
                    ):
                        # If we previously marked the PR stale, unwind
                        # that state now that the contributor has acted.
                        if self._clear_stale_label(pr):
                            self._reassign_unassigned_linked_issues(pr)
                        print(
                            f"PR #{pr.number}: waiting for maintainer review,"
                            " skipping"
                        )
                        continue
                    stages = (
                        (
                            self.DAYS_BEFORE_STALE_WARNING,
                            self.DAYS_BEFORE_UNASSIGN,
                            "stale_warning",
                            self.send_stale_warning,
                        ),
                        (
                            self.DAYS_BEFORE_UNASSIGN,
                            None,
                            "stale",
                            self.mark_pr_stale,
                        ),
                        (
                            self.DAYS_BEFORE_FINAL_FOLLOWUP,
                            None,
                            "final_followup",
                            self.send_final_followup,
                        ),
                    )
                    posted_stale_this_run = False
                    for low, high, marker, action in stages:
                        if days_inactive < low:
                            continue
                        if high is not None and days_inactive >= high:
                            continue
                        if self.has_bot_comment(
                            pr,
                            marker,
                            after_date=last_changes_requested,
                            issue_comments=issue_comments,
                        ):
                            continue
                        # Don't post final-followup in the same run as stale.
                        if marker == "final_followup" and posted_stale_this_run:
                            continue
                        if action(pr, days_inactive):
                            processed_count += 1
                            if marker == "stale":
                                posted_stale_this_run = True
                except Exception as e:
                    print(f"Error processing PR #{pr.number}: {e}")
                    continue
                finally:
                    time.sleep(0.5)
            print(f"Checked {pr_count} open PRs, processed {processed_count} stale PRs")
            return True
        except Exception as e:
            print(f"Error in process_stale_prs: {e}")
            return False

    def run(self):
        if not self.github or not self.repo:
            print("GitHub client not properly initialized, cannot proceed")
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
