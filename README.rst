openwisp-utils
==============

.. image:: https://travis-ci.org/openwisp/openwisp-utils.svg?branch=master
    :target: https://travis-ci.org/openwisp/openwisp-utils

.. image:: https://coveralls.io/repos/github/openwisp/openwisp-utils/badge.svg
    :target: https://coveralls.io/github/openwisp/openwisp-utils

.. image:: https://requires.io/github/openwisp/openwisp-utils/requirements.svg?branch=master
    :target: https://requires.io/github/openwisp/openwisp-utils/requirements/?branch=master
    :alt: Requirements Status

.. image:: https://badge.fury.io/py/openwisp-utils.svg
    :target: http://badge.fury.io/py/openwisp-utils

------------

Python and Django utilities shared between different OpenWISP modules.

The admin theme requires Django >= 2.2.

------------

.. contents:: **Table of Contents**:
   :backlinks: none
   :depth: 3

------------

Current features
----------------

* **Customized admin theme** for OpenWISP modules
* **Configurable navigation menu**
* **TimeStamped** models and mixins which add self-updating ``created`` and ``modified`` fields.
* **UUIDModel**: base model with a UUID4 primary key
* **KeyField**: base field for a unique string key
* **UUIDAdmin**: base admin which defines a uuid field from a UUID primary key
* **ReceiveUrlAdmin**: base admin which defines a receive_url field
* **get_random_key**: generates an object key of 32 characters
* **DependencyLoader**: template loader which looks in the templates dir of all django-apps
  listed in ``EXTENDED_APPS``
* **DependencyFinder**: finds static files of django-apps listed in ``EXTENDED_APPS``
* **Test utilities**: it contains utilities used for automated testing across various modules
* **QA**: logic and utilities to perform quality assurance checks across different modules

Project goals
-------------

* Minimize code duplication among OpenWISP modules

Install stable version from pypi
--------------------------------

Install from pypi:

.. code-block:: shell

    pip install openwisp-utils
    # install optional dependencies for tests (flake8, black and isort)
    pip install openwisp-utils[qa]

Install development version
---------------------------

Install tarball:

.. code-block:: shell

    pip install https://github.com/openwisp/openwisp-utils/tarball/master

Alternatively you can install via pip using git:

.. code-block:: shell

    pip install -e git+git://github.com/openwisp/openwisp-utils#egg=openwisp-utils

If you want to contribute, install your cloned fork:

.. code-block:: shell

    git clone git@github.com:<your_fork>/openwisp-utils.git
    cd openwisp-utils
    python setup.py develop

Using the utilities in OpenWISP modules
---------------------------------------

``INSTALLED_APPS`` in ``settings.py`` should look like the following if you want to use the OpenWISP admin-theme:

.. code-block:: python

    INSTALLED_APPS = [
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        # customized admin theme
        'openwisp_utils.admin_theme',
        'django.contrib.sites',
        # admin
        'django.contrib.admin',
    ]

Using the ``admin_theme``
^^^^^^^^^^^^^^^^^^^^^^^^^

* Add ``openwisp_utils.admin_theme`` to ``INSTALLED_APPS`` in ``settings.py``.


Using ``DependencyLoader`` and ``DependencyFinder``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add the list of all packages extended to ``EXTENDED_APPS`` in ``settings.py``.
If you've extended ``django_netjsonconfig`` and ``django_x509``:

.. code-block:: python

    EXTENDED_APPS = ['django_netjsonconfig', 'django_x509']

``DependencyFinder``
~~~~~~~~~~~~~~~~~~~~

Add ``openwisp_utils.staticfiles.DependencyFinder`` to ``STATICFILES_FINDERS``
in ``settings.py``.

.. code-block:: python

    STATICFILES_FINDERS = [
        'django.contrib.staticfiles.finders.FileSystemFinder',
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
        'openwisp_utils.staticfiles.DependencyFinder',
    ]

``DependencyLoader``
~~~~~~~~~~~~~~~~~~~~

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
                    'openwisp_utils.loaders.DependencyLoader',
                ],
                'context_processors': [
                    # ... omitted ...
                ],
            },
        },
    ]

Main navigation menu
~~~~~~~~~~~~~~~~~~~~

Add ``openwisp_utils.admin_theme.context_processor.menu_items`` to
template ``context_processors`` in ``settings.py`` as shown below.

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
                    'openwisp_utils.admin_theme.context_processor.menu_items'
                ],
            },
        },
    ]

