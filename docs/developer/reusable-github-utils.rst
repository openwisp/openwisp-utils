Re-usable GitHub Actions and Workflows
======================================

GitHub Actions
--------------

Retry Command
~~~~~~~~~~~~~

This GitHub Action retries a shell command if it fails. It is useful for
handling flaky tests in CI/CD pipelines.

**Inputs**

- ``command`` (required): The shell command to run.
- ``max_attempts`` (optional): The number of retry attempts. Defaults to
  ``3``.
- ``delay_seconds`` (optional): The delay between retries in seconds.
  Defaults to ``5``.

**Usage Example**

You can use this action in your workflow as follows:

.. code-block:: yaml

    name: Retry Example

    on:
      push:
        branches:
          - main

    jobs:
      retry-command-example:
        runs-on: ubuntu-latest
        steps:
          - name: Checkout code
            uses: actions/checkout@v3

          - name: Test
            uses: openwisp/openwisp-utils/.github/actions/retry-command@master
            with:
              delay_seconds: 30
              max_attempts: 5
              command: ./runtests.py --parallel
            env:
              SELENIUM_HEADLESS: 1

This example retries the ``./runtests.py --parallel`` command up to 5
times with a 30 second delay between attempts.

.. note::

    If the command continues to fail after the specified number of
    attempts, the action will exit with a non-zero status, causing the
    workflow to fail.

CI Failure Bot
~~~~~~~~~~~~~~

This GitHub workflow automatically analyzes failed CI builds and provides
intelligent feedback to contributors using AI-powered analysis.

The bot examines build logs, PR changes, and workflow context to generate
specific, actionable guidance that helps contributors fix issues quickly.

**Inputs**

- ``GEMINI_API_KEY`` (optional): Google Gemini API key for AI analysis. If
  not provided, the bot uses fallback responses
- ``GEMINI_MODEL`` (optional): Gemini model to use. Defaults to
  ``gemini-2.5-flash``

**Usage Example**

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
              pip install -e .[github_actions]

          - name: Run CI Failure Bot
            env:
              GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
              GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
              WORKFLOW_RUN_ID: ${{ github.event.workflow_run.id }}
              REPOSITORY: ${{ github.repository }}
              PR_NUMBER: ${{ github.event.workflow_run.pull_requests[0].number || '' }}
            run: python -m openwisp_utils.ci_failure_bot

This example automatically triggers when the "OpenWISP Utils CI Build"
workflow fails, analyzes the failure using Gemini AI, and posts
intelligent feedback to the associated pull request.

**Features**

- **Automatic triggering**: Responds to CI build failures in pull requests
- **AI-powered analysis**: Uses Google Gemini to analyze failure logs and
  provide specific guidance
- **OpenWISP QA integration**: Instructs contributors to use ``pip install
  -e .[qa]``, ``./run-qa-checks``, and ``openwisp-qa-format`` for proper
  code formatting
- **Intelligent responses**: Provides direct, actionable feedback based on
  actual failure context
- **Comment deduplication**: Updates existing comments instead of creating
  duplicates
- **Dependabot exclusion**: Automatically skips dependency update PRs
- **Fork detection**: Skips external PRs for security
- **Fallback handling**: Provides basic guidance if AI analysis fails

**Configuration**
+++++++++++++++++

Repository Secrets
++++++++++++++++++

The following secrets can be configured in the repository for enhanced
functionality:

- ``GEMINI_API_KEY``: Google Gemini API key for AI analysis (optional -
  fallback responses used if not provided)

Environment Variables
+++++++++++++++++++++

Optional environment variables for customization:

- ``GEMINI_MODEL``: Gemini model to use (default: ``gemini-2.5-flash``)

**Limitations**

- **Optional Gemini API**: Google Gemini API access enhances analysis
  quality, but the bot provides fallback responses when unavailable
- **Privacy consideration**: PR diffs and build logs are sent to Google's
  Gemini AI service for analysis when API key is provided. Organizations
  with sensitive codebases should review Google's data handling policies
- **API costs**: Each CI failure with Gemini enabled triggers an API call.
  Monitor usage to manage costs, especially in repositories with frequent
  CI failures
- Analysis quality depends on error log clarity
- May not handle very complex or unusual failure scenarios
- Skips dependabot PRs to avoid unnecessary noise

.. note::

    If the Gemini API is unavailable, the bot provides a fallback response
    with basic troubleshooting guidance. The workflow will fail loudly if
    the bot script encounters critical errors, ensuring issues are visible
    in GitHub Actions logs.

GitHub Workflows
----------------

Replicate Commits to Version Branch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This re-usable workflow replicates commits from the ``master`` branch to a
version branch. The version branch name is derived from the version of the
Python package specified in the workflow.

Version branches are essential during development to ensure that each
OpenWISP module depends on compatible versions of its OpenWISP
dependencies. Without version branches, modules depending on the
``master`` branch of other modules may encounter errors, as the ``master``
branch could include future changes that are incompatible with previous
versions. This makes it impossible to build a specific commit reliably
after such changes.

To address this, we use version branches so that each module can depend on
a compatible version of its dependencies during development. Managing
these version branches manually is time-consuming, which is why this
re-usable GitHub workflow automates the process of keeping version
branches synchronized with the ``master`` branch.

You can invoke this workflow from another workflow using the following
example:

.. code-block:: yaml

    name: Replicate Commits to Version Branch

    on:
      push:
        branches:
          - master

    jobs:
      version-branch:
        uses: openwisp/openwisp-utils/.github/workflows/reusable-version-branch.yml@master
        with:
          # The name of the Python package (required)
          module_name: openwisp_utils
          # Whether to install the Python package. Defaults to false.
          install_package: true

.. note::

    If the ``master`` branch is force-pushed, this workflow will fail due
    to conflicts. To resolve this, you must manually synchronize the
    version branch with the ``master`` branch. You can use the following
    commands to perform this synchronization:

    .. code-block:: bash

        VERSION=<enter-version-number> # e.g. 1.2
        git fetch origin
        git checkout $VERSION
        git reset --hard origin/master
        git push origin $VERSION --force-with-lease
