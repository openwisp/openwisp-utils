import re

from github import GithubException


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


def get_valid_linked_issues(repo, repository_name, pr_body):
    """Generator yielding valid linked issues (skipping cross-repo and PRs)."""
    linked_issues = extract_linked_issues(pr_body)
    if not linked_issues:
        return

    for issue_number in linked_issues:
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


def unassign_linked_issues_helper(repo, repository_name, pr_body, pr_author):
    """Shared helper to unassign linked issues from PR author."""
    unassigned_issues = []
    for issue_number, issue in get_valid_linked_issues(repo, repository_name, pr_body):
        try:
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
