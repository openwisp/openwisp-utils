Changelog
=========

Version 1.3.0 [2026-08-29]
--------------------------

Features
~~~~~~~~

- Implemented sub-filter functionality in Django admin `#700
  <https://github.com/openwisp/openwisp-utils/issues/700>`_

  Introduced ``SubFilterMixin`` to allow admin filters to be displayed and
  applied only when a parent filter has specific values. This enhances the
  admin interface by enabling hierarchical filtering.

  The filter rendering system has been updated to group parent filters
  with their sub-filters, displaying sub-filters vertically below their
  parents. Client-side JavaScript logic dynamically shows or hides
  sub-filters based on parent filter selections.

  Invalid sub-filter usage, such as providing a sub-filter value when its
  parent is inactive, will now raise ``IncorrectLookupParameters``.
  Misconfigured orphaned sub-filters will be logged as errors and not
  rendered.

- Add OpenWispPagination class with default values `#586
  <https://github.com/openwisp/openwisp-utils/issues/586>`_

  Introduces the ``OpenWispPagination`` class, inheriting from DRF's
  ``PageNumberPagination``. This class provides sensible default values
  for pagination across OpenWISP modules, configurable via settings.

  The default page size is set to 10 and the maximum page size to 100.
  These can be overridden by ``OPENWISP_API_DEFAULT_PAGE_SIZE`` and
  ``OPENWISP_API_MAX_PAGE_SIZE`` respectively. Views can also set a
  ``pagination_page_size`` attribute to override the default for specific
  endpoints.

- Added changelog entry bot `#523
  <https://github.com/openwisp/openwisp-utils/issues/523>`_
- Automate assigning/unassigning issues `#571
  <https://github.com/openwisp/openwisp-utils/issues/571>`_

  Added auto-assignment bot with issue assignment, management of stale PR,
  reassignment on PR reopen and shared helpers in utils.py.

- Added CI build failure bot `#524
  <https://github.com/openwisp/openwisp-utils/issues/524>`_

  When a CI workflow fails, the bot examines the failure logs and
  repository context with AI to offer specific guidance for fixing QA
  check issues, test failures and other common bugs.

- Added reusable backport workflow `#501
  <https://github.com/openwisp/openwisp-utils/issues/501>`_

  Automates cherry-picking fixes to stable branches via ``[backport X.Y]``
  in commit messages or ``/backport X.Y`` comments, with conflict
  notification.

- Standardized commit messages using commitizen `#110
  <https://github.com/openwisp/openwisp-utils/issues/110>`_

  Commitizen has been integrated in openwisp-utils to standardize how
  commit messages are written across the project. It introduces an
  interactive commit workflow that guides contributors to use the correct
  OpenWISP commit format, ensures commit titles are properly structured,
  and enforces the presence of an issue reference. The commit message
  footer is generated automatically using the provided issue number,
  improving consistency and making commits easier to review and track.

- Releaser: added support for non-python packages `#522
  <https://github.com/openwisp/openwisp-utils/issues/522>`_

Changes
~~~~~~~

Backward-incompatible changes
+++++++++++++++++++++++++++++

- Removed deprecated ``UUIDAdmin`` class `#328
  <https://github.com/openwisp/openwisp-utils/issues/328>`_

  The deprecated ``UUIDAdmin`` class has been removed. For equivalent
  functionality, use ``CopyableFieldsAdmin`` with ``copyable_fields =
  ('uuid',)``.

Other changes
+++++++++++++

- Included commit bodies in releaser changelog
- Allowed cascade deletions in ``ReadOnlyAdmin``

  ``ReadOnlyAdmin.has_delete_permission`` previously returned ``False``
  unconditionally, which blocked cascade deletions from parent models
  (like ``Organization``).

  Added ``openwisp_utils.admin.BlockDeleteAllowCascadeMixin`` to allow
  reusability of this logic in other OpenWISP modules.

- Excluded local python venv dirs from QA checks `#720
  <https://github.com/openwisp/openwisp-utils/issues/720>`_
- Made menu item registration idempotent `#641
  <https://github.com/openwisp/openwisp-utils/issues/641>`_

  Previously, calling ``register_menu_group`` or ``register_menu_subitem``
  twice with the same configuration at the same position would always
  raise an ``ImproperlyConfigured`` exception. This behavior prevented
  re-registration, even when the same application was re-initializing its
  menu items during testing.

  This change modifies these functions to check if the configuration being
  registered is identical to the one already present at that position. If
  the configurations match, the function now logs an informational message
  and skips the re-registration instead of raising an error. This makes
  the menu item registration process idempotent, improving testability and
  handling of repeated app initializations.

