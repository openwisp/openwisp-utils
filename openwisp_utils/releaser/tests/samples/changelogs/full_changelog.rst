Changelog
=========

[unreleased]
------------

Features
~~~~~~~~

- ValidatedModelSerializer: added exclude_validation, don't set m2m

  - Allow excluding fields from validation in ValidatedModelSerializer.
  - Handled exclusion of direct setting of m2m fields.

- Added retry mechanism to SeleniumTestMixin `#464
  <https://github.com/#REPO#/issues/464>`_

  Retry selenium tests if the tests fails on the first attempt. This
  prevents failng the CI build from flaky tests.

  Closes `#464 <https://github.com/#REPO#/issues/464>`_

- Generate CHANGES.rst automatically `#496
  <https://github.com/#REPO#/issues/496>`_

  Closes `#496 <https://github.com/#REPO#/issues/496>`_

Changes
~~~~~~~

Backward-incompatible changes
+++++++++++++++++++++++++++++

- Dropped support for OPENWISP_EMAIL_TEMPLATE setting `#482
  <https://github.com/#REPO#/issues/482>`_

  Updated docs to suggest overriding the template.

  Closes `#482 <https://github.com/#REPO#/issues/482>`_

Other changes
+++++++++++++

- Use docstrfmt for checking ReStructuredText files
- Rollback DRF to 3.15 (security)
- Switched to prettier for CSS/JS linting `#367
  <https://github.com/#REPO#/issues/367>`_

  Closes `#367 <https://github.com/#REPO#/issues/367>`_

Dependencies
++++++++++++

- Bumped ``djangorestframework<3.16.1``

  Updates the requirements on `djangorestframework
  <https://github.com/encode/django-rest-framework>`__ to permit the
  latest version. - `Release notes
  <https://github.com/encode/django-rest-framework/releases>`__ - `Commits
  <https://github.com/encode/django-rest-framework/compare/3.14.0...3.16.0>`__

- Bumped ``pytest-asyncio<0.27``

  Updates the requirements on `pytest-asyncio
  <https://github.com/pytest-dev/pytest-asyncio>`__ to permit the latest
  version. - `Release notes
  <https://github.com/pytest-dev/pytest-asyncio/releases>`__ - `Commits
  <https://github.com/pytest-dev/pytest-asyncio/compare/v0.24.0...v0.26.0>`__

- Bumped ``selenium<4.35``

  Updates the requirements on `selenium
  <https://github.com/SeleniumHQ/Selenium>`__ to permit the latest
  version. - `Release notes
  <https://github.com/SeleniumHQ/Selenium/releases>`__ - `Commits
  <https://github.com/SeleniumHQ/Selenium/compare/selenium-4.10.0...selenium-4.34.0>`__

- Bumped ``swapper~=1.4.0``

  Updates the requirements on `swapper
  <https://github.com/openwisp/django-swappable-models>`__ to ~=1.4.0. -
  `Release notes
  <https://github.com/openwisp/django-swappable-models/releases>`__ -
  `Changelog
  <https://github.com/openwisp/django-swappable-models/blob/master/CHANGES.rst>`__
  - `Commits
  <https://github.com/openwisp/django-swappable-models/compare/v1.3.0...v1.4.0>`__

- Updated QA dependencies

Bugfixes
~~~~~~~~

- Fixed padding of the email container

  - Removed margin-top on logo container

- Fixed the recipient string in email template
- Fixed the height of the logo in email template

  Bug: Setting both heights and width would require overriding the
  template when the logo is customized.

  Fix: Setting the height to auto let's the logo adapt to width. If
  further customizations are required, then the user will need to override
  the email template.
