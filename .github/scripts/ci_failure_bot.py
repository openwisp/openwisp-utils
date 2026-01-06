#!/usr/bin/env python3
"""
CI Failure Bot - AI-powered analysis of build failures using Gemini
"""

import json
import os
import sys

import google.generativeai as genai
import requests
from github import Github, GithubException


class CIFailureBot:
    def __init__(self):
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY")
        self.workflow_run_id = os.environ.get("WORKFLOW_RUN_ID")
        self.repository_name = os.environ.get("REPOSITORY")
        self.pr_number = os.environ.get("PR_NUMBER")

        if not all(
            [
                self.github_token,
                self.gemini_api_key,
                self.workflow_run_id,
                self.repository_name,
            ]
        ):
            missing = []
            if not self.github_token:
                missing.append("GITHUB_TOKEN")
            if not self.gemini_api_key:
                missing.append("GEMINI_API_KEY")
            if not self.workflow_run_id:
                missing.append("WORKFLOW_RUN_ID")
            if not self.repository_name:
                missing.append("REPOSITORY")
            print(f"Missing required environment variables: {', '.join(missing)}")
            sys.exit(1)

        try:
            self.workflow_run_id = int(self.workflow_run_id)
        except ValueError:
            print("Invalid WORKFLOW_RUN_ID: must be numeric")
            sys.exit(1)

        self.github = Github(self.github_token)
        self.repo = self.github.get_repo(self.repository_name)

        genai.configure(api_key=self.gemini_api_key)
        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        self.model = genai.GenerativeModel(model_name)

    def get_build_logs(self):
        """Get actual build logs and error output from failed jobs"""
        try:
            workflow_run = self.repo.get_workflow_run(self.workflow_run_id)
            jobs = workflow_run.jobs()

            build_logs = []
            for job in jobs:
                if job.conclusion == "failure":
                    # Get job logs URL and fetch content
                    logs_url = job.logs_url
                    if logs_url:
                        headers = {
                            "Authorization": f"token {self.github_token}",
                            "Accept": "application/vnd.github.v3+json",
                        }
                        response = requests.get(logs_url, headers=headers, timeout=30)
                        if response.status_code == 200:
                            build_logs.append(
                                {
                                    "job_name": job.name,
                                    "logs": response.text[
                                        -5000:
                                    ],  # Last 5000 chars to avoid token limits
                                }
                            )

                    # Also get step details
                    for step in job.steps:
                        if step.conclusion == "failure":
                            build_logs.append(
                                {
                                    "job_name": job.name,
                                    "step_name": step.name,
                                    "step_number": step.number,
                                }
                            )

            return build_logs
        except (GithubException, ValueError) as e:
            print(f"Error getting build logs: {e}")
            return []

    def get_pr_diff(self):
        """Get the PR diff/changes if PR exists"""
        if not self.pr_number or self.pr_number.strip() == "":
            return None

        try:
            pr_num = int(self.pr_number)
            pr = self.repo.get_pull(pr_num)

            # Get diff content
            diff_url = pr.diff_url
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3.diff",
            }
            response = requests.get(diff_url, headers=headers, timeout=30)
            if response.status_code == 200:
                diff_text = response.text
                if len(diff_text) > 8000:
                    # Take first 4000 and last 4000 chars for context
                    diff_text = (
                        diff_text[:4000]
                        + "\n\n[...middle truncated...]\n\n"
                        + diff_text[-4000:]
                    )

                return {
                    "title": pr.title,
                    "body": pr.body or "",
                    "diff": diff_text,
                }
        except (GithubException, requests.RequestException) as e:
            print(f"Error getting PR diff: {e}")

        return None

    def get_workflow_yaml(self):
        """Get the workflow YAML configuration"""
        try:
            workflow_run = self.repo.get_workflow_run(self.workflow_run_id)
            workflow_path = workflow_run.path

            # Get workflow file content
            workflow_file = self.repo.get_contents(workflow_path)
            return workflow_file.decoded_content.decode("utf-8")
        except GithubException as e:
            print(f"Error getting workflow YAML: {e}")
            return None

    def analyze_with_gemini(self, build_logs, pr_diff, workflow_yaml):
        """Send context to Gemini for intelligent analysis"""

        # Prepare context for Gemini
        project_name = self.repository_name.split("/")[-1]
        repo_url = f"https://github.com/{self.repository_name}"
        qa_checks_url = f"{repo_url}/blob/master/openwisp-qa-check"
        runtests_url = f"{repo_url}/blob/master/runtests"

        # Build the context string with proper line breaks
        build_logs_json = json.dumps(build_logs, indent=2)
        if pr_diff:
            pr_diff_json = json.dumps(pr_diff, indent=2)
        else:
            pr_diff_json = "No PR associated"

        # Gemini prompt - ignore line length for readability
        context = f"""
### ROLE
You are the "Automated Maintainer Gatekeeper." Your goal is to analyze Pull Request (PR) build failures and provide direct, technically accurate, and no-nonsense feedback to contributors.

### INPUT CONTEXT PROVIDED
1. **Build Output/Logs:** {build_logs_json}
2. **YAML Workflow:** {workflow_yaml or "Not available"}
3. **PR Diff:** {pr_diff_json}
4. **Project Name:** {project_name}
5. **Repository:** {repo_url}
6. **run-qa-checks:** {qa_checks_url}
7. **runtests:** {runtests_url}

### TASK
Analyze the provided context to determine why the build failed. Categorize the failure and respond according to the "Tone Guidelines" below.

### TONE GUIDELINES
- **Direct & Honest:** Do not use "fluff" or overly polite corporate language.
- **Firm Standards:** If a PR is low-effort, spammy, or fails to follow basic instructions, state that clearly.
- **Action-Oriented:** Provide the exact command or file change needed to fix the error, unless the PR is spammy, in which case we should just declare the PR as potential SPAM and ask maintainers to manually review it.

### RESPONSE STRUCTURE
1. **Status Summary:** A one-sentence blunt assessment of the failure.
2. **Technical Diagnosis:**
   - Identify the specific line/test that failed.
   - Explain *why* it failed.
3. **Required Action:** Provide a code block or specific steps the contributor must take.
4. **Quality Warning (If Applicable):** If the PR appears to be "spam" (e.g., trivial README changes, AI-generated nonsense, or repeated basic errors), include a firm statement that such contributions are a drain on project resources and ping the maintainers asking them for manual review.

### EXAMPLE RESPONSE STYLE
"The build failed because you neglected to update the test suite to match your logic changes. This project does not accept functional changes without corresponding test updates. Refer to the log at line 452. Update tests/logic_test.py before re-submitting. We prioritize high-quality, ready-to-merge code; please ensure you run local tests before pushing."

Analyze the failure and provide your response:
"""  # noqa: E501

        try:
            response = self.model.generate_content(context)
            return response.text
        except (ValueError, ConnectionError, Exception) as e:
            print(f"Error calling Gemini API: {e}")
            return self.fallback_response()

    def fallback_response(self):
        """Fallback response if Gemini fails"""
        return """
## CI Build Failed

The automated analysis is temporarily unavailable. Please check the CI logs above for specific error details.

Common fixes:
- Run `openwisp-qa-format` for code style issues
- Run `./runtests` locally to debug test failures
- Check dependencies for setup issues

See: https://openwisp.io/docs/dev/developer/contributing.html
"""

    def post_comment(self, message):
        """Post or update comment on PR"""
        if not self.pr_number or self.pr_number.strip() == "":
            print("No PR number, skipping comment")
            return

        # Add consistent marker for deduplication
        marker = "<!-- ci-failure-bot-comment -->"
        message_with_marker = f"{marker}\n{message}"

        try:
            pr_num = int(self.pr_number)
            pr = self.repo.get_pull(pr_num)

            # Check for existing bot comments to avoid duplicates
            bot_login = self.github.get_user().login
            existing_comments = pr.get_issue_comments()

            for comment in existing_comments:
                if comment.user.login == bot_login and marker in comment.body:
                    print("Bot comment already exists, updating it")
                    comment.edit(message_with_marker)
                    return

            # No existing comment, create new one
            pr.create_issue_comment(message_with_marker)
            print(f"Posted comment to PR #{pr_num}")
        except (GithubException, ValueError) as e:
            print(f"Error posting comment: {e}")

    def run(self):
        """Main execution flow"""
        print("CI Failure Bot starting - AI-powered analysis")

        # Double-check: Skip if this is a dependabot PR
        try:
            workflow_run = self.repo.get_workflow_run(self.workflow_run_id)
            if workflow_run.actor and "dependabot" in workflow_run.actor.login.lower():
                print(f"Skipping dependabot PR from {workflow_run.actor.login}")
                return
        except (GithubException, AttributeError) as e:
            print(f"Warning: Could not check actor: {e}")

        # Get all context
        build_logs = self.get_build_logs()
        pr_diff = self.get_pr_diff()
        workflow_yaml = self.get_workflow_yaml()

        if not build_logs:
            print("No build logs found")
            return

        print("Analyzing failure with Gemini AI...")

        # Get AI analysis
        ai_response = self.analyze_with_gemini(build_logs, pr_diff, workflow_yaml)

        # Post intelligent comment
        self.post_comment(ai_response)

        print("CI Failure Bot completed")


if __name__ == "__main__":
    bot = CIFailureBot()
    bot.run()