- Releaser: defined a generic package type to use as fallback

  The logic which detected OpenWrt packages has been generalized so that
  any file which doesn't fall under well defined categories like "python
  package", "npm package", "ansible role", etc., can fall under the
  "generic package" type, as long as a VERSION file is defined in the top
  level directory of the repository, the releaser tool will be able to
  deal with it, regardless of the tech stack used.

- Made changelog bot model configurable and quota-resilient

  The changelog bot kept failing with Gemini free-tier quota errors
  (``RequestsPerDayPerProjectPerModel``, 20/day) and marked the workflow
  as failed, while the CI failure bot stayed green because it swallows the
  same error. The changelog bot also had no way to switch models and could
  spend up to three requests per pull request.

  Forward ``GEMINI_MODEL`` through the action and reusable workflow so a
  single variable controls both bots, harden model resolution so an empty
  value falls back to the default, lower the generation retries from three
  to two, and exit cleanly on quota errors so the workflow no longer turns
  red on exhaustion.

  Also document the ``GEMINI_MODEL`` variable for both bots.

- SeleniumTestMixin now requires two successful retries after an initial
  failure
- Added default ``uuid`` method to ``CopyableFieldsAdmin`` `#328
  <https://github.com/openwisp/openwisp-utils/issues/328>`_

  ``CopyableFieldsAdmin`` now ships with a default ``uuid()`` method that
  returns ``obj.pk`` and has ``short_description`` set to ``'UUID'``. This
  allows subclasses to use ``copyable_fields = ('uuid',)`` without
  defining their own ``uuid`` method when their model uses a UUID primary
  key.

  The ``uuid`` field is not automatically added to ``copyable_fields``,
  that's still the developer's explicit decision.

- Releaser: removed chatGPT integration `#645
  <https://github.com/openwisp/openwisp-utils/issues/645>`_
- Releaser: automated branch selection in changelog porting step `#646
  <https://github.com/openwisp/openwisp-utils/issues/646>`_

Dependencies
++++++++++++

- Bumped ``black`` to 26.5.1 (``>=25.1,<26.6``)

  Updates the requirements on `black <https://github.com/psf/black>`__ to
  permit the latest version. - `Release notes
  <https://github.com/psf/black/releases>`__ - `Changelog
  <https://github.com/psf/black/blob/main/CHANGES.md>`__ - `Commits
  <https://github.com/psf/black/compare/25.1.0...26.5.1>`__

- Bumped ``celery`` to 5.6.1 (``~=5.6.1``)

  Updates the requirements on `celery
  <https://github.com/celery/celery>`__ to permit the latest version. -
  `Release notes <https://github.com/celery/celery/releases>`__ -
  `Changelog <https://github.com/celery/celery/blob/main/Changelog.rst>`__
  - `Commits <https://github.com/celery/celery/compare/v5.5.3...v5.6.1>`__

- Bumped ``djangorestframework`` to 3.17.1 (``~=3.17.1``)

  Updates the requirements on `djangorestframework
  <https://github.com/encode/django-rest-framework>`__ to permit the
  latest version. - `Release notes
  <https://github.com/encode/django-rest-framework/releases>`__ - `Commits
  <https://github.com/encode/django-rest-framework/compare/3.16.0...3.17.1>`__

- Bumped ``git-cliff`` to 2.13.1 (``~=2.13.1``)

  Updates the requirements on `git-cliff
  <https://github.com/orhun/git-cliff>`__ to permit the latest version. -
  `Release notes <https://github.com/orhun/git-cliff/releases>`__ -
  `Changelog
  <https://github.com/orhun/git-cliff/blob/main/CHANGELOG.md>`__ -
  `Commits
  <https://github.com/orhun/git-cliff/compare/v2.10.0...v2.13.1>`__

- Bumped ``isort`` to 8.0.1 (``>=6.0.1,<8.1.0``)

  Updates the requirements on `isort <https://github.com/PyCQA/isort>`__
  to permit the latest version. - `Release notes
  <https://github.com/PyCQA/isort/releases>`__ - `Changelog
  <https://github.com/PyCQA/isort/blob/main/CHANGELOG.md>`__ - `Commits
  <https://github.com/PyCQA/isort/compare/6.0.1...8.0.1>`__

- Bumped ``pytest-asyncio`` to 1.4.0 (``>=1.3.0,<1.5.0``)

  Updates the requirements on `pytest-asyncio
  <https://github.com/pytest-dev/pytest-asyncio>`__ to permit the latest
  version. - `Release notes
  <https://github.com/pytest-dev/pytest-asyncio/releases>`__ - `Commits
  <https://github.com/pytest-dev/pytest-asyncio/compare/v0.24.0...v1.4.0>`__

