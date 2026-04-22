import re

from github import GithubException

_LINK_KEYWORDS_ALL = r"fix(?:e[sd])?|close[sd]?|resolve[sd]?|relat(?:e[sd]?|ed)\s+to"
_LINK_KEYWORDS_CLOSING = r"fix(?:e[sd])?|close[sd]?|resolve[sd]?"


def extract_linked_issues(pr_body, strict=False):
    """Extract unique issue numbers referenced in ``pr_body``.

    By default matches fix/close/resolve/relate-to keywords. With
    ``strict=True``, excludes relate-to (used when the caller needs
    to know the PR claims to close the issue, not just reference it).
    """
    if not pr_body:
        return []
    keywords = _LINK_KEYWORDS_CLOSING if strict else _LINK_KEYWORDS_ALL
    issue_pattern = rf"\b(?:{keywords})\s*:?\s*(?![\w-]+/[\w-]+#)#(\d+)"
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


def find_open_pr_for_issue(repo, author, issue_number, max_prs=100):
    """Return the most recently updated open PR by ``author`` that
    closes ``issue_number``, or ``None``.
    """
    author_lower = (author or "").lower()
    try:
        pulls = repo.get_pulls(state="open", sort="updated", direction="desc")
        for index, pr in enumerate(pulls):
            if index >= max_prs:
                print(
                    f"find_open_pr_for_issue: reached {max_prs}-PR cap"
                    f" while searching for {author}"
                )
                break
            pr_author = getattr(getattr(pr, "user", None), "login", None) or ""
            if pr_author.lower() != author_lower:
                continue
            if issue_number in extract_linked_issues(pr.body or "", strict=True):
                return pr
    except GithubException as e:
        print(f"GitHub API error searching open PRs by {author}: {e}")
    return None


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
