openwisp-utils
==============

.. image:: https://travis-ci.com/openwisp/openwisp-utils.svg?branch=master
    :target: https://travis-ci.com/openwisp/openwisp-utils
    :alt: ci build

.. image:: https://coveralls.io/repos/github/openwisp/openwisp-utils/badge.svg
    :target: https://coveralls.io/github/openwisp/openwisp-utils
    :alt: Test coverage

.. image:: https://requires.io/github/openwisp/openwisp-utils/requirements.svg?branch=master
    :target: https://requires.io/github/openwisp/openwisp-utils/requirements/?branch=master
    :alt: Requirements Status

.. image:: https://badge.fury.io/py/openwisp-utils.svg
    :target: http://badge.fury.io/py/openwisp-utils
    :alt: pypi

.. image:: https://pepy.tech/badge/openwisp-utils
   :target: https://pepy.tech/project/openwisp-utils
   :alt: downloads

.. image:: https://img.shields.io/gitter/room/nwjs/nw.js.svg?style=flat-square
   :target: https://gitter.im/openwisp/general
   :alt: support chat

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://pypi.org/project/black/
   :alt: code style: black

------------

Python and Django functions, classes and settings re-used across different OpenWISP modules,
stored here with the aim of avoiding code duplication and ease maintenance.

**Don't repeat yourself!**

.. image:: https://raw.githubusercontent.com/openwisp/openwisp2-docs/master/assets/design/openwisp-logo-black.svg
  :target: http://openwisp.org

Current features
----------------

* `Configurable admin theme <#using-the-admin_theme>`_
* `Configurable navigation menu <#main-navigation-menu>`_
* `OpenAPI / Swagger documentation <#openwisp_api_docs>`_
* `Model utilities <#model-utilities>`_
* `Admin utilities <#admin-utilities>`_
* `Code utilities <#code-utilities>`_
* `REST API utilities <#rest-api-utilities>`_
* `Test utilities <#test-utilities>`_
* `Quality assurance checks <#quality-assurance-checks>`_

------------

.. contents:: **Table of Contents**:
   :backlinks: none
   :depth: 3

------------

Install stable version from pypi
--------------------------------

Install from pypi:

.. code-block:: shell

    pip install openwisp-utils

    # install optional dependencies for REST framework
    pip install openwisp-utils[rest]

    # install optional dependencies for tests (flake8, black and isort)
    pip install openwisp-utils[qa]

    # or install everything
    pip install openwisp-utils[rest,qa]

Install development version
---------------------------

Install tarball:

.. code-block:: shell

    pip install https://github.com/openwisp/openwisp-utils/tarball/master

Alternatively you can install via pip using git:

.. code-block:: shell

    pip install -e git+git://github.com/openwisp/openwisp-utils#egg=openwisp-utils

Using the ``admin_theme``
-------------------------

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
and `OPENWISP_ADMIN_THEME_JS <openwisp_admin_theme_js>`_ settings
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

Main navigation menu
--------------------

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
                    'openwisp_utils.admin_theme.context_processor.menu_items'    # <----- add this
                ],
            },
        },
    ]

If you need to define custom menu items, see:
`OPENWISP_ADMIN_MENU_ITEMS <#openwisp_admin_menu_items>`_.

Users will only be able to see menu items for objects they have permission to either view or edit.

Model utilities
---------------

``openwisp_utils.base.UUIDModel``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Model class which provides a UUID4 primary key.

``openwisp_utils.base.TimeStampedEditableModel``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Model class inheriting ``UUIDModel`` which provides two additional fields:

- ``created``
- ``modified``

Which use respectively ``AutoCreatedField``, ``AutoLastModifiedField`` from ``model_utils.fields``
(self-updating fields providing the creation date-time and the last modified date-time).

``openwisp_utils.base.KeyField``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A model field whic provides a random key or token, widely used across openwisp modules.

Admin utilities
---------------

``openwisp_utils.admin.TimeReadonlyAdminMixin``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Admin mixin which adds two readonly fields ``created`` and ``modified``.

This is an admin mixin for models inheriting ``TimeStampedEditableModel``
which adds the fields ``created`` and ``modified`` to the database.

``openwisp_utils.admin.ReadOnlyAdmin``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A read-only ``ModelAdmin`` base class.

Will include the ``id`` field by default, which can be excluded by supplying
the ``exclude`` attribute, eg:

.. code-block:: python

    from openwisp_utils.admin import ReadOnlyAdmin

    class PostAuthReadOnlyAdmin(ReadOnlyAdmin):
        exclude = ['id']

``openwisp_utils.admin.AlwaysHasChangedMixin``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A mixin designed for inline items and model forms, ensures the item
is created even if the default values are unchanged.

Without this, when creating new objects, inline items won't be saved
unless users change the default values.

