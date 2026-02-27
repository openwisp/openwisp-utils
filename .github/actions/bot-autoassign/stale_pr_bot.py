"""Stale PR Management Bot - Automated stale PR detection and management"""

import time
from datetime import datetime, timezone

from base import GitHubBot
from utils import extract_linked_issues


class StalePRBot(GitHubBot):
    def __init__(self):
        super().__init__()
        self.DAYS_BEFORE_STALE_WARNING = 7
        self.DAYS_BEFORE_UNASSIGN = 14
        self.DAYS_BEFORE_CLOSE = 60

    def get_days_since_activity(
        self,
        pr,
        last_changes_requested,
        issue_comments=None,
        all_reviews=None,
        review_comments=None,
    ):
        """Calculate days since last contributor activity after changes requested"""
        if not last_changes_requested:
            return 0

        try:
            pr_author = pr.user.login
            last_author_activity = None

            commits = list(pr.get_commits()[:50])
            for commit in commits:
                commit_date = commit.commit.author.date
                if commit_date > last_changes_requested:
                    if commit.author and commit.author.login == pr_author:
                        if (
                            not last_author_activity
                            or commit_date > last_author_activity
                        ):
                            last_author_activity = commit_date

            if issue_comments is None:
                issue_comments = list(pr.get_issue_comments())
            comments = (
                issue_comments[-20:] if len(issue_comments) > 20 else issue_comments
            )
            for comment in comments:
                if comment.user.login == pr_author:
                    comment_date = comment.created_at
                    if comment_date > last_changes_requested:
                        if (
                            not last_author_activity
                            or comment_date > last_author_activity
                        ):
                            last_author_activity = comment_date

            if review_comments is None:
                review_comments = list(pr.get_review_comments())
            all_review_comments = review_comments
            review_comments = (
                all_review_comments[-20:]
                if len(all_review_comments) > 20
                else all_review_comments
            )
            for comment in review_comments:
                if comment.user.login == pr_author:
                    comment_date = comment.created_at
                    if comment_date > last_changes_requested:
                        if (
                            not last_author_activity
                            or comment_date > last_author_activity
                        ):
                            last_author_activity = comment_date

            if all_reviews is None:
                all_reviews = list(pr.get_reviews())
            reviews = all_reviews[-20:] if len(all_reviews) > 20 else all_reviews
            for review in reviews:
                if review.user.login == pr_author:
                    review_date = review.submitted_at
                    if review_date and review_date > last_changes_requested:
                        if (
                            not last_author_activity
                            or review_date > last_author_activity
                        ):
                            last_author_activity = review_date

            reference_date = last_author_activity or last_changes_requested
            now = datetime.now(timezone.utc)
            return (now - reference_date).days

        except Exception as e:
            print(f"Error calculating activity for PR #{pr.number}: {e}")
            return 0

    def get_last_changes_requested(self, pr, all_reviews=None):
        """Get the date of the most recent 'changes_requested' review"""
        try:
            if all_reviews is None:
                all_reviews = list(pr.get_reviews())
            reviews = all_reviews[-50:] if len(all_reviews) > 50 else all_reviews
            changes_requested_reviews = [
                r for r in reviews if r.state == "CHANGES_REQUESTED"
            ]

            if not changes_requested_reviews:
                return None

            changes_requested_reviews.sort(key=lambda r: r.submitted_at, reverse=True)
            return changes_requested_reviews[0].submitted_at

        except Exception as e:
            print(f"Error getting reviews for PR #{pr.number}: {e}")
            return None

    def has_bot_comment(self, pr, comment_type, after_date=None, issue_comments=None):
        """Check if PR already has a specific type of bot comment using HTML markers.

        If ``after_date`` is provided, only considers comments posted
        after that date. This prevents stale markers from old cycles
        suppressing new warnings after activity resumes.
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
            print(f"Error checking bot comments for PR #{pr.number}: {e}")
            return False

    def unassign_linked_issues(self, pr):
        """Unassign linked issues from PR author"""
        try:
            linked_issues = extract_linked_issues(pr.body or "")
            pr_author = pr.user.login
            unassigned_count = 0

            for issue_number in linked_issues:
                try:
                    issue = self.repo.get_issue(issue_number)
                    if (
                        hasattr(issue, "repository")
                        and issue.repository.full_name != self.repository_name
                    ):
                        print(
                            f"Issue #{issue_number} is from a "
                            "different repository, skipping"
                        )
                        continue

                    if issue.pull_request:
                        continue
                    assignees = [
                        assignee.login
                        for assignee in issue.assignees
                        if hasattr(assignee, "login")
                    ]
                    if pr_author in assignees:
                        issue.remove_from_assignees(pr_author)
                        unassigned_count += 1
                        print(f"Unassigned {pr_author} from issue #{issue_number}")

                except Exception as e:
                    print(f"Error unassigning issue #{issue_number}: {e}")

            return unassigned_count

        except Exception as e:
            print(f"Error processing linked issues for PR #{pr.number}: {e}")
            return 0

    def close_stale_pr(self, pr, days_inactive):
        """Close PR after extended inactivity"""
        # Check if PR is already closed
        if pr.state == "closed":
            print(f"PR #{pr.number} is already closed, skipping")
            return False

        try:
            pr_author = pr.user.login

            close_lines = [
                "<!-- bot:closed -->",
                f"Hi @{pr_author} 👋,",
                "",
                f"This pull request has been automatically closed due to "
                f"**{days_inactive} days of inactivity**.",
                "After changes were requested, the PR remained inactive.",
                "",
                "We understand that life gets busy, and we appreciate "
                "your initial contribution! 💙",
                "",
                "**The door is always open** for you to come back:",
                "- You can **reopen this PR** at any time",
                "  if you'd like to continue working on it",
                "- Feel free to push new commits",
                "  addressing the requested changes",
                "- If you reopen the PR, the linked issue will be",
                "  reassigned to you",
                "",
                "If you have any questions or need help,",
                "don't hesitate to reach out. We're here to support you!",
                "",
                "Thank you for your interest in contributing " "to OpenWISP! 🙏",
            ]

            pr.edit(state="closed")
            pr.create_issue_comment("\n".join(close_lines))

            unassigned_count = self.unassign_linked_issues(pr)
            print(
                f"Closed PR #{pr.number} after {days_inactive} days of "
                f"inactivity, unassigned {unassigned_count} issues"
            )

            return True

        except Exception as e:
            print(f"Error closing PR #{pr.number}: {e}")
            return False

    def mark_pr_stale(self, pr, days_inactive):
        """Mark PR as stale after moderate inactivity"""
        try:
            pr_author = pr.user.login

            unassign_lines = [
                "<!-- bot:stale -->",
                f"Hi @{pr_author} 👋,",
                "",
                (
                    f"This pull request has been marked as **stale** due to "
                    f"**{days_inactive} days of inactivity** after changes "
                    "were requested."
                ),
                "",
                (
                    "As a result, **the linked issue(s) have been "
                    "unassigned** from you to allow other contributors "
                    "to work on it."
                ),
                "",
                "However, **you can still continue working on this PR**! "
                "If you push new commits",
                "or respond to the review feedback:",
                "- The issue will be reassigned to you",
                "- Your contribution is still very welcome",
                "",
                "If you need more time or have questions about the "
                "requested changes, please let us know.",
                "We're happy to help! 🤝",
                "",
                (
                    f"If there's no further activity within "
                    f"**{self.DAYS_BEFORE_CLOSE - days_inactive} "
                    "more days**, this PR will be automatically closed "
                    "(but can be reopened anytime)."
                ),
            ]

            pr.create_issue_comment("\n".join(unassign_lines))

            unassigned_count = self.unassign_linked_issues(pr)
            try:
                pr.add_to_labels("stale")
            except Exception as e:
                print(f"Could not add stale label: {e}")

            print(
                f"Marked PR #{pr.number} as stale after {days_inactive} "
                f"days, unassigned {unassigned_count} issues"
            )
            return True

        except Exception as e:
            print(f"Error marking PR #{pr.number} as stale: {e}")
            return False

    def send_stale_warning(self, pr, days_inactive):
        """Send warning about upcoming stale status"""
        try:
            pr_author = pr.user.login

            remaining = self.DAYS_BEFORE_UNASSIGN - days_inactive

            warning_lines = [
                "<!-- bot:stale_warning -->",
                f"Hi @{pr_author} 👋,",
                "",
                (
                    "This is a friendly reminder that this pull request "
                    f"has had **no activity for {days_inactive} days** "
                    "since changes were requested."
                ),
                "",
                "We'd love to see this contribution merged! "
                "Please take a moment to:",
                "- Address the review feedback",
                "- Push your changes",
                "- Let us know if you have any questions " "or need clarification",
                "",
                "If you're busy or need more time, no worries! "
                "Just leave a comment to let us know",
                "you're still working on it.",
                "",
                (
                    f"**Note:** within **{remaining} more days**, "
                    "the linked issue will be unassigned to allow "
                    "other contributors to work on it."
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
        """Process all open PRs for stale management"""
        if not self.repo:
            print("GitHub repository not initialized")
            return

        try:
            open_prs = self.repo.get_pulls(state="open")
            print(f"Found {open_prs.totalCount} open pull requests")

            processed_count = 0

            for pr in open_prs:
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
                        f"PR #{pr.number}: {days_inactive} days "
                        "since contributor activity"
                    )
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

                    time.sleep(0.1)

                except Exception as e:
                    print(f"Error processing PR #{pr.number}: {e}")
                    continue

            print(f"Processed {processed_count} stale PRs")

        except Exception as e:
            print(f"Error in process_stale_prs: {e}")

    def run(self):
        """Main execution flow"""
        if not self.github or not self.repo:
            print("GitHub client not properly initialized, cannot proceed")
            return False

        print("Stale PR Management Bot starting...")

        try:
            self.process_stale_prs()
            return True
        except Exception as e:
            print(f"Error in main execution: {e}")
            return False
        finally:
            print("Stale PR Management Bot completed")


def main():
    """Entry point for command line usage"""
    bot = StalePRBot()
    bot.run()


if __name__ == "__main__":
    main()
