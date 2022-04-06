openwisp-utils
==============

.. image:: https://github.com/openwisp/openwisp-utils/workflows/OpenWISP%20Utils%20CI%20Build/badge.svg?branch=master
   :target: https://github.com/openwisp/openwisp-utils/actions?query=workflow%3A%22OpenWISP+Utils+CI+Build%22
   :alt: CI build status

.. image:: https://coveralls.io/repos/github/openwisp/openwisp-utils/badge.svg
    :target: https://coveralls.io/github/openwisp/openwisp-utils
    :alt: Test coverage

.. image:: https://img.shields.io/librariesio/release/github/openwisp/openwisp-utils
  :target: https://libraries.io/github/openwisp/openwisp-utils#repository_dependencies
  :alt: Dependency monitoring

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
* `OpenWISP Dashboard <#openwisp-dashboard>`_
* `Configurable navigation menu <#main-navigation-menu>`_
* `Improved admin filters <#admin-filters>`_
* `OpenAPI / Swagger documentation <#openwisp_api_docs>`_
* `Model utilities <#model-utilities>`_
* `Storage utilities <#storage-utilities>`_
* `Admin utilities <#admin-utilities>`_
* `Code utilities <#code-utilities>`_
* `Admin Theme utilities <#admin-theme-utilities>`_
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

OpenWISP Dashboard
------------------

The ``admin_theme`` sub app of this package provides an admin dashboard
for OpenWISP which can be manipulated with the functions described in
the next sections.

Example 1, monitoring:

.. figure:: https://raw.githubusercontent.com/openwisp/openwisp-utils/master/docs/dashboard1.png
  :align: center

Example 2, controller:

.. figure:: https://raw.githubusercontent.com/openwisp/openwisp-utils/master/docs/dashboard2.png
  :align: center

``register_dashboard_template``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Allows including a specific django template in the OpenWISP dashboard.

It is designed to allow the inclusion of the geographic map
shipped by
`OpenWISP Monitoring <https://github.com/openwisp/openwisp-monitoring>`_
but can be used to include any custom element in the dashboard.

**Note**: templates are loaded before charts.

**Syntax:**

.. code-block:: python

    register_dashboard_template(position, config)

+--------------------+----------------------------------------------------------------------------------+
| **Parameter**      | **Description**                                                                  |
+--------------------+----------------------------------------------------------------------------------+
| ``position``       | (``int``) The position of the template.                                          |
+--------------------+----------------------------------------------------------------------------------+
| ``config``         | (``dict``) The configuration of the template.                                    |
+--------------------+----------------------------------------------------------------------------------+
| ``extra_config``   | **optional** (``dict``) Extra configuration you want to pass to custom template. |
+--------------------+----------------------------------------------------------------------------------+

Following properties can be configured for each template ``config``:

+-----------------+------------------------------------------------------------------------------------------------------+
| **Property**    | **Description**                                                                                      |
+-----------------+------------------------------------------------------------------------------------------------------+
| ``template``    | (``str``) Path to pass to the template loader.                                                       |
+-----------------+------------------------------------------------------------------------------------------------------+
| ``css``         | (``tuple``) List of CSS files to load in the HTML page.                                              |
+-----------------+------------------------------------------------------------------------------------------------------+
| ``js``          | (``tuple``) List of Javascript files to load in the HTML page.                                       |
+-----------------+------------------------------------------------------------------------------------------------------+

Code example:

.. code-block:: python

	from openwisp_utils.admin_theme import register_dashboard_template

  register_dashboard_template(
      position=0,
      config={
          'template': 'admin/dashboard/device_map.html',
          'css': (
              'monitoring/css/device-map.css',
              'leaflet/leaflet.css',
              'monitoring/css/leaflet.fullscreen.css',
          ),
          'js': (
              'monitoring/js/device-map.js',
              'leaflet/leaflet.js',
              'leaflet/leaflet.extras.js',
              'monitoring/js/leaflet.fullscreen.min.js'
          )
      },
      extra_config={
          'optional_variable': 'any_valid_value',
      },
  )