Using Custom CSS and JS for Admin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add ``openwisp_utils.admin_theme.context_processor.admin_theme_settings`` to
template ``context_processors`` in ``settings.py`` as shown below.
This will allow to set ``OPENWISP_ADMIN_THEME_LINKS`` and ``OPENWISP_ADMIN_THEME_JS`` settings
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
                    'openwisp_utils.admin_theme.context_processor.admin_theme_settings'
                ],
            },
        },
    ]

.. note::
    You will have to deploy these static files on your own.

    In order to make django able to find and load these files
    you may want to use the ``STATICFILES_DIR`` setting in ``settings.py``.

    You can learn more in the `Django documentation <https://docs.djangoproject.com/en/3.0/ref/settings/#std:setting-STATICFILES_DIRS>`_.


Settings
^^^^^^^^

``OPENWISP_ADMIN_SITE_CLASS``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**default**: ``openwisp_utils.admin_theme.admin.OpenwispAdminSite``

If you need to use a customized admin site class, you can use this setting.

``OPENWISP_ADMIN_SITE_TITLE``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**default**: ``OpenWISP Admin``

Title value used in the ``<title>`` HTML tag of the admin site.

``OPENWISP_ADMIN_SITE_HEADER``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**default**: ``OpenWISP``

Heading text used in the main ``<h1>`` HTML tag (the logo) of the admin site.

``OPENWISP_ADMIN_INDEX_TITLE``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**default**: ``Network administration``

Title shown to users in the index page of the admin site.

``OPENWISP_ADMIN_MENU_ITEMS``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**default**: ``[]``

Allows to pass a custom list of menu items to display in the admin menu.

If passed, overrides the default menu which is built by different openwisp modules.

The list should not include "home", "change password" and "log out", because those
are automatically added and cannot be removed.

Example usage:

.. code-block:: python

    OPENWISP_ADMIN_MENU_ITEMS = [
        {'model': 'config.Device'},
        {'model': 'config.Template'},
        {'model': 'openwisp_users.User'},
        {
            'model': 'openwisp_radius.Accounting',
            'label': 'Radius sessions'  # custom label
        }
    ]

``OPENWISP_ADMIN_THEME_LINKS``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**default**: ``[]``

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**default**: ``[]``

Allows to pass a list of strings representing URLs of custom JS files to load.

Example usage:

.. code-block:: python

    OPENWISP_ADMIN_THEME_JS = [
        '/static/custom-admin-theme.js',
    ]

``OPENWISP_REST_SWAGGER``
~~~~~~~~~~~~~~~~~~~~~~~~~

**default**: ``True``

Enable or disable Swagger API documentation endpoint.

When enabled, you can view the available documentation using the
Swagger endpoint at ``/api/v1/swagger/``.

You also need to add the following url to your project urls.py:

.. code-block:: python

    urlpatterns += [
        url(r'^api/v1/', include('openwisp_utils.api.urls')),
    ]

``OPENWISP_API_INFO``
~~~~~~~~~~~~~~~~~~~~~

**default**:

.. code-block:: python

    {
        'title': 'OpenWISP API',
        'default_version': 'v1',
        'description': 'OpenWISP REST API',
    }

Define OpenAPI general information.
NOTE: This setting requires ``OPENWISP_REST_SWAGGER = True`` to take effect.

For more information about optional parameters check the
`drf-yasg documentation <https://drf-yasg.readthedocs.io/en/stable/readme.html#quickstart>`_
.

Admin mixins
^^^^^^^^^^^^

* **TimeReadonlyAdminMixin**: Admin mixin which adds two readonly fields
  ``created`` and ``modified``.
  This is an admin mixin for models inheriting ``TimeStampedEditableModel``
  which adds the fields ``created`` and ``modified`` to the database.

Test utilities
^^^^^^^^^^^^^^

This package contains some utilities that are used in the automated builds
of different OpenWISP modules.

``catch_signal``
~~~~~~~~~~~~~~~~

This method can be used to mock a signal call inorder to easily verify
that the signal has been called.

Usage example as a context-manager:

.. code-block:: python

    from openwisp_utils.tests import catch_signal

    with catch_signal(openwisp_signal) as handler:
        model_instance.trigger_signal()
        handler.assert_called_once_with(
            arg1='value1',
            arg2='value2',
            sender=ModelName,
            signal=openwisp_signal,
        )

Quality Assurance checks
^^^^^^^^^^^^^^^^^^^^^^^^

This package contains some common QA checks that are used in the
automated builds of different OpenWISP modules.

``openwisp-qa-format``
~~~~~~~~~~~~~~~~~~~~~~