- Bumped ``selenium`` to 4.46.0 (``>=4.32,<4.47``)

  Updates the requirements on `selenium
  <https://github.com/SeleniumHQ/Selenium>`__ to permit the latest
  version. - `Release notes
  <https://github.com/SeleniumHQ/Selenium/releases>`__ - `Commits
  <https://github.com/SeleniumHQ/Selenium/compare/selenium-4.10.0...selenium-4.46.0>`__

- Bumped ``tblib`` to 3.2.2 (``~=3.2.2``)

  Updates the requirements on `tblib
  <https://github.com/ionelmc/python-tblib>`__ to permit the latest
  version. - `Release notes
  <https://github.com/ionelmc/python-tblib/releases>`__ - `Changelog
  <https://github.com/ionelmc/python-tblib/blob/master/CHANGELOG.rst>`__ -
  `Commits
  <https://github.com/ionelmc/python-tblib/compare/v3.1.0...v3.2.2>`__

- Bumped ``django-filter`` to 26.1 (``>=25.1,<27.0``)

  Updates the requirements on `django-filter
  <https://github.com/carltongibson/django-filter>`__ to permit the latest
  version. - `Release notes
  <https://github.com/carltongibson/django-filter/releases>`__ -
  `Changelog
  <https://github.com/carltongibson/django-filter/blob/main/CHANGES.rst>`__
  - `Commits
  <https://github.com/carltongibson/django-filter/compare/25.1...26.1>`__

- Bumped ``coverage`` to 7.15.2 (``>=7.10.0,<7.16.0``)

  Updates the requirements on `coverage
  <https://github.com/coveragepy/coveragepy>`__ to permit the latest
  version. - `Release notes
  <https://github.com/coveragepy/coveragepy/releases>`__ - `Changelog
  <https://github.com/coveragepy/coveragepy/blob/main/CHANGES.rst>`__ -
  `Commits
  <https://github.com/coveragepy/coveragepy/compare/7.10.0...7.15.2>`__

- Bumped ``docstrfmt`` to 2.2.0 (``>=2.0.0,<2.3.0``)

  Updates the requirements on `docstrfmt
  <https://github.com/LilSpazJoekp/docstrfmt>`__ to permit the latest
  version. - `Release notes
  <https://github.com/LilSpazJoekp/docstrfmt/releases>`__ - `Changelog
  <https://github.com/LilSpazJoekp/docstrfmt/blob/master/CHANGES.rst>`__ -
  `Commits
  <https://github.com/LilSpazJoekp/docstrfmt/compare/v2.0.0...v2.2.0>`__

- Bumped ``google-genai`` to 2.7.0 (``>=1.62.0,<3.0.0``)

  Updates the requirements on `google-genai
  <https://github.com/googleapis/python-genai>`__ to permit the latest
  version. - `Release notes
  <https://github.com/googleapis/python-genai/releases>`__ - `Changelog
  <https://github.com/googleapis/python-genai/blob/main/CHANGELOG.md>`__ -
  `Commits
  <https://github.com/googleapis/python-genai/compare/v1.62.0...v2.7.0>`__

- Bumped ``django-minify-compress-staticfiles`` to 1.1.1

  See Release Notes:
  https://github.com/openwisp/django-minify-compress-staticfiles/releases/tag/1.1.1

- Bumped ``pytest-django`` to 4.12.0 (``>=4.10,<4.13``)

  Updates the requirements on `pytest-django
  <https://github.com/pytest-dev/pytest-django>`__ to permit the latest
  version. - `Release notes
  <https://github.com/pytest-dev/pytest-django/releases>`__ - `Changelog
  <https://github.com/pytest-dev/pytest-django/blob/main/docs/changelog.rst>`__
  - `Commits
  <https://github.com/pytest-dev/pytest-django/compare/v4.10.0...v4.12.0>`__

Bugfixes
~~~~~~~~

- Reload DRF settings after configuring defaults

  Bug: ``ApiAppConfig.configure_rest_framework_defaults`` updated Django's
  ``settings.REST_FRAMEWORK``, but DRF's ``api_settings`` had already
  loaded its own copy of the configuration. As a result, changes made by
  apps initialized after ``rest_framework`` were not reflected in the
  settings actually used by DRF.

  Fix: Reload ``rest_framework.settings.api_settings`` after updating
  ``settings.REST_FRAMEWORK`` so DRF uses the latest configuration.

- Prevented capture decorators from polluting exceptions

  CaptureOutput previously tried injecting streams and retried any
  TypeError. A real failure in a no-argument decorated test retained the
  expected signature mismatch as exception context, obscuring the
  regression traceback.

  The decorator now selects the valid call signature before executing the
  test, while preserving support for explicit captured streams, variadic
  arguments, and stacked ``mock.patch`` decorators.