It is recommended to register dashboard templates from the ``ready``
method of the AppConfig of the app where the templates are defined.

``unregister_dashboard_template``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This function can be used to remove a template from the dashboard.

**Syntax:**

.. code-block:: python

    unregister_dashboard_template(template_name)

+-------------------+---------------------------------------------------+
| **Parameter**     | **Description**                                   |
+-------------------+---------------------------------------------------+
| ``template_name`` | (``str``) The name of the template to remove.     |
+-------------------+---------------------------------------------------+

Code example:

.. code-block:: python

    from openwisp_utils.admin_theme import unregister_dashboard_template

    unregister_dashboard_template('admin/dashboard/device_map.html')

**Note**: an ``ImproperlyConfigured`` exception is raised the
specified dashboard template is not registered.

``register_dashboard_chart``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Adds a chart to the OpenWISP dashboard.

At the moment only pie charts are supported.

The code works by defining the type of query which will be executed,
and optionally, how the returned values have to be colored and labeled.

**Syntax:**

.. code-block:: python

    register_dashboard_chart(position, config)

+--------------------+-------------------------------------------------------------+
| **Parameter**      | **Description**                                             |
+--------------------+-------------------------------------------------------------+
| ``position``       | (``int``) Position of the chart.                            |
+--------------------+-------------------------------------------------------------+
| ``config``         | (``dict``) Configuration of chart.                          |
+--------------------+-------------------------------------------------------------+

Following properties can be configured for each chart ``config``:

+------------------+--------------------------------------------------------------------------------------------------------+
| **Property**     | **Description**                                                                                        |
+------------------+--------------------------------------------------------------------------------------------------------+
| ``query_params`` | It is a required property in form of ``dict`` containing following properties:                         |
|                  |                                                                                                        |
|                  | +-----------------+---------------------------------------------------------------------------------+  |
|                  | | **Property**    | **Description**                                                                 |  |
|                  | +-----------------+---------------------------------------------------------------------------------+  |
|                  | | ``name``        | (``str``) Chart title shown in the user interface.                              |  |
|                  | +-----------------+---------------------------------------------------------------------------------+  |
|                  | | ``app_label``   | (``str``) App label of the model that will be used to query the database.       |  |
|                  | +-----------------+---------------------------------------------------------------------------------+  |
|                  | | ``model``       | (``str``) Name of the model that will be used to query the database.            |  |
|                  | +-----------------+---------------------------------------------------------------------------------+  |
|                  | | ``group_by``    | (``str``) The property which will be used to group values.                      |  |
|                  | +-----------------+---------------------------------------------------------------------------------+  |
|                  | | ``annotate``    | Alternative to ``group_by``, ``dict`` used for more complex queries.            |  |
|                  | +-----------------+---------------------------------------------------------------------------------+  |
|                  | | ``aggregate``   | Alternative to ``group_by``, ``dict`` used for more complex queries.            |  |
|                  | +-----------------+---------------------------------------------------------------------------------+  |
+------------------+--------------------------------------------------------------------------------------------------------+
| ``colors``       | An **optional** ``dict`` which can be used to define colors for each distinct                          |
|                  | value shown in the pie charts.                                                                         |
+------------------+--------------------------------------------------------------------------------------------------------+
| ``labels``       | An **optional** ``dict`` which can be used to define translatable strings for each distinct            |
|                  | value shown in the pie charts. Can be used also to provide fallback human readable values for          |
|                  | raw values stored in the database which would be otherwise hard to understand for the user.            |
+------------------+--------------------------------------------------------------------------------------------------------+
| ``filters``      | An **optional** ``dict`` which can be used when using ``aggregate`` and ``annotate`` in                |
|                  | ``query_params`` to define the link that will be generated to filter results (pie charts are           |
|                  | clickable and clicking on a portion of it will show the filtered results).                             |
+------------------+--------------------------------------------------------------------------------------------------------+

Code example:

.. code-block:: python

	from openwisp_utils.admin_theme import register_dashboard_chart

    register_dashboard_chart(
        position=1,
        config={
            'query_params': {
                'name': 'Operator Project Distribution',
                'app_label': 'test_project',
                'model': 'operator',
                'group_by': 'project__name',
            },
            'colors': {'Utils': 'red', 'User': 'orange'},
        },
    )

