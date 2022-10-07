Changelog
=========

Version 1.1.0 [unreleased]
--------------------------

WIP.

Version 1.0.4 [2022-10-07]
--------------------------

Bugfixes
~~~~~~~~

- Fixed **importlib-metadata** dependency, pinned it to ``<5.0``.
  The newer versions of **importlib-metadata** breaks openwisp-utils
  on **Python 3.7**.

Version 1.0.3 [2022-08-03]
--------------------------

Bugfixes
~~~~~~~~

- Fixed **django-fitler** dependency, pinned it to ``~=21.1``.
  Earlier, it was installing the latest version of django-filter.

Version 1.0.2 [2022-07-01]
--------------------------

Bugfixes
~~~~~~~~

- Fixed empty charts showing annotations from
  the previous chart
- Fixed dashboard template ``extra_config`` getting
  over-written when multiple dashboard templates
  are used
- Fixed `empty dashboard charts not displaying total as "0"
  <https://github.com/openwisp/openwisp-utils/issues/301>`_

Version 1.0.1 [2022-04-07]
--------------------------

- Fixed ``ImportError`` in click dependency of black
  (updated black dependency to ``black~=22.3.0``)
- Fixed target link of pie charts which use group by queries

Version 1.0.0 [2022-02-18]
--------------------------

Features
~~~~~~~~

- Added `customizable navigation menu <https://github.com/openwisp/openwisp-utils#main-navigation-menu>`_
- Added `horizontal filters <https://github.com/openwisp/openwisp-utils#admin-filters>`_
- Added `customizable admin dashboard <https://github.com/openwisp/openwisp-utils#openwisp-dashboard>`_
- Added `send_email function <https://github.com/openwisp/openwisp-utils#openwisp_utilsadmin_themeemailsend_email>`_
- Added `CompressStaticFilesStorage <https://github.com/openwisp/openwisp-utils#openwisp_utilsstoragecompressstaticfilesstorage>`_ -
  a static storage backend for Django that also compresses static files
- Added `AssertNumQueriesSubTestMixin <https://github.com/openwisp/openwisp-utils#openwisp_utilstestsassertnumqueriessubtestmixin>`_
- Added `HelpTextStackedInline admin class <https://github.com/openwisp/openwisp-utils#openwisp_utilsadminhelptextstackedinline>`_
- Added `OpenwispCeleryTask <https://github.com/openwisp/openwisp-utils#openwisp-utils-tasks-openwispcelerytask>`_ - a custom celery task class
- Added support for linting CSS and JS in `openwisp-qa-check <https://github.com/openwisp/openwisp-utils#openwisp-qa-check>`_
- Added support for formatting CSS and JS in `openwisp-qa-format <https://github.com/openwisp/openwisp-utils#openwisp-qa-format>`_
- Added `git pre-push hook <https://github.com/openwisp/openwisp-utils/issues/161>`_

Changes
~~~~~~~

- `Updated OpenWISP's admin theme <https://medium.com/@niteshsinha1707/new-navigation-menu-and-ui-ux-improvements-project-report-a94c37514b7d>`__

**Dependencies**:

- Bumped ``django-model-utils~=4.2.0``
- Bumped ``black<=21.10b0``
- Bumped ``djangorestframework~=3.13.0``
- Added ``swapper~=1.3.0``, ``django-compress-staticfiles~=1.0.1b`` and ``celery~=5.2.3``
- Added support for Django ``3.2.x`` and ``4.0.x``
- Added support for Python ``3.9``

Bugfixes
~~~~~~~~

- Fixed `checkcommit` failing for `trailing period (.) after closing keyword <https://github.com/openwisp/openwisp-utils/issues/187>`_

Version 0.7.5 [2021-06-01]
--------------------------

- [fix] Added workaround for minification of browsable API view.
  Django-pipeline strips spaces from pre-formatted text on minifying HTML
  which destroys the representation of data on browsable API views.
  Added a workaround to restore presentation to original form using CSS.

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

- [fix] Fixed bug in``openwisp_utils.admin.UUIDAdmin`` which caused the removal of all
  the ``readonly_fields`` from the admin add page, now only the ``uuid`` field is removed
- [change] Changed commit check to allow commit messages from `Dependabot <https://dependabot.com/>`_

Version 0.7.0 [2020-11-13]
--------------------------

Features
~~~~~~~~

- [qa] Added a `ReStructuredText syntax check (checkrst) <https://github.com/openwisp/openwisp-utils#checkrst>`_
  to ``openwisp-qa-check``, which allows to ensure ``README.rst`` and other top level rst files
  do not contain syntax errors
- [utils] Added `register_menu_items <https://github.com/openwisp/openwisp-utils#openwisp-utils-utils-register-menu-items>`_
  to easily register menu items
- [tests] Added test utilities to capture output (eg: to make assertions on it):
  `capture_stdout <https://github.com/openwisp/openwisp-utils#openwisp-utils-tests-capture-stdout>`_,
  `capture_stderr <https://github.com/openwisp/openwisp-utils#openwisp_utilstestscapture_stderr>`_,
  `capture_any_output <https://github.com/openwisp/openwisp-utils#openwisp_utilstestscapture_any_output>`_

Changes
~~~~~~~

- [utils] Removed deprecated openwisp-utils-qa-checks

