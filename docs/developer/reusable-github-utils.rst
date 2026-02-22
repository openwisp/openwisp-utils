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

Auto-Assignment Bot
~~~~~~~~~~~~~~~~~~~

A collection of Python scripts that automate issue and PR management for
OpenWISP repositories. When a contributor opens a PR referencing an issue,
the issue is automatically assigned to the PR author. It also responds to
assignment requests with contributing guidelines, manages stale PRs
(warning after 7 days, marking stale after 14 days, closing after 60 days
of inactivity), and reassigns issues when stale PRs are reopened.

**Secrets**

- ``OPENWISP_BOT_APP_ID`` (required): OpenWISP Bot GitHub App ID.
- ``OPENWISP_BOT_PRIVATE_KEY`` (required): OpenWISP Bot GitHub App private
  key.

**Usage Example**

To enable the auto-assignment bot in any OpenWISP repository, copy the
workflow files from ``.github/workflows/`` (``bot-autoassign-issue.yml``,
``bot-autoassign-pr-issue-link.yml``, ``bot-autoassign-pr-reopen.yml``,
``bot-autoassign-stale-pr.yml``):

.. code-block:: yaml

    name: Issue Assignment Bot

    on:
      issue_comment:
        types: [created]

    permissions:
      contents: read
      issues: write

    jobs:
      respond-to-assign-request:
        runs-on: ubuntu-latest
        if: github.event.issue.pull_request == null
        steps:
          - name: Generate GitHub App token
            id: generate-token
            uses: actions/create-github-app-token@v1
            with:
              app-id: ${{ secrets.OPENWISP_BOT_APP_ID }}
              private-key: ${{ secrets.OPENWISP_BOT_PRIVATE_KEY }}

          - name: Checkout repository
            uses: actions/checkout@v4

          - name: Set up Python
            uses: actions/setup-python@v5
            with:
              python-version: "3.12"

          - name: Install dependencies
            run: pip install PyGithub

          - name: Run issue assignment bot
            env:
              GITHUB_TOKEN: ${{ steps.generate-token.outputs.token }}
              REPOSITORY: ${{ github.repository }}
              GITHUB_EVENT_NAME: ${{ github.event_name }}
            run: >
              python .github/actions/bot-autoassign/__main__.py
              issue_assignment "$GITHUB_EVENT_PATH"

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