- Prevented FallbackMixin from generating spurious migrations `#1231
  <https://github.com/openwisp/openwisp-utils/issues/1231>`_
- Collect Firefox console logs via WebDriver BiDi `#696
  <https://github.com/openwisp/openwisp-utils/issues/696>`_

  Firefox >= 135 no longer loads the Manifest v2 console-capture
  extension, and Manifest v3 content scripts are not granted host
  permissions for temporarily installed add-ons, so the content script
  never runs. As a result ``get_browser_logs()`` returned ``undefined``
  (which translated to ``None`` in Python) instead of the captured logs on
  modern Firefox versions, which in turn broke CI builds.

  The extension was replaced with WebDriver BiDi: a console message
  handler records every console entry, including those emitted during page
  load, and the log buffer is reset on each navigation to preserve the
  previous per-page semantics.

  This fixes console capture for every OpenWISP module that relies on
  ``SeleniumTestMixin`` without changing its public API.

- Excluded ``node_modules`` dir and other hidden directories from the
  ReStructuredText QA check
- Fixed ``ValidatedModelSerializer`` validation of PUT/PATCH and
  relationships `#633
  <https://github.com/openwisp/openwisp-utils/issues/633>`_

  Updated ``ValidatedModelSerializer.validate()`` to:

  - Use ``copy()`` for existing instances to avoid mutating the original.
  - Skip reverse relations (``ForeignObjectRel``) during ``setattr``.
  - Skip nested relationships.
  - Convert Django ``ValidationError`` to DRF ``ValidationError`` so
    errors are properly serialized in API responses and picklable in the
    parallel test runner.

- Triggered changelog bot for backward incompatible changes

  Accept ``[change!]`` entries in the changelog bot trigger and validation
  so backward incompatible PRs receive generated changelog suggestions.

- Fixed double encoding of device model labels in dashboard `#651
  <https://github.com/openwisp/openwisp-utils/issues/651>`_

  Fixed the double-encoding issue in admin dashboard charts where device
  models with special characters (like &) generated malformed URLs.

- Fixed broken skipped Selenium tests in Django parallel runner `#619
  <https://github.com/openwisp/openwisp-utils/issues/619>`_
- Fixed gemini call
- Switched to django-minify-compress-staticfiles `#565
  <https://github.com/openwisp/openwisp-utils/issues/565>`_

  Replaced the unmaintained django-compress-staticfiles with the new
  django-minify-compress-staticfiles package for static file minification
  and compression.

- Releaser: perform ``git pull --tags`` before changelog generation

Version 1.2.2 [2026-01-28]
--------------------------

Bugfixes
~~~~~~~~

- Temporarily pinned drf-yasg to 1.21.11 `#565
  <https://github.com/openwisp/openwisp-utils/issues/565>`_
- Fixed releaser to only commit tracked files `#552
  <https://github.com/openwisp/openwisp-utils/issues/552>`_
- Releaser: Fixed insertion of backported bugfix entries in ReST changelog
  `#532 <https://github.com/openwisp/openwisp-utils/issues/532>`_

Version 1.2.1 [2025-12-19]
--------------------------

Bugfixes
~~~~~~~~

- Updated `system info to retrieve friendly OS identifiers
  <https://github.com/openwisp/openwisp-utils/issues/544>`_.

Version 1.2.0 [2025-10-23]
--------------------------

Features
~~~~~~~~

- Added `guided release tool
  <https://openwisp.io/docs/dev/utils/developer/releaser-tool.html>`_.
- Added retry mechanism to SeleniumTestMixin `#464
  <https://github.com/openwisp/openwisp-utils/issues/464>`_.
- Enhanced ``ValidatedModelSerializer``: introduced ``exclude_validation``
  and avoided setting many-to-many fields automatically.
- Added reusable `retry-command GitHub action
  <https://openwisp.io/docs/dev/utils/developer/reusable-github-utils.html#retry-command>`_.
- Made HTML template configurable in
  `openwisp_utils.admin_theme.email.send_email
  <https://openwisp.io/docs/dev/utils/developer/admin-theme.html#openwisp-utils-admin-theme-email-send-email>`_..

Changes
~~~~~~~

Backward-incompatible changes
+++++++++++++++++++++++++++++

- Dropped support for OPENWISP_EMAIL_TEMPLATE setting `#482
  <https://github.com/openwisp/openwisp-utils/issues/482>`_.

Other changes
+++++++++++++

- Moved theme color definitions in CSS to variables `#487
  <https://github.com/openwisp/openwisp-utils/issues/487>`_.
- Standardized code style by switching to Prettier for CSS and JavaScript
  linting `#367 <https://github.com/openwisp/openwisp-utils/issues/367>`_.
