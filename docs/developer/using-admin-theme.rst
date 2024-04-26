Using the ``admin_theme``
-------------------------

.. include:: /partials/developers-docs-warning.rst

**The admin theme requires Django >= 2.2.**.

Add ``openwisp_utils.admin_theme`` to ``INSTALLED_APPS`` in ``settings.py``:

.. code-block:: python

    INSTALLED_APPS = [
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',

        'openwisp_utils.admin_theme',    # <----- add this
        # add when using autocomplete filter
        'admin_auto_filters',    # <----- add this

        'django.contrib.sites',
        # admin
        'django.contrib.admin',
    ]

Using ``DependencyLoader`` and ``DependencyFinder``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add the list of all packages extended to ``EXTENDED_APPS`` in ``settings.py``.

For example, if you've extended ``django_x509``:

.. code-block:: python

    EXTENDED_APPS = ['django_x509']

``DependencyFinder``
~~~~~~~~~~~~~~~~~~~~

This is a static finder which looks for static files in the ``static``
directory of the apps listed in ``settings.EXTENDED_APPS``.

Add ``openwisp_utils.staticfiles.DependencyFinder`` to ``STATICFILES_FINDERS``
in ``settings.py``.

.. code-block:: python

    STATICFILES_FINDERS = [
        'django.contrib.staticfiles.finders.FileSystemFinder',
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
        'openwisp_utils.staticfiles.DependencyFinder',    # <----- add this
    ]

``DependencyLoader``
~~~~~~~~~~~~~~~~~~~~

This is a template loader which looks for templates in the ``templates``
directory of the apps listed in ``settings.EXTENDED_APPS``.

Add ``openwisp_utils.loaders.DependencyLoader`` to
template ``loaders`` in ``settings.py`` as shown below.

.. code-block:: python

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'OPTIONS': {
                'loaders': [
                    # ... other loaders ...
                    'openwisp_utils.loaders.DependencyLoader',    # <----- add this
                ],
                'context_processors': [
                    # ... omitted ...
                ],
            },
        },
    ]

Supplying custom CSS and JS for the admin theme
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add ``openwisp_utils.admin_theme.context_processor.admin_theme_settings`` to
template ``context_processors`` in ``settings.py`` as shown below.
This will allow to set `OPENWISP_ADMIN_THEME_LINKS <#openwisp_admin_theme_links>`_
and `OPENWISP_ADMIN_THEME_JS <#openwisp_admin_theme_js>`__ settings
to provide CSS and JS files to customise admin theme.

.. code-block:: python

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'OPTIONS': {
                'loaders': [
                    # ... omitted ...
                ],
                'context_processors': [
                    # ... other context processors ...
                    'openwisp_utils.admin_theme.context_processor.admin_theme_settings'    # <----- add this
                ],
            },
        },
    ]

.. note::
    You will have to deploy these static files on your own.

    In order to make django able to find and load these files
    you may want to use the ``STATICFILES_DIR`` setting in ``settings.py``.

    You can learn more in the `Django documentation <https://docs.djangoproject.com/en/3.0/ref/settings/#std:setting-STATICFILES_DIRS>`_.

Extend admin theme programmatically
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``openwisp_utils.admin_theme.theme.register_theme_link``
""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Allows adding items to `OPENWISP_ADMIN_THEME_LINKS <#openwisp_admin_theme_links>`__.

This function is meant to be used by third party apps or OpenWISP modules which
aim to extend the core look and feel of the OpenWISP theme (eg: add new menu icons).

**Syntax:**

.. code-block:: python

    register_theme_link(links)

+--------------------+--------------------------------------------------------------+
| **Parameter**      | **Description**                                              |
+--------------------+--------------------------------------------------------------+
| ``links``          | (``list``) List of *link* items to be added to               |
|                    | `OPENWISP_ADMIN_THEME_LINKS <#openwisp_admin_theme_links>`__ |
+--------------------+--------------------------------------------------------------+

``openwisp_utils.admin_theme.theme.unregister_theme_link``
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Allows removing items from `OPENWISP_ADMIN_THEME_LINKS <#openwisp_admin_theme_links>`__.

This function is meant to be used by third party apps or OpenWISP modules which
aim additional functionalities to UI of OpenWISP (eg: adding a support chatbot).

**Syntax:**

.. code-block:: python

    unregister_theme_link(links)

+--------------------+--------------------------------------------------------------+
| **Parameter**      | **Description**                                              |
+--------------------+--------------------------------------------------------------+
| ``links``          | (``list``) List of *link* items to be removed from           |
|                    | `OPENWISP_ADMIN_THEME_LINKS <#openwisp_admin_theme_links>`__ |
+--------------------+--------------------------------------------------------------+

``openwisp_utils.admin_theme.theme.register_theme_js``
""""""""""""""""""""""""""""""""""""""""""""""""""""""

Allows adding items to `OPENWISP_ADMIN_THEME_JS <#openwisp_admin_theme_JS>`__.

**Syntax:**

.. code-block:: python

    register_theme_js(js)

+--------------------+---------------------------------------------------------------+
| **Parameter**      | **Description**                                               |
+--------------------+---------------------------------------------------------------+
| ``js``             | (``list``) List of relative path of *js* files to be added to |
|                    | `OPENWISP_ADMIN_THEME_JS <#openwisp_admin_theme_js>`__        |
+--------------------+---------------------------------------------------------------+

``openwisp_utils.admin_theme.theme.unregister_theme_js``
""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Allows removing items from `OPENWISP_ADMIN_THEME_JS <#openwisp_admin_theme_JS>`__.

**Syntax:**

.. code-block:: python

    unregister_theme_js(js)

+--------------------+--------------------------------------------------------------------+
| **Parameter**      | **Description**                                                    |
+--------------------+--------------------------------------------------------------------+
| ``js``             | (``list``) List of relative path of *js* files to be removed from  |
|                    | `OPENWISP_ADMIN_THEME_JS <#openwisp_admin_theme_js>`__             |
+--------------------+--------------------------------------------------------------------+
