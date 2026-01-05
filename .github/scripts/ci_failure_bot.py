#!/usr/bin/env python3
"""
CI Failure Bot - responds to failed builds with helpful info
"""

import os
import sys

from github import Github


class CIFailureBot:
    def __init__(self):
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.workflow_run_id = os.environ.get("WORKFLOW_RUN_ID")
        self.repository_name = os.environ.get("REPOSITORY")
        self.pr_number = os.environ.get("PR_NUMBER")

        if not all([self.github_token, self.workflow_run_id, self.repository_name]):
            print("Missing env vars")
            sys.exit(1)

        try:
            self.workflow_run_id = int(self.workflow_run_id)
        except ValueError:
            print("Invalid WORKFLOW_RUN_ID: must be numeric")
            sys.exit(1)

        self.github = Github(self.github_token)
        self.repo = self.github.get_repo(self.repository_name)

    def get_workflow_logs(self):
        try:
            workflow_run = self.repo.get_workflow_run(self.workflow_run_id)
            jobs = workflow_run.jobs()

            failed_jobs = []
            for job in jobs:
                if job.conclusion == "failure":
                    for step in job.steps:
                        if step.conclusion == "failure":
                            failed_jobs.append(
                                {
                                    "job_name": job.name,
                                    "step_name": step.name,
                                    "step_number": step.number,
                                }
                            )
            return failed_jobs
        except Exception as e:
            print(f"Error getting logs: {e}")
            return []

    def analyze_failure_type(self, logs):
        failure_types = []

        for log_entry in logs:
            step_name = log_entry["step_name"].lower()

            if "qa checks" in step_name:
                failure_types.append("qa_checks")
            elif "tests" in step_name:
                failure_types.append("tests")
            elif any(
                keyword in step_name for keyword in ["install", "dependencies", "setup"]
            ):
                failure_types.append("setup")

        return list(set(failure_types))

    def generate_qa_response(self):
        return """
## QA Checks Failed

The code quality checks didn't pass. To fix this:

```bash
openwisp-qa-format
```

This will automatically fix most flake8, black, and isort issues.

After running the command, commit and push the changes.

See the [contributing guidelines](https://openwisp.io/docs/dev/developer/contributing.html) for more details.
"""

    def generate_test_response(self):
        return """
## Tests Failed

Some tests are failing. To debug:

```bash
./runtests
```

Check the CI logs above for specific error details. Common issues:
- Import errors from missing dependencies
- Logic changes that broke existing functionality
- Missing test dependencies

See the [contributing guidelines](https://openwisp.io/docs/dev/developer/contributing.html) for testing help.
"""

    def generate_setup_response(self):
        return """
## Setup Failed

There was an issue with dependencies or environment setup.

Check if you added new dependencies to requirements-test.txt.
Verify Python/Django version compatibility:
- Python: 3.10, 3.11, 3.12, 3.13
- Django: 4.2, 5.0, 5.1, 5.2

The CI will retry automatically, or push a small change to trigger rebuild.
"""

    def post_comment(self, message):
        if not self.pr_number or self.pr_number.strip() == "":
            print("No PR number, skipping comment")
            return

        try:
            try:
                pr_num = int(self.pr_number)
            except ValueError:
                print(f"Invalid PR_NUMBER: {self.pr_number}")
                return

            pr = self.repo.get_pull(pr_num)

            # Check for existing bot comments to avoid duplicates
            bot_login = self.github.get_user().login
            existing_comments = pr.get_issue_comments()

            for comment in existing_comments:
                if comment.user.login == bot_login and (
                    "CI Build Failed" in comment.body
                    or "QA Checks Failed" in comment.body
                ):
                    print("Bot comment already exists, updating it")
                    comment.edit(message)
                    return

            # No existing comment, create new one
            pr.create_issue_comment(message)
            print(f"Posted comment to PR #{pr_num}")
        except Exception as e:
            print(f"Error posting comment: {e}")

    def run(self):
        print("CI Failure Bot starting")

        logs = self.get_workflow_logs()
        if not logs:
            print("No failure logs found")
            return

        failure_types = self.analyze_failure_type(logs)
        print(f"Detected failure types: {failure_types}")

        responses = []

        if "qa_checks" in failure_types:
            responses.append(self.generate_qa_response())

        if "tests" in failure_types:
            responses.append(self.generate_test_response())

        if "setup" in failure_types:
            responses.append(self.generate_setup_response())

        if not responses:
            responses.append(
                """
## CI Build Failed

Check the logs above for details. Common fixes:
- Run `openwisp-qa-format` for code style issues
- Run `./runtests` locally to debug test failures
- Check dependencies for setup issues

See: https://openwisp.io/docs/dev/developer/contributing.html
"""
            )

        final_message = "\n\n".join(responses)
        self.post_comment(final_message)

        print("CI Failure Bot completed")


if __name__ == "__main__":
    bot = CIFailureBot()
    bot.run()
