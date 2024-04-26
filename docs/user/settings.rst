Settings
--------

``OPENWISP_ADMIN_SITE_CLASS``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**default**: ``openwisp_utils.admin_theme.admin.OpenwispAdminSite``

If you need to use a customized admin site class, you can use this setting.

``OPENWISP_ADMIN_SITE_TITLE``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**default**: ``OpenWISP Admin``

Title value used in the ``<title>`` HTML tag of the admin site.

``OPENWISP_ADMIN_SITE_HEADER``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**default**: ``OpenWISP``

Heading text used in the main ``<h1>`` HTML tag (the logo) of the admin site.

``OPENWISP_ADMIN_INDEX_TITLE``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**default**: ``Network administration``

Title shown to users in the index page of the admin site.

``OPENWISP_ADMIN_DASHBOARD_ENABLED``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**default**: ``True``

When ``True``, enables the `OpenWISP Dashboard <#openwisp-dashboard>`_.
Upon login, the user will be greeted with the dashboard instead of the default
Django admin index page.

``OPENWISP_ADMIN_THEME_LINKS``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**default**: ``[]``

**Note**: this setting requires
`the admin_theme_settings context processor <#supplying-custom-css-and-js-for-the-admin-theme>`_
in order to work.

Allows to override the default CSS and favicon, as well as add extra
<link> HTML elements if needed.

This setting overrides the default theme, you can reuse the default CSS or replace it entirely.

The following example shows how to keep using the default CSS,
supply an additional CSS and replace the favicon.

Example usage:

.. code-block:: python

    OPENWISP_ADMIN_THEME_LINKS = [
        {'type': 'text/css', 'href': '/static/admin/css/openwisp.css', 'rel': 'stylesheet', 'media': 'all'},
        {'type': 'text/css', 'href': '/static/admin/css/custom-theme.css', 'rel': 'stylesheet', 'media': 'all'},
        {'type': 'image/x-icon', 'href': '/static/favicon.png', 'rel': 'icon'}
    ]

``OPENWISP_ADMIN_THEME_JS``
^^^^^^^^^^^^^^^^^^^^^^^^^^^

**default**: ``[]``

Allows to pass a list of strings representing URLs of custom JS files to load.

Example usage:

.. code-block:: python

    OPENWISP_ADMIN_THEME_JS = [
        '/static/custom-admin-theme.js',
    ]

``OPENWISP_ADMIN_SHOW_USERLINKS_BLOCK``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**default**: ``False``

When True, enables Django user links on the admin site.

i.e. (USER NAME/ VIEW SITE / CHANGE PASSWORD / LOG OUT).

These links are already shown in the main navigation menu and for this reason are hidden by default.

``OPENWISP_API_DOCS``
^^^^^^^^^^^^^^^^^^^^^

**default**: ``True``

Whether the OpenAPI documentation is enabled.

When enabled, you can view the available documentation using the
Swagger endpoint at ``/api/v1/docs/``.

You also need to add the following url to your project urls.py:

.. code-block:: python

    urlpatterns += [
        url(r'^api/v1/', include('openwisp_utils.api.urls')),
    ]

``OPENWISP_API_INFO``
^^^^^^^^^^^^^^^^^^^^^

**default**:

.. code-block:: python

    {
        'title': 'OpenWISP API',
        'default_version': 'v1',
        'description': 'OpenWISP REST API',
    }

Define OpenAPI general information.
NOTE: This setting requires ``OPENWISP_API_DOCS = True`` to take effect.

For more information about optional parameters check the
`drf-yasg documentation <https://drf-yasg.readthedocs.io/en/stable/readme.html#quickstart>`_.

``OPENWISP_SLOW_TEST_THRESHOLD``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**default**: ``[0.3, 1]`` (seconds)

It can be used to change the thresholds used by `TimeLoggingTestRunner <#openwisp_utilsteststimeloggingtestrunner>`_
to detect slow tests (0.3s by default) and highlight the slowest ones (1s by default) amongst them.

``OPENWISP_STATICFILES_VERSIONED_EXCLUDE``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**default**: ``['leaflet/*/*.png']``

