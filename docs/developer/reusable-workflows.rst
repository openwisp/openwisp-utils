Re-usable GitHub Workflows
==========================

Replicate Commits to Version Branch
-----------------------------------

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