``openwisp_utils.admin.UUIDAdmin``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

An admin class that provides the UUID of the object as a read-only input field
(to make it easy and quick to copy/paste).

``openwisp_utils.admin.ReceiveUrlAdmin``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

An admin class that provides an URL as a read-only input field
(to make it easy and quick to copy/paste).

Code utilities
--------------

``openwisp_utils.utils.get_random_key``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Generates an random string of 32 characters.

``openwisp_utils.utils.register_menu_items``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Takes input of a list of models name and settings_menu name and adds
them to the side navigation bar in the admin dashboard interface.

Usage:

.. code-block:: python

    from openwisp_utils.utils import register_menu_items
    from openwisp_utils.api.apps import ApiAppConfig

    class YourAwesomeAppConfig(ApiAppConfig):
        def ready(self, *args, **kwargs):
            super().ready(*args, **kwargs)
            items = [{'model': 'your_project.your_model_name'}]
            # register_menu_items(items[, name_menu=YOUR_SETTINGS_MENU_NAME])
            register_menu_items(items, name_menu='OPENWISP_DEFAULT_ADMIN_MENU_ITEMS')


``openwisp_utils.utils.deep_merge_dicts``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Returns a new ``dict`` which is the result of the merge of the two dictionaries,
all elements are deep-copied to avoid modifying the original data structures.

Usage:

.. code-block:: python

    from openwisp_utils.utils import deep_merge_dicts

    mergd_dict = deep_merge_dicts(dict1, dict2)

``openwisp_utils.utils.default_or_test``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If the program is being executed during automated tests the value supplied in
the ``test`` argument will be returned, otherwise the one supplied in the
``value`` argument is returned.

.. code-block:: python

    from openwisp_utils.utils import default_or_test

    THROTTLE_RATE = getattr(
        settings,
        'THROTTLE_RATE',
        default_or_test(value='20/day', test=None),
    )

``openwisp_utils.utils.print_color``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**default colors**: ``['white_bold', 'green_bold', 'yellow_bold', 'red_bold']``

If you want to print a string in ``Red Bold``, you can do it as below.

.. code-block:: python

    from openwisp_utils.utils import print_color

    print_color('This is the printed in Red Bold', color_name='red_bold')

You may also provide the ``end`` arguement similar to built-in print method.

REST API utilities
------------------

``openwisp_utils.api.serializers.ValidatedModelSerializer``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A model serializer which calls the model instance ``full_clean()``.

``openwisp_utils.api.apps.ApiAppConfig``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you're creating an OpenWISP module which provides a REST API built with Django REST Framework,
chances is that you may need to define some default settings to control its throttling or other aspects.

Here's how to easily do it:

.. code-block:: python

    from django.conf import settings
    from django.utils.translation import ugettext_lazy as _
    from openwisp_utils.api.apps import ApiAppConfig


    class MyModuleConfig(ApiAppConfig):
        name = 'my_openwisp_module'
        label = 'my_module'
        verbose_name = _('My OpenWISP Module')

        # assumes API is enabled by default
        API_ENABLED = getattr(settings, 'MY_OPENWISP_MODULE_API_ENABLED', True)
        # set throttling rates for your module here
        REST_FRAMEWORK_SETTINGS = {
            'DEFAULT_THROTTLE_RATES': {'my_module': '400/hour'},
        }

Every openwisp module which has an API should use this class to configure
its own default settings, which will be merged with the settings of the other
modules.

Test utilities
--------------

``openwisp_utils.tests.catch_signal``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

``openwisp_utils.tests.TimeLoggingTestRunner``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. figure:: https://raw.githubusercontent.com/openwisp/openwisp-utils/master/docs/TimeLoggingTestRunner.png
  :align: center

This class extends the `default test runner provided by Django <https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEST_RUNNER>`_
and logs the time spent by each test, making it easier to spot slow tests by highlighting
time taken by it in yellow (time shall be highlighted in red if it crosses the second threshold).

By default tests are considered slow if they take more than 0.3 seconds but you can control
this with `OPENWISP_SLOW_TEST_THRESHOLD <#openwisp_slow_test_threshold>`_.

In order to switch to this test runner you have set the following in your `settings.py`:

.. code-block:: python

    TEST_RUNNER = 'openwisp_utils.tests.TimeLoggingTestRunner'

``openwisp_utils.tests.capture_stdout``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This decorator can be used to capture standard output produced by tests,
either to silence it or to write assertions.

Example usage:

.. code-block:: python

    from openwisp_utils.tests import capture_stdout

    @capture_stdout()
    def test_something(self):
        function_generating_output() # pseudo code

    @capture_stdout()
    def test_something_again(self, captured_ouput):
        # pseudo code
        function_generating_output()
        # now you can create assertions on the captured output
        self.assertIn('expected stdout', captured_ouput.getvalue())
        # if there are more than one assertions, clear the captured output first
        captured_error.truncate(0)
        captured_error.seek(0)
        # you can create new assertion now
        self.assertIn('another output', captured_ouput.getvalue())