Bugfixes
~~~~~~~~

- [admin] Hide menu options for unauthenticated users
- [admin] Fixed menu buttons being clicked on some sections of page when not visible

Version 0.6.3 [2020-09-02]
--------------------------

- [deps] Updated django-filter range: >=2.2.0<2.4.0

Version 0.6.2 [2020-08-29]
--------------------------

- [fix] Fixed commit message check when close/fix keyword is missing
- [change] Changed QA commit check prefix hint to mention conventional commit prefixes

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
~~~~~~~~

- [change] Changed QA checks to use isort~=5.0 instead of isort<=4.3;
  **this will cause changes to the way the code is formatted**
- Always execute ``commitcheck`` when run locally
  (on travis it will be run only in pull requests)

Bugfixes
~~~~~~~~

- [admin] Fixed a bug which caused some menu items to be shown also if the
  user did not have permission to view or edit them
- [qa] Fixed a regression which caused ``commitcheck`` to not be run on travis pull requests
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
- [improvement] Moved to importlib for Dependency loader & staticfiles for importing files
- [improvement] Added "Related to #<issue>" for commit-check
- [enchancement] Added strict mode to run-qa-checks

Version 0.4.5 [2020-04-07]
--------------------------

- [admin-theme] Minor CSS improvements for login-form
- [tests] Added ``catch_signal`` test utility
- [qa] Added ``coveralls`` (and hence coverage) to ``extra_requires['qa']``
- [qa] Added merge cases to cases to skip in commit check
- [qa] Added ``--force-checkcommit`` argument to force message commit check

Version 0.4.4 [2020-02-28]
--------------------------

- [theme] Made it easier to customize theme
  (``OPENWISP_ADMIN_THEME_LINKS``,``OPENWISP_ADMIN_THEME_JS``, and
  ``openwisp_utils.admin_theme.context_processor.admin_theme_settings``)

Version 0.4.3 [2020-02-26]
--------------------------

- [utils] Added optional ``receive_url_baseurl`` and ``receive_url_urlconf`` to ``ReceiveUrlAdmin``
- [menu] Fixed JS error in popup pages (which have no header)
- [utils] ``KeyField`` now allows overrding ``default`` and ``validators``

Version 0.4.2 [2020-01-25]
--------------------------

- Removed unwanted "Running" messages before some tests
- Added exception in checkcommit for pattern "^[A-Za-z0-9.]* release$'"

Version 0.4.1 [2020-01-20]
--------------------------

- Added utilities commonly used in other OpenWISP modules:
  ``UUIDAdmin``, ``KeyField``, ``ReceiveUrlAdmin``, ``get_random_key``
- Fixed a minor issue regarding a new line ``\n`` not being formatted properly
  in ``openwisp-utils-qa-check``

Version 0.4.0 [2020-01-13]
--------------------------

- Dropped support for python 2.7
- Added support for Django 3.0

Version 0.3.2 [2020-01-09]
--------------------------

- [change] Simplified implementation and usage of ``OPENWISP_ADMIN_SITE_CLASS``

Version 0.3.1 [2020-01-07]
--------------------------

- [feature] Added configurable ``AdminSite`` class and ``OPENWISP_ADMIN_SITE_CLASS``
- [theme] Adapted theme to django 2.2
- [qa] openwisp-utils-qa-checks now runs all checks before failing
- [qa] Added support for multiple migration name check in openwisp-utils-qa-checks
- [qa] Added pending migrations check (``runcheckpendingmigrations``) to openwisp-utils-qa-checks

Version 0.3.0 [2019-12-10]
--------------------------

- Added ``ReadOnlyAdmin``
- Added ``AlwaysHasChangedMixin``
- Added ``UUIDModel``
- Moved multitenancy features to
  `openwisp-users <https://github.com/openwisp/openwisp-users>`_
- [qa] Added ``checkendline``, ``checkmigrations``, ``checkcommit``,
  later integrated in ``openwisp-utils-qa-checks`` (corrected)
- Added navigation menu
- Added configurable settings for admin headings

Version 0.2.2 [2018-12-02]
--------------------------

- `#20 <https://github.com/openwisp/openwisp-utils/issues/20>`_:
  [qa] Added ``checkcommit`` QA check (thanks to `@ppabcd <https://github.com/ppabcd>`_)

Version 0.2.1 [2018-11-04]
--------------------------

- `dc977d2 <https://github.com/openwisp/openwisp-utils/commit/dc977d2>`_:
  [multitenancy] Avoid failure if org field not present
- `#13 <https://github.com/openwisp/openwisp-utils/pull/13>`_:
  [DRF] Added ``BaseSerializer``
- `#16 <https://github.com/openwisp/openwisp-utils/pull/16>`_:
  [qa] Added migration filename check
- `babbd74 <https://github.com/openwisp/openwisp-utils/commit/babbd74>`_:
  [multitenancy] Added ``MultitenantAdminMixin.multitenant_parent``
- `6d45df5 <https://github.com/openwisp/openwisp-utils/commit/6d45df5>`_:
  [qa] Pin down ``flake8`` and ``isort`` in ``extra_requires['qa']``

Version 0.2.0 [2018-02-06]
--------------------------

- `#10 <https://github.com/openwisp/openwisp-utils/pull/10>`_:
  [qa] add django 2.0 compatibility
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
