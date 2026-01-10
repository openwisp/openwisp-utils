CI Failure Bot
==============

This GitHub workflow automatically analyzes failed CI builds and provides
intelligent feedback to contributors using AI-powered analysis.

The bot examines build logs, PR changes, and workflow context to generate
specific, actionable guidance that helps contributors fix issues quickly.

Inputs
------

- ``GEMINI_API_KEY`` (required): Google Gemini API key for AI analysis
- ``GEMINI_MODEL`` (optional): Gemini model to use. Defaults to
  ``gemini-2.5-flash``

Usage Example
-------------

You can use this workflow in your repository as follows:

.. code-block:: yaml

    name: CI Failure Bot

    on:
      workflow_run:
        workflows: ["OpenWISP Utils CI Build"]
        types:
          - completed

    permissions:
      issues: write
      pull-requests: write
      contents: read

    jobs:
      ci-failure-bot:
        runs-on: ubuntu-latest
        if: ${{ github.event.workflow_run.conclusion == 'failure' && !contains(github.event.workflow_run.actor.login, 'dependabot') }}

        steps:
          - name: Checkout repository
            uses: actions/checkout@v6

          - name: Set up Python
            uses: actions/setup-python@v6
            with:
              python-version: "3.11"

          - name: Install dependencies
            run: |
              pip install requests>=2.32.5 PyGithub>=2.0.0 google-genai>=1.0.0

          - name: Run CI Failure Bot
            env:
              GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
              GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
              WORKFLOW_RUN_ID: ${{ github.event.workflow_run.id }}
              REPOSITORY: ${{ github.repository }}
              PR_NUMBER: ${{ github.event.workflow_run.pull_requests[0].number || '' }}
            run: python .github/scripts/ci_failure_bot.py

This example automatically triggers when the "OpenWISP Utils CI Build"
workflow fails, analyzes the failure using Gemini AI, and posts
intelligent feedback to the associated pull request.

Note
----

If the Gemini API is unavailable, the bot provides a fallback response
with basic troubleshooting guidance. The workflow will fail loudly if the
bot script encounters critical errors, ensuring issues are visible in
GitHub Actions logs.
