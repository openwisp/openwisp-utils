#!/usr/bin/env python3
"""
Changelog Generator for OpenWISP PRs

This script analyzes a PR and generates a RestructuredText changelog entry
using Google's Gemini API.

The generated entry follows the commit message format expected by git-cliff:
- [feature] for new features
- [fix] for bug fixes
- [change] for changes (non-breaking)


Usage:
    python generate_changelog.py

Environment Variables:
    GEMINI_API_KEY: API key for Google Gemini (required)
    PR_NUMBER: The PR number to analyze
    REPO_NAME: The repository name (e.g., openwisp/openwisp-utils)
    GITHUB_TOKEN: GitHub token for API access
    LLM_MODEL: Model to use (default: 'gemini-2.0-flash')
"""

import os
import re
import subprocess
import sys

from google import genai
from google.genai import types
from openwisp_utils.utils import retryable_request
from requests.exceptions import RequestException


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
    try:
        response = retryable_request(
            method="get",
            url=url,
            timeout=(4, 8),
            max_retries=5,
            backoff_factor=3,
            backoff_jitter=0.0,
            status_forcelist=(429, 500, 502, 503, 504),
            headers=headers,
        )
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        error_msg = str(e)
        error_msg = re.sub(r"Bearer\s+[a-zA-Z0-9_-]+", "Bearer ***", error_msg)
        print(f"GitHub API error: {error_msg}", file=sys.stderr)
        sys.exit(1)


def get_pr_details(repo: str, pr_number: int, token: str) -> dict:
    """Fetch PR details from GitHub API."""
    pr_data = github_api_request(f"/repos/{repo}/pulls/{pr_number}", token)
    return {
        "title": pr_data.get("title", ""),
        "body": pr_data.get("body", "") or "",
        "labels": [label["name"] for label in pr_data.get("labels", [])],
        "base_branch": pr_data.get("base", {}).get("ref", ""),
        "head_branch": pr_data.get("head", {}).get("ref", ""),
        "user": pr_data.get("user", {}).get("login", ""),
        "html_url": pr_data.get("html_url", ""),
        "number": pr_number,
    }


def get_pr_diff(base_branch: str) -> str:
    """Get PR diff using local git."""
    try:
        result = subprocess.run(
            ["git", "diff", f"origin/{base_branch}..HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        diff = result.stdout
        if len(diff) > 15000:
            # Truncate at line boundary to avoid breaking syntax
            truncate_at = diff.rfind("\n", 0, 15000)
            if truncate_at == -1:
                truncate_at = 15000
            diff = diff[:truncate_at] + "\n\n... [diff truncated] ..."
        return diff
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not get diff: {e}", file=sys.stderr)
        return ""


def get_pr_commits(base_branch: str) -> list:
    """Get PR commits using local git."""
    try:
        result = subprocess.run(
            ["git", "log", f"origin/{base_branch}..HEAD", "--oneline"],
            capture_output=True,
            text=True,
            check=True,
        )
        commits = []
        for line in result.stdout.strip().split("\n")[:10]:
            if line:
                parts = line.split(" ", 1)
                sha = parts[0]
                message = parts[1] if len(parts) > 1 else ""
                commits.append({"sha": sha, "message": message})
        return commits
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not get commits: {e}", file=sys.stderr)
        return []


def detect_changelog_format() -> str:
    """Detect whether the repo uses RST or Markdown for changelogs.

    Returns:
        'rst' if CHANGES.rst exists, 'md' if CHANGES.md exists,
        defaults to 'rst' if neither exists.
    """
    if os.path.exists("CHANGES.rst"):
        return "rst"
    elif os.path.exists("CHANGES.md"):
        return "md"
    return "rst"


def get_linked_issues(repo: str, pr_body: str, token: str) -> list:
    """Extract and fetch linked issues from PR body."""
    # Common patterns for linking issues
    patterns = [
        r"(?:closes?|fixes?|resolves?)\s*#(\d+)",
        r"(?:closes?|fixes?|resolves?)\s+https://github\.com/[^/]+/[^/]+/issues/(\d+)",
    ]
    issue_numbers = set()
    for pattern in patterns:
        matches = re.findall(pattern, pr_body, re.IGNORECASE)
        issue_numbers.update(matches)
    issues = []
    for issue_num in sorted(list(issue_numbers))[
        :3
    ]:  # Limit to 3 issues in sorted order
        try:
            issue_data = github_api_request(f"/repos/{repo}/issues/{issue_num}", token)
            issues.append(
                {
                    "number": issue_num,
                    "title": issue_data.get("title", ""),
                    "body": (issue_data.get("body", "") or "")[:500],
                }
            )
        except (Exception, SystemExit):
            # Skip issues that fail to fetch (including SystemExit from github_api_request)
            continue
    return issues


def call_gemini(
    prompt: str,
    api_key: str,
    model: str = "gemini-2.0-flash",
    changelog_format: str = "rst",
) -> str:
    """Call Google Gemini API to generate changelog using google-genai SDK."""
    client = genai.Client(api_key=api_key)
    format_name = "RestructuredText" if changelog_format == "rst" else "Markdown"
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are a technical writer who creates concise changelog "
                    f"entries for software projects. You follow the {format_name} format strictly."
                ),
                temperature=0.3,
                max_output_tokens=1000,
                timeout=90,
            ),
        )
        if not response.text:
            raise ValueError("Empty response from Gemini")
        return response.text
    except Exception as e:
        error_msg = str(e)
        error_msg = re.sub(r"key=[a-zA-Z0-9_-]+", "key=***", error_msg)
        error_msg = re.sub(r"Bearer\s+[a-zA-Z0-9_-]+", "Bearer ***", error_msg)
        print(f"Gemini API error: {error_msg}", file=sys.stderr)
        sys.exit(1)