For real world examples, look at the code of
`OpenWISP Controller <https://github.com/openwisp/openwisp-controller>`__
and `OpenWISP Monitoring <https://github.com/openwisp/openwisp-monitoring>`_.

**Note**: an ``ImproperlyConfigured`` exception is raised if a
dashboard element is already registered at same position.

It is recommended to register dashboard charts from the ``ready`` method
of the AppConfig of the app where the models are defined.
Checkout `app.py of the test_project
<https://github.com/openwisp/openwisp-utils/blob/master/tests/test_project/apps.py>`_
for reference.

``unregister_dashboard_chart``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This function can used to remove a chart from the dashboard.

**Syntax:**

.. code-block:: python

    unregister_dashboard_chart(chart_name)

+------------------+---------------------------------------------------+
| **Parameter**    | **Description**                                   |
+------------------+---------------------------------------------------+
| ``chart_name``   | (``str``) The name of the chart to remove.        |
+------------------+---------------------------------------------------+

Code example:

.. code-block:: python

    from openwisp_utils.admin_theme import unregister_dashboard_chart

    unregister_dashboard_chart('Operator Project Distribution')

**Note**: an ``ImproperlyConfigured`` exception is raised the
specified dashboard chart is not registered.

Main navigation menu
--------------------

The ``admin_theme`` sub app of this package provides a navigation menu that can be
manipulated with the functions described in the next sections.

Add ``openwisp_utils.admin_theme.context_processor.menu_groups`` to
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
                    'openwisp_utils.admin_theme.context_processor.menu_groups'    # <----- add this
                ],
            },
        },
    ]

``register_menu_group``
^^^^^^^^^^^^^^^^^^^^^^^

Allows registering a new menu item or group at the specified position in the Main Navigation Menu.

**Syntax:**

.. code-block:: python

    register_menu_group(position, config)

+--------------------+-------------------------------------------------------------+
| **Parameter**      | **Description**                                             |
+--------------------+-------------------------------------------------------------+
| ``position``       | (``int``) Position of the group or item.                    |
+--------------------+-------------------------------------------------------------+
| ``config``         | (``dict``) Configuration of the goup or item.               |
+--------------------+-------------------------------------------------------------+

Code example:

.. code-block:: python

    from django.utils.translation import ugettext_lazy as _
    from openwisp_utils.admin_theme.menu import register_menu_group

    register_menu_group(
        position=1,
        config={
            'label': _('My Group'),
            'items': {
                1: {
                    'label': _('Users List'),
                    'model': 'auth.User',
                    'name': 'changelist',
                    'icon': 'list-icon',
                },
                2: {
                    'label': _('Add User'),
                    'model': 'auth.User',
                    'name': 'add',
                    'icon': 'add-icon',
                },
            },
            'icon': 'user-group-icon',
        },
    )
    register_menu_group(
        position=2,
        config={
            'model': 'test_project.Shelf',
            'name': 'changelist',
            'label': _('View Shelf'),
            'icon': 'shelf-icon',
        },
    )
    register_menu_group(
        position=3, config={'label': _('My Link'), 'url': 'https://link.com'}
    )

.. note::
    An ``ImproperlyConfigured`` exception is raised if a menu element is already registered at the same position.

    An ``ImproperlyConfigured`` exception is raised if the supplied configuration does not match with the different types of
    possible configurations available (different configurations will be discussed in the next section).

    It is recommended to use ``register_menu_group`` in the ``ready`` method of the ``AppConfig``.

    ``register_menu_items`` is obsoleted by ``register_menu_group`` and will be removed in
    future versions. Links added using ``register_menu_items`` will be shown at the top
    of navigation menu and above any ``register_menu_group`` items.

Adding a custom link
~~~~~~~~~~~~~~~~~~~~~

To add a link that contains a custom URL the following syntax can be used.

**Syntax:**

