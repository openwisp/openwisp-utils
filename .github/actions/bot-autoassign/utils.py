import re
import time

from github import GithubException

VERIFICATION_RETRY_DELAY_SECONDS = 1.0
FIND_OPEN_PR_MAX_RESULTS = 20


def user_in_logins(user, logins):
    user_lower = (user or "").lower()
    return any(user_lower == (login or "").lower() for login in logins)


def get_assignee_logins(issue):
    return [a.login for a in issue.assignees if hasattr(a, "login")]


def verify_assignment(repo, issue_number, user):
    """Re-fetch to confirm `user` was assigned. Returns True/False
    on verified state, None when every fetch errored — caller
    stays silent on None since the true state is unknown.
    """
    had_successful_fetch = False
    for attempt in range(2):
        try:
            updated_issue = repo.get_issue(issue_number)
            had_successful_fetch = True
            if user_in_logins(user, get_assignee_logins(updated_issue)):
                return True
        except Exception as e:
            print(
                f"Error verifying assignment for #{issue_number}"
                f" (attempt {attempt + 1}/2): {e}"
            )
        if attempt == 0:
            time.sleep(VERIFICATION_RETRY_DELAY_SECONDS)
    return False if had_successful_fetch else None


def extract_linked_issues(pr_body):
    """Extract issue numbers from PR body.

    Returns a list of unique issue numbers referenced in the PR body using
    keywords like 'fixes', 'closes', 'resolves', 'relates to', 'related
    to'. Supports patterns with optional colons and owner/repo references.
    """
    if not pr_body:
        return []
    issue_pattern = (
        r"\b(?:fix(?:e[sd])?|close[sd]?|resolve[sd]?|relat(?:e[sd]?|ed)\s+to)"
        r"\s*:?\s*(?![\w-]+/[\w-]+#)#(\d+)"
    )
    matches = re.findall(issue_pattern, pr_body, re.IGNORECASE)
    return list(dict.fromkeys(int(match) for match in matches))


def get_valid_linked_issues(repo, repository_name, issue_numbers):
    """Generator yielding valid linked issues (skipping cross-repo and PRs)."""
    for issue_number in issue_numbers:
        try:
            issue = repo.get_issue(issue_number)
            if (
                hasattr(issue, "repository")
                and issue.repository.full_name != repository_name
            ):
                print(f"Issue #{issue_number} is from a different repository, skipping")
                continue
            if issue.pull_request:
                print(f"#{issue_number} is a PR, skipping")
                continue
            yield issue_number, issue
        except Exception as e:
            if isinstance(e, GithubException) and e.status == 404:
                print(f"Issue #{issue_number} not found")
            else:
                print(f"Error fetching issue #{issue_number}: {e}")


def find_open_pr_for_issue(github, repo_full_name, author, issue_number):
    """Return the most recently updated open PR by ``author`` that
    references ``issue_number``, or ``None`` if none is found.
    Search-API errors propagate so the caller can tell a verified
    miss from an unknown state.
    """
    if not author:
        return None
    query = f"repo:{repo_full_name} is:pr is:open author:{author}"
    results = github.search_issues(query, sort="updated", order="desc")
    for index, item in enumerate(results):
        if index >= FIND_OPEN_PR_MAX_RESULTS:
            break
        if issue_number in extract_linked_issues(item.body or ""):
            return item.as_pull_request()
    return None


def unassign_linked_issues_helper(repo, repository_name, pr_body, pr_author):
    """Shared helper to unassign linked issues from PR author."""
    unassigned_issues = []
    linked_issues = extract_linked_issues(pr_body)
    for issue_number, issue in get_valid_linked_issues(
        repo, repository_name, linked_issues
    ):
        try:
            if user_in_logins(pr_author, get_assignee_logins(issue)):
                issue.remove_from_assignees(pr_author)
                unassigned_issues.append(issue_number)
                print(f"Unassigned {pr_author} from issue #{issue_number}")
        except Exception as e:
            print(f"Error unassigning issue #{issue_number}: {e}")
    return unassigned_issues
