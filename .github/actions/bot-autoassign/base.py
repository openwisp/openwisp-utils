import os

from github import Github, GithubException
from utils import extract_all_linked_issues

MAINTAINER_ROLES = frozenset({"OWNER", "MEMBER", "COLLABORATOR"})
DEFAULT_EXCLUDE_PR_AUTHORS = "dependabot[bot]"
MAX_VALIDATION_ISSUES = 10
CONTRIBUTING_GUIDELINES_URL = "https://openwisp.io/docs/dev/developer/contributing.html"
VALIDATED_ISSUES_URL = f"{CONTRIBUTING_GUIDELINES_URL}#look-for-validated-issues"
DEVELOPER_CHAT_URL = "https://matrix.to/#/#openwisp_development:gitter.im"
ANTI_AI_SPAM_POLICY_URL = (
    "https://openwisp.io/docs/dev/general/code-of-conduct.html#anti-ai-spam-policy"
)
# Stable ProjectV2 node IDs for the OpenWISP contributor boards.
# These IDs never change even if a board is renamed.
REQUIRED_CONTRIBUTOR_PROJECT_IDS = frozenset(
    {
        "PVT_kwDOABGNI84Amkl7",  # OpenWISP Contributor's Board (project 42)
        "PVT_kwDOABGNI84Amkjx",  # OpenWISP Priorities for next releases (project 37)
    }
)
INVALID_ISSUE_LABELS = frozenset({"invalid", "wontfix"})


