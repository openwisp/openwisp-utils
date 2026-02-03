Changelog Bot
=============

.. include:: ../partials/developer-docs.rst

The Changelog Bot is a GitHub Action that automatically generates
changelog entry suggestions for Pull Requests. When triggered, it analyzes
the PR's title, description, code changes, and linked issues, then uses
Google Gemini to generate a properly formatted RestructuredText changelog
entry that will be picked up by the :doc:`releaser-tool`.

Purpose
-------

This bot solves several problems in the release process:

1. **Consistency**: Ensures all changelog entries follow the same format
2. **Automation**: Reduces manual work for maintainers
3. **Integration**: Works seamlessly with the existing releaser tool and
   ``git-cliff`` configuration
4. **Org-wide**: Can be used across all OpenWISP repositories from a
   single source

How It Works
------------

1. A maintainer approves a PR or comments ``@openwisp-bot changelog``
2. The bot fetches the PR details (title, description, diff, linked
   issues)
3. It sends this context to Google Gemini to generate a changelog entry
4. The entry is posted as a PR comment in RestructuredText format
5. The maintainer reviews and copies the entry into ``CHANGES.rst``
6. The releaser tool later includes this in the release notes

Changelog Entry Format
----------------------

The bot generates entries in RestructuredText format for ``CHANGES.rst``:

.. code-block:: restructuredtext

    Section Name
    ~~~~~~~~~~~~

    - Description of the change with `link to PR or issue
      <https://github.com/org/repo/pull/123>`_.

**Available sections:**

- ``Features`` - New functionality
- ``Bugfixes`` - Bug fixes
- ``Changes`` - Non-breaking changes, refactors
- ``Dependencies`` - Dependency updates

Setup for openwisp-utils
------------------------

The bot is already configured in ``openwisp-utils``. You just need to add
the API key secret:

1. Go to **Settings** > **Secrets and variables** > **Actions**
2. Add a new repository secret:

   - Name: ``GEMINI_API_KEY``
   - Value: Your Google Gemini API key

Setup for Other OpenWISP Repositories
-------------------------------------

To enable the changelog bot in any OpenWISP repository, create a workflow
file at ``.github/workflows/changelog-bot.yml``:

.. code-block:: yaml

    name: Changelog Bot

    on:
      # Trigger on PR comments containing the trigger phrase
      issue_comment:
        types: [created]

      # Trigger when a PR is approved
      pull_request_review:
        types: [submitted]

    jobs:
      changelog:
        uses: openwisp/openwisp-utils/.github/workflows/reusable-changelog-bot.yml@master
        with:
          trigger-phrase: "@openwisp-bot changelog"
        secrets:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}

Then add the ``GEMINI_API_KEY`` secret to the repository (or use an
organization-level secret for all repos).

Configuration Options
---------------------

The reusable workflow accepts the following inputs:

.. list-table::
    :header-rows: 1
    :widths: 20 15 15 50

    - - Input
      - Required
      - Default
      - Description
    - - ``llm-model``
      - No
      - ``gemini-2.0-flash``
      - Gemini model to use (e.g., ``gemini-2.0-flash``, ``gemini-1.5-pro``)
    - - ``trigger-phrase``
      - No
      - ``@openwisp-bot changelog``
      - Comment text that triggers the bot

**Secrets:**

- ``GEMINI_API_KEY`` - Required. Your Google Gemini API key.

Usage
-----

**Automatic trigger (on PR approval):**

When a maintainer approves a PR, the bot automatically generates a
changelog suggestion.

**Manual trigger (via comment):**

Any user with write access to the repository can trigger the bot by
commenting on a PR:

.. code-block:: text

    @openwisp-bot changelog

The bot will:

1. React to the comment with a 🚀 emoji
2. Analyze the PR
3. Post a comment with the suggested changelog entry

**Using the suggestion:**

1. Review the generated RestructuredText entry
2. Copy the entry into the appropriate section of ``CHANGES.rst``
3. Adjust if needed and commit

Example Output
--------------

Given a PR that adds a retry mechanism for Selenium tests, the bot might
generate:

.. code-block:: restructuredtext

    Features
    ~~~~~~~~

    - Added retry mechanism to ``SeleniumTestMixin`` to retry failed
      selenium tests, preventing CI failures from flaky tests.
      `#464 <https://github.com/openwisp/openwisp-utils/pull/464>`_.

This entry can then be copied directly into ``CHANGES.rst``.

Troubleshooting
---------------

**Bot doesn't respond to comments**

- Ensure the user has write access to the repository
- Check that the trigger phrase matches exactly
- Verify the ``GEMINI_API_KEY`` secret is set

**Generated entry is incorrect**

- The bot uses AI which may occasionally produce imperfect results
- Maintainers should review and edit the suggestion as needed
- You can re-trigger by commenting ``@openwisp-bot changelog`` again

**API rate limits**

- Gemini has rate limits; if exceeded, wait a few minutes
- Consider using organization-level API keys for higher limits

Security Considerations
-----------------------

- The bot only responds to users with write access
- API keys are stored as GitHub secrets (encrypted)
- The bot cannot modify code, only post comments
- PR diffs are truncated to prevent sending too much data to the LLM