.. code-block:: python

    register_menu_group(position=1, config={
        "label": "Link Label",
        "url": "link_url",
        "icon": "my-icon"
    })

Following is the description of the configuration:

+------------------+--------------------------------------------------------------+
| **Parameter**    | **Description**                                              |
+------------------+--------------------------------------------------------------+
| ``label``        | (``str``) Display text for the link.                         |
+------------------+--------------------------------------------------------------+
| ``url``          | (``str``) url for the link.                                  |
+------------------+--------------------------------------------------------------+
| ``icon``         | An **optional** ``str`` CSS class name for the icon. No icon |
|                  | is displayed if not provided.                                |
+------------------+--------------------------------------------------------------+

Adding a model link
~~~~~~~~~~~~~~~~~~~

To add a link that contains URL of add form or change list page of a model
then following syntax can be used. Users will only be able to see links for
models they have permission to either view or edit.

**Syntax:**

.. code-block:: python

    # add a link of list page
    register_menu_group(
        position=1,
        config={
            'model': 'my_project.MyModel',
            'name': 'changelist',
            'label': 'MyModel List',
            'icon': 'my-model-list-class',
        },
    )

    # add a link of add page
    register_menu_group(
        position=2,
        config={
            'model': 'my_project.MyModel',
            'name': 'add',
            'label': 'MyModel Add Item',
            'icon': 'my-model-add-class',
        },
    )

Following is the description of the configuration:

+------------------+--------------------------------------------------------------+
| **Parameter**    | **Description**                                              |
+------------------+--------------------------------------------------------------+
| ``model``        | (``str``) Model of the app for which you to add link.        |
+------------------+--------------------------------------------------------------+
| ``name``         | (``str``) url name. eg. changelist or add.                   |
+------------------+--------------------------------------------------------------+
| ``label``        | An **optional** ``str`` display text for the link. It is     |
|                  | automatically generated if not provided.                     |
+------------------+--------------------------------------------------------------+
| ``icon``         | An **optional** ``str`` CSS class name for the icon. No icon |
|                  | is displayed if not provided.                                |
+------------------+--------------------------------------------------------------+

Adding a menu group
~~~~~~~~~~~~~~~~~~~

To add a nested group of links in the menu the following syntax can be used.
It creates a dropdown in the menu.

**Syntax:**

.. code-block:: python

    register_menu_group(
        position=1,
        config={
            'label': 'My Group Label',
            'items': {
                1: {'label': 'Link Label', 'url': 'link_url', 'icon': 'my-icon'},
                2: {
                    'model': 'my_project.MyModel',
                    'name': 'changelist',
                    'label': 'MyModel List',
                    'icon': 'my-model-list-class',
                },
            },
            'icon': 'my-group-icon-class',
        },
    )

Following is the description of the configuration:

+------------------+--------------------------------------------------------------+
| **Parameter**    | **Description**                                              |
+------------------+--------------------------------------------------------------+
| ``label``        | (``str``) Display name for the link.                         |
+------------------+--------------------------------------------------------------+
| ``items``        | (``dict``) Items to be displayed in the dropdown.            |
|                  | It can be a dict of custom links or model links              |
|                  | with key as their position in the group.                     |
+------------------+--------------------------------------------------------------+
| ``icon``         | An **optional** ``str`` CSS class name for the icon. No icon |
|                  | is displayed if not provided.                                |
+------------------+--------------------------------------------------------------+

``register_menu_subitem``
^^^^^^^^^^^^^^^^^^^^^^^^^

Allows adding an item to a registered group.

**Syntax:**

.. code-block:: python

    register_menu_subitem(group_position, item_position, config)

+--------------------------+----------------------------------------------------------------+
| **Parameter**            | **Description**                                                |
+--------------------------+----------------------------------------------------------------+
| ``group_position``       | (``int``) Position of the group in which item should be added. |
+--------------------------+----------------------------------------------------------------+
| ``item_position``        | (``int``) Position at which item should be added in the group  |
+--------------------------+----------------------------------------------------------------+
| ``config``               | (``dict``) Configuration of the item.                          |
+--------------------------+----------------------------------------------------------------+

Code example:

.. code-block:: python

    from django.utils.translation import ugettext_lazy as _
    from openwisp_utils.admin_theme.menu import register_menu_subitem

    # To register a model link
    register_menu_subitem(
        group_position=10,
        item_position=2,
        config={
            'label': _('Users List'),
            'model': 'auth.User',
            'name': 'changelist',
            'icon': 'list-icon',
        },
    )

    # To register a custom link
    register_menu_subitem(
        group_position=10,
        item_position=2,
        config={'label': _('My Link'), 'url': 'https://link.com'},
    )

.. note::
    An ``ImproperlyConfigured`` exception is raised if the group is not already
    registered at ``group_position``.

    An ``ImproperlyConfigured`` exception is raised if the group already has an
    item registered at ``item_position``.

    It is only possible to register links to specific models or custom URL.
    An ``ImproperlyConfigured`` exception is raised if the configuration of
    group is provided in the function.

    It is recommended to use ``register_menu_subitem`` in the ``ready``
    method of the ``AppConfig``.

How to use custom icons in the menu
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create a CSS file and use the following syntax to provide the image for each
icon used in the menu. The CSS class name should be the same as the ``icon``
parameter used in the configuration of a menu item or group. Also icon being used
should be in ``svg`` format.

Example:

.. code-block:: css

    .icon-class-name:{
        mask-image: url(imageurl);
        -webkit-mask-image: url(imageurl);
    }

Follow the instructions in
`Supplying custom CSS and JS for the admin theme <#supplying-custom-css-and-js-for-the-admin-theme>`_
to know how to configure your OpenWISP instance to load custom CSS files.

Admin filters
-------------

.. figure:: https://github.com/openwisp/openwisp-utils/raw/media/docs/filter.gif
  :align: center

The ``admin_theme`` sub app provides an improved UI for the changelist filter
which occupies less space compared to the original implementation in django:
filters are displayed horizontally on the top (instead of vertically on the side)
and filter options are hidden in dropdown menus which are expanded once clicked.

Multiple filters can be applied at same time with the help of "apply filter" button.
This button is only visible when total number of filters is greater than 4.
When filters in use are less or equal to 4 the "apply filter" button is not visible
and filters work like in the original django implementation
(as soon as a filter option is selected the filter is applied and the page is reloaded).

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

``openwisp_utils.admin.HelpTextStackedInline``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. figure:: https://github.com/openwisp/openwisp-utils/raw/media/docs/help-text-stacked-inline.png
  :align: center

A stacked inline admin class that displays a help text for entire
inline object. Following is an example:

.. code-block:: python

    from openwisp_utils.admin import HelpTextStackedInline

    class SubnetDivisionRuleInlineAdmin(
        MultitenantAdminMixin, TimeReadonlyAdminMixin, HelpTextStackedInline
    ):
        model = Model
        # It is required to set "help_text" attribute
        help_text = {
            # (required) Help text to display
            'text': _(
                'Please keep in mind that once the subnet division rule is created '
                'and used, changing "Size" and "Number of Subnets" and decreasing '
                '"Number of IPs" will not be possible.'
            ),
            # (optional) You can provide a link to documentation for user reference
            'documentation_url': (
                'https://github.com/openwisp/openwisp-utils'
            )
            # (optional) Icon to be shown along with help text. By default it uses
            # "/static/admin/img/icon-alert.svg"
            'image_url': '/static/admin/img/icon-alert.svg'
        }

``openwisp_utils.admin_theme.filters.InputFilter``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``admin_theme`` sub app of this package provides an input filter that can be used in changelist page
to filter ``UUIDField`` or ``CharField``.

Code example:

.. code-block:: python

    from django.contrib import admin
    from openwisp_utils.admin_theme.filters import InputFilter
    from my_app.models import MyModel

    @admin.register(MyModel)
    class MyModelAdmin(admin.ModelAdmin):
        list_filter = [
            ('my_field', InputFilter),
            'other_field'
            ...
        ]

By default ``InputFilter`` use exact lookup to filter items which matches to the value being
searched by the user. But this behavior can be changed by modifying ``InputFilter`` as following:

.. code-block:: python

    from django.contrib import admin
    from openwisp_utils.admin_theme.filters import InputFilter
    from my_app.models import MyModel

    class MyInputFilter(InputFilter):
        lookup = 'icontains'


    @admin.register(MyModel)
    class MyModelAdmin(admin.ModelAdmin):
        list_filter = [
            ('my_field', MyInputFilter),
            'other_field'
            ...
        ]

To know about other lookups that can be used please check
`Django Lookup API Reference <https://docs.djangoproject.com/en/3.2/ref/models/lookups/#django.db.models.Lookup>`__

``openwisp_utils.admin_theme.filters.SimpleInputFilter``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A stripped down version of ``openwisp_utils.admin_theme.filters.InputFilter`` that provides
flexibility to customize filtering. It can be used to filter objects using indirectly
related fields.

The derived filter class should define the ``queryset`` method as shown in following example:

.. code-block:: python

    from django.contrib import admin
    from openwisp_utils.admin_theme.filters import SimpleInputFilter
    from my_app.models import MyModel

    class MyInputFilter(SimpleInputFilter):
        parameter_name = 'shelf'
        title = _('Shelf')

        def queryset(self, request, queryset):
            if self.value() is not None:
                return queryset.filter(name__icontains=self.value())


    @admin.register(MyModel)
    class MyModelAdmin(admin.ModelAdmin):
        list_filter = [
            MyInputFilter,
            'other_field'
            ...
        ]

Code utilities
--------------

``openwisp_utils.utils.get_random_key``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Generates an random string of 32 characters.

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

``openwisp_utils.utils.SorrtedOrderedDict``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Extends ``collections.SortedDict`` and implements logic to sort inserted
items based on ``key`` value. Sorting is done at insert operation which
incurs memory space overhead.

``openwisp_utils.tasks.OpenwispCeleryTask``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A custom celery task class that sets hard and soft time limits of celery tasks
using `OPENWISP_CELERY_HARD_TIME_LIMIT <#openwisp_celery_hard_time_limit>`_
and `OPENWISP_CELERY_SOFT_TIME_LIMIT <#openwisp_celery_soft_time_limit>`_
settings respectively.

Usage:

.. code-block:: python

    from celery import shared_task

    from openwisp_utils.tasks import OpenwispCeleryTask

    @shared_task(base=OpenwispCeleryTask)
    def your_celery_task():
        pass

**Note:** This task class should be used for regular background tasks
but not for complex background tasks which can take a long time to execute
(eg: firmware upgrades, network operations with retry mechanisms).

Storage utilities
-----------------

``openwisp_utils.storage.CompressStaticFilesStorage``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A static storage backend for compression inheriting from `django-compress-staticfiles's <https://pypi.org/project/django-compress-staticfiles/>`_ ``CompressStaticFilesStorage`` class.

Adds support for excluding file types using `OPENWISP_STATICFILES_VERSIONED_EXCLUDE <#openwisp_staticfiles_versioned_exclude>`_ setting.

To use point ``STATICFILES_STORAGE`` to ``openwisp_utils.storage.CompressStaticFilesStorage`` in ``settings.py``.

.. code-block:: python

    STATICFILES_STORAGE = 'openwisp_utils.storage.CompressStaticFilesStorage'

Admin Theme utilities
---------------------

``openwisp_utils.admin_theme.email.send_email``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This function allows sending email in both plain text and HTML version (using the template
and logo that can be customised using `OPENWISP_EMAIL_TEMPLATE <#openwisp_email_template>`_
and `OPENWISP_EMAIL_LOGO <#openwisp_email_logo>`_ respectively).

In case the HTML version if not needed it may be disabled by
setting `OPENWISP_HTML_EMAIL <#openwisp_html_email>`_ to ``False``.

**Syntax:**

.. code-block:: python

    send_email(subject, body_text, body_html, recipients)

