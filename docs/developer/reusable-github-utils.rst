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
