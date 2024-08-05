OpenWISP Dashboard
==================

.. include:: ../partials/developer-docs.rst

The ``admin_theme`` sub app of this package provides an admin dashboard
for OpenWISP which can be manipulated with the functions described in the
next sections.

Example taken from the :doc:`Controller Module </controller/index>`:

.. figure:: https://raw.githubusercontent.com/openwisp/openwisp-utils/media/docs/dashboard2.png
    :target: https://raw.githubusercontent.com/openwisp/openwisp-utils/media/docs/dashboard2.png
    :align: center

.. contents:: **Table of Contents**:
    :depth: 2
    :local:

``register_dashboard_template``
-------------------------------

Allows including a specific django template in the OpenWISP dashboard.

It is designed to allow the inclusion of the geographic map shipped by
:doc:`OpenWISP Monitoring </monitoring/index>` but can be used to include
any custom element in the dashboard.

.. note::

    It is possible to register templates to be loaded before or after
    charts using the ``after_charts`` keyword argument (see below).

**Syntax:**

.. code-block:: python

    register_dashboard_template(position, config)

================ =======================================================
**Parameter**    **Description**
``position``     (``int``) The position of the template.
``config``       (``dict``) The configuration of the template.
``extra_config`` **optional** (``dict``) Extra configuration you want to
                 pass to custom template.
``after_charts`` **optional** (``bool``) Whether the template should be
                 loaded after dashboard charts. Defaults to ``False``,
                 i.e. templates are loaded before dashboard charts by
                 default.
================ =======================================================

Following properties can be configured for each template ``config``:

============ ========================================================
**Property** **Description**
``template`` (``str``) Path to pass to the template loader.
``css``      (``tuple``) List of CSS files to load in the HTML page.
``js``       (``tuple``) List of Javascript files to load in the HTML
             page.
============ ========================================================

Code example:

.. code-block:: python

    from openwisp_utils.admin_theme import register_dashboard_template

    register_dashboard_template(
        position=0,
        config={
            "template": "admin/dashboard/device_map.html",
            "css": (
                "monitoring/css/device-map.css",
                "leaflet/leaflet.css",
                "monitoring/css/leaflet.fullscreen.css",
            ),
            "js": (
                "monitoring/js/device-map.js",
                "leaflet/leaflet.js",
                "leaflet/leaflet.extras.js",
                "monitoring/js/leaflet.fullscreen.min.js",
            ),
        },
        extra_config={
            "optional_variable": "any_valid_value",
        },
        after_charts=True,
    )

It is recommended to register dashboard templates from the ``ready``
method of the AppConfig of the app where the templates are defined.

``unregister_dashboard_template``
---------------------------------

This function can be used to remove a template from the dashboard.

**Syntax:**

.. code-block:: python

    unregister_dashboard_template(template_name)

================= =============================================
**Parameter**     **Description**
``template_name`` (``str``) The name of the template to remove.
================= =============================================

Code example:

.. code-block:: python

    from openwisp_utils.admin_theme import unregister_dashboard_template

    unregister_dashboard_template("admin/dashboard/device_map.html")

An ``ImproperlyConfigured`` exception is raised the specified dashboard
template is not registered.

``register_dashboard_chart``
----------------------------

Adds a chart to the OpenWISP dashboard.

At the moment only pie charts are supported.

The code works by defining the type of query which will be executed, and
optionally, how the returned values have to be colored and labeled.

**Syntax:**

.. code-block:: python

    register_dashboard_chart(position, config)

============= ==================================
**Parameter** **Description**
``position``  (``int``) Position of the chart.
``config``    (``dict``) Configuration of chart.
============= ==================================

Following properties can be configured for each chart ``config``:

================ =========================================================
**Property**     **Description**
``query_params`` It is a required property in form of ``dict``. Refer to
                 the :ref:`utils_dashboard_chart_query_params` table below
                 for supported properties.
``colors``       An **optional** ``dict`` which can be used to define
                 colors for each distinct value shown in the pie charts.
