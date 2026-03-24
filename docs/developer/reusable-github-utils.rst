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
            uses: actions/checkout@v6

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

Auto-Assignment Bot
~~~~~~~~~~~~~~~~~~~

A collection of Python scripts that automate issue and PR management for
OpenWISP repositories. The bot provides the following features:

- **Issue auto-assignment**: When a contributor opens a PR referencing an
  issue (e.g., ``Fixes #123``), the issue is automatically assigned to the
  PR author.
- **Assignment request responses**: When someone comments asking to be
  assigned, the bot responds with contributing guidelines explaining that
  no assignment is needed — just open a PR.
- **Stale PR management**: Warns PR authors after 7 days of inactivity,
  marks stale and unassigns after 14 days, and closes after 60 days.
- **PR reopen reassignment**: When a stale PR is reopened, linked issues
  are reassigned back to the author.

**Secrets**

These secrets are used by the workflow to generate a ``GITHUB_TOKEN`` via
the ``actions/create-github-app-token`` action. The bot itself consumes
the following environment variables at runtime: ``GITHUB_TOKEN``,
``REPOSITORY``, and ``GITHUB_EVENT_NAME``.

- ``OPENWISP_BOT_APP_ID`` (required): OpenWISP Bot GitHub App ID.
- ``OPENWISP_BOT_PRIVATE_KEY`` (required): OpenWISP Bot GitHub App private
  key.

**Setup for Other Repositories**

To enable the auto-assignment bot in another OpenWISP repository, you must
create four workflow files under ``.github/workflows/`` that call the
reusable GitHub Workflow. This reusable workflow automatically handles
token generation, environment setup, and executing the bot scripts.

.. note::

    Each caller workflow must declare its own ``permissions`` block.
    GitHub Actions reusable workflows inherit permissions from the caller,
    so the reusable workflow cannot set them on its own.

Create the following workflow files in your repository.

**1. Issue Assignment Bot**
(``.github/workflows/bot-autoassign-issue.yml``)

.. code-block:: yaml

    name: Issue Assignment Bot
    on:
      issue_comment:
        types: [created]
    permissions:
      contents: read
      issues: write
    concurrency:
      group: bot-autoassign-issue-${{ github.repository }}-${{ github.event.issue.number }}
      cancel-in-progress: true
    jobs:
      respond-to-assign-request:
        if: github.event.issue.pull_request == null
        uses: openwisp/openwisp-utils/.github/workflows/reusable-bot-autoassign.yml@master
        with:
          bot_command: issue_assignment
        secrets:
          OPENWISP_BOT_APP_ID: ${{ secrets.OPENWISP_BOT_APP_ID }}
          OPENWISP_BOT_PRIVATE_KEY: ${{ secrets.OPENWISP_BOT_PRIVATE_KEY }}

**2. PR Issue Link**
(``.github/workflows/bot-autoassign-pr-issue-link.yml``)

.. code-block:: yaml

    name: PR Issue Auto-Assignment
    on:
      pull_request_target:
        types: [opened, reopened, closed]
    permissions:
      contents: read
      issues: write
      pull-requests: read
    concurrency:
      group: bot-autoassign-pr-link-${{ github.repository }}-${{ github.event.pull_request.number }}
      cancel-in-progress: true
    jobs:
      auto-assign-issue:
        if: github.event.action != 'closed' || github.event.pull_request.merged == false
        uses: openwisp/openwisp-utils/.github/workflows/reusable-bot-autoassign.yml@master
        with:
          bot_command: issue_assignment
        secrets:
          OPENWISP_BOT_APP_ID: ${{ secrets.OPENWISP_BOT_APP_ID }}
          OPENWISP_BOT_PRIVATE_KEY: ${{ secrets.OPENWISP_BOT_PRIVATE_KEY }}

**3. PR Reopen** (``.github/workflows/bot-autoassign-pr-reopen.yml``)

.. code-block:: yaml

    name: PR Reopen Reassignment
    on:
      pull_request_target:
        types: [reopened]
      issue_comment:
        types: [created]
    permissions:
      contents: read
      issues: write
      pull-requests: write
    concurrency:
      group: bot-autoassign-pr-reopen-${{ github.repository }}-${{ github.event.pull_request.number || github.event.issue.number }}
      cancel-in-progress: true
    jobs:
      reassign-on-reopen:
        if: github.event_name == 'pull_request_target' && github.event.action == 'reopened'
        uses: openwisp/openwisp-utils/.github/workflows/reusable-bot-autoassign.yml@master
        with:
          bot_command: pr_reopen
        secrets:
          OPENWISP_BOT_APP_ID: ${{ secrets.OPENWISP_BOT_APP_ID }}
          OPENWISP_BOT_PRIVATE_KEY: ${{ secrets.OPENWISP_BOT_PRIVATE_KEY }}
      handle-pr-activity:
        if: github.event_name == 'issue_comment' && github.event.issue.pull_request && github.event.issue.user.login == github.event.comment.user.login
        uses: openwisp/openwisp-utils/.github/workflows/reusable-bot-autoassign.yml@master
        with:
          bot_command: pr_reopen
        secrets:
          OPENWISP_BOT_APP_ID: ${{ secrets.OPENWISP_BOT_APP_ID }}
          OPENWISP_BOT_PRIVATE_KEY: ${{ secrets.OPENWISP_BOT_PRIVATE_KEY }}

.. note::

    Both jobs use ``bot_command: pr_reopen``. The ``pr_reopen`` command
    dispatches to ``PRReopenBot`` on ``pull_request_target`` events (to
    reassign issues when a PR is reopened) and to ``PRActivityBot`` on
    ``issue_comment`` events (to remove the stale label when the PR author
    comments on their stale PR).

**4. Stale PR** (``.github/workflows/bot-autoassign-stale-pr.yml``)

.. code-block:: yaml

    name: Stale PR Management
    on:
      schedule:
        - cron: "0 0 * * *"
      workflow_dispatch:
    permissions:
      contents: read
      issues: write
      pull-requests: write
    concurrency:
      group: bot-autoassign-stale-pr-${{ github.repository }}
      cancel-in-progress: false
    jobs:
      manage-stale-prs-python:
        uses: openwisp/openwisp-utils/.github/workflows/reusable-bot-autoassign.yml@master
        with:
          bot_command: stale_pr
        secrets:
          OPENWISP_BOT_APP_ID: ${{ secrets.OPENWISP_BOT_APP_ID }}
          OPENWISP_BOT_PRIVATE_KEY: ${{ secrets.OPENWISP_BOT_PRIVATE_KEY }}

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

Backport Fixes to Stable Branch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This re-usable workflow automates cherry-picking fixes from ``master`` or
``main`` to stable release branches.

It supports two triggers:

- **Commit message**: Add ``[backport X.Y]`` or ``[backport: X.Y]`` to the
  squash merge commit body to automatically backport when merged to
  ``master`` or ``main``.
- **Comment**: Comment ``/backport X.Y`` on a merged PR (org members
  only).

If the cherry-pick fails due to conflicts, the bot comments on the PR with
manual resolution steps. If the target branch does not exist or the PR is
not yet merged, the workflow exits safely without failing.

.. code-block:: yaml

    name: Backport fixes to stable branch

    on:
      push:
        branches:
          - master
          - main
      issue_comment:
        types: [created]

    concurrency:
      group: backport-${{ github.workflow }}-${{ github.ref }}
      cancel-in-progress: false

    permissions:
      contents: write
      pull-requests: write

    jobs:
      backport-on-push:
        if: github.event_name == 'push'
        uses: openwisp/openwisp-utils/.github/workflows/reusable-backport.yml@master
        with:
          commit_sha: ${{ github.sha }}
        secrets:
          app_id: ${{ secrets.OPENWISP_BOT_APP_ID }}
          private_key: ${{ secrets.OPENWISP_BOT_PRIVATE_KEY }}

      backport-on-comment:
        if: >
          github.event_name == 'issue_comment' &&
          github.event.issue.pull_request &&
          github.event.issue.pull_request.merged_at != null &&
          github.event.issue.state == 'closed' &&
          contains(fromJSON('["MEMBER", "OWNER"]'), github.event.comment.author_association) &&
          startsWith(github.event.comment.body, '/backport')
        uses: openwisp/openwisp-utils/.github/workflows/reusable-backport.yml@master
        with:
          pr_number: ${{ github.event.issue.number }}
          comment_body: ${{ github.event.comment.body }}
        secrets:
          app_id: ${{ secrets.OPENWISP_BOT_APP_ID }}
          private_key: ${{ secrets.OPENWISP_BOT_PRIVATE_KEY }}

Automated CI Failure Bot
~~~~~~~~~~~~~~~~~~~~~~~~

To assist contributors with debugging, this reusable workflow leverages
Google's Gemini API to analyze continuous integration failures in
real-time. Upon detecting a failed CI run, it intelligently gathers the
relevant source code context (safely bypassing unnecessary assets)
alongside the raw error logs. It then posts a concise summary and an
actionable remediation plan directly to the Pull Request.

When the bot detects that all failures are transient (e.g., network
errors, browser crashes, Coveralls flakiness), it automatically re-runs
the failed jobs up to 3 times and posts a short notification instead of
the full analysis. This requires ``actions: write`` permission in the
caller workflow and the GitHub App must have the **Actions** permission
enabled. If the permission is not granted (e.g., in repositories that
haven't updated their caller workflow yet), the auto-retry is skipped
gracefully and the full analysis is posted instead.

This workflow is intended to be triggered via the ``workflow_run`` event
after your primary test suite concludes. It features strict
cross-repository concurrency locks and token limits to prevent PR spam on
rapid, consecutive commits.

**Usage Example**

Set up a caller workflow in your repository (e.g.,
``.github/workflows/bot-ci-failure.yml``) that monitors your primary CI
job:

.. code-block:: yaml

    name: CI Failure Bot (Caller)

    on:
      workflow_run:
        workflows: ["CI Build"]
        types:
          - completed

    permissions:
      pull-requests: read
      actions: read
      contents: read

    concurrency:
      group: ci-failure-${{ github.repository }}-${{ github.event.workflow_run.pull_requests[0].number || github.event.workflow_run.head_branch }}
      cancel-in-progress: true

    jobs:
      find-pr:
        runs-on: ubuntu-latest
        if: ${{ github.event.workflow_run.conclusion == 'failure' && github.event.workflow_run.event == 'pull_request' }}
        outputs:
          pr_number: ${{ steps.pr.outputs.number }}
          pr_author: ${{ steps.pr.outputs.author }}
        steps:
          - name: Find PR Number
            id: pr
            env:
              GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
              REPO: ${{ github.repository }}
              PR_NUMBER_PAYLOAD: ${{ github.event.workflow_run.pull_requests[0].number }}
              EVENT_HEAD_SHA: ${{ github.event.workflow_run.head_sha }}
            run: |
              emit_pr() {
                local pr_number="$1"
                local pr_author
                pr_author=$(gh pr view "$pr_number" --repo "$REPO" --json author --jq '.author.login // empty' 2>/dev/null || echo "")
                if [ -z "$pr_author" ] || [ "$pr_author" = "null" ]; then
                  echo "::warning::Could not fetch PR author for PR #$pr_number"
                fi
                echo "number=$pr_number" >> "$GITHUB_OUTPUT"
                echo "author=$pr_author" >> "$GITHUB_OUTPUT"
              }
              PR_NUMBER="$PR_NUMBER_PAYLOAD"
              if [ -n "$PR_NUMBER" ]; then
                echo "Found PR #$PR_NUMBER from workflow payload."
                emit_pr "$PR_NUMBER"
                exit 0
              fi
              HEAD_SHA="$EVENT_HEAD_SHA"
              echo "Payload empty. Searching for PR via Commits API..."
              PR_NUMBER=$(gh api repos/$REPO/commits/$HEAD_SHA/pulls -q '.[0].number' 2>/dev/null || true)
              if [ -n "$PR_NUMBER" ] && [ "$PR_NUMBER" != "null" ]; then
                 echo "Found PR #$PR_NUMBER using Commits API."
                 emit_pr "$PR_NUMBER"
                 exit 0
              fi
              echo "API lookup failed/empty. Scanning open PRs for matching head SHA..."
              PR_NUMBER=$(gh pr list --repo "$REPO" --state open --limit 100 --json number,headRefOid --jq ".[] | select(.headRefOid == \"$HEAD_SHA\") | .number" | head -n 1)
              if [ -n "$PR_NUMBER" ]; then
                 echo "Found PR #$PR_NUMBER by scanning open PRs."
                 emit_pr "$PR_NUMBER"
                 exit 0
              fi
              echo "::warning::No open PR found. This workflow run might not be attached to an open PR."
              exit 0

      call-ci-failure-bot:
        needs: find-pr
        if: ${{ needs.find-pr.outputs.pr_number != '' }}
        permissions:
          pull-requests: write
          actions: write
          contents: read
        uses: openwisp/openwisp-utils/.github/workflows/reusable-bot-ci-failure.yml@master
        with:
          pr_number: ${{ needs.find-pr.outputs.pr_number }}
          head_sha: ${{ github.event.workflow_run.head_sha }}
          head_repo: ${{ github.event.workflow_run.head_repository.full_name }}
          base_repo: ${{ github.repository }}
          run_id: ${{ github.event.workflow_run.id }}
          pr_author: ${{ needs.find-pr.outputs.pr_author }}
          actor: ${{ github.event.workflow_run.actor.login }}
        secrets:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          APP_ID: ${{ secrets.OPENWISP_BOT_APP_ID }}
          PRIVATE_KEY: ${{ secrets.OPENWISP_BOT_PRIVATE_KEY }}

Changelog Bot
~~~~~~~~~~~~~

This workflow automatically generates changelog entry suggestions for Pull
Requests using Google Gemini. It gets triggered when a PR with a title
prefixed with ``[feature]``, ``[fix]``, or ``[change]`` is approved by a
maintainer. It analyzes the PR's title, description, code changes, and
linked issues, then posts a properly formatted changelog entry as a
comment on the PR.

**Secrets**

- ``GEMINI_API_KEY`` (required): Google Gemini API key.
- ``OPENWISP_BOT_APP_ID`` (required): OpenWISP Bot GitHub App ID.
- ``OPENWISP_BOT_PRIVATE_KEY`` (required): OpenWISP Bot GitHub App private
  key.

**Usage Example**

To enable the changelog bot in any OpenWISP repository, create a workflow
file at ``.github/workflows/changelog-bot.yml``:

.. code-block:: yaml

    name: Changelog Bot
    on:
      pull_request_review:
        types: [submitted]
    jobs:
      changelog:
        uses: openwisp/openwisp-utils/.github/workflows/reusable-bot-changelog.yml@master
        secrets:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          OPENWISP_BOT_APP_ID: ${{ secrets.OPENWISP_BOT_APP_ID }}
          OPENWISP_BOT_PRIVATE_KEY: ${{ secrets.OPENWISP_BOT_PRIVATE_KEY }}
