Changelog
=========

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
