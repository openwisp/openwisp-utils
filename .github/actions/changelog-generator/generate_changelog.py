#!/usr/bin/env python3
"""
Changelog Generator for OpenWISP PRs

This script analyzes a PR and generates a RestructuredText changelog entry
using Google's Gemini API.

The generated entry follows the commit message format expected by git-cliff:
- [feature] for new features
- [fix] for bug fixes
- [change] for changes (non-breaking)
- [change!] for breaking changes
- [deps] for dependency updates

Usage:
    python generate_changelog.py

Environment Variables:
    GEMINI_API_KEY: API key for Google Gemini (required)
    PR_NUMBER: The PR number to analyze
    REPO_NAME: The repository name (e.g., openwisp/openwisp-utils)
    GITHUB_TOKEN: GitHub token for API access
    LLM_MODEL: Model to use (default: 'gemini-2.0-flash')
"""

import json
import os
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from google import genai
from google.genai import types


def get_env_or_exit(name: str) -> str:
    """Get environment variable or exit with error."""
    value = os.environ.get(name)
    if not value:
        print(f"Error: {name} environment variable is required", file=sys.stderr)
        sys.exit(1)
    return value


def github_api_request(endpoint: str, token: str) -> dict:
    """Make a GitHub API request."""
    url = f"https://api.github.com{endpoint}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "OpenWISP-Changelog-Bot",
    }
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as e:
        print(f"GitHub API error: {e.code} - {e.reason}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Network error: {e.reason}", file=sys.stderr)
        sys.exit(1)


def get_pr_details(repo: str, pr_number: int, token: str) -> dict:
    """Fetch PR details from GitHub API."""
    pr_data = github_api_request(f"/repos/{repo}/pulls/{pr_number}", token)
    return {
        "title": pr_data.get("title", ""),
        "body": pr_data.get("body", ""),
        "labels": [label["name"] for label in pr_data.get("labels", [])],
        "base_branch": pr_data.get("base", {}).get("ref", ""),
        "head_branch": pr_data.get("head", {}).get("ref", ""),
        "user": pr_data.get("user", {}).get("login", ""),
        "html_url": pr_data.get("html_url", ""),
        "number": pr_number,
    }


def get_pr_diff(repo: str, pr_number: int, token: str) -> str:
    """Fetch PR diff from GitHub API."""
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "Authorization": f"Bearer {token}",
        "User-Agent": "OpenWISP-Changelog-Bot",
    }
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=60) as response:
            diff = response.read().decode("utf-8", errors="replace")
            # Truncate if too large (keep first 15000 chars for context)
            if len(diff) > 15000:
                diff = diff[:15000] + "\n\n... [diff truncated for brevity] ..."
            return diff
    except (HTTPError, URLError) as e:
        print(f"Warning: Could not fetch diff: {e}", file=sys.stderr)
        return ""


def get_pr_commits(repo: str, pr_number: int, token: str) -> list:
    """Fetch PR commits from GitHub API."""
    commits_data = github_api_request(f"/repos/{repo}/pulls/{pr_number}/commits", token)
    return [
        {
            "sha": commit["sha"][:7],
            "message": commit["commit"]["message"].split("\n")[0],
        }
        for commit in commits_data[:10]  # Limit to first 10 commits
    ]


def get_linked_issues(repo: str, pr_body: str, token: str) -> list:
    """Extract and fetch linked issues from PR body."""
    # Common patterns for linking issues
    patterns = [
        r"(?:closes?|fixes?|resolves?)\s*#(\d+)",
        r"(?:closes?|fixes?|resolves?)\s+https://github\.com/[^/]+/[^/]+/issues/(\d+)",
        r"#(\d+)",
    ]

    issue_numbers = set()
    body_lower = pr_body.lower()
    for pattern in patterns:
        matches = re.findall(pattern, body_lower, re.IGNORECASE)
        issue_numbers.update(matches)

    issues = []
    for issue_num in list(issue_numbers)[:3]:  # Limit to 3 issues
        try:
            issue_data = github_api_request(f"/repos/{repo}/issues/{issue_num}", token)
            issues.append(
                {
                    "number": issue_num,
                    "title": issue_data.get("title", ""),
                    "body": (issue_data.get("body", "") or "")[:500],
                }
            )
        except Exception:
            continue
    return issues


