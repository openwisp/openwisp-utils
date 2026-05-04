import json
import os

from base import GitHubBot
from utils import (
    extract_linked_issues,
    get_assignee_logins,
    get_valid_linked_issues,
    user_in_logins,
    verify_assignment,
)


class PRReopenBot(GitHubBot):
    def reassign_issues_to_author(self, pr_number, pr_author, pr_body):
        try:
            reassigned_issues = []
            linked_issues = extract_linked_issues(pr_body)
            for issue_number, issue in get_valid_linked_issues(
                self.repo, self.repository_name, linked_issues
            ):
                try:
                    current_assignees = get_assignee_logins(issue)
                    if current_assignees and not user_in_logins(
                        pr_author, current_assignees
                    ):
                        print(
                            f"Issue #{issue_number} is assigned"
                            " to others:"
                            f' {", ".join(current_assignees)}'
                        )
                        continue
                    if user_in_logins(pr_author, current_assignees):
                        continue
                    issue.add_to_assignees(pr_author)
                    if (
                        verify_assignment(self.repo, issue_number, pr_author)
                        is not True
                    ):
                        print(
                            f"Reassign of #{issue_number} to {pr_author}"
                            " was silently rejected or unverifiable."
                        )
                        continue
                    reassigned_issues.append(issue_number)
                    print(f"Reassigned issue #{issue_number} to {pr_author}")
                    welcome_message = (
                        f"Welcome back, @{pr_author}! 🎉"
                        " This issue has been reassigned"
                        " to you as you've reopened"
                        f" PR #{pr_number}."
                    )
                    issue.create_comment(welcome_message)
                except Exception as e:
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
                print("Removed stale label from" f" PR #{pr_number}")
                return True
            else:
                print("No stale label found on" f" PR #{pr_number}")
                return False
        except Exception as e:
            print("Error removing stale label from" f" PR #{pr_number}: {e}")
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
            print(f"Handling PR #{pr_number}" f" reopen by {pr_author}")
            reassigned = self.reassign_issues_to_author(pr_number, pr_author, pr_body)
            self.remove_stale_label(pr_number)
            print(f"Reassigned {len(reassigned)}" f" issues to {pr_author}")
            return True
        except Exception as e:
            print(f"Error handling reopened PR: {e}")
            return False

    def run(self):
        if not self.github or not self.repo:
            print("GitHub client not properly initialized," " cannot proceed")
            return False
        print("PR Reopen Bot starting" f" for event: {self.event_name}")
        try:
            if self.event_name == "pull_request_target":
                return self.handle_pr_reopen()
            else:
                print(f"Event type '{self.event_name}'" " not supported")
                return True
        except Exception as e:
            print(f"Error in main execution: {e}")
            return False
        finally:
            print("PR Reopen Bot completed")


class PRActivityBot(GitHubBot):
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
                print("Comment is on an issue," " not a PR, skipping")
                return True
            pr = self.repo.get_pull(pr_number)
            if not pr.user or not user_in_logins(commenter, [pr.user.login]):
                print("Comment not from PR author, skipping")
                return True
            labels = [label.name for label in pr.get_labels()]
            if "stale" not in labels:
                print("PR is not stale, skipping")
                return True
            try:
                pr.remove_from_labels("stale")
                print("Removed stale label")
            except Exception as e:
                print(f"Could not remove stale label: {e}")
            reassigned_count = 0
            linked_issues = extract_linked_issues(pr.body or "")
            for issue_number, issue in get_valid_linked_issues(
                self.repo, self.repository_name, linked_issues
            ):
                try:
                    if get_assignee_logins(issue):
                        continue
                    issue.add_to_assignees(commenter)
                    if (
                        verify_assignment(self.repo, issue_number, commenter)
                        is not True
                    ):
                        print(
                            f"Reassign of #{issue_number} to {commenter}"
                            " was silently rejected or unverifiable."
                        )
                        continue
                    reassigned_count += 1
                    print(f"Reassigned issue #{issue_number} to {commenter}")
                except Exception as e:
                    print(f"Error reassigning issue #{issue_number}: {e}")
            if reassigned_count > 0:
                encouragement_message = (
                    f"Thanks for following up, @{commenter}! 🙌"
                    " The stale status has been removed and"
                    " the linked issue(s) have been reassigned"
                    " to you. Looking forward to your updates!"
                )
                pr.create_issue_comment(encouragement_message)
            print(
                "Handled contributor activity," f" reassigned {reassigned_count} issues"
            )
            return True
        except Exception as e:
            print(f"Error handling contributor activity: {e}")
            return False

    def run(self):
        if not self.github or not self.repo:
            print("GitHub client not properly initialized," " cannot proceed")
            return False
        print("PR Activity Bot starting" f" for event: {self.event_name}")
        try:
            if self.event_name == "issue_comment":
                return self.handle_contributor_activity()
            else:
                print(f"Event type '{self.event_name}'" " not supported")
                return True
        except Exception as e:
            print(f"Error in main execution: {e}")
            return False
        finally:
            print("PR Activity Bot completed")


def main():
    import sys

    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1], "r") as f:
                event_payload = json.load(f)
            event_name = os.environ.get("GITHUB_EVENT_NAME", "")
            if event_name == "issue_comment":
                bot = PRActivityBot()
            else:
                bot = PRReopenBot()
            bot.load_event_payload(event_payload)
            result = bot.run()
            return 0 if result else 1
        except Exception as e:
            print(f"Error running bot: {e}")
            return 1
    else:
        print("Usage: python pr_reopen_bot.py" " <event_payload.json>")
        return 1


if __name__ == "__main__":
    main()