Allows to pass a list of **Unix shell-style wildcards** for files to be excluded by `CompressStaticFilesStorage <#openwisp_utilsstorageCompressStaticFilesStorage>`_.

By default Leaflet PNGs have been excluded to avoid bugs like `openwisp/ansible-openwisp2#232 <https://github.com/openwisp/ansible-openwisp2/issues/232>`_.

Example usage:

.. code-block:: python

    OPENWISP_STATICFILES_VERSIONED_EXCLUDE = [
        '*png',
    ]

``OPENWISP_HTML_EMAIL``
^^^^^^^^^^^^^^^^^^^^^^^

+---------+----------+
| type    | ``bool`` |
+---------+----------+
| default | ``True`` |
+---------+----------+

If ``True``, an HTML themed version of the email can be sent using
the `send_email <#openwisp_utilsadmin_themeemailsend_email>`_ function.

``OPENWISP_EMAIL_TEMPLATE``
^^^^^^^^^^^^^^^^^^^^^^^^^^^

+---------+----------------------------------------+
| type    | ``str``                                |
+---------+----------------------------------------+
| default | ``openwisp_utils/email_template.html`` |
+---------+----------------------------------------+

This setting allows to change the django template used for sending emails with
the `send_email <#openwisp_utilsadmin_themeemailsend_email>`_ function.
It is recommended to extend the default email template as in the example below.

.. code-block:: django

    {% extends 'openwisp_utils/email_template.html' %}
    {% block styles %}
    {{ block.super }}
    <style>
      .background {
        height: 100%;
        background: linear-gradient(to bottom, #8ccbbe 50%, #3797a4 50%);
        background-repeat: no-repeat;
        background-attachment: fixed;
        padding: 50px;
      }

      .mail-header {
        background-color: #3797a4;
        color: white;
      }
    </style>
    {% endblock styles %}

Similarly, you can customize the HTML of the template by overriding the ``body`` block.
See `email_template.html <https://github.com/openwisp/openwisp-utils/blob/
master/openwisp_utils/admin_theme/templates/openwisp_utils/email_template.html>`_
for reference implementation.

``OPENWISP_EMAIL_LOGO``
^^^^^^^^^^^^^^^^^^^^^^^

+---------+-------------------------------------------------------------------------------------+
| type    | ``str``                                                                             |
+---------+-------------------------------------------------------------------------------------+
| default | `OpenWISP logo <https://raw.githubusercontent.com/openwisp/openwisp-utils/master/ \ |
|         | openwisp_utils/static/openwisp-utils/images/openwisp-logo.png>`_                    |
+---------+-------------------------------------------------------------------------------------+

This setting allows to change the logo which is displayed in HTML version of the email.

**Note**: Provide a URL which points to the logo on your own web server. Ensure that the URL provided is
publicly accessible from the internet. Otherwise, the logo may not be displayed in the email.
Please also note that SVG images do not get processed by some email clients
like Gmail so it is recommended to use PNG images.

``OPENWISP_CELERY_SOFT_TIME_LIMIT``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

+---------+---------------------+
| type    | ``int``             |
+---------+---------------------+
| default | ``30`` (in seconds) |
+---------+---------------------+

Sets the soft time limit for celery tasks using
`OpenwispCeleryTask <#openwisp_utilstasksopenwispcelerytask>`_.

``OPENWISP_CELERY_HARD_TIME_LIMIT``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

+---------+----------------------+
| type    | ``int``              |
+---------+----------------------+
| default | ``120`` (in seconds) |
+---------+----------------------+

Sets the hard time limit for celery tasks using
`OpenwispCeleryTask <#openwisp_utilstasksopenwispcelerytask>`_.

``OPENWISP_AUTOCOMPLETE_FILTER_VIEW``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+---------+-------------------------------------------------------------+
| type    | ``str``                                                     |
+---------+-------------------------------------------------------------+
| default | ``'openwisp_utils.admin_theme.views.AutocompleteJsonView'`` |
+---------+-------------------------------------------------------------+

Dotted path to the ``AutocompleteJsonView`` used by the
``openwisp_utils.admin_theme.filters.AutocompleteFilter``.
