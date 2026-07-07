import os

from github import Github


class GitHubBot:
    def __init__(self):
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.repository_name = os.environ.get("REPOSITORY")
        self.event_name = os.environ.get("GITHUB_EVENT_NAME")
        self.event_payload = None

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

    def get_issue_projects(self, owner, repo_name, issue_number):
        query = """
        query($owner: String!, $repo: String!, $issueNumber: Int!) {
          repository(owner: $owner, name: $repo) {
            issue(number: $issueNumber) {
              projectItems(first: 10) {
                nodes {
                  project {
                    title
                  }
                }
              }
            }
          }
        }
        """
        variables = {
            "owner": owner,
            "repo": repo_name,
            "issueNumber": issue_number
        }
        result = self.github.raw_graphql(query, variables)
        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")
        
        repo_data = result.get("data", {}).get("repository", {}) or {}
        issue_data = repo_data.get("issue", {}) or {}
        project_items = issue_data.get("projectItems", {}) or {}
        nodes = project_items.get("nodes", []) or []
        
        return [
            node["project"]["title"]
            for node in nodes
            if node and node.get("project") and node["project"].get("title")
        ]

    def validate_pr_issues(self, pr):
        """Validate if a pull request is from an exempt user or references a validated issue."""
        if not self.github or not self.repository_name:
            print("GitHub client or repository name not initialized")
            return False

        pr_author = pr.user.login if pr.user and isinstance(getattr(pr.user, "login", None), str) else ""
        
        # Check if the author is in the exclude list
        exclude_authors_env = os.environ.get("EXCLUDE_PR_AUTHORS", "dependabot[bot]")
        excluded_authors = [auth.strip() for auth in exclude_authors_env.split(",") if auth.strip()]
        if pr_author in excluded_authors:
            print(f"Author {pr_author} is in the exclude list. Proceeding.")
            return True

        # Check if the author is a maintainer/collaborator
        author_association = getattr(pr, "author_association", None)
        if isinstance(author_association, str) and author_association in ["OWNER", "MEMBER", "COLLABORATOR"]:
            print(f"Author {pr_author} is exempt due to association: {author_association}. Proceeding.")
            return True

        # For external contributors, extract linked issues
        from utils import extract_all_linked_issues
        pr_body = pr.body if isinstance(pr.body, str) else ""
        linked_issues = extract_all_linked_issues(pr_body, self.repository_name)
        if not linked_issues:
            print("No linked issues found in PR body for external contributor.")
            return False

        current_org = self.repository_name.split("/")[0].lower()
        required_projects = [
            "OpenWISP Contributor's Board",
            "OpenWISP Priorities for next releases"
        ]

        for owner, repo_name, issue_number in linked_issues:
            # 1. Check if the issue belongs to the same organization
            if owner.lower() != current_org:
                print(f"Issue {owner}/{repo_name}#{issue_number} does not belong to organization {current_org}, skipping validation.")
                continue

            try:
                from github import GithubException
                target_repo = self.github.get_repo(f"{owner}/{repo_name}")
                issue = target_repo.get_issue(issue_number)
            except Exception as e:
                if isinstance(e, GithubException) and e.status == 404:
                    print(f"Issue {owner}/{repo_name}#{issue_number} not found, skipping validation.")
                    continue
                else:
                    print(f"Error fetching issue {owner}/{repo_name}#{issue_number}: {e}")
                    raise

            # 2. Check if the issue is a PR
            if issue.pull_request:
                print(f"Reference {owner}/{repo_name}#{issue_number} is a pull request, skipping validation.")
                continue

            # 3. Check if the issue is open
            if issue.state != "open":
                print(f"Issue {owner}/{repo_name}#{issue_number} is not open, skipping validation.")
                continue

            # 4. Check if the issue has at least one label, and none are invalid/wontfix
            issue_labels = [label.name.lower() for label in issue.labels]
            valid_labels = [l for l in issue_labels if l not in ["invalid", "wontfix"]]
            if not valid_labels:
                print(f"Issue {owner}/{repo_name}#{issue_number} has no valid labels, skipping validation.")
                continue
            if any(l in ["invalid", "wontfix"] for l in issue_labels):
                print(f"Issue {owner}/{repo_name}#{issue_number} contains invalid/wontfix label, skipping validation.")
                continue

            # 5. Check if the issue is assigned to one of the required projects
            try:
                projects = self.get_issue_projects(owner, repo_name, issue_number)
            except Exception as e:
                print(f"Error fetching projects for issue {owner}/{repo_name}#{issue_number}: {e}")
                raise

            has_valid_project = any(project in required_projects for project in projects)
            if has_valid_project:
                print(f"Issue {owner}/{repo_name}#{issue_number} is validated. PR is valid.")
                return True
            else:
                print(f"Issue {owner}/{repo_name}#{issue_number} is not assigned to any required project, skipping validation.")

        return False

    def has_bot_comment(self, pr, comment_type, after_date=None, issue_comments=None):
        """Check if PR already has a specific type of bot comment.

        Uses HTML markers. If ``after_date`` is provided,
        only considers comments posted after that date.
        """
        try:
            if issue_comments is None:
                issue_comments = list(pr.get_issue_comments())
            marker = f"<!-- bot:{comment_type} -->"
            for comment in issue_comments:
                if (
                    comment.user
                    and comment.user.type == "Bot"
                    and marker in comment.body
                ):
                    if after_date and comment.created_at <= after_date:
                        continue
                    return True
            return False
        except Exception as e:
            print("Error checking bot comments" f" for PR #{pr.number}: {e}")
            return False