- Added line-length enforcement to prettier.
- Unified Prettier checks into a single command; now includes YAML,
  Markdown, and JSON files.
- Updated UI of HTML email templates.
- Switched selenium browser tests to Firefox.

Dependencies
++++++++++++

- Bumped ``django-model-utils>=4.5,<5.1"``.
- Bumped ``swapper~=1.4.0``.
- Bumped ``djangorestframework~=3.16.0``.
- Bumped ``celery~=5.5.3``.
- Bumped ``django-filter>=25.1,<26.0``.
- Bumped ``black>=25.1,<25.10``.
- Bumped ``flake8~=7.3.0``.
- Bumped ``isort~=6.0.1``.
- Bumped ``tblib~=3.1.0``.
- Bumped ``docstrfmt~=1.11.1``.
- Bumped ``selenium>=4.10,<4.36``.
- Added ``channels`` and ``channels-test`` extra requires `#388
  <https://github.com/openwisp/openwisp-utils/issues/388>`_.
- Removed ``coveralls`` in favor of ``coverage`` package.
- Added support for Django ``5.x``.
- Dropped support for Django ``3.2.0`` and Django ``4.1.0``.
- Added support for Python ``3.11``, ``3.12``, and ``3.13``.
- Dropped support for Python ``3.8``.

Version 1.1.2 [2025-06-18]
--------------------------

- [fix:ui] Avoided JS error when menu is not displayed.
- [chores:ui] Removed border from submit and search buttons.
- [chores:ui] Updated "Apply filters" button to use standard styling.
- [chores:ui] Improved metric collection consent UI.
- [tests] Minor fixes for flaky tests and 1.1 branch CI testing.

Version 1.1.1 [2024-11-20]
--------------------------

- [fix:ui] Added CSS for djang-allauth forms submit button.
- [fix:docs] Updated links to django documentation and other minor
  improvements to the docuemntation.

Version 1.1.0 [2024-08-16]
--------------------------

Features
~~~~~~~~

- Added quick link button to the dashboard chart and introduced option to
  filter queryset.
- Added the option to add dashboard templates after charts.
- Added `retryable_request
  <https://openwisp.io/docs/stable/utils/developer/other-utilities.html#openwisp-utils-utils-retryable-request>`_
  utility function for making HTTP requests with built-in retry logic.
- Added `AutocompleteFilter
  <https://openwisp.io/docs/stable/utils/developer/admin-utilities.html#openwisp-utils-admin-theme-filters-autocompletefilter>`_
  to load filter data asynchronously.
- Added `fallback fields
  <https://openwisp.io/docs/stable/utils/developer/custom-fields.html#openwisp-utils-fields-fallbackbooleanchoicefield>`_
  which returns the fallback value when the field is set to ``None``.
- Added `CopyableFieldsAdmin
  <https://openwisp.io/docs/stable/utils/developer/admin-utilities.html#openwisp-utils-admin-copyablefieldsadmin>`_
  which allows to set admin fields to be read-only and makes it easy to
  copy the fields contents.
- Added the `SeleniumTestMixin
  <https://openwisp.io/docs/stable/utils/developer/test-utilities.html#openwisp-utils-tests-assertnumqueriessubtestmixin>`_
  for streamlined Selenium testing.
- Added the `openwisp_utils.db.backends.spatialite
  <https://openwisp.io/docs/stable/utils/developer/admin-utilities.html#openwisp-utils-admin-copyablefieldsadmin>`_
  database backend to implement a workaround for handling `issue with
  sqlite 3.36 and spatialite 5
  <https://code.djangoproject.com/ticket/32935>`_.
- Added a page to display installed OpenWISP modules and system
  information.
- Added an optional feature for `collecting usage metrics
  <https://openwisp.io/docs/stable/utils/user/metric-collection.html>`_,
  utilizing `Clean Insights <https://cleaninsights.org/>`_.

Changes
~~~~~~~

- Allowed passing extra arguments to the Django ``send_email`` function,
  providing more flexibility in email handling.
- Replaced the ReStructuredText check with ``docstrfmt``, improving
  documentation formatting and validation.

**Dependencies**:

- Bumped ``django-model-utils~=4.3.1``
- Bumped ``djangorestframework>=3.14,<3.15.2``
- Bumped ``django-filter~=23.2``
- Bumped ``drf-yasg~=1.21.7``
- Bumped ``celery~=5.3.0``
- Bumped ``black~=23.12.1``
- Bumped ``flake8~=7.1.0``
- Bumped ``isort~=5.13.2``
- Bumped ``coveralls~=4.0.1``
- Bumped ``selenium>=4.10,<4.24``
- Added ``django-admin-autocomplete-filter~=0.7.1``,
  ``urllib3>=2.0.0,<3.0.0``, ``tblib~=3.0.0``, ``selenium>=4.10,<4.24``,
  and ``docstrfmt~=1.8.0``.