class GitHubBot:
    def __init__(self):
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.github_validation_token = os.environ.get("VALIDATION_GITHUB_TOKEN")
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
                print(f"Warning: Could not initialize GitHub write client: {e}")
                self.github = None
                self.repo = None
        else:
            print("Warning: GITHUB_TOKEN or REPOSITORY env vars not set")
            self.github = None
            self.repo = None

        if self.github_validation_token:
            try:
                self.github_validation = Github(self.github_validation_token)
            except Exception as e:
                print(f"Warning: Could not initialize GitHub validation client: {e}")
                self.github_validation = None
        else:
            print(
                "Warning: VALIDATION_GITHUB_TOKEN env var not set, falling back to GITHUB_TOKEN"
            )
            self.github_validation = self.github

    def load_event_payload(self, event_payload):
        self.event_payload = event_payload

    def get_unvalidated_issue_message(self, context):
        return (
            f"{context}\n\n"
            "Read [how to find a validated issue]"
            f"({VALIDATED_ISSUES_URL}).\n\n"
            "Join the [developer chat]"
            f"({DEVELOPER_CHAT_URL}) to ask questions or coordinate."
        )

    def get_issue_projects(self, owner, repo_name, issue_number):
        query = """
        query($owner: String!, $repo: String!, $issueNumber: Int!, $cursor: String) {
          repository(owner: $owner, name: $repo) {
            issue(number: $issueNumber) {
              projectItems(first: 100, after: $cursor) {
                nodes {
                  project {
                    id
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
            headers, result = self.github_validation.requester.graphql_query(
                query, variables
            )

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
                project_id = project.get("id")
                if project_id:
                    projects.append(project_id)

            page_info = project_items.get("pageInfo") or {}
            has_next_page = page_info.get("hasNextPage", False)
            cursor = page_info.get("endCursor")

        return projects

    def validate_issue(self, owner, repo_name, issue_number):
        if not self.github_validation:
            print("GitHub validation client not initialized")
            return False
        try:
            target_repo = self.github_validation.get_repo(f"{owner}/{repo_name}")
            issue = target_repo.get_issue(issue_number)
        except Exception as e:
            if isinstance(e, GithubException) and e.status == 404:
                print(
                    f"Issue {owner}/{repo_name}#{issue_number} not found, skipping validation."
                )
                return False
            print(f"Error fetching issue {owner}/{repo_name}#{issue_number}: {e}")
            raise
        if issue.pull_request:
            print(
                f"Reference {owner}/{repo_name}#{issue_number} is a pull request, skipping validation."
            )
            return False
        if issue.state != "open":
            print(
                f"Issue {owner}/{repo_name}#{issue_number} is not open, skipping validation."
            )
            return False
        issue_labels = [label.name.lower() for label in issue.labels]
        valid_labels = [lbl for lbl in issue_labels if lbl not in INVALID_ISSUE_LABELS]
        if not valid_labels:
            print(
                f"Issue {owner}/{repo_name}#{issue_number} has no valid labels, skipping validation."
            )
            return False
        if any(lbl in INVALID_ISSUE_LABELS for lbl in issue_labels):
            print(
                f"Issue {owner}/{repo_name}#{issue_number} contains "
                "invalid/wontfix label, skipping validation."
            )
            return False
        try:
            projects = self.get_issue_projects(owner, repo_name, issue_number)
        except Exception as e:
            print(
                f"Error fetching projects for issue {owner}/{repo_name}#{issue_number}: {e}"
            )
            raise
        if REQUIRED_CONTRIBUTOR_PROJECT_IDS.intersection(projects):
            print(f"Issue {owner}/{repo_name}#{issue_number} is validated.")
            return True
        print(
            f"Issue {owner}/{repo_name}#{issue_number} is not assigned "
            f"to any required project (found: {projects or 'none'}), "
            "skipping validation."
        )
        return False

    def is_contributor_exempt(self, login, association):
        login = login if isinstance(login, str) else ""
        if login == self.bot_login:
            print(f"Contributor {login} is the configured bot. Proceeding.")
            return True
        exclude_authors_env = os.environ.get(
            "EXCLUDE_PR_AUTHORS", DEFAULT_EXCLUDE_PR_AUTHORS
        )
        excluded_authors = [
            auth.strip() for auth in exclude_authors_env.split(",") if auth.strip()
        ]
        if login in excluded_authors:
            print(f"Contributor {login} is in the exclude list. Proceeding.")
            return True
        association = str(association or "")
        if association in MAINTAINER_ROLES:
            print(
                f"Contributor {login} is exempt due to association: "
                f"{association}. Proceeding."
            )
            return True
        return False

    def is_pr_author_exempt(self, pr):
        pr_author = (
            pr.user.login
            if pr.user and isinstance(getattr(pr.user, "login", None), str)
            else ""
        )
        return self.is_contributor_exempt(
            pr_author, getattr(pr, "author_association", "")
        )

    def validate_pr_issues(self, pr):
        """Validate if a pull request is from an exempt user or references a validated issue."""
        if not self.github_validation or not self.repository_name:
            print("GitHub validation client or repository name not initialized")
            return False
        if self.is_pr_author_exempt(pr):
            return True
        pr_body = pr.body if isinstance(pr.body, str) else ""
        linked_issues = extract_all_linked_issues(pr_body, self.repository_name)
        if not linked_issues:
            print("No linked issues found in PR body for external contributor.")
            return False
        if len(linked_issues) > MAX_VALIDATION_ISSUES:
            print(
                f"Found {len(linked_issues)} issue references, validating first "
                f"{MAX_VALIDATION_ISSUES} to avoid rate limits"
            )
        current_org = self.repository_name.split("/")[0].lower()
        for owner, repo_name, issue_number in linked_issues[:MAX_VALIDATION_ISSUES]:
            if owner.lower() != current_org:
                print(
                    f"Issue {owner}/{repo_name}#{issue_number} does not belong "
                    f"to organization {current_org}, skipping validation."
                )
                continue
            if self.validate_issue(owner, repo_name, issue_number):
                print(
                    f"Issue {owner}/{repo_name}#{issue_number} is validated. PR is valid."
                )
                return True
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
        message = self.get_unvalidated_issue_message(
            f"{greeting}"
            "Thanks for your contribution to OpenWISP.\n\n"
            "This pull request has been flagged as invalid because it does not link "
            "to a validated issue.\n\n"
            "Link this pull request to a validated issue by adding "
            "`Fixes #ISSUE_NUMBER`, `Closes #ISSUE_NUMBER`, or "
            "`Related to #ISSUE_NUMBER` to its description.\n\n"
            "See the [contributing guidelines]"
            f"({VALIDATED_ISSUES_URL}) and [Anti AI Spam Policy]"
            f"({ANTI_AI_SPAM_POLICY_URL}).\n\n"
            "This pull request will be closed 24 hours after this comment if it "
            "remains invalid."
        )
        return (
            "<!-- bot:invalid_unvalidated_issue -->\n\n"
            f"{message}\n\n"
            "Thank you for your understanding."
        )
