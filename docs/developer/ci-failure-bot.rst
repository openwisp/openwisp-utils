CI Failure Bot
==============

This GitHub workflow automatically analyzes failed CI builds and provides intelligent feedback to contributors using AI-powered analysis.

The bot examines build logs, PR changes, and workflow context to generate specific, actionable guidance that helps contributors fix issues quickly.

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
             pip install requests>=2.31.0 PyGithub>=2.0.0 google-generativeai>=0.3.0

         - name: Run CI Failure Bot
           env:
             GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
             GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
             WORKFLOW_RUN_ID: ${{ github.event.workflow_run.id }}
             REPOSITORY: ${{ github.repository }}
             PR_NUMBER: ${{ github.event.workflow_run.pull_requests[0].number || '' }}
           run: python .github/scripts/ci_failure_bot.py

Configuration
-------------

Repository Secrets
~~~~~~~~~~~~~~~~~~~

The following secrets must be configured in your repository:

- ``GEMINI_API_KEY``: Google Gemini API key for AI analysis

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Optional environment variables for customization:

- ``GEMINI_MODEL``: Gemini model to use (default: ``gemini-2.5-flash``)

Features
--------

- **Automatic triggering**: Responds to CI build failures in pull requests
- **AI-powered analysis**: Uses Google Gemini to analyze failure logs and provide specific guidance  
- **Intelligent responses**: Provides direct, actionable feedback based on actual failure context
- **Comment deduplication**: Updates existing comments instead of creating duplicates
- **Dependabot exclusion**: Automatically skips dependency update PRs
- **Fallback handling**: Provides basic guidance if AI analysis fails

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

Note
----

If the Gemini API is unavailable or the analysis fails, the bot will provide a fallback response with basic troubleshooting guidance. The workflow will not fail silently - any errors in the bot execution will be visible in the GitHub Actions logs.

Implementation Details
----------------------

Architecture
~~~~~~~~~~~~

The CI failure bot consists of two main components:

1. **GitHub Actions Workflow** (``.github/workflows/ci-failure-bot.yml``)
2. **Python Analysis Script** (``.github/scripts/ci_failure_bot.py``)

The workflow uses the ``workflow_run`` trigger to respond to CI failures, ensuring proper access to workflow run metadata and logs with correct PR association.

Testing
-------

The test suite (``test_ci_failure_bot.py``) provides comprehensive coverage:

**Test Categories**:

- Initialization and configuration validation
- Build log retrieval with various scenarios
- PR diff handling and truncation
- Gemini API integration and error handling
- Comment posting and deduplication
- Full workflow execution

**Mocking Strategy**:

- External APIs (GitHub, Gemini) are fully mocked
- Environment variables are patched for isolation
- Network requests are intercepted to avoid external dependencies

Running Tests
~~~~~~~~~~~~~

.. code-block:: bash

   # Run specific CI bot tests
   python manage.py test openwisp_utils.tests.test_ci_failure_bot

   # Run with coverage
   coverage run --source='.' manage.py test openwisp_utils.tests.test_ci_failure_bot
   coverage report

Configuration Options
---------------------

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

- ``GITHUB_TOKEN``: GitHub API access (automatically provided by Actions)
- ``GEMINI_API_KEY``: Google Gemini API key (repository secret)
- ``WORKFLOW_RUN_ID``: Workflow run identifier (automatically provided)
- ``REPOSITORY``: Repository name (automatically provided)
- ``PR_NUMBER``: Pull request number (automatically provided)
- ``GEMINI_MODEL``: Gemini model name (optional, defaults to ``gemini-2.5-flash``)

Permissions
~~~~~~~~~~~

The workflow requires these GitHub permissions:

.. code-block:: yaml

   permissions:
     issues: write
     pull-requests: write
     contents: read

Deployment
----------

Adding to New Repositories
~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Copy workflow file to ``.github/workflows/ci-failure-bot.yml``
2. Copy script to ``.github/scripts/ci_failure_bot.py``
3. Configure ``GEMINI_API_KEY`` in repository secrets
4. Update workflow name in trigger to match target CI workflow

Customization
~~~~~~~~~~~~~

**Prompt Customization**:
Modify the Gemini prompt in ``analyze_with_gemini()`` to adjust:

- Response tone and style
- Project-specific guidance
- Error categorization logic

**Trigger Customization**:
Adjust the workflow trigger to target different CI workflows or conditions.

Troubleshooting
---------------

Common Development Issues
~~~~~~~~~~~~~~~~~~~~~~~~~

**Import Errors in Tests**:
The test file adds the scripts directory to Python path:

.. code-block:: python

   scripts_path = os.path.join(os.path.dirname(__file__), '../../.github/scripts')
   sys.path.insert(0, scripts_path)

**API Rate Limits**:
The bot implements request timeouts and error handling for API limits.

**Token Limits**:
Build logs and PR diffs are truncated to stay within Gemini token limits.

Debugging
~~~~~~~~~

Enable debug output by adding print statements or using the workflow logs:

.. code-block:: bash

   # View workflow run logs
   gh run view <run-id> --log

   # Check specific job logs
   gh run view <run-id> --log --job="ci-failure-bot"

Future Enhancements
-------------------

Potential improvements:

- **Multi-language support**: Extend beyond Python projects
- **Custom rules**: Repository-specific failure analysis rules
- **Integration metrics**: Track bot effectiveness and accuracy
- **Advanced AI**: Use function calling for more structured responses

Contributing
------------

When contributing to the CI failure bot:

1. **Add tests**: All new functionality must include comprehensive tests
2. **Update documentation**: Keep both user and developer docs current
3. **Follow patterns**: Maintain consistency with existing OpenWISP code style
4. **Test thoroughly**: Verify on demo repositories before submitting

For more information, see the main `OpenWISP contribution guidelines <https://openwisp.io/docs/developer/contributing.html>`_.