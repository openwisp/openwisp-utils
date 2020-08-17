Changelog
=========

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