- Added support for Django ``4.1.x`` and ``4.2.x``
- Added support for Python ``3.10``
- Dropped support for Python ``3.7``
- Dropped support for Django ``3.0.x`` and ``3.1.x``

Bugfixes
~~~~~~~~

- Fixed the alert icon URL in the ``HelpTextStackedInline`` template

Version 1.0.4 [2022-10-07]
--------------------------

Bugfixes
~~~~~~~~

- Fixed **importlib-metadata** dependency, pinned it to ``<5.0``. The
  newer versions of **importlib-metadata** breaks openwisp-utils on
  **Python 3.7**.

Version 1.0.3 [2022-08-03]
--------------------------

Bugfixes
~~~~~~~~

- Fixed **django-fitler** dependency, pinned it to ``~=21.1``. Earlier, it
  was installing the latest version of django-filter.

Version 1.0.2 [2022-07-01]
--------------------------

Bugfixes
~~~~~~~~

- Fixed empty charts showing annotations from the previous chart
- Fixed dashboard template ``extra_config`` getting over-written when
  multiple dashboard templates are used
- Fixed `empty dashboard charts not displaying total as "0"
  <https://github.com/openwisp/openwisp-utils/issues/301>`_

Version 1.0.1 [2022-04-07]
--------------------------

- Fixed ``ImportError`` in click dependency of black (updated black
  dependency to ``black~=22.3.0``)
- Fixed target link of pie charts which use group by queries

Version 1.0.0 [2022-02-18]
--------------------------

Features
~~~~~~~~

- Added `customizable navigation menu
  <https://github.com/openwisp/openwisp-utils#main-navigation-menu>`_
- Added `horizontal filters
  <https://github.com/openwisp/openwisp-utils#admin-filters>`_
- Added `customizable admin dashboard
  <https://github.com/openwisp/openwisp-utils#openwisp-dashboard>`_
- Added `send_email function
  <https://github.com/openwisp/openwisp-utils#openwisp_utilsadmin_themeemailsend_email>`_
- Added `CompressStaticFilesStorage
  <https://github.com/openwisp/openwisp-utils#openwisp_utilsstoragecompressstaticfilesstorage>`_
  - a static storage backend for Django that also compresses static files
- Added `AssertNumQueriesSubTestMixin
  <https://github.com/openwisp/openwisp-utils#openwisp_utilstestsassertnumqueriessubtestmixin>`_
- Added `HelpTextStackedInline admin class
  <https://github.com/openwisp/openwisp-utils#openwisp_utilsadminhelptextstackedinline>`_
- Added `OpenwispCeleryTask
  <https://github.com/openwisp/openwisp-utils#openwisp-utils-tasks-openwispcelerytask>`_
  - a custom celery task class
- Added support for linting CSS and JS in `openwisp-qa-check
  <https://github.com/openwisp/openwisp-utils#openwisp-qa-check>`_
- Added support for formatting CSS and JS in `openwisp-qa-format
  <https://github.com/openwisp/openwisp-utils#openwisp-qa-format>`_
- Added `git pre-push hook
  <https://github.com/openwisp/openwisp-utils/issues/161>`_

Changes
~~~~~~~

- `Updated OpenWISP's admin theme
  <https://medium.com/@niteshsinha1707/new-navigation-menu-and-ui-ux-improvements-project-report-a94c37514b7d>`__

**Dependencies**:

- Bumped ``django-model-utils~=4.2.0``
- Bumped ``black<=21.10b0``
- Bumped ``djangorestframework~=3.13.0``
- Added ``swapper~=1.3.0``, ``django-compress-staticfiles~=1.0.1b`` and
  ``celery~=5.2.3``
- Added support for Django ``3.2.x`` and ``4.0.x``
- Added support for Python ``3.9``

Bugfixes
~~~~~~~~

- Fixed `checkcommit` failing for `trailing period (.) after closing
  keyword <https://github.com/openwisp/openwisp-utils/issues/187>`_

Version 0.7.5 [2021-06-01]
--------------------------

- [fix] Added workaround for minification of browsable API view.
  Django-pipeline strips spaces from pre-formatted text on minifying HTML
  which destroys the representation of data on browsable API views. Added
  a workaround to restore presentation to original form using CSS.

Version 0.7.4 [2021-04-08]
--------------------------

- [fix] Fixed commit check for co-authored commits

Version 0.7.3 [2021-01-12]
--------------------------

- [change] Bind coveralls to 3.0.0

