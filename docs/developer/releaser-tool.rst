The Releaser tool
=================

.. include:: ../partials/developer-docs.rst

This tool automates the project release workflow, from change log
generation to creating a draft release on GitHub.

It supports two modes for version bumping, making it suitable for both
Python and non-Python projects.

.. contents:: **Table of Contents**:
    :depth: 2
    :local:

Configuration: ``releaser.toml``
--------------------------------

The script is controlled by a ``releaser.toml`` file in the project's
root.

**Required Keys:**

- ``repo`` (str): The GitHub repository in ``"owner/repo"`` format.
- ``changelog_path`` (str): Path to the changelog file (e.g.,
  ``"CHANGES.rst"``).

**Optional Key (Controls the Workflow):**

- ``version_path`` (str): Path to a Python file containing a ``VERSION``
  tuple. * **If present (Automatic Mode):** The script reads and
  automatically updates the version number in this file. * **If omitted
  (Manual Mode):** The script will pause and prompt you to update the
  version number manually. This is ideal for non-Python projects.

**Example for Automatic Bumping (Python Project):**

.. code-block:: toml

    repo = "openwisp/openwisp-utils"
    changelog_path = "CHANGES.rst"
    version_path = "openwisp_utils/__init__.py"

**Example for Manual Bumping (Non-Python Project):**

.. code-block:: toml

    repo = "openwisp/my-ansible-role"
    changelog_path = "CHANGELOG.md"
    # version_path is omitted

Prerequisites
-------------

Before running, ensure these are installed and available in your `PATH`:

- ``git-cliff``
- ``docstrfmt``
- ``pandoc``

You must also export a ``GITHUB_TOKEN`` environment variable with `repo`
scope.

Usage
-----

Run the script from your project's root directory:

.. code-block:: shell

    python -m openwisp_utils.releaser.release

The Release Workflow
--------------------

The script will guide you through the following automated steps:

1. **Checks prerequisites**.
2. **Generates changelog** from unreleased commits.
3. **Asks for confirmation** before proceeding.
4. **Handles version bumping** (either automatically or by pausing for
   manual input).
5. **Updates changelog file** with the new release section.
6. **Creates a ``release/<version>`` branch** and commits changes with the
   message ``<version> release``.
7. **Creates a pull request** on GitHub.
8. **Waits for the PR to be merged**.
9. **Creates and pushes a signed git tag**.
10. **Creates a draft release** on GitHub.
11. **Offers to port changelog** to the main branch if the release was
    made from a bugfix branch.
