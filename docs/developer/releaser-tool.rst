The Releaser Tool
=================

.. include:: ../partials/developer-docs.rst

This interactive command-line tool streamlines the entire project release
workflow, from generating a change log to creating a draft release on
GitHub. It is designed to be resilient, allowing you to recover from
common failures like network errors without starting over.

Prerequisites
-------------

**1. Installation**
~~~~~~~~~~~~~~~~~~~

Install the releaser and all its Python dependencies from the root of the
``openwisp-utils`` repository:

.. code-block:: shell

    pip install .[releaser]

**2. GitHub Personal Access Token**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The tool requires a GitHub Fine-grained Personal Access Token to create
pull requests, tags, and releases on your behalf.

1. Navigate to **Settings** > **Developer settings** > **Personal access
   tokens** > **Fine-grained tokens**.
2. Click **Generate new token**.
3. Give it a descriptive name (e.g., "OpenWISP Releaser") and set an
   expiration date.
4. Under **Repository access**, choose either **All repositories** or
   select the specific repositories you want to manage.
5. Under **Permissions**, click on **Add permissions**.
6. Grant the following permissions:

   - **Metadata**: Read-only
   - **Pull requests**: Read & write

7. Generate the token and export it as an environment variable:

.. code-block:: shell

    export OW_GITHUB_TOKEN="github_pat_YourTokenGoesHere"

.. image:: https://raw.githubusercontent.com/openwisp/openwisp-utils/media/docs/releaser/github-access-token.png
    :alt: Screenshot showing the required repository permissions for a new fine-grained GitHub Personal Access Token.

**3. OpenAI API Token (Optional)**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The tool can use GPT-4o to generate a human-readable summary of your
change log. If you wish to use this feature, export your OpenAI API key:

.. code-block:: shell

    export OPENAI_CHATGPT_TOKEN="sk-YourOpenAITokenGoesHere"

Usage
-----

Navigate to the root directory of the project you want to release and run
the following command:

.. code-block:: shell

    python -m openwisp_utils.releaser

The Interactive Workflow
------------------------

The tool will guide you through each step. Here are the key interactions:

**1. Version Confirmation** The tool will detect the current version and
suggest the next one. You can either accept the suggestion or enter a
different version manually.

.. image:: https://raw.githubusercontent.com/openwisp/openwisp-utils/media/docs/releaser/version-confirmation.png
    :alt: Screenshot showing the tool suggesting a new version number and asking for user confirmation.

**2. Change Log Generation & Review** A changelog is generated from your
recent commits. If an OpenAI token is configured, the tool will offer to
generate a more readable summary (this is disabled by default). You will
then be shown the final changelog block and asked to accept it before the
files are modified.

**3. Resilient Error Handling** If any network operation fails (e.g.,
creating a pull request), the tool won't crash. Instead, it will prompt
you to **Retry**, **Skip** the step (with manual instructions), or
**Abort**.

.. image:: https://raw.githubusercontent.com/openwisp/openwisp-utils/media/docs/releaser/error-handling.png
    :alt: Screenshot of the interactive prompt after a network error, showing Retry, Skip, and Abort options.

Summary of Automated Steps
--------------------------

Once you confirm the change log, the tool automates the rest of the
process:

1. Updates the version number in your project's ``__init__.py``.
2. Writes the new release notes to your ``CHANGES.rst`` or ``CHANGES.md``
   file.
3. Creates a ``release/<version>`` branch and commits the changes.
4. Pushes the new branch to GitHub.
5. Creates a pull request and waits for you to merge it.
6. Once merged, it creates and pushes a signed git tag.
7. Finally, it creates a draft release on GitHub with the changelog notes.
8. If releasing a bugfix, it offers to port the changelog to the ``main``
   or ``master`` branch.
