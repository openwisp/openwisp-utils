import re

from base import GitHubBot
from utils import (
    extract_linked_issues,
    find_open_pr_for_issue,
    get_assignee_logins,
    get_valid_linked_issues,
    unassign_linked_issues_helper,
    user_in_logins,
    verify_assignment,
)


class IssueAssignmentBot(GitHubBot):

    def is_bot_assign_command(self, comment_body):
        if not comment_body:
            return False
        pattern = rf"(?<![\w-])@{re.escape(self.bot_username)}\s+assign\b"
        return bool(re.search(pattern, comment_body, re.IGNORECASE))

    def is_assignment_request(self, comment_body):
        if not comment_body:
            return False
        comment_lower = comment_body.lower()
        negated_patterns = [
            r"\b(?:do not|don't|dont|never)(?:\s+(?:want|wish|need|expect|mean|"
            r"intend|plan))?(?:\s+(?:you|to))*\s+assign(?: this issue)?(?: to)? me\b"
        ]
        if any(re.search(pattern, comment_lower) for pattern in negated_patterns):
            return False
        assignment_patterns = [
            r"\bassign this issue to me\b",
            r"\bassign to me\b",
            r"\bassign me\b",
            r"\bplease assign this to me\b",
            r"\bcan you assign this to me\b",
            r"\bcan i work on this\b",
            r"\bi want to work on this\b",
            r"\bi would like to work on this\b",
            r"\bi'd like to work on this\b",
            r"\btake up this issue\b",
        ]
        return any(re.search(pattern, comment_lower) for pattern in assignment_patterns)

    def respond_to_assignment_request(self, issue_number, commenter, is_exempt=False):
        if not self.repo:
            print("GitHub client not initialized")
            return False
        try:
            issue = self.repo.get_issue(issue_number)
            if getattr(issue, "state", "open") == "closed":
                print(f"Issue #{issue_number} is closed, ignoring assignment request")
                return True
            owner, repo_name = self.repository_name.split("/")
            if not is_exempt and not self.validate_issue(
                owner, repo_name, issue_number
            ):
                issue.create_comment(
                    self.get_unvalidated_issue_assignment_request_comment(commenter)
                )
                print(f"Posted unvalidated issue response to issue #{issue_number}")
                return True
            message_lines = [
                f"Hi @{commenter} 👋,",
                "",
                "Thanks for your interest in contributing to OpenWISP!",
                "",
                "If nobody is assigned to this issue, you can start working.",
                "",
                "Open a draft pull request linked to this issue, for example "
                f"`Fixes #{issue_number}`.",
                "",
                "Join the [developer chat](https://matrix.to/#/#openwisp_development:gitter.im) "
                "to coordinate or ask questions.",
            ]
            message = "\n".join(message_lines)
            issue.create_comment(message)
            print(f"Posted assignment response to issue #{issue_number}")
            return True
        except Exception as e:
            print(f"Error responding to assignment request: {e}")
            return False

    def get_unvalidated_issue_assignment_request_comment(self, commenter):
        return self.get_unvalidated_issue_message(
            f"Hi @{commenter} 👋,\n\n"
            "Thanks for your interest in contributing to OpenWISP!\n\n"
            "This issue is not currently available to external contributors. "
            "Please choose a validated issue."
        )

    def _cannot_auto_assign_message(self, pr_author, pr_number):
        return (
            f"Hi @{pr_author} 👋,\n\n"
            f"Thank you for opening PR #{pr_number} to address this issue!\n\n"
            "GitHub requires external contributors to comment on the issue before "
            "it allows the bot to assign them automatically.\n\n"
            f"Comment `@{self.bot_username} assign` on this issue to try again."
        )

    def handle_bot_assign_request(self, issue_number, commenter, is_exempt=False):
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
            if user_in_logins(commenter, get_assignee_logins(issue)):
                print(f"{commenter} is already assigned to #{issue_number}")
                return True
            if not is_exempt:
                owner, repo_name = self.repository_name.split("/")
                if not self.validate_issue(owner, repo_name, issue_number):
                    issue.create_comment(
                        self.get_unvalidated_issue_assignment_request_comment(commenter)
                    )
                    print(f"Issue #{issue_number} is unvalidated, declining assignment")
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
                    "Thanks for your interest in contributing to OpenWISP! I could not find "
                    "an open PR by you that references"
                    f" this issue (#{issue_number}). Please open a PR"
                    f" linking to this issue (e.g. `Fixes #{issue_number}`)"
                    f" and then comment `@{self.bot_username} assign` again."
                )
                return True
            issue.add_to_assignees(commenter)
            verified = verify_assignment(self.repo, issue_number, commenter)
            if verified is True:
                issue.create_comment(
                    f"This issue has been assigned to @{commenter}, who opened PR "
                    f"#{pr.number}. 🎯"
                )
                print(f"Assigned #{issue_number} to {commenter} via bot command")
            elif verified is False:
                # Commenter has commented but the assignment still
                # failed (perm block, outage, etc.).
                issue.create_comment(
                    f"Sorry @{commenter}, GitHub still did not allow this assignment. "
                    "A maintainer must assign this issue manually."
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

    def auto_assign_issues_from_pr(
        self, pr_number, pr_author, pr_body, max_issues=10, validate_issues=False
    ):
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
            owner, repo_name = self.repository_name.split("/")
            for issue_number, issue in get_valid_linked_issues(
                self.repo, self.repository_name, linked_issues
            ):
                if len(assigned_issues) >= max_issues:
                    break
                try:
                    if validate_issues and not self.validate_issue(
                        owner, repo_name, issue_number
                    ):
                        print(
                            f"Issue #{issue_number} is invalid, skipping auto-assignment"
                        )
                        continue
                    if getattr(issue, "state", "open") == "closed":
                        print(
                            f"Issue #{issue_number} is closed, skipping"
                            " auto-assignment"
                        )
                        continue
                    current_assignees = get_assignee_logins(issue)
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
                    verified = verify_assignment(self.repo, issue_number, pr_author)
                    if verified is True:
                        assigned_issues.append(issue_number)
                        print(f"Assigned issue #{issue_number} to {pr_author}")
                        comment_message = (
                            "This issue has been automatically assigned to "
                            f"@{pr_author}, who opened PR #{pr_number}. 🎯"
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
                is_exempt = self.is_contributor_exempt(
                    commenter, comment.get("author_association")
                )
                return self.handle_bot_assign_request(
                    issue_number, commenter, is_exempt
                )
            if self.is_assignment_request(comment_body):
                is_exempt = self.is_contributor_exempt(
                    commenter, comment.get("author_association")
                )
                return self.respond_to_assignment_request(
                    issue_number, commenter, is_exempt
                )
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
            pr_title = pr.get("title", "")
            pr_body = pr.get("body", "")
            if not all([pr_number, pr_author]):
                print("Missing required PR data")
                return False
            if action == "closed":
                if pr.get("merged", False):
                    print(f"PR #{pr_number} was merged, keeping issue assignments")
                else:
                    self.unassign_issues_from_pr(pr_body, pr_author)
                return True
            if action in ["opened", "reopened", "edited", "ready_for_review"]:
                pr_obj = self.repo.get_pull(pr_number)
                is_exempt = self.is_pr_author_exempt(pr_obj)
                is_valid = is_exempt or self.validate_pr_issues(pr_obj)
                # Cross-repo issues are intentionally excluded from auto-assignment
                # because when multiple PRs in different repos are created for a
                # single issue, it's likely that multiple people will work on it
                if is_valid:
                    self.auto_assign_issues_from_pr(
                        pr_number,
                        pr_author,
                        pr_body,
                        validate_issues=not is_exempt,
                    )
                labels_lower = set()
                try:
                    labels_lower = {label.name.lower() for label in pr_obj.labels}
                except (TypeError, AttributeError):
                    pass
                if is_valid:
                    if "invalid" in labels_lower:
                        pr_obj.remove_from_labels("invalid")
                        print(f"Removed 'invalid' label from PR #{pr_number}")
                    skip_label = (
                        pr_author.lower() == "dependabot[bot]"
                        or pr_title.lower().startswith(("[release]", "[backport]"))
                    )
                    if "ai-review" not in labels_lower and not skip_label:
                        pr_obj.add_to_labels("ai-review")
                        print(f"Added 'ai-review' label to PR #{pr_number}")
                else:
                    if "invalid" not in labels_lower:
                        pr_obj.add_to_labels("invalid")
                        print(f"Added 'invalid' label to PR #{pr_number}")
                    if not self.has_bot_comment(pr_obj, "invalid_unvalidated_issue"):
                        comment_body = self.get_invalid_unvalidated_issue_comment(
                            pr_author
                        )
                        pr_obj.create_issue_comment(comment_body)
                        print(
                            f"Posted unvalidated issue warning comment on PR #{pr_number}"
                        )
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