``labels``       An **optional** ``dict`` which can be used to define
                 translatable strings for each distinct value shown in the
                 pie charts. Can be used also to provide fallback human
                 readable values for raw values stored in the database
                 which would be otherwise hard to understand for the user.
``filters``      An **optional** ``dict`` which can be used when using
                 ``aggregate`` and ``annotate`` in ``query_params`` to
                 define the link that will be generated to filter results
                 (pie charts are clickable and clicking on a portion of it
                 will show the filtered results).
``main_filters`` An **optional** ``dict`` which can be used to add
                 additional filtering on the target link.
``filtering``    An **optional** ``str`` which can be set to ``'False'``
                 (str) to disable filtering on target links. This is
                 useful when clicking on any section of the chart should
                 take user to the same URL.
``quick_link``   An **optional** ``dict`` which contains configuration for
                 the quick link button rendered below the chart. Refer to
                 the :ref:`dashboard_chart_quick_link` table below for
                 supported properties.

                 **Note**: The chart legend is disabled if configuration
                 for quick link button is provided.
================ =========================================================

.. _utils_dashboard_chart_query_params:

Dashboard Chart ``query_params``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

====================== ===================================================
**Property**           **Description**
``name``               (``str``) Chart title shown in the user interface.
``app_label``          (``str``) App label of the model that will be used
                       to query the database.
``model``              (``str``) Name of the model that will be used to
                       query the database.
``group_by``           (``str``) The property which will be used to group
                       values.
``annotate``           Alternative to ``group_by``, ``dict`` used for more
                       complex queries.
``aggregate``          Alternative to ``group_by``, ``dict`` used for more
                       complex queries.
``filter``             ``dict`` used for filtering queryset.
``organization_field`` (``str``) If the model does not have a direct
                       relation with the ``Organization`` model, then
                       indirect relation can be specified using this
                       property. E.g.: ``device__organization_id``.
====================== ===================================================

.. _dashboard_chart_quick_link:

Dashboard chart ``quick_link``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

====================== =================================================
**Property**           **Description**
``url``                (``str``) URL for the anchor tag
``label``              (``str``) Label shown on the button
``title``              (``str``) Title attribute of the button element
``custom_css_classes`` (``list``) List of CSS classes that'll be applied
                       on the button
====================== =================================================

Code example:

.. code-block:: python

    from openwisp_utils.admin_theme import register_dashboard_chart

    register_dashboard_chart(
        position=1,
        config={
            "query_params": {
                "name": "Operator Project Distribution",
                "app_label": "test_project",
                "model": "operator",
                "group_by": "project__name",
            },
            "colors": {"Utils": "red", "User": "orange"},
            "quick_link": {
                "url": "/admin/test_project/operator",
                "label": "Open Operators list",
                "title": "View complete list of operators",
                "custom_css_classes": ["negative-top-20"],
            },
        },
    )

For real world examples, look at the code of :doc:`OpenWISP Controller
</controller/index>` and :doc:`OpenWISP Monitoring </monitoring/index>`.

An ``ImproperlyConfigured`` exception is raised if a dashboard element is
already registered at same position.

It is recommended to register dashboard charts from the ``ready`` method
of the AppConfig of the app where the models are defined. Checkout `app.py
of the test_project
<https://github.com/openwisp/openwisp-utils/blob/master/tests/test_project/apps.py>`_
for reference.

``unregister_dashboard_chart``
------------------------------

This function can used to remove a chart from the dashboard.

**Syntax:**

.. code-block:: python

    unregister_dashboard_chart(chart_name)

============== ==========================================
**Parameter**  **Description**
``chart_name`` (``str``) The name of the chart to remove.
============== ==========================================

Code example:

.. code-block:: python

    from openwisp_utils.admin_theme import unregister_dashboard_chart

    unregister_dashboard_chart("Operator Project Distribution")

An ``ImproperlyConfigured`` exception is raised the specified dashboard
chart is not registered.