+--------------------+------------------------------------------------------------------------+
| **Parameter**      | **Description**                                                        |
+--------------------+------------------------------------------------------------------------+
| ``subject``        | (``str``) The subject of the email template.                           |
+--------------------+------------------------------------------------------------------------+
| ``body_text``      | (``str``) The body of the text message to be emailed.                  |
+--------------------+------------------------------------------------------------------------+
| ``body_html``      | (``str``) The body of the html template to be emailed.                 |
+--------------------+------------------------------------------------------------------------+
| ``recipients``     | (``list``) The list of recipients to send the mail to.                 |
+--------------------+------------------------------------------------------------------------+
| ``extra_context``  | **optional** (``dict``) Extra context which is passed to the template. |
|                    | The dictionary keys ``call_to_action_text`` and ``call_to_action_url`` |
|                    | can be passed to show a call to action button.                         |
|                    | Similarly, ``footer`` can be passed to add a footer.                   |
+--------------------+------------------------------------------------------------------------+


**Note**: Data passed in body should be validated and user supplied data should not be sent directly to the function.

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

``openwisp_utils.tests.AssertNumQueriesSubTestMixin``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This mixin overrides the
`assertNumQueries <https://docs.djangoproject.com/en/dev/topics/testing/tools/#django.test.TransactionTestCase.assertNumQueries>`_
assertion from the django test case to run in a ``subTest`` so that the
query check does not block the whole test if it fails.

Example usage:

.. code-block:: python

    from django.test import TestCase
    from openwisp_utils.tests import AssertNumQueriesSubTestMixin


    class MyTest(AssertNumQueriesSubTestMixin, TestCase):
        def my_test(self):
            with self.assertNumQueries(2):
                MyModel.objects.count()

            # the assertion above will fail but this line will be executed
            print('This will be printed anyway.')

Quality Assurance Checks
------------------------

This package contains some common QA checks that are used in the
automated builds of different OpenWISP modules.

``openwisp-qa-format``
^^^^^^^^^^^^^^^^^^^^^^

This shell script automatically formats Python and CSS code according
to the `OpenWISP coding style conventions <https://openwisp.io/docs/developer/contributing.html#coding-style-conventions>`_.

It runs ``isort`` and ``black`` to format python code
(these two dependencies are required and installed automatically when running
``pip install openwisp-utils[qa]``).

The ``stylelint`` and ``jshint`` programs are used to perform style checks on CSS and JS code respectively, but they are optional:
if ``stylelint`` and/or ``jshint`` are not installed, the check(s) will be skipped.

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
* ``csslinter`` - Formats and checks CSS code using stylelint common standard
* ``jslinter`` - Checks Javascript code using jshint common standard

If a check requires a flag, it can be passed forward in the same way.

Usage example::

    openwisp-qa-check --migration-path <path> --message <commit-message>

Any unneeded checks can be skipped by passing ``--skip-<check-name>``

Usage example::

    openwisp-qa-check --skip-isort

For backward compatibility ``csslinter`` and ``jslinter`` are skipped by default.
To run them in checks pass arguements in this way.

Usage example::

    # To activate csslinter
    openwisp-qa-check --csslinter

    # To activate jslinter
    openwisp-qa-check --jslinter

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

``OPENWISP_ADMIN_DASHBOARD_ENABLED``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**default**: ``False``

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

Installing for development
--------------------------

Install the system dependencies:

.. code-block:: shell

    sudo apt-get install sqlite3 libsqlite3-dev

    # For running E2E Selenium tests
    sudo apt install chromium

Install your forked repo:

.. code-block:: shell

    git clone git://github.com/<your_fork>/openwisp-utils
    cd openwisp-utils/
    pip install -e .[qa,rest]

Install test requirements:

.. code-block:: shell

    pip install -r requirements-test.txt

Install node dependencies used for testing:

.. code-block:: shell

    npm install -g stylelint jshint

Set up the pre-push hook to run tests and QA checks automatically right before the git push action, so that if anything fails the push operation will be aborted:

.. code-block:: shell

    openwisp-pre-push-hook --install

Install WebDriver for Chromium for your browser version from `<https://chromedriver.chromium.org/home>`_
and Extract ``chromedriver`` to one of directories from your ``$PATH`` (example: ``~/.local/bin/``).

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