Shell script to automatically format Python code. It runs ``isort`` and ``black``.

``openwisp-qa-check``
~~~~~~~~~~~~~~~~~~~~~

Shell script to run the following quality assurance checks:

* `checkmigrations <#checkmigrations>`_
* `checkcommit <#checkcommit>`_
* `checkendline <#checkendline>`_
* `checkpendingmigrations <#checkpendingmigrations>`_
* ``flake8`` - Python code linter
* ``isort`` - Sorts python imports alphabetically, and seperated into sections
* ``black`` - Formats python code using a common standard

If a check requires a flag, it can be passed forward in the same way.

Usage example::

    openwisp-qa-check --migration-path <path> --message <commit-message>

Any unneeded checks can be skipped by passing ``--skip-<check-name>``

Usage example::

    openwisp-qa-check --skip-isort

You can do multiple ``checkmigrations`` by passing the arguments with space-delimited string.

For example, this multiple ``checkmigrations``::

    checkmigrations --migrations-to-ignore 3 \
		    --migration-path ./openwisp_users/migrations/ || exit 1

    checkmigrations --migrations-to-ignore 2 \
		    --migration-path ./tests/testapp/migrations/ || exit 1

Can be changed with::

    openwisp-qa-check --migrations-to-ignore "3 2" \
            --migration-path "./openwisp_users/migrations/ ./tests/testapp/migrations/"

``checkmigrations``
~~~~~~~~~~~~~~~~~~~

Ensures the latest migrations created have a human readable name.

We want to avoid having many migrations named like ``0003_auto_20150410_3242.py``.

This way we can reconstruct the evolution of our database schemas faster, with
less efforts and hence less costs.

Usage example::

    checkmigrations --migration-path ./django_freeradius/migrations/

``checkcommit``
~~~~~~~~~~~~~~~

Ensures the last commit message follows our `commit message style guidelines
<http://openwisp.io/docs/developer/contributing.html#commit-message-style-guidelines>`_.

We want to keep the commit log readable, consistent and easy to scan in order
to make it easy to analyze the history of our modules, which is also a very
important activity when performing maintenance.

Usage example::

    checkcommit --message "$(git log --format=%B -n 1)"

If, for some reason, you wish to skip this QA check for a specific commit message
you can add ``#noqa`` to the end of your commit message.

Usage example::

    [qa] Improved #20

    Simulation of a special unplanned case
    #noqa

``checkendline``
~~~~~~~~~~~~~~~~~

Ensures that a blank line is kept at the end of each file.

``checkpendingmigrations``
~~~~~~~~~~~~~~~~~~~~~~~~~~

Ensures there django migrations are up to date and no new migrations need to
be created.

It accepts an optional ``--migration-module`` flag indicating the django app
name that should be passed to ``./manage.py makemigrations``, eg:
``./manage.py makemigrations $MIGRATION_MODULE``.

Installing for development
--------------------------

Install sqlite:

.. code-block:: shell

    sudo apt-get install sqlite3 libsqlite3-dev

Install your forked repo:

.. code-block:: shell

    git clone git://github.com/<your_fork>/openwisp-utils
    cd openwisp-utils/
    python setup.py develop

Install test requirements:

.. code-block:: shell

    pip install -r requirements-test.txt

Create database:

.. code-block:: shell

    cd tests/
    ./manage.py migrate
    ./manage.py createsuperuser

You can access the admin interface of the test project at http://127.0.0.1:8000/admin/.

Run tests with:

.. code-block:: shell

    ./runtests.py

Contributing
------------

1. Announce your intentions in the `OpenWISP Mailing List <https://groups.google.com/d/forum/openwisp>`_
   and open relavant issues using the `issue tracker <https://github.com/openwisp/openwisp-utils/issues>`_
2. Fork this repo and install the project following the
   `instructions <https://github.com/openwisp/openwisp-utils#install-development-version>`_
3. Follow `PEP8, Style Guide for Python Code`_
4. Write code and corresponding tests
5. Ensure that all tests pass and the test coverage does not decrease
6. Document your changes
7. Send a pull request

.. _PEP8, Style Guide for Python Code: http://www.python.org/dev/peps/pep-0008/

Changelog
---------

See `CHANGES <https://github.com/openwisp/openwisp-utils/blob/master/CHANGES.rst>`_.

License
-------

See `LICENSE <https://github.com/openwisp/openwisp-utils/blob/master/LICENSE>`_.

Support
-------

See `OpenWISP Support Channels <http://openwisp.org/support.html>`_.