def call_gemini(prompt: str, api_key: str, model: str = "gemini-2.0-flash") -> str:
    """Call Google Gemini API to generate changelog using google-genai SDK."""
    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction="You are a technical writer who creates concise changelog entries for software projects. You follow the RestructuredText format strictly.",
                temperature=0.3,
                max_output_tokens=1000,
            ),
        )

        if not response.text:
            raise ValueError("Empty response from Gemini")

        return response.text

    except Exception as e:
        print(f"Gemini API error: {e}", file=sys.stderr)
        sys.exit(1)


def build_prompt(pr_details: dict, diff: str, commits: list, issues: list) -> str:
    """Build the prompt for the LLM."""
    issues_text = ""
    if issues:
        issues_text = "\n\nLinked Issues:\n"
        for issue in issues:
            issues_text += f"- #{issue['number']}: {issue['title']}\n"
            if issue["body"]:
                issues_text += f"  Description: {issue['body'][:200]}...\n"

    commits_text = ""
    if commits:
        commits_text = "\n\nCommits:\n"
        for commit in commits:
            commits_text += f"- {commit['sha']}: {commit['message']}\n"

    labels_text = ""
    if pr_details["labels"]:
        labels_text = f"\nLabels: {', '.join(pr_details['labels'])}"

    prompt = f"""Analyze this Pull Request and generate a changelog entry in RestructuredText format.

PR #{pr_details['number']}: {pr_details['title']}
{labels_text}

PR Description:
{pr_details['body'][:2000] if pr_details['body'] else 'No description provided.'}
{issues_text}
{commits_text}

Code Changes (diff):
```
{diff if diff else 'Diff not available.'}
```

---

Generate a changelog entry following these STRICT rules:

1. FORMAT: RestructuredText (RST) format for changelogs.

2. STRUCTURE:
   - Start with a section header indicating the change type
   - Use RST bullet points for the changes
   - Reference the PR number with a GitHub link

3. CHANGE TYPE SECTIONS (use one of these as header):
   - **Features** - New functionality
   - **Bugfixes** - Bug fixes
   - **Changes** - Non-breaking changes, refactors, updates
   - **Breaking Changes** - Backwards incompatible changes
   - **Dependencies** - Dependency updates

4. RST FORMAT RULES:
   - Use ``- `` for bullet points
   - Reference PR as: `#<number> <<repo_url>/pull/<number>>`_
   - Keep descriptions concise but informative
   - Use proper RST inline markup for code: ````code````

5. Keep the entry concise (1-4 bullet points).

Output ONLY the RST changelog entry.
Do NOT include any markdown code fences or explanations.

Example output format:
Features
~~~~~~~~

- Added retry mechanism to ``SeleniumTestMixin`` to prevent CI failures
  from flaky tests.
  `#464 <https://github.com/openwisp/openwisp-utils/pull/464>`_
"""
    return prompt


def post_github_comment(repo: str, pr_number: int, comment: str, token: str) -> None:
    """Post a comment on the PR. Raises exception on failure."""
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "OpenWISP-Changelog-Bot",
    }
    data = json.dumps({"body": comment}).encode("utf-8")
    req = Request(url, data=data, headers=headers, method="POST")
    with urlopen(req, timeout=30) as response:
        if response.status != 201:
            raise HTTPError(
                url, response.status, "Failed to create comment", headers, None
            )


def main():
    """Main entry point."""
    # Get configuration from environment
    pr_number = int(get_env_or_exit("PR_NUMBER"))
    repo = get_env_or_exit("REPO_NAME")
    github_token = get_env_or_exit("GITHUB_TOKEN")
    api_key = get_env_or_exit("GEMINI_API_KEY")
    model = os.environ.get("LLM_MODEL", "gemini-2.0-flash")
    pr_details = get_pr_details(repo, pr_number, github_token)
    diff = get_pr_diff(repo, pr_number, github_token)
    commits = get_pr_commits(repo, pr_number, github_token)
    issues = get_linked_issues(repo, pr_details["body"], github_token)

    prompt = build_prompt(pr_details, diff, commits, issues)
    changelog_entry = call_gemini(prompt, api_key, model)
    changelog_entry = changelog_entry.strip()
    comment = f"```rst\n{changelog_entry}\n```"
    try:
        post_github_comment(repo, pr_number, comment, github_token)
    except (HTTPError, URLError) as e:
        raise RuntimeError(f"Failed to post comment: {e}") from e


if __name__ == "__main__":
    main()