Version 0.7.2 [2020-12-11]
--------------------------

- [fix] Fixed menu height on long pages
- [change] Minor improvement to UI colors to improve readability

Version 0.7.1 [2020-11-18]
--------------------------

- [fix] Fixed bug in``openwisp_utils.admin.UUIDAdmin`` which caused the
  removal of all the ``readonly_fields`` from the admin add page, now only
  the ``uuid`` field is removed
- [change] Changed commit check to allow commit messages from `Dependabot
  <https://dependabot.com/>`_

Version 0.7.0 [2020-11-13]
--------------------------

Features
~~~~~~~~

- [qa] Added a `ReStructuredText syntax check (checkrst)
  <https://github.com/openwisp/openwisp-utils#checkrst>`_ to
  ``openwisp-qa-check``, which allows to ensure ``README.rst`` and other
  top level rst files do not contain syntax errors
- [utils] Added `register_menu_items
  <https://github.com/openwisp/openwisp-utils#openwisp-utils-utils-register-menu-items>`_
  to easily register menu items
- [tests] Added test utilities to capture output (e.g.: to make assertions
  on it): `capture_stdout
  <https://github.com/openwisp/openwisp-utils#openwisp-utils-tests-capture-stdout>`_,
  `capture_stderr
  <https://github.com/openwisp/openwisp-utils#openwisp_utilstestscapture_stderr>`_,
  `capture_any_output
  <https://github.com/openwisp/openwisp-utils#openwisp_utilstestscapture_any_output>`_

Changes
~~~~~~~

- [utils] Removed deprecated openwisp-utils-qa-checks

Bugfixes
~~~~~~~~

- [admin] Hide menu options for unauthenticated users
- [admin] Fixed menu buttons being clicked on some sections of page when
  not visible

Version 0.6.3 [2020-09-02]
--------------------------

- [deps] Updated django-filter range: >=2.2.0<2.4.0

Version 0.6.2 [2020-08-29]
--------------------------

- [fix] Fixed commit message check when close/fix keyword is missing
- [change] Changed QA commit check prefix hint to mention conventional
  commit prefixes

Version 0.6.1 [2020-08-17]
--------------------------

- [fix] Commit check run only on Pull Request & workbench
- [deps] Added support for django 3.1
- [ux/admin-theme] Force z-index on main menu to stay on top

Version 0.6.0 [2020-08-14]
--------------------------

Features
~~~~~~~~

- [admin] ``TestReadOnlyAdmin``: added support for exclude attribute

Changes
~~~~~~~

- [change] Changed QA checks to use isort~=5.0 instead of isort<=4.3;
  **this will cause changes to the way the code is formatted**
- Always execute ``commitcheck`` when run locally (on travis it will be
  run only in pull requests)

Bugfixes
~~~~~~~~

- [admin] Fixed a bug which caused some menu items to be shown also if the
  user did not have permission to view or edit them
- [qa] Fixed a regression which caused ``commitcheck`` to not be run on
  travis pull requests
- [tests] Fixed ``SITE_ID`` in test project settings

Version 0.5.1 [2020-06-29]
--------------------------

- [feature] Added ``TimeLoggingTestRunner`` to detect slow tests
- [fix] Admin-theme: ensure menu is above other CSS elements
- [fix] Removed ``/tests`` directory from python package

Version 0.5.0 [2020-06-02]
--------------------------

- [fix] Fix crash when pending migrations check fails
- [add] default_or_test function
- [add] Added deep_merge_dicts function
- [add] formatter: black<=19.10b0
- [add] OPENWISP_API_INFO setting
- [add][api] Require authentication for API docs if DEBUG is False
- [add][api] Implement ScopedRateThrottle by default
- [add][api] Introduced api.ApiAppConfig
- [add][rest] optional swagger API endpoints
- [add][rest] django-filter
- [docs] Re-ordered, added information and improved existing docs
- [update] Added support for flake8 flake8<=3.9
- [change] Renamed test_api to api for consistency
- [change] Rename openwisp-utils-qa-checks to openwisp-qa-check
- [change][api] Renamed /api/v1/swagger/ to /api/v1/docs/
- [improvement] Moved to importlib for Dependency loader & staticfiles for
  importing files
- [improvement] Added "Related to #<issue>" for commit-check
- [enchancement] Added strict mode to run-qa-checks

Version 0.4.5 [2020-04-07]
--------------------------

- [admin-theme] Minor CSS improvements for login-form
- [tests] Added ``catch_signal`` test utility
- [qa] Added ``coveralls`` (and hence coverage) to
  ``extra_requires['qa']``
- [qa] Added merge cases to cases to skip in commit check
- [qa] Added ``--force-checkcommit`` argument to force message commit
  check

