CI Failure Bot
===============

The CI Failure Bot is an automated system that analyzes failed CI builds and provides intelligent feedback to contributors. It uses AI-powered analysis to examine build logs, PR changes, and workflow context to generate specific, actionable guidance.

Features
--------

- **Automatic triggering**: Responds to CI build failures in pull requests
- **AI-powered analysis**: Uses Google Gemini to analyze failure logs and provide specific guidance
- **Intelligent responses**: Provides direct, actionable feedback based on actual failure context
- **Comment deduplication**: Updates existing comments instead of creating duplicates
- **Dependabot exclusion**: Automatically skips dependency update PRs
- **Fallback handling**: Provides basic guidance if AI analysis fails

How It Works
------------

When a CI build fails on a pull request, the bot:

1. **Collects context**: Gathers build logs, PR diff, and workflow configuration
2. **AI analysis**: Sends context to Gemini AI for intelligent analysis
3. **Posts feedback**: Creates or updates a comment with specific guidance
4. **Avoids spam**: Uses markers to prevent duplicate comments

The bot provides direct, no-nonsense feedback following OpenWISP's standards for code quality and contribution guidelines.

Configuration
-------------

Repository Secrets
~~~~~~~~~~~~~~~~~~

The following secrets must be configured in the repository:

- ``GEMINI_API_KEY``: Google Gemini API key for AI analysis

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Optional environment variables for customization:

- ``GEMINI_MODEL``: Gemini model to use (default: ``gemini-2.5-flash``)

Setup
-----

The CI failure bot is automatically enabled for repositories with the workflow file. No additional setup is required beyond configuring the API key.

Workflow Integration
~~~~~~~~~~~~~~~~~~~~

The bot integrates with existing CI workflows through the ``workflow_run`` trigger:

.. code-block:: yaml

   on:
     workflow_run:
       workflows: ["OpenWISP Utils CI Build"]
       types:
         - completed

This ensures the bot only runs after the main CI workflow completes with a failure.

Response Examples
-----------------

The bot provides different types of responses based on the failure:

**Code Quality Issues**::

   The build failed because of code formatting violations. Run `openwisp-qa-format` 
   to fix black, flake8, and isort issues before pushing. The project requires 
   clean code that passes all quality checks.

**Test Failures**::

   Tests are failing in tests/test_models.py at line 45. The error indicates a 
   missing migration for the new field you added. Run `python manage.py makemigrations` 
   and include the migration file in your commit.

**Low-Quality Contributions**::

   This PR appears to be spam or low-effort. Trivial README changes without 
   substantial improvements are not accepted. Please review the contribution 
   guidelines and submit meaningful changes.

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Bot not responding**
   - Verify ``GEMINI_API_KEY`` is configured correctly
   - Check that the workflow file exists and is properly formatted
   - Ensure the PR has an associated workflow run failure

**Incorrect analysis**
   - The bot learns from context - more specific error messages lead to better analysis
   - Complex failures may require manual review and contributor guidance

**Permission errors**
   - Verify the workflow has proper permissions for ``issues: write`` and ``pull-requests: write``

Limitations
-----------

- Requires Google Gemini API access
- Analysis quality depends on error log clarity
- May not handle very complex or unusual failure scenarios
- Skips dependabot PRs to avoid unnecessary noise

For more information about contributing to OpenWISP projects, see the `contribution guidelines <https://openwisp.io/docs/developer/contributing.html>`_.