**Notes**:

- If assertions need to be made on the captured output, an additional argument
  (in the example above is named ``captured_output``) can be passed as an argument
  to the decorated test method, alternatively it can be omitted.
- A ``StingIO`` instance is used for capturing output by default but if needed
  it's possible to pass a custom ``StringIO`` instance to the decorator function.

``openwisp_utils.tests.capture_stderr``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Equivalent to ``capture_stdout``, but for standard error.

Example usage:

.. code-block:: python

    from openwisp_utils.tests import capture_stderr

    @capture_stderr()
    def test_error(self):
        function_generating_error() # pseudo code

    @capture_stderr()
    def test_error_again(self, captured_error):
        # pseudo code
        function_generating_error()
        # now you can create assertions on captured error
        self.assertIn('expected error', captured_error.getvalue())
        # if there are more than one assertions, clear the captured error first
        captured_error.truncate(0)
        captured_error.seek(0)
        # you can create new assertion now
        self.assertIn('another expected error', captured_error.getvalue())

``openwisp_utils.tests.capture_any_output``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Equivalent to ``capture_stdout`` and ``capture_stderr``, but captures both types of
output (standard output and standard error).

Example usage:

.. code-block:: python

    from openwisp_utils.tests import capture_any_output

    @capture_any_output()
    def test_something_out(self):
        function_generating_output() # pseudo code

    @capture_any_output()
    def test_out_again(self, captured_output, captured_error):
        # pseudo code
        function_generating_output_and_errors()
        # now you can create assertions on captured error
        self.assertIn('expected stdout', captured_output.getvalue())
        self.assertIn('expected stderr', captured_error.getvalue())

Quality Assurance Checks
------------------------

This package contains some common QA checks that are used in the
automated builds of different OpenWISP modules.

``openwisp-qa-format``
^^^^^^^^^^^^^^^^^^^^^^

Shell script to automatically format Python code. It runs ``isort`` and ``black``.

``openwisp-qa-check``
^^^^^^^^^^^^^^^^^^^^^

Shell script to run the following quality assurance checks:

* `checkmigrations <#checkmigrations>`_
* `checkcommit <#checkcommit>`_
* `checkendline <#checkendline>`_
* `checkpendingmigrations <#checkpendingmigrations>`_
* `checkrst <#checkrst>`_
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
^^^^^^^^^^^^^^^^^^^

Ensures the latest migrations created have a human readable name.

We want to avoid having many migrations named like ``0003_auto_20150410_3242.py``.

This way we can reconstruct the evolution of our database schemas faster, with
less efforts and hence less costs.

Usage example::

    checkmigrations --migration-path ./django_freeradius/migrations/

``checkcommit``
^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^

Ensures that a blank line is kept at the end of each file.

``checkpendingmigrations``
^^^^^^^^^^^^^^^^^^^^^^^^^^

Ensures there django migrations are up to date and no new migrations need to
be created.

It accepts an optional ``--migration-module`` flag indicating the django app
name that should be passed to ``./manage.py makemigrations``, eg:
``./manage.py makemigrations $MIGRATION_MODULE``.

``checkrst``
^^^^^^^^^^^^^

Checks the syntax of all ReStructuredText files to ensure they can be published on pypi or using python-sphinx.

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

``OPENWISP_ADMIN_MENU_ITEMS``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

Installing for development
--------------------------

Install sqlite:

.. code-block:: shell

    sudo apt-get install sqlite3 libsqlite3-dev

Install your forked repo:

.. code-block:: shell

    git clone git://github.com/<your_fork>/openwisp-utils
    cd openwisp-utils/
    pip install -e .[qa,rest]

Install test requirements:

.. code-block:: shell

    pip install -r requirements-test.txt

Create database:

.. code-block:: shell

    cd tests/
    ./manage.py migrate
    ./manage.py createsuperuser

Run development server:

.. code-block:: shell

    cd tests/
    ./manage.py runserver

You can access the admin interface of the test project at http://127.0.0.1:8000/admin/.

Run tests with:

.. code-block:: shell

    ./runtests.py --parallel

Contributing
------------

Please refer to the `OpenWISP contributing guidelines <http://openwisp.io/docs/developer/contributing.html>`_.

Support
-------

See `OpenWISP Support Channels <http://openwisp.org/support.html>`_.

Changelog
---------

See `CHANGES <https://github.com/openwisp/openwisp-utils/blob/master/CHANGES.rst>`_.

License
-------

See `LICENSE <https://github.com/openwisp/openwisp-utils/blob/master/LICENSE>`_.