Version 0.4.4 [2020-02-28]
--------------------------

- [theme] Made it easier to customize theme
  (``OPENWISP_ADMIN_THEME_LINKS``,``OPENWISP_ADMIN_THEME_JS``, and
  ``openwisp_utils.admin_theme.context_processor.admin_theme_settings``)

Version 0.4.3 [2020-02-26]
--------------------------

- [utils] Added optional ``receive_url_baseurl`` and
  ``receive_url_urlconf`` to ``ReceiveUrlAdmin``
- [menu] Fixed JS error in popup pages (which have no header)
- [utils] ``KeyField`` now allows overrding ``default`` and ``validators``

Version 0.4.2 [2020-01-25]
--------------------------

- Removed unwanted "Running" messages before some tests
- Added exception in checkcommit for pattern "^[A-Za-z0-9.]* release$'"

Version 0.4.1 [2020-01-20]
--------------------------

- Added utilities commonly used in other OpenWISP modules: ``UUIDAdmin``,
  ``KeyField``, ``ReceiveUrlAdmin``, ``get_random_key``
- Fixed a minor issue regarding a new line ``\n`` not being formatted
  properly in ``openwisp-utils-qa-check``

Version 0.4.0 [2020-01-13]
--------------------------

- Dropped support for python 2.7
- Added support for Django 3.0

Version 0.3.2 [2020-01-09]
--------------------------

- [change] Simplified implementation and usage of
  ``OPENWISP_ADMIN_SITE_CLASS``

Version 0.3.1 [2020-01-07]
--------------------------

- [feature] Added configurable ``AdminSite`` class and
  ``OPENWISP_ADMIN_SITE_CLASS``
- [theme] Adapted theme to django 2.2
- [qa] openwisp-utils-qa-checks now runs all checks before failing
- [qa] Added support for multiple migration name check in
  openwisp-utils-qa-checks
- [qa] Added pending migrations check (``runcheckpendingmigrations``) to
  openwisp-utils-qa-checks

Version 0.3.0 [2019-12-10]
--------------------------

- Added ``ReadOnlyAdmin``
- Added ``AlwaysHasChangedMixin``
- Added ``UUIDModel``
- Moved multitenancy features to `openwisp-users
  <https://github.com/openwisp/openwisp-users>`_
- [qa] Added ``checkendline``, ``checkmigrations``, ``checkcommit``, later
  integrated in ``openwisp-utils-qa-checks`` (corrected)
- Added navigation menu
- Added configurable settings for admin headings

Version 0.2.2 [2018-12-02]
--------------------------

- `#20 <https://github.com/openwisp/openwisp-utils/issues/20>`_: [qa]
  Added ``checkcommit`` QA check (thanks to `@ppabcd
  <https://github.com/ppabcd>`_)

Version 0.2.1 [2018-11-04]
--------------------------

- `dc977d2 <https://github.com/openwisp/openwisp-utils/commit/dc977d2>`_:
  [multitenancy] Avoid failure if org field not present
- `#13 <https://github.com/openwisp/openwisp-utils/pull/13>`_: [DRF] Added
  ``BaseSerializer``
- `#16 <https://github.com/openwisp/openwisp-utils/pull/16>`_: [qa] Added
  migration filename check
- `babbd74 <https://github.com/openwisp/openwisp-utils/commit/babbd74>`_:
  [multitenancy] Added ``MultitenantAdminMixin.multitenant_parent``
- `6d45df5 <https://github.com/openwisp/openwisp-utils/commit/6d45df5>`_:
  [qa] Pin down ``flake8`` and ``isort`` in ``extra_requires['qa']``

Version 0.2.0 [2018-02-06]
--------------------------

- `#10 <https://github.com/openwisp/openwisp-utils/pull/10>`_: [qa] add
  django 2.0 compatibility
- `d742d4 <https://github.com/openwisp/openwisp-utils/commit/d742d4>`_:
  [version] Improved get_version to follow PEP440

Version 0.1.2 [2017-07-10]
--------------------------

- [admin_theme] Added ``submit_line.html`` template

Version 0.1.1 [2017-06-28]
--------------------------

- renamed ``MultitenantObjectFilter`` to ``MultitenantRelatedOrgFilter``
- made *openwisp-users* optional

Version 0.1.0 [2017-06-28]
--------------------------

- added ``admin_theme``
- added ``MultitenantAdminMixin`` and ``TestMultitenantAdminMixin``
- added ``MultitenantOrgFilter`` and ``MultitenantObjectFilter``
- added ``TimeStampedEditableModel`` and ``TimeReadonlyAdminMixin``
- added ``DependencyLoader`` and ``DependencyFinder``
