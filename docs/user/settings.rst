Settings
========

.. include:: /partials/settings-note.rst

``OPENWISP_ADMIN_SITE_CLASS``
-----------------------------

**Default**: ``openwisp_utils.admin_theme.admin.OpenwispAdminSite``

If you need to use a customized admin site class, you can use this
setting.

``OPENWISP_ADMIN_SITE_TITLE``
-----------------------------

**Default**: ``OpenWISP Admin``

Title value used in the ``<title>`` HTML tag of the admin site.

``OPENWISP_ADMIN_SITE_HEADER``
------------------------------

**Default**: ``OpenWISP``

Heading text used in the main ``<h1>`` HTML tag (the logo) of the admin
site.

``OPENWISP_ADMIN_INDEX_TITLE``
------------------------------

**Default**: ``Network administration``

Title shown to users in the index page of the admin site.

.. _utils_admin_dashboard_enabled:

``OPENWISP_ADMIN_DASHBOARD_ENABLED``
------------------------------------

**Default**: ``True``

When ``True``, enables the :doc:`OpenWISP Dashboard
<../developer/dashboard>`. Upon login, the user will be greeted with the
dashboard instead of the default Django admin index page.

.. _openwisp_admin_theme_links:

``OPENWISP_ADMIN_THEME_LINKS``
------------------------------

**Default**: ``[]``

.. note::

    This setting requires :ref:`the admin_theme_settings context processor
    <utils_custom_admin_theme>` in order to work.

Allows to override the default CSS and favicon, as well as add extra
``<link>`` HTML elements if needed.

This setting overrides the default theme, you can reuse the default CSS or
replace it entirely.

The following example shows how to keep using the default CSS, supply an
additional CSS and replace the favicon.

Example usage:

.. code-block:: python

    OPENWISP_ADMIN_THEME_LINKS = [
        {
            "type": "text/css",
            "href": "/static/admin/css/openwisp.css",
            "rel": "stylesheet",
            "media": "all",
        },
        {
            "type": "text/css",
            "href": "/static/admin/css/custom-theme.css",
            "rel": "stylesheet",
            "media": "all",
        },
        {
            "type": "image/x-icon",
            "href": "/static/favicon.png",
            "rel": "icon",
        },
    ]

.. _openwisp_admin_theme_js:

``OPENWISP_ADMIN_THEME_JS``
---------------------------

**Default**: ``[]``

Allows to pass a list of strings representing URLs of custom JS files to
load.

Example usage:

.. code-block:: python

    OPENWISP_ADMIN_THEME_JS = [
        "/static/custom-admin-theme.js",
    ]

``OPENWISP_ADMIN_SHOW_USERLINKS_BLOCK``
---------------------------------------

**Default**: ``False``

When set to ``True``, enables Django user links on the admin site.

i.e. (USER NAME/ VIEW SITE / CHANGE PASSWORD / LOG OUT).

These links are already shown in the main navigation menu and for this
reason are hidden by default.

``OPENWISP_API_DOCS``
---------------------

**Default**: ``True``

Whether the OpenAPI documentation is enabled.

When enabled, you can view the available documentation using the Swagger
endpoint at ``/api/v1/docs/``.

You also need to add the following URL to your project ``urls.py``:

.. code-block:: python

    urlpatterns += [
        url(r"^api/v1/", include("openwisp_utils.api.urls")),
    ]

``OPENWISP_API_INFO``
---------------------

**Default**:

.. code-block:: python

    {
        "title": "OpenWISP API",
        "default_version": "v1",
        "description": "OpenWISP REST API",
    }

Define OpenAPI general information. NOTE: This setting requires
``OPENWISP_API_DOCS = True`` to take effect.

For more information about optional parameters check the `drf-yasg
documentation
<https://drf-yasg.readthedocs.io/en/stable/readme.html#quickstart>`_.

.. _openwisp_slow_test_threshold:

``OPENWISP_SLOW_TEST_THRESHOLD``
--------------------------------

**Default**: ``[0.3, 1]`` (seconds)

It can be used to change the thresholds used by
:ref:`TimeLoggingTestRunner <utils_time_logging_test_runner>` to detect
slow tests (0.3s by default) and highlight the slowest ones (1s by
default) among them.

.. _openwisp_staticfiles_versioned_exclude:

``OPENWISP_STATICFILES_VERSIONED_EXCLUDE``
------------------------------------------

**Default**: ``['leaflet/*/*.png']``

Allows to pass a list of **Unix shell-style wildcards** for files to be
excluded by :ref:`CompressStaticFilesStorage
<utils_compress_static_files_storage>`.

By default Leaflet PNGs have been excluded to avoid bugs like
`openwisp/ansible-openwisp2#232
<https://github.com/openwisp/ansible-openwisp2/issues/232>`_.

Example usage:

.. code-block:: python

    OPENWISP_STATICFILES_VERSIONED_EXCLUDE = [
        "*png",
    ]

.. _openwisp_html_email:

``OPENWISP_HTML_EMAIL``
-----------------------

======= ========
type    ``bool``
default ``True``
======= ========

If ``True``, an HTML themed version of the email can be sent using the
:ref:`send_email <utils_send_email>` function.

.. _openwisp_email_logo:

``OPENWISP_EMAIL_LOGO``
-----------------------

======= ==================================================================================================================================
type    ``str``
default `OpenWISP logo
        <https://raw.githubusercontent.com/openwisp/openwisp-utils/master/openwisp_utils/static/openwisp-utils/images/openwisp-logo.png>`_
======= ==================================================================================================================================

This setting allows to change the logo which is displayed in HTML version
of the email.

.. note::

    Provide a URL which points to the logo on your own web server. Ensure
    that the URL provided is publicly accessible from the internet.
    Otherwise, the logo may not be displayed in the email. Please also
    note that SVG images do not get processed by some email clients like
    Gmail so it is recommended to use PNG images.

.. _openwisp_celery_soft_time_limit:

``OPENWISP_CELERY_SOFT_TIME_LIMIT``
-----------------------------------

======= ===================
type    ``int``
default ``30`` (in seconds)
======= ===================

Sets the soft time limit for celery tasks using :ref:`OpenwispCeleryTask
<utils_openwispcelerytask>`.

.. _openwisp_celery_hard_time_limit:

``OPENWISP_CELERY_HARD_TIME_LIMIT``
-----------------------------------

======= ====================
type    ``int``
default ``120`` (in seconds)
======= ====================

Sets the hard time limit for celery tasks using :ref:`OpenwispCeleryTask
<utils_openwispcelerytask>`.

``OPENWISP_AUTOCOMPLETE_FILTER_VIEW``
-------------------------------------

======= ===========================================================
type    ``str``
default ``'openwisp_utils.admin_theme.views.AutocompleteJsonView'``
======= ===========================================================

Dotted path to the ``AutocompleteJsonView`` used by the
``openwisp_utils.admin_theme.filters.AutocompleteFilter``.
