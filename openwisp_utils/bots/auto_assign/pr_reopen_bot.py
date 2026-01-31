import json
import os

from .base import GitHubBot
from .utils import extract_linked_issues


class PRReopenBot(GitHubBot):
    def __init__(self):
        super().__init__()

    def reassign_issues_to_author(self, pr_number, pr_author, pr_body):
        try:
            linked_issues = extract_linked_issues(pr_body)
            if not linked_issues:
                print("No linked issues found in PR body")
                return []

            reassigned_issues = []

            for issue_number in linked_issues:
                try:
                    issue = self.repo.get_issue(issue_number)
                    if issue.pull_request:
                        print(f"#{issue_number} is a PR, skipping")
                        continue

                    current_assignees = [assignee.login for assignee in issue.assignees]
                    if current_assignees and pr_author not in current_assignees:
                        print(
                            f'Issue #{issue_number} is assigned to others: {", ".join(current_assignees)}'
                        )
                        continue

                    if pr_author not in current_assignees:
                        issue.add_to_assignees(pr_author)
                        reassigned_issues.append(issue_number)
                        print(f"Reassigned issue #{issue_number} to {pr_author}")

                        welcome_message = (
                            f"Welcome back, @{pr_author}! 🎉 This issue has been reassigned to you "
                            f"as you've reopened PR #{pr_number}."
                        )
                        issue.create_comment(welcome_message)

                except Exception as e:
                    if "404" in str(e):
                        print(f"Issue #{issue_number} not found")
                    else:
                        print(f"Error processing issue #{issue_number}: {e}")

            return reassigned_issues

        except Exception as e:
            print(f"Error in reassign_issues_to_author: {e}")
            return []

    def remove_stale_label(self, pr_number):
        try:
            pr = self.repo.get_pull(pr_number)
            labels = [label.name for label in pr.get_labels()]

            if "stale" in labels:
                pr.remove_from_labels("stale")
                print(f"Removed stale label from PR #{pr_number}")
                return True
            else:
                print(f"No stale label found on PR #{pr_number}")
                return False

        except Exception as e:
            print(f"Error removing stale label from PR #{pr_number}: {e}")
            return False

    def handle_pr_reopen(self):
        if not self.event_payload:
            print("No event payload available")
            return False

        try:
            pr = self.event_payload.get("pull_request", {})
            pr_number = pr.get("number")
            pr_author = pr.get("user", {}).get("login", "")
            pr_body = pr.get("body", "")

            if not all([pr_number, pr_author]):
                print("Missing required PR data")
                return False

            print(f"Handling PR #{pr_number} reopen by {pr_author}")
            reassigned = self.reassign_issues_to_author(pr_number, pr_author, pr_body)
            label_removed = self.remove_stale_label(pr_number)

            print(f"Reassigned {len(reassigned)} issues to {pr_author}")
            return len(reassigned) > 0 or label_removed

        except Exception as e:
            print(f"Error handling PR reopen: {e}")
            return False

    def run(self):
        if not self.github or not self.repo:
            print("GitHub client not properly initialized, cannot proceed")
            return False

        print(f"PR Reopen Bot starting for event: {self.event_name}")

        try:
            if self.event_name == "pull_request_target":
                return self.handle_pr_reopen()
            else:
                print(f"Event type '{self.event_name}' not supported")
                return False

        except Exception as e:
            print(f"Error in main execution: {e}")
            return False
        finally:
            print("PR Reopen Bot completed")


class PRActivityBot(GitHubBot):
    def __init__(self):
        super().__init__()

    def handle_contributor_activity(self):
        if not self.event_payload:
            print("No event payload available")
            return False

        try:
            issue_data = self.event_payload.get("issue", {})
            pr_number = issue_data.get("number")
            commenter = (
                self.event_payload.get("comment", {}).get("user", {}).get("login", "")
            )

            if not all([pr_number, commenter]):
                print("Missing required comment data")
                return False
            if not issue_data.get("pull_request"):
                print("Comment is on an issue, not a PR, skipping")
                return False

            pr = self.repo.get_pull(pr_number)
            if commenter != pr.user.login:
                print("Comment not from PR author, skipping")
                return False

            labels = [label.name for label in pr.get_labels()]
            if "stale" not in labels:
                print("PR is not stale, skipping")
                return False

            try:
                pr.remove_from_labels("stale")
                print("Removed stale label")
            except Exception as e:
                print(f"Could not remove stale label: {e}")

            linked_issues = extract_linked_issues(pr.body or "")
            reassigned_count = 0

            for issue_number in linked_issues:
                try:
                    issue = self.repo.get_issue(issue_number)

                    if issue.pull_request:
                        continue

                    current_assignees = [assignee.login for assignee in issue.assignees]

                    if not current_assignees:
                        issue.add_to_assignees(commenter)
                        reassigned_count += 1
                        print(f"Reassigned issue #{issue_number} to {commenter}")

                except Exception as e:
                    print(f"Error reassigning issue #{issue_number}: {e}")

            if reassigned_count > 0:
                encouragement_message = (
                    f"Thanks for following up, @{commenter}! 🙌 The stale status has been removed "
                    "and the linked issue(s) have been reassigned to you. Looking forward to your updates!"
                )
                pr.create_issue_comment(encouragement_message)

            print(f"Handled contributor activity, reassigned {reassigned_count} issues")
            return True

        except Exception as e:
            print(f"Error handling contributor activity: {e}")
            return False

    def run(self):
        if not self.github or not self.repo:
            print("GitHub client not properly initialized, cannot proceed")
            return False

        print(f"PR Activity Bot starting for event: {self.event_name}")

        try:
            if self.event_name == "issue_comment":
                return self.handle_contributor_activity()
            else:
                print(f"Event type '{self.event_name}' not supported")
                return False

        except Exception as e:
            print(f"Error in main execution: {e}")
            return False
        finally:
            print("PR Activity Bot completed")


def main():
    import sys

    if len(sys.argv) > 1:
        # Determine which bot to use based on event type in the payload
        try:
            with open(sys.argv[1], "r") as f:
                event_payload = json.load(f)

            # Check event type to determine bot
            event_name = os.environ.get("GITHUB_EVENT_NAME", "")
            if event_name == "issue_comment":
                bot = PRActivityBot()
            else:
                bot = PRReopenBot()

            bot.load_event_payload(event_payload)
            bot.run()
        except Exception as e:
            print(f"Error running bot: {e}")
    else:
        print("Usage: python pr_reopen_bot.py <event_payload.json>")


if __name__ == "__main__":
    main()
