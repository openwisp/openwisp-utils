import os
import re
import time

from base import GitHubBot
from utils import (
    extract_linked_issues,
    find_open_pr_for_issue,
    get_valid_linked_issues,
    unassign_linked_issues_helper,
    user_in_logins,
)

VERIFICATION_RETRY_DELAY_SECONDS = 1.0


class IssueAssignmentBot(GitHubBot):
    def __init__(self):
        super().__init__()
        self.bot_username = os.environ.get("BOT_USERNAME", "openwisp-companion")

    def is_bot_assign_command(self, comment_body):
        if not comment_body:
            return False
        pattern = rf"(?<![\w-])@{re.escape(self.bot_username)}\s+assign\b"
        return bool(re.search(pattern, comment_body, re.IGNORECASE))

    def is_assignment_request(self, comment_body):
        if not comment_body:
            return False
        comment_lower = comment_body.lower()
        assignment_patterns = [
            r"\bassign this issue to me\b",
            r"\bassign me\b",
            r"\bcan i work on this\b",
            r"\bi would like to work on this\b",
            r"\bi want to work on this\b",
            r"\bplease assign this to me\b",
            r"\bcan you assign this to me\b",
        ]
        return any(re.search(pattern, comment_lower) for pattern in assignment_patterns)

    def get_contributing_guidelines_url(self):
        return "https://openwisp.io/docs/stable/developer/contributing.html"

    def detect_issue_type(self, issue):
        """Analyzes labels, title and body.

        Returns 'bug', 'feature', or None.
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
                    "**Link your PR to this issue** by including "
                    f"`{suggested_keyword} #{issue_number}`"
                    " in the PR description"
                )
                keyword_explanation = (
                    "\n\n**Note**: We suggest "
                    f"`{suggested_keyword}` because"
                    f" {detection_reason}. "
                    "You can also use:\n"
                    f"- `Closes #{issue_number}`"
                    " for features/changes\n"
                    f"- `Fixes #{issue_number}` for bugs\n"
                    f"- `Related to #{issue_number}`"
                    " for PRs that contribute "
                    "but don't completely solve the issue"
                )
            else:
                linking_instruction = (
                    "**Link your PR to this issue** by"
                    " including one of the following "
                    "in the PR description:\n"
                    f"   - `Closes #{issue_number}`"
                    " for features/changes\n"
                    f"   - `Fixes #{issue_number}` for bugs\n"
                    f"   - `Related to #{issue_number}`"
                    " for PRs that contribute "
                    "but don't completely solve the issue"
                )
                keyword_explanation = ""
            message_lines = [
                f"Hi @{commenter} 👋,",
                "",
                ("Thank you for your interest in" " contributing to OpenWISP! 🎉"),
                "",
                (
                    "According to our [contributing guidelines]"
                    f"({contributing_url}), **you don't need to"
                    " wait to be assigned** to start working"
                    " on an issue."
                ),
                "We encourage you to:",
                "",
                ("1. **Fork the repository** and start" " working on your solution"),
                (
                    "2. **Open a Pull Request (PR) as soon as"
                    " possible** - even as a draft if it's"
                    " still in progress"
                ),
                f"3. {linking_instruction}{keyword_explanation}",
                "",
                (
                    "Once you open a PR that references this"
                    " issue, you will be automatically"
                    " assigned to it."
                ),
                "",
                "This approach helps us:",
                "- See your progress and provide early feedback",
                (
                    "- Avoid multiple contributors working"
                    " on the same issue unknowingly"
                ),
                "- Keep the contribution process moving smoothly",
                "",
                (
                    "We look forward to your contribution!"
                    " If you have any questions, feel free"
                    " to ask in the PR or check our"
                    f" [documentation]({contributing_url})."
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

    @staticmethod
    def _get_assignee_logins(issue):
        return [a.login for a in issue.assignees if hasattr(a, "login")]

    def _verify_assignment(self, issue_number, user):
        """Re-fetch to confirm `user` was assigned. Returns True/False
        on verified state, None when every fetch errored — caller
        stays silent on None since the true state is unknown.
        """
        had_successful_fetch = False
        for attempt in range(2):
            try:
                updated_issue = self.repo.get_issue(issue_number)
                had_successful_fetch = True
                if user_in_logins(user, self._get_assignee_logins(updated_issue)):
                    return True
            except Exception as e:
                print(
                    f"Error verifying assignment for #{issue_number}"
                    f" (attempt {attempt + 1}/2): {e}"
                )
            if attempt == 0:
                time.sleep(VERIFICATION_RETRY_DELAY_SECONDS)
        return False if had_successful_fetch else None

    def _cannot_auto_assign_message(self, pr_author, pr_number):
        return (
            f"Hi @{pr_author} 👋,\n\n"
            f"Thank you for opening PR #{pr_number} to address this issue!\n\n"
            "GitHub did not allow the bot to assign this issue to you"
            " automatically, because you are not yet an organization"
            " member and have not previously commented on this issue.\n\n"
            f"To get assigned, please comment `@{self.bot_username} assign`"
            " on this issue. Your comment satisfies GitHub's requirement"
            " and the bot will then assign the issue to you."
        )

    def handle_bot_assign_request(self, issue_number, commenter):
        if not self.repo:
            print("GitHub client not initialized")
            return False
        try:
            issue = self.repo.get_issue(issue_number)
            if (
                hasattr(issue, "repository")
                and issue.repository.full_name != self.repository_name
            ):
                print(
                    f"Issue #{issue_number} is from a different"
                    " repository, ignoring bot command"
                )
                return True
            if issue.pull_request:
                print(f"#{issue_number} is a PR, ignoring bot command")
                return True
            if getattr(issue, "state", "open") == "closed":
                print(f"#{issue_number} is closed, ignoring bot command")
                return True
            if user_in_logins(commenter, self._get_assignee_logins(issue)):
                print(f"{commenter} is already assigned to #{issue_number}")
                return True
            try:
                pr = find_open_pr_for_issue(
                    self.github, self.repository_name, commenter, issue_number
                )
            except Exception as e:
                # Don't post "no PR found" on a search error — that's
                # not the same as a verified miss.
                print(f"Error searching open PRs by {commenter}: {e}")
                return True
            if pr is None:
                issue.create_comment(
                    f"Hi @{commenter} 👋,\n\n"
                    "I could not find an open PR by you that references"
                    f" this issue (#{issue_number}). Please open a PR"
                    f" linking to this issue (e.g. `Fixes #{issue_number}`)"
                    f" and then comment `@{self.bot_username} assign` again."
                )
                return True
            issue.add_to_assignees(commenter)
            verified = self._verify_assignment(issue_number, commenter)
            if verified is True:
                issue.create_comment(
                    f"This issue has been assigned to @{commenter}"
                    f" who opened PR #{pr.number} to address it. 🎯"
                )
                print(f"Assigned #{issue_number} to {commenter} via bot command")
            elif verified is False:
                # Commenter has commented but the assignment still
                # failed (perm block, outage, etc.).
                issue.create_comment(
                    f"Sorry @{commenter}, GitHub still did not allow"
                    " this assignment. A maintainer will need to assign"
                    " this issue manually."
                )
                print(
                    f"Bot-command assignment of #{issue_number} to"
                    f" {commenter} was silently rejected."
                )
            else:
                print(
                    f"Skipping comment for #{issue_number}:"
                    " assignment state could not be verified."
                )
            return True
        except Exception as e:
            print(f"Error handling bot assign command: {e}")
            return False

    def auto_assign_issues_from_pr(self, pr_number, pr_author, pr_body, max_issues=10):
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
                    f"Found {len(linked_issues)} issue references,"
                    f" processing first {max_issues}"
                    " to avoid rate limits"
                )
            assigned_issues = []
            for issue_number, issue in get_valid_linked_issues(
                self.repo, self.repository_name, linked_issues
            ):
                if len(assigned_issues) >= max_issues:
                    break
                try:
                    if getattr(issue, "state", "open") == "closed":
                        print(
                            f"Issue #{issue_number} is closed, skipping"
                            " auto-assignment"
                        )
                        continue
                    current_assignees = self._get_assignee_logins(issue)
                    if current_assignees:
                        if user_in_logins(pr_author, current_assignees):
                            print(
                                f"Issue #{issue_number} already"
                                f" assigned to {pr_author}"
                            )
                        else:
                            print(
                                f"Issue #{issue_number} already"
                                " assigned to:"
                                f' {", ".join(current_assignees)}'
                            )
                        continue
                    issue.add_to_assignees(pr_author)
                    verified = self._verify_assignment(issue_number, pr_author)
                    if verified is True:
                        assigned_issues.append(issue_number)
                        print(f"Assigned issue #{issue_number} to {pr_author}")
                        comment_message = (
                            "This issue has been automatically"
                            f" assigned to @{pr_author}"
                            f" who opened PR #{pr_number}"
                            " to address it. 🎯"
                        )
                        issue.create_comment(comment_message)
                    elif verified is False:
                        print(
                            f"Assignment of #{issue_number} to {pr_author}"
                            " was silently rejected by GitHub."
                        )
                        issue.create_comment(
                            self._cannot_auto_assign_message(pr_author, pr_number)
                        )
                    else:
                        print(
                            f"Skipping comment for #{issue_number}:"
                            " assignment state could not be verified."
                        )
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
            return unassign_linked_issues_helper(
                self.repo, self.repository_name, pr_body, pr_author
            )
        except Exception as e:
            print(f"Error in unassign_issues_from_pr: {e}")
            return []

    def _is_bot_comment(self, comment):
        user = comment.get("user") or {}
        if (user.get("type") or "").lower() == "bot":
            return True
        if comment.get("performed_via_github_app"):
            return True
        login = (user.get("login") or "").lower()
        return login in {
            self.bot_username.lower(),
            f"{self.bot_username}[bot]".lower(),
        }

    def handle_issue_comment(self):
        if not self.event_payload:
            print("No event payload available")
            return False
        try:
            action = self.event_payload.get("action")
            if action and action != "created":
                print(f"Ignoring issue_comment action '{action}'")
                return True
            if self.event_payload.get("issue", {}).get("pull_request"):
                print("Comment is on a PR, not an issue - skipping")
                return True
            comment = self.event_payload.get("comment", {})
            issue = self.event_payload.get("issue", {})
            comment_body = comment.get("body", "")
            commenter = comment.get("user", {}).get("login", "")
            issue_number = issue.get("number")
            if not all([comment_body, commenter, issue_number]):
                print("Missing required comment data")
                return False
            if self._is_bot_comment(comment):
                print("Ignoring comment posted by a bot")
                return True
            if self.is_bot_assign_command(comment_body):
                return self.handle_bot_assign_request(issue_number, commenter)
            if self.is_assignment_request(comment_body):
                return self.respond_to_assignment_request(issue_number, commenter)
            print("Comment does not contain an assignment request or bot command")
            return True
        except Exception as e:
            print(f"Error handling issue comment: {e}")
            return False

    def handle_pull_request(self):
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
                self.auto_assign_issues_from_pr(pr_number, pr_author, pr_body)
                # We consider the event handled even if no issues were linked
                return True
            elif action == "closed":
                if pr.get("merged", False):
                    print(f"PR #{pr_number} was merged, keeping issue assignments")
                else:
                    self.unassign_issues_from_pr(pr_body, pr_author)
                return True
            print(f"PR action '{action}' not handled")
            return True
        except Exception as e:
            print(f"Error handling pull request: {e}")
            return False

    def run(self):
        if not self.github or not self.repo:
            print("GitHub client not properly initialized," " cannot proceed")
            return False
        print("Issue Assignment Bot starting" f" for event: {self.event_name}")
        try:
            if self.event_name == "issue_comment":
                return self.handle_issue_comment()
            elif self.event_name == "pull_request_target":
                return self.handle_pull_request()
            else:
                print(f"Event type '{self.event_name}'" " not supported")
                return True
        except Exception as e:
            print(f"Error in main execution: {e}")
            return False
        finally:
            print("Issue Assignment Bot completed")


def main():
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
            return 1
    result = bot.run()
    return 0 if result else 1


if __name__ == "__main__":
    main()
