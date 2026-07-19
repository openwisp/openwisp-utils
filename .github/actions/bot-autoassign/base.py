import os

from github import Github, GithubException
from utils import extract_all_linked_issues

MAINTAINER_ROLES = frozenset({"OWNER", "MEMBER", "COLLABORATOR"})
DEFAULT_EXCLUDE_PR_AUTHORS = "dependabot[bot]"
REQUIRED_CONTRIBUTOR_PROJECTS = (
    "OpenWISP Contributor's Board",
    "OpenWISP Priorities for next releases",
)
INVALID_ISSUE_LABELS = frozenset({"invalid", "wontfix"})


class GitHubBot:
    def __init__(self):
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.repository_name = os.environ.get("REPOSITORY")
        self.event_name = os.environ.get("GITHUB_EVENT_NAME")
        self.event_payload = None
        bot_username = os.environ.get("BOT_USERNAME", "openwisp-companion")
        self.bot_username = bot_username
        self.bot_login = (
            bot_username if bot_username.endswith("[bot]") else f"{bot_username}[bot]"
        )
        if self.github_token and self.repository_name:
            try:
                self.github = Github(self.github_token)
                self.repo = self.github.get_repo(self.repository_name)
            except Exception as e:
                print(f"Warning: Could not initialize GitHub client: {e}")
                self.github = None
                self.repo = None
        else:
            print("Warning: GITHUB_TOKEN or REPOSITORY env vars not set")
            self.github = None
            self.repo = None

    def load_event_payload(self, event_payload):
        self.event_payload = event_payload

    @staticmethod
    def _normalize_project_title(title: str) -> str:
        """Normalize project titles for stable comparisons."""
        return " ".join(title.replace("\u2019", "'").split()).strip()

    @classmethod
    def _project_title_key(cls, title: str) -> str:
        """Loose match key: casefold + ignore apostrophes."""
        normalized = cls._normalize_project_title(title).casefold()
        return normalized.replace("'", "")

    def get_issue_projects(self, owner, repo_name, issue_number):
        query = """
        query($owner: String!, $repo: String!, $issueNumber: Int!, $cursor: String) {
          repository(owner: $owner, name: $repo) {
            issue(number: $issueNumber) {
              projectItems(first: 100, after: $cursor) {
                nodes {
                  project {
                    title
                  }
                }
                pageInfo {
                  hasNextPage
                  endCursor
                }
              }
            }
          }
        }
        """
        projects = []
        has_next_page = True
        cursor = None

        while has_next_page:
            variables = {
                "owner": owner,
                "repo": repo_name,
                "issueNumber": issue_number,
                "cursor": cursor,
            }
            headers, result = self.github.requester.graphql_query(query, variables)

            if "errors" in result:
                raise ValueError(f"GraphQL API Permission Error: {result['errors']}")

            repo_data = result.get("data", {}).get("repository")
            if not repo_data:
                raise ValueError(
                    f"GraphQL could not access repository {owner}/{repo_name}; "
                    "possible GitHub API or permission error"
                )

            issue_node = repo_data.get("issue")
            if issue_node is None:
                raise ValueError(
                    f"GraphQL could not access issue {owner}/{repo_name}#{issue_number}; "
                    "possible GitHub API or permission error"
                )

            project_items = issue_node.get("projectItems")
            if project_items is None:
                raise ValueError(
                    f"GraphQL could not read project assignments for "
                    f"{owner}/{repo_name}#{issue_number}; "
                    "possible GitHub API or permission error"
                )

            nodes = project_items.get("nodes") or []
            for node in nodes:
                if not node:
                    continue
                project = node.get("project") or {}
                title = project.get("title")
                if title:
                    projects.append(self._normalize_project_title(title))

            page_info = project_items.get("pageInfo") or {}
            has_next_page = page_info.get("hasNextPage", False)
            cursor = page_info.get("endCursor")

        return projects

    def validate_pr_issues(self, pr):
        """Validate if a pull request is from an exempt user or references a validated issue."""
        if not self.github or not self.repository_name:
            print("GitHub client or repository name not initialized")
            return False
        pr_author = (
            pr.user.login
            if pr.user and isinstance(getattr(pr.user, "login", None), str)
            else ""
        )
        exclude_authors_env = os.environ.get(
            "EXCLUDE_PR_AUTHORS", DEFAULT_EXCLUDE_PR_AUTHORS
        )
        excluded_authors = [
            auth.strip() for auth in exclude_authors_env.split(",") if auth.strip()
        ]
        if pr_author in excluded_authors:
            print(f"Author {pr_author} is in the exclude list. Proceeding.")
            return True
        author_association = str(getattr(pr, "author_association", "") or "")
        if author_association in MAINTAINER_ROLES:
            print(
                f"Author {pr_author} is exempt due to association: "
                f"{author_association}. Proceeding."
            )
            return True
        pr_body = pr.body if isinstance(pr.body, str) else ""
        linked_issues = extract_all_linked_issues(pr_body, self.repository_name)
        if not linked_issues:
            print("No linked issues found in PR body for external contributor.")
            return False
        current_org = self.repository_name.split("/")[0].lower()
        required_projects = {
            self._project_title_key(p) for p in REQUIRED_CONTRIBUTOR_PROJECTS
        }
        for owner, repo_name, issue_number in linked_issues:
            if owner.lower() != current_org:
                print(
                    f"Issue {owner}/{repo_name}#{issue_number} does not belong "
                    f"to organization {current_org}, skipping validation."
                )
                continue
            try:
                target_repo = self.github.get_repo(f"{owner}/{repo_name}")
                issue = target_repo.get_issue(issue_number)
            except Exception as e:
                if isinstance(e, GithubException) and e.status == 404:
                    print(
                        f"Issue {owner}/{repo_name}#{issue_number} not found, skipping validation."
                    )
                    continue
                print(f"Error fetching issue {owner}/{repo_name}#{issue_number}: {e}")
                raise
            if issue.pull_request:
                print(
                    f"Reference {owner}/{repo_name}#{issue_number} is a pull request, skipping validation."
                )
                continue
            if issue.state != "open":
                print(
                    f"Issue {owner}/{repo_name}#{issue_number} is not open, skipping validation."
                )
                continue
            issue_labels = [label.name.lower() for label in issue.labels]
            valid_labels = [
                lbl for lbl in issue_labels if lbl not in INVALID_ISSUE_LABELS
            ]
            if not valid_labels:
                print(
                    f"Issue {owner}/{repo_name}#{issue_number} has no valid labels, skipping validation."
                )
                continue
            if any(lbl in INVALID_ISSUE_LABELS for lbl in issue_labels):
                print(
                    f"Issue {owner}/{repo_name}#{issue_number} contains "
                    "invalid/wontfix label, skipping validation."
                )
                continue
            try:
                projects = self.get_issue_projects(owner, repo_name, issue_number)
            except Exception as e:
                print(
                    f"Error fetching projects for issue {owner}/{repo_name}#{issue_number}: {e}"
                )
                raise
            project_keys = [self._project_title_key(p) for p in projects]
            has_valid_project = any(key in required_projects for key in project_keys)
            if has_valid_project:
                print(
                    f"Issue {owner}/{repo_name}#{issue_number} is validated. PR is valid."
                )
                return True
            else:
                print(
                    f"Issue {owner}/{repo_name}#{issue_number} is not assigned "
                    f"to any required project (found: {projects or 'none'}), "
                    "skipping validation."
                )
        return False

    def get_bot_comment(self, pr, comment_type, after_date=None, issue_comments=None):
        """Get the comment of this bot with the given marker if it exists.
        If ``after_date`` is provided, only considers comments posted after that date.
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
                    return comment
            return None
        except Exception as e:
            print(f"Error getting bot comment for PR #{pr.number}: {e}")
            return None

    def has_bot_comment(self, pr, comment_type, after_date=None, issue_comments=None):
        """Check if PR already has a specific type of bot comment.
        Uses HTML markers. If ``after_date`` is provided,
        only considers comments posted after that date.
        """
        return bool(self.get_bot_comment(pr, comment_type, after_date, issue_comments))

    def get_invalid_unvalidated_issue_comment(self, pr_author):
        """Returns the comment body warning that the PR is invalid/unvalidated."""
        greeting = f"Hi @{pr_author},\n\n" if pr_author else "Hi,\n\n"
        return (
            "<!-- bot:invalid_unvalidated_issue -->\n\n"
            f"{greeting}"
            "Thank you for your interest in contributing to OpenWISP.\n\n"
            "This pull request has been flagged because external contributors "
            "must target an issue validated by maintainers before requesting "
            "review.\n\n"
            "Please link this pull request to a validated issue by adding "
            "`Fixes #ISSUE_NUMBER`, `Closes #ISSUE_NUMBER`, or "
            "`Related to #ISSUE_NUMBER` to the pull request description. "
            "The issue may be in this repository or another OpenWISP "
            "repository.\n\n"
            "If there is no validated issue yet, please open one first and wait "
            "for maintainer validation before continuing with this pull "
            "request.\n\n"
            "An issue is considered validated when it is open, has an appropriate "
            "label other than `invalid` or `wontfix`, and is assigned to one of "
            "the project boards mentioned in the "
            "[OpenWISP Contributing Guidelines]"
            "(https://openwisp.io/docs/dev/developer/contributing.html).\n\n"
            "Please see the [OpenWISP Anti AI Spam Policy]"
            "(https://openwisp.io/docs/dev/general/code-of-conduct.html).\n\n"
            "Feel free to join the [OpenWISP dev chatroom]"
            "(https://matrix.to/#/#openwisp_development:gitter.im) "
            "to coordinate with the development team.\n\n"
            "If this is not resolved within 24 hours, this pull request "
            "will be closed automatically. "
            "Thank you for your understanding."
        )