def build_prompt(
    pr_details: dict,
    diff: str,
    commits: list,
    issues: list,
    changelog_format: str = "rst",
) -> str:
    """Build the prompt for the LLM."""
    pr_url = pr_details.get("html_url") or ""
    pr_number = pr_details["number"]
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
    if changelog_format == "md":
        format_name = "Markdown"
        file_name = "CHANGES.md"
        format_rules = """4. MARKDOWN FORMAT RULES:
        - Use ``- `` for bullet points
        - Reference PR using: [#PR_NUMBER](PR_URL)
        - Keep descriptions concise but informative
        - Use backticks for inline code: `code`"""
        example = f"""### Features
        - Added retry mechanism to `SeleniumTestMixin` to prevent CI failures
        from flaky tests.
        [#{pr_number}]({pr_url})"""
    else:
        format_name = "RestructuredText"
        file_name = "CHANGES.rst"
        format_rules = f"""4. RST FORMAT RULES:
        - Use ``- `` for bullet points
        - Reference PR using the exact URL provided: `#{pr_number} <{pr_url}>`_
        - Keep descriptions concise but informative
        - Use proper RST inline markup for code: ``code``"""
        example = f"""Features
        ~~~~~~~~
        - Added retry mechanism to ``SeleniumTestMixin`` to prevent CI failures
        from flaky tests.
        `#{pr_number} <{pr_url}>`_"""

    prompt = f"""Analyze this Pull Request and generate a changelog entry in {format_name} format.
    PR #{pr_number}: {pr_details['title']}
    PR URL: {pr_url}
    {labels_text}
    PR Description:
    {pr_details['body'][:2000] if pr_details['body'] else 'No description provided.'}
    {issues_text}
    {commits_text}
    Code Changes (diff):
    ```
    {diff if diff else 'Diff not available.'}
    ```
    -----
    Generate a changelog entry following these STRICT rules:
    1. FORMAT: {format_name} format for {file_name}.
    2. STRUCTURE:
    - Start with a section header indicating the change type
    - Use bullet points for the changes
    - Reference the PR number with a GitHub link
    3. CHANGE TYPE SECTIONS (use one of these as header):
    - **Features** - New functionality
    - **Bugfixes** - Bug fixes
    - **Changes** - Non-breaking changes, refactors, updates
    - **Breaking Changes** - Backwards incompatible changes
    - **Dependencies** - Dependency updates
    {format_rules}
    5. Keep the entry concise (1-4 bullet points).
    Output ONLY the {format_name} changelog entry.
    Do NOT include any markdown code fences or explanations.
    Example output format (use the actual PR URL provided above, not this example URL):
    {example}
    """
    return prompt


def post_github_comment(repo: str, pr_number: int, comment: str, token: str) -> None:
    """Post a comment on the PR."""
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "OpenWISP-Changelog-Bot",
    }
    try:
        response = retryable_request(
            method="post",
            url=url,
            timeout=(4, 8),
            max_retries=5,
            backoff_factor=3,
            backoff_jitter=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            headers=headers,
            json={"body": comment},
        )
        response.raise_for_status()
    except RequestException as e:
        raise RuntimeError(f"Failed to post comment: {e}") from e


def main():
    """Main entry point."""
    # Get configuration from environment
    pr_number = int(get_env_or_exit("PR_NUMBER"))
    repo = get_env_or_exit("REPO_NAME")
    github_token = get_env_or_exit("GITHUB_TOKEN")
    api_key = get_env_or_exit("GEMINI_API_KEY")
    model = os.environ.get("LLM_MODEL", "gemini-2.0-flash")
    pr_details = get_pr_details(repo, pr_number, github_token)
    base_branch = pr_details["base_branch"]
    diff = get_pr_diff(base_branch)
    commits = get_pr_commits(base_branch)
    issues = get_linked_issues(repo, pr_details["body"], github_token)
    changelog_format = detect_changelog_format()

    prompt = build_prompt(pr_details, diff, commits, issues, changelog_format)
    changelog_entry = call_gemini(prompt, api_key, model, changelog_format)
    changelog_entry = changelog_entry.strip()
    comment = f"```{changelog_format}\n{changelog_entry}\n```"
    try:
        post_github_comment(repo, pr_number, comment, github_token)
    except RuntimeError as e:
        error_msg = str(e)
        error_msg = re.sub(r"Bearer\s+[a-zA-Z0-9_-]+", "Bearer ***", error_msg)
        print(f"Error: {error_msg}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
