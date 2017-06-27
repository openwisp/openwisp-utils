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

Python and Django utilities shared between different OpenWISP modules

------------

.. contents:: **Table of Contents**:
   :backlinks: none
   :depth: 3

------------

Current utilities
-----------------

* **Customized admin theme** for OpenWISP modules
* **Multitenant** admin interface and testing mixins
* **TimeStamped** models and mixins which add self-updating ``created`` and ``modified`` fields.
* **DependencyLoader**: template loader which looks in the templates dir of all django-apps listed in ``EXTENDED_APPS``
* **DependencyFinder**: finds static files of django-apps listed in ``EXTENDED_APPS``

Project goals
-------------

* Minimize code duplication among OpenWISP modules

Install stable version from pypi
--------------------------------

Install from pypi:

.. code-block:: shell

    pip install openwisp-utils

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

``INSTALLED_APPS`` in ``settings.py`` should look like the following if you want to use all the utilities

.. code-block:: python

    INSTALLED_APPS = [
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        # customized admin theme
        'openwisp_utils.admin_theme',
        # all-auth
        'django.contrib.sites',
        'allauth',
        'allauth.account',
        'allauth.socialaccount',
        'django_extensions',
        # openwisp2 modules
        'openwisp_users',
        # admin
        'django.contrib.admin',
    ]

Adding admin theme
^^^^^^^^^^^^^^^^^^

For using the customized admin theme, 

* Make sure you've added ``openwisp_utils.admin_theme`` to ``INSTALLED_APPS`` in ``settings.py``

* Add the following into your ``urls.py`` file which contains ``admin`` urls.

.. code-block:: python

    from django.conf.urls import include, url

    from openwisp_utils.admin_theme.admin import admin, openwisp_admin

    openwisp_admin()

    urlpatterns = [
        # other url patterns
        url(r'^admin/', include(admin.site.urls)),
    ]

Using Multitenant and other admin mixins
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These are mixins which make a ModelAdmin class multitenant: users will see only the objects related to the organizations they are associated with.

* **MultitenantAdminMixin**: inheriting this class would make a ModelAdmin class multitenant. set ``multitenant_shared_relations`` to the list of parameters you wish to have only organization specific options.

* **MultitenantObjectFilter**: Admin filter that shows only organizations the current user is associated with in its available choices.

* **MultitenantObjectFilter**: Admin filter that shows only objects of organizations the current user is associated with.

* **TimeReadonlyAdminMixin**: Admin mixin which adds two readonly fields ``created`` and ``modified``. This is an admin mixin for models inheriting ``TimeStampedEditableModel`` which adds the fields ``created`` and ``modified`` to the database.

.. code-block:: python

    from django.contrib import admin

    from openwisp_utils.admin import (MultitenantAdminMixin,
                                      MultitenantObjectFilter,
                                      MultitenantOrgFilter,
                                      TimeReadonlyAdminMixin)

    from .models import Book, Shelf


    class BaseAdmin(MultitenantAdminMixin, TimeReadonlyAdminMixin, admin.ModelAdmin):
        pass


    class ShelfAdmin(BaseAdmin):
        list_display = ['name', 'organization']
        list_filter = [('organization', MultitenantOrgFilter)]
        fields = ['name', 'organization', 'created', 'modified']


    class BookAdmin(BaseAdmin):
        list_display = ['name', 'author', 'organization', 'shelf']
        list_filter = [('organization', MultitenantOrgFilter),
                       ('shelf', MultitenantObjectFilter)]
        fields = ['name', 'author', 'organization', 'shelf', 'created', 'modified']
        multitenant_shared_relations = ['shelf']

Using ``DependencyLoader`` and ``DependencyFinder``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add the list of all packages extended to ``EXTENDED_APPS`` in ``settings.py``. If you've extended ``django_netjsonconfig`` and ``django_x509``:

.. code-block:: python

    EXTENDED_APPS = ['django_netjsonconfig', 'django_x509']

* **DependencyFinder**: Add ``openwisp_utils.staticfiles.DependencyFinder`` to ``STATICFILES_FINDERS`` in ``settings.py``.

.. code-block:: python

    STATICFILES_FINDERS = [
        'django.contrib.staticfiles.finders.FileSystemFinder',
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
        'openwisp_utils.staticfiles.DependencyFinder',
    ]

* **DependencyLoader**: Add ``openwisp_utils.staticfiles.DependencyFinder`` to ``TEMPLATES_LOADERS`` in ``settings.py`` or as shown below.

.. code-block:: python

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'OPTIONS': {
                'loaders': [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                    'openwisp_utils.loaders.DependencyLoader',
                ],
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                ],
            },
        },
    ]

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

Set ``EMAIL_PORT`` in ``settings.py`` to a port number (eg: ``1025``):

.. code-block:: python

    EMAIL_PORT = '1025'

Launch development server and SMTP deubgging server:

.. code-block:: shell

    ./manage.py runserver
    # open another session and run
    python -m smtpd -n -c DebuggingServer localhost:1025

You can access the admin interface of the test project at http://127.0.0.1:8000/admin/.

Run tests with:

.. code-block:: shell

    ./runtests.py

Contributing
------------

1. Announce your intentions in the `OpenWISP Mailing List <https://groups.google.com/d/forum/openwisp>`_ and open relavant issues using the `issue tracker <https://github.com/openwisp/openwisp-utils/issues>`_
2. Fork this repo and install the project following the `instructions <https://github.com/openwisp/openwisp-utils#install-development-version>`_
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
