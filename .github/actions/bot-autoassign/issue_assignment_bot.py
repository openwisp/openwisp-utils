"""Issue Assignment Bot - Automated issue assignment and PR management"""

import re

from base import GitHubBot
from github import GithubException
from utils import extract_linked_issues


class IssueAssignmentBot(GitHubBot):
    def __init__(self):
        super().__init__()

    def is_assignment_request(self, comment_body):
        """Check if comment is requesting assignment"""
        if not comment_body:
            return False

        comment_lower = comment_body.lower()
        assignment_phrases = [
            "assign this issue to me",
            "assign me",
            "can i work on this",
            "i would like to work on this",
            "i want to work on this",
            "please assign this to me",
            "can you assign this to me",
        ]
        return any(phrase in comment_lower for phrase in assignment_phrases)

    def get_contributing_guidelines_url(self):
        """Get the contributing guidelines URL for the repository"""
        return "https://openwisp.io/docs/developer/contributing.html"

    def detect_issue_type(self, issue):
        """Intelligently detect issue type.

        Analyzes labels, title and body and returns 'bug', 'feature', or
        None.
        """
        bug_keywords = [
            "bug",
            "error",
            "crash",
            "fail",
            "broken",
            "problem",
            "not working",
            "doesn't work",
            "does not work",
            "fix",
            "incorrect",
            "wrong",
            "exception",
            "traceback",
            "breaking",
            "regression",
        ]

        feature_keywords = [
            "feature",
            "enhancement",
            "add",
            "implement",
            "support",
            "new",
            "create",
            "allow",
            "enable",
            "improve",
            "improvement",
            "upgrade",
            "extend",
            "functionality",
            "capability",
            "ability",
            "option",
        ]

        issue_labels = [label.name.lower() for label in issue.labels]
        if any(label in issue_labels for label in ["bug", "bugfix", "fix"]):
            return "bug"
        elif any(
            label in issue_labels for label in ["feature", "enhancement", "improvement"]
        ):
            return "feature"

        title = (issue.title or "").lower()
        body = (issue.body or "").lower()
        combined_text = f"{title} {body}"

        # Use word boundary matching to avoid false positives
        bug_score = sum(
            1
            for keyword in bug_keywords
            if re.search(rf"\b{re.escape(keyword)}\b", combined_text)
        )
        feature_score = sum(
            1
            for keyword in feature_keywords
            if re.search(rf"\b{re.escape(keyword)}\b", combined_text)
        )

        if bug_score > feature_score and bug_score > 0:
            return "bug"
        elif feature_score > bug_score and feature_score > 0:
            return "feature"

        return None

    def respond_to_assignment_request(self, issue_number, commenter):
        """Respond to assignment request with contributing guidelines"""
        if not self.repo:
            print("GitHub client not initialized")
            return False

        try:
            contributing_url = self.get_contributing_guidelines_url()
            issue = self.repo.get_issue(issue_number)

            issue_type = self.detect_issue_type(issue)
            suggested_keyword = None
            detection_reason = ""

            if issue_type == "bug":
                suggested_keyword = "Fixes"
                detection_reason = "this appears to be a bug"
            elif issue_type == "feature":
                suggested_keyword = "Closes"
                detection_reason = "this appears to be a feature or enhancement"

            if suggested_keyword:
                linking_instruction = (
                    f"**Link your PR to this issue** by including "
                    f"`{suggested_keyword} #{issue_number}` in the PR description"
                )
                keyword_explanation = (
                    "\n\n**Note**: We suggest "
                    f"`{suggested_keyword}` because {detection_reason}. You can also use:\n"
                    f"- `Closes #{issue_number}` for features/changes\n"
                    f"- `Fixes #{issue_number}` for bugs\n"
                    f"- `Related to #{issue_number}` for PRs that contribute\n"
                    f"  but don't completely solve the issue"
                )
            else:
                linking_instruction = (
                    "**Link your PR to this issue** by including one of the following "
                    "in the PR description:\n"
                    f"   - `Closes #{issue_number}` for features/changes\n"
                    f"   - `Fixes #{issue_number}` for bugs\n"
                    f"   - `Related to #{issue_number}` for PRs that contribute\n"
                    f"     but don't completely solve the issue"
                )
                keyword_explanation = ""

            message_lines = [
                f"Hi @{commenter} 👋,",
                "",
                "Thank you for your interest in contributing to OpenWISP! 🎉",
                "",
                (
                    f"According to our [contributing guidelines]({contributing_url}),"
                    " **you don't need to wait to be assigned** to start working on an issue."
                ),
                "We encourage you to:",
                "",
                "1. **Fork the repository** and start working on your solution",
                (
                    "2. **Open a Pull Request (PR) as soon as possible** - even as a draft "
                    "if it's still in progress"
                ),
                f"3. {linking_instruction}{keyword_explanation}",
                "",
                (
                    "Once you open a PR that references this issue, you will be automatically "
                    "assigned to it."
                ),
                "",
                "This approach helps us:",
                "- See your progress and provide early feedback",
                "- Avoid multiple contributors working on the same issue unknowingly",
                "- Keep the contribution process moving smoothly",
                "",
                (
                    "We look forward to your contribution! If you have any questions, "
                    "feel free to ask in the PR or check our "
                    f"[documentation]({contributing_url})."
                ),
                "",
                "Happy coding! 🚀",
            ]
            message = "\n".join(message_lines)

            issue.create_comment(message)
            print(f"Posted assignment response to issue #{issue_number}")
            return True
        except Exception as e:
            print(f"Error responding to assignment request: {e}")
            return False

    def auto_assign_issues_from_pr(self, pr_number, pr_author, pr_body, max_issues=10):
        """Auto-assign linked issues to PR author"""
        if not self.repo:
            print("GitHub client not initialized")
            return []

        try:
            linked_issues = extract_linked_issues(pr_body)
            if not linked_issues:
                print("No linked issues found in PR body")
                return []

            if len(linked_issues) > max_issues:
                print(
                    f"Found {len(linked_issues)} issue references, processing "
                    f"first {max_issues} to avoid rate limits"
                )
                linked_issues = sorted(linked_issues)[:max_issues]

            assigned_issues = []

            for issue_number in linked_issues:
                try:
                    issue = self.repo.get_issue(issue_number)
                    if issue.pull_request:
                        print(f"#{issue_number} is a pull request, skipping")
                        continue

                    current_assignees = [assignee.login for assignee in issue.assignees]
                    if current_assignees:
                        if pr_author in current_assignees:
                            print(
                                f"Issue #{issue_number} already assigned "
                                f"to {pr_author}"
                            )
                        else:
                            print(
                                f"Issue #{issue_number} already assigned "
                                f'to: {", ".join(current_assignees)}'
                            )
                        continue

                    issue.add_to_assignees(pr_author)
                    assigned_issues.append(issue_number)
                    print(f"Assigned issue #{issue_number} to {pr_author}")
                    comment_message = (
                        f"This issue has been automatically assigned to @{pr_author} "
                        f"who opened PR #{pr_number} to address it. 🎯"
                    )
                    issue.create_comment(comment_message)

                except GithubException as e:
                    if e.status == 404:
                        print(f"Issue #{issue_number} not found")
                    else:
                        print(f"Error processing issue #{issue_number}: {e}")
                except Exception as e:
                    print(f"Error processing issue #{issue_number}: {e}")
            return assigned_issues
        except Exception as e:
            print(f"Error in auto_assign_issues_from_pr: {e}")
            return []

    def unassign_issues_from_pr(self, pr_body, pr_author):
        """Unassign linked issues from PR author"""
        if not self.repo:
            print("GitHub client not initialized")
            return []

        try:
            linked_issues = extract_linked_issues(pr_body)
            if not linked_issues:
                return []

            unassigned_issues = []

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
                        print(f"#{issue_number} is a PR, skipping unassignment")
                        continue

                    current_assignees = [
                        assignee.login
                        for assignee in issue.assignees
                        if hasattr(assignee, "login")
                    ]
                    if pr_author in current_assignees:
                        issue.remove_from_assignees(pr_author)
                        unassigned_issues.append(issue_number)
                        print(f"Unassigned {pr_author} from issue #{issue_number}")

                except Exception as e:
                    print(f"Error unassigning issue #{issue_number}: {e}")

            return unassigned_issues

        except Exception as e:
            print(f"Error in unassign_issues_from_pr: {e}")
            return []

    def handle_issue_comment(self):
        """Handle issue comment events"""
        if not self.event_payload:
            print("No event payload available")
            return False

        try:
            if self.event_payload.get("issue", {}).get("pull_request"):
                print("Comment is on a PR, not an issue - skipping")
                return False

            comment = self.event_payload.get("comment", {})
            issue = self.event_payload.get("issue", {})

            comment_body = comment.get("body", "")
            commenter = comment.get("user", {}).get("login", "")
            issue_number = issue.get("number")

            if not all([comment_body, commenter, issue_number]):
                print("Missing required comment data")
                return False

            if self.is_assignment_request(comment_body):
                return self.respond_to_assignment_request(issue_number, commenter)

            print("Comment does not contain assignment request")
            return False

        except Exception as e:
            print(f"Error handling issue comment: {e}")
            return False

    def handle_pull_request(self):
        """Handle pull request events (opened, reopened)"""
        if not self.event_payload:
            print("No event payload available")
            return False

        try:
            pr = self.event_payload.get("pull_request", {})
            action = self.event_payload.get("action", "")

            pr_number = pr.get("number")
            pr_author = pr.get("user", {}).get("login", "")
            pr_body = pr.get("body", "")

            if not all([pr_number, pr_author]):
                print("Missing required PR data")
                return False

            if action in ["opened", "reopened"]:
                assigned_issues = self.auto_assign_issues_from_pr(
                    pr_number, pr_author, pr_body
                )
                return len(assigned_issues) > 0
            elif action == "closed":
                unassigned_issues = self.unassign_issues_from_pr(pr_body, pr_author)
                return len(unassigned_issues) > 0

            print(f"PR action '{action}' not handled")
            return False

        except Exception as e:
            print(f"Error handling pull request: {e}")
            return False

    def run(self):
        """Main execution flow"""
        if not self.github or not self.repo:
            print("GitHub client not properly initialized, cannot proceed")
            return False

        print(f"Issue Assignment Bot starting for event: {self.event_name}")

        try:
            if self.event_name == "issue_comment":
                return self.handle_issue_comment()
            elif self.event_name == "pull_request_target":
                return self.handle_pull_request()
            else:
                print(f"Event type '{self.event_name}' not supported")
                return False

        except Exception as e:
            print(f"Error in main execution: {e}")
            return False
        finally:
            print("Issue Assignment Bot completed")


def main():
    """Entry point for command line usage"""
    import json
    import sys

    bot = IssueAssignmentBot()
    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1], "r") as f:
                event_payload = json.load(f)
                bot.load_event_payload(event_payload)
        except Exception as e:
            print(f"Could not load event payload: {e}")
            return

    bot.run()


if __name__ == "__main__":
    main()
