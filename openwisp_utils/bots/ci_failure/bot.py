#!/usr/bin/env python3
"""CI Failure Bot - AI-powered analysis of build failures using Gemini"""
import io
import json
import os
import subprocess
import zipfile

import requests
from github import Github, GithubException

try:
    import google.generativeai as genai
except ImportError:
    genai = None


class CIFailureBot:
    def __init__(self):
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY")
        self.workflow_run_id = os.environ.get("WORKFLOW_RUN_ID")
        self.repository_name = os.environ.get("REPOSITORY")
        self.pr_number = os.environ.get("PR_NUMBER")

        # Initialize with None values if missing - bot will still try to comment
        self.github = None
        self.repo = None

        if self.github_token and self.repository_name:
            try:
                self.github = Github(self.github_token)
                self.repo = self.github.get_repo(self.repository_name)
            except Exception as e:
                print(f"Warning: Could not initialize GitHub client: {e}")
        else:
            missing = []
            if not self.github_token:
                missing.append("GITHUB_TOKEN")
            if not self.repository_name:
                missing.append("REPOSITORY")
            print(f"Warning: Missing environment variables: {', '.join(missing)}")

        if self.gemini_api_key and genai is not None:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
                self.model = genai.GenerativeModel(self.model_name)
            except Exception as e:
                print(f"Warning: Could not initialize Gemini: {e}")
                self.model = None
        else:
            if not self.gemini_api_key:
                print(
                    "Warning: GEMINI_API_KEY not provided, will use fallback responses"
                )
            else:
                print(
                    "Warning: google-generativeai not installed, will use fallback responses"
                )
            self.model = None

    def get_build_logs(self):
        """Get actual build logs and error output from failed jobs"""
        if not self.repo:
            print("GitHub client not initialized")
            return []
        if not self.workflow_run_id:
            print("No WORKFLOW_RUN_ID provided")
            return []
        try:
            workflow_run_id = int(self.workflow_run_id)
            workflow_run = self.repo.get_workflow_run(workflow_run_id)
            print(
                f"Fetching jobs for workflow run {workflow_run_id}: {workflow_run.name}"
            )
            jobs = workflow_run.jobs()
            build_logs = []
            for job in jobs:
                print(f"Job: {job.name} - conclusion: {job.conclusion}")
                if job.conclusion == "failure":
                    # Always add job info with name for classification
                    job_entry = {"job_name": job.name}
                    logs_url = job.logs_url
                    if logs_url:
                        try:
                            headers = {
                                "Authorization": f"token {self.github_token}",
                                "Accept": "application/vnd.github.v3+json",
                            }
                            response = requests.get(
                                logs_url, headers=headers, timeout=30
                            )
                            response.raise_for_status()
                            raw = response.content
                            if raw[:2] == b"PK":
                                with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                                    parts = []
                                    for name in zf.namelist():
                                        if name.endswith(".txt"):
                                            parts.append(
                                                zf.read(name).decode("utf-8", "replace")
                                            )
                                    log_text = "\n".join(parts).strip()
                            else:
                                log_text = raw.decode("utf-8", "replace")
                            if len(log_text) > 5000:
                                log_text = (
                                    log_text[:2000]
                                    + "\n\n[...middle truncated...]\n\n"
                                    + log_text[-3000:]
                                )
                            job_entry["logs"] = log_text
                            print(f"  Fetched {len(log_text)} chars of logs")
                        except (requests.RequestException, zipfile.BadZipFile) as e:
                            print(f"  Warning: Could not fetch logs: {e}")
                            job_entry["logs"] = ""
                    else:
                        print("  No logs_url available")
                        job_entry["logs"] = ""
                    build_logs.append(job_entry)
                    # Add step-level failure info
                    for step in getattr(job, "steps", []):
                        if step.conclusion == "failure":
                            print(f"  Failed step: {step.name}")
                            build_logs.append(
                                {
                                    "job_name": job.name,
                                    "step_name": step.name,
                                    "step_number": step.number,
                                }
                            )
            print(f"Total build_logs entries: {len(build_logs)}")
            return build_logs
        except (GithubException, ValueError) as e:
            print(f"Error getting build logs: {e}")
            return []

    def get_pr_diff(self):
        """Get the PR diff using local git"""
        if not self.repo:
            print("GitHub client not initialized")
            return None
        if not self.pr_number:
            return None
        try:
            pr_num = int(self.pr_number)
        except ValueError as e:
            print(f"Invalid PR number: {e}")
            return None
        try:
            pr = self.repo.get_pull(pr_num)
        except GithubException as e:
            print(f"Error fetching PR: {e}")
            return None
        try:
            result = subprocess.run(
                ["git", "diff", f"origin/{self.repo.default_branch}"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except subprocess.SubprocessError as e:
            print(f"Error running git diff: {e}")
            return None
        if result.returncode != 0 or not result.stdout:
            return None
        diff_text = result.stdout
        if len(diff_text) > 8000:
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

    def classify_failure(self, build_logs):
        """Classify failure type based on job names and logs"""
        if not build_logs:
            return "unknown"

        failure_types = set()
        for log_entry in build_logs:
            job_name = log_entry.get("job_name", "").lower()
            logs = log_entry.get("logs", "").lower()

            # Check for QA/formatting failures
            if any(x in job_name for x in ["qa", "lint", "format", "style"]):
                failure_types.add("qa")
            elif any(x in logs for x in ["flake8", "black", "isort", "pep 8"]):
                failure_types.add("qa")

            # Check for test failures
            if any(x in job_name for x in ["test", "pytest", "unittest"]):
                failure_types.add("tests")
            elif any(x in logs for x in ["test failed", "assertion", "pytest"]):
                failure_types.add("tests")

            # Check for setup/dependency failures
            if any(
                x in logs
                for x in ["modulenotfounderror", "importerror", "no module named"]
            ):
                failure_types.add("setup")

        if not failure_types:
            return "unknown"
        elif len(failure_types) == 1:
            return next(iter(failure_types))
        else:
            return "mixed"

    def get_failed_jobs_summary(self, build_logs):
        """Extract summary of failed jobs and steps"""
        failed_jobs = []
        for log_entry in build_logs:
            if "job_name" in log_entry:
                job_info = {"name": log_entry["job_name"]}
                if "step_name" in log_entry:
                    job_info["step"] = log_entry["step_name"]
                failed_jobs.append(job_info)
        return failed_jobs

    def analyze_with_gemini(self, build_logs, pr_diff):
        """Send context to Gemini for intelligent analysis"""
        if not self.model:
            return self.fallback_response()

        if not self.repository_name:
            return self.fallback_response()

        # Classify failure and get context
        failure_type = self.classify_failure(build_logs)
        failed_jobs = self.get_failed_jobs_summary(build_logs)

        project_name = self.repository_name.split("/")[-1]
        repo_url = f"https://github.com/{self.repository_name}"
        build_logs_json = json.dumps(build_logs, indent=2)
        failed_jobs_json = json.dumps(failed_jobs, indent=2)

        if pr_diff:
            pr_diff_json = json.dumps(pr_diff, indent=2)
        else:
            pr_diff_json = "No PR associated"

        context = f"""
### ROLE
You are analyzing CI build failures for OpenWISP. Provide diagnosis AND remediation advice.

### INPUT CONTEXT
1. **Failure Type:** {failure_type}
2. **Failed Jobs:** {failed_jobs_json}
3. **Build Logs:** {build_logs_json}
4. **PR Diff:** {pr_diff_json}
5. **Project:** {project_name}
6. **Repository:** {repo_url}

### CRITICAL RULES - MUST FOLLOW EXACTLY

**Rule 1: Suggest ONLY remediation for failures that actually occurred**
- If failure_type != "qa", DO NOT mention QA commands
- If failure_type != "tests", DO NOT mention test commands
- If failure_type != "setup", DO NOT mention dependency commands
- NEVER suggest fixes for checks that passed

**Rule 2: Remediation by failure type**

**If failure_type = "qa":**
```bash
pip install -e .[qa]
openwisp-qa-format
./run-qa-checks
```
Link: https://openwisp.io/docs/stable/developer/contributing.html
DO NOT mention ./runtests

**If failure_type = "tests":**
```bash
./runtests
```
Review test logic and fix failing assertions.
DO NOT mention QA commands (pip install -e .[qa], openwisp-qa-format, ./run-qa-checks)

**If failure_type = "setup":**
Check dependencies and imports.
```bash
pip install -e .[qa]
```
Focus on ModuleNotFoundError or ImportError.
DO NOT mention formatting or tests unless they also failed.

**If failure_type = "mixed":**
List each issue type separately with appropriate commands.
Example: "Fix formatting issues first, then address test failures."

**If failure_type = "unknown":**
```bash
./run-qa-checks
./runtests
```
General troubleshooting only.

**Rule 3: Response format**
1. **Technical Diagnosis:** 2-3 sentences stating which files/tests failed and why
2. **Required Actions:** Commands in code blocks, based ONLY on failure_type

**Rule 4: Prohibited behaviors**
- DO NOT hallucinate failures that didn't occur
- DO NOT suggest "run all checks" when only one type failed
- DO NOT add extra commands beyond what failure_type requires
- DO NOT use vague language like "might need" or "consider"

### EXAMPLES

**Example 1 - QA failure only:**
"The file bad_format.py contains PEP 8 violations (missing spaces around operators).
The Build / Python 3.11 job failed due to formatting issues.

Required Actions:
```bash
pip install -e .[qa]
openwisp-qa-format
./run-qa-checks
```
See [OpenWISP contributing guidelines](
https://openwisp.io/docs/stable/developer/contributing.html)."

**Example 2 - Test failure only:**
"The test test_always_fails in test_fail.py asserts 1 == 2, which is false.
The Build / Python 3.11 job failed.

Required Actions:
Review and fix the failing test logic:
```bash
./runtests
```"

**Example 3 - Setup failure only:**
"Import failed: ModuleNotFoundError for 'nonexistent_module' in final_test.py.
The Build / Python 3.11 job failed.

Required Actions:
Check dependencies and install requirements:
```bash
pip install -e .[qa]
```"

Analyze the failure and provide diagnosis + remediation following these rules:
"""
        try:
            response = self.model.generate_content(context)
            return response.text.strip()
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return self.fallback_response()

    def fallback_response(self):
        """Fallback response if Gemini fails"""
        return """
The build failed. Automated analysis is unavailable.

**Recommended Actions:**
```bash
pip install -e .[qa]
./run-qa-checks
./runtests
```

See the [OpenWISP contributing guidelines](
https://openwisp.io/docs/stable/developer/contributing.html) for more details.
""".strip()

    def post_comment(self, message):
        """Post or update comment on PR"""
        if not self.pr_number:
            print("No PR number, skipping comment")
            return
        if not self.github or not self.repo:
            print("GitHub client not initialized, cannot post comment")
            return
        marker = "<!-- ci-failure-bot-comment -->"
        message_with_marker = (
            f"{marker}\n🤖 **CI Failure Bot** (AI-powered)\n\n{message}"
        )
        try:
            pr_num = int(self.pr_number)
        except ValueError as e:
            print(f"Invalid PR number: {e}")
            return
        try:
            pr = self.repo.get_pull(pr_num)
        except GithubException as e:
            print(f"Error fetching PR: {e}")
            return
        try:
            existing_comments = pr.get_issue_comments()
            for comment in existing_comments:
                if marker in comment.body:
                    print("Bot comment already exists, updating it")
                    comment.edit(message_with_marker)
                    return
        except GithubException as e:
            print(f"Error checking existing comments: {e}")
            return  # Don't create duplicate if listing fails
        try:
            pr.create_issue_comment(message_with_marker)
            print(f"Posted comment to PR #{pr_num}")
        except GithubException as e:
            print(f"Error posting comment: {e}")

    def run(self):
        """Main execution flow - adapted for workflow_run"""
        message = None
        should_skip = False
        skip_reason = ""
        try:
            print("CI Failure Bot starting - AI-powered analysis")

            # Early guard for repo
            if not self.repo:
                print("GitHub client not initialized, cannot proceed")
                return

            # Check for skip conditions (but don't return early)
            try:
                if self.workflow_run_id:
                    workflow_run = self.repo.get_workflow_run(int(self.workflow_run_id))
                    if (
                        workflow_run.actor
                        and "dependabot" in workflow_run.actor.login.lower()
                    ):
                        should_skip = True
                        skip_reason = f"dependabot PR from {workflow_run.actor.login}"
                if self.pr_number and not should_skip:
                    try:
                        pr_num = int(self.pr_number)
                        pr = self.repo.get_pull(pr_num)
                        if pr.head.repo is None:
                            should_skip = True
                            skip_reason = "PR with deleted head repository"
                        elif pr.head.repo.full_name != self.repository_name:
                            should_skip = True
                            skip_reason = f"fork PR from {pr.head.repo.full_name}"
                    except (GithubException, ValueError) as e:
                        print(f"Warning: Could not check fork status: {e}")
            except (GithubException, AttributeError, ValueError) as e:
                print(f"Warning: Could not check actor: {e}")
            # Determine message based on context
            if not self.pr_number:
                print("No PR context available - workflow_run without PR")
                message = None
            elif should_skip:
                print(f"Skipping: {skip_reason}")
                return
            else:
                # We have PR context, proceed with analysis
                build_logs = self.get_build_logs()
                pr_diff = self.get_pr_diff()
                if not build_logs and not pr_diff:
                    print("No build logs or PR diff found, using fallback response")
                    message = self.fallback_response()
                else:
                    print("Analyzing failure with Gemini AI...")
                    message = self.analyze_with_gemini(build_logs, pr_diff)
        except Exception as e:
            print(f"Error in analysis: {e}")
            message = self.fallback_response()
        # Single comment decision point
        if message:
            self.post_comment(message)
        else:
            print("No PR context available, no comment posted (expected)")
        print("CI Failure Bot completed successfully")


if __name__ == "__main__":
    bot = CIFailureBot()
    bot.run()
