Main Navigation Menu
====================

.. include:: ../partials/developer-docs.rst

.. contents:: **Table of Contents**:
    :depth: 2
    :local:

The ``admin_theme`` sub app of this package provides a navigation menu
that can be manipulated with the functions described in the next sections.

Context Processor
-----------------

For this feature to work, we must make sure that the context processor
``openwisp_utils.admin_theme.context_processor.menu_groups`` is enabled in
``settings.py`` as shown below.

.. code-block:: python

    TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "OPTIONS": {
                "loaders": [
                    # ... omitted ...
                ],
                "context_processors": [
                    # ... other context processors ...
                    "openwisp_utils.admin_theme.context_processor.menu_groups"  # <----- add this
                ],
            },
        },
    ]

This context processor is enabled by default in any OpenWISP installer and
in the test project of this module.

The ``register_menu_group`` function
------------------------------------

Allows registering a new menu item or group at the specified position in
the Main Navigation Menu.

**Syntax:**

.. code-block:: python

    register_menu_group(position, config)

============= ==============================================
**Parameter** **Description**
``position``  (``int``) Position of the group or item.
``config``    (``dict``) Configuration of the group or item.
============= ==============================================

Code example:

.. code-block:: python

    from django.utils.translation import ugettext_lazy as _
    from openwisp_utils.admin_theme.menu import register_menu_group

    register_menu_group(
        position=1,
        config={
            "label": _("My Group"),
            "items": {
                1: {
                    "label": _("Users List"),
                    "model": "auth.User",
                    "name": "changelist",
                    "icon": "list-icon",
                },
                2: {
                    "label": _("Add User"),
                    "model": "auth.User",
                    "name": "add",
                    "icon": "add-icon",
                },
            },
            "icon": "user-group-icon",
        },
    )
    register_menu_group(
        position=2,
        config={
            "model": "test_project.Shelf",
            "name": "changelist",
            "label": _("View Shelf"),
            "icon": "shelf-icon",
        },
    )
    register_menu_group(
        position=3, config={"label": _("My Link"), "url": "https://link.com"}
    )

An ``ImproperlyConfigured`` exception is raised if a menu element is
already registered at the same position.

An ``ImproperlyConfigured`` exception is raised if the supplied
configuration does not match with the different types of possible
configurations available (different configurations will be discussed in
the next section).

.. note::

    It is recommended to use ``register_menu_group`` in the ``ready``
    method of the ``AppConfig``.

.. important::

    ``register_menu_items`` is obsoleted by ``register_menu_group`` and
    will be removed in future versions. Links added using
    ``register_menu_items`` will be shown at the top of navigation menu
    and above any ``register_menu_group`` items.

Adding a Custom Link
~~~~~~~~~~~~~~~~~~~~

To add a link that contains a custom URL the following syntax can be used.

**Syntax:**

.. code-block:: python

    register_menu_group(
        position=1,
        config={"label": "Link Label", "url": "link_url", "icon": "my-icon"},
    )

Following is the description of the configuration:

============= ============================================================
**Parameter** **Description**
``label``     (``str``) Display text for the link.
``url``       (``str``) URL for the link.
``icon``      An **optional** ``str`` CSS class name for the icon. No icon
              is displayed if not provided.
============= ============================================================

Adding a Model Link
~~~~~~~~~~~~~~~~~~~

To add a link that contains URL of add form or change list page of a model
then following syntax can be used. Users will only be able to see links
for models they have permission to either view or edit.

**Syntax:**

.. code-block:: python

    # add a link of list page
    register_menu_group(
        position=1,
        config={
            "model": "my_project.MyModel",
            "name": "changelist",
            "label": "MyModel List",
            "icon": "my-model-list-class",
        },
    )

    # add a link of add page
    register_menu_group(
        position=2,
        config={
            "model": "my_project.MyModel",
            "name": "add",
            "label": "MyModel Add Item",
            "icon": "my-model-add-class",
        },
    )

Following is the description of the configuration:

============= ============================================================
**Parameter** **Description**
``model``     (``str``) Model of the app for which you to add link.
``name``      (``str``) argument name, e.g.: *changelist* or *add*.
``label``     An **optional** ``str`` display text for the link. It is
              automatically generated if not provided.
``icon``      An **optional** ``str`` CSS class name for the icon. No icon
              is displayed if not provided.
============= ============================================================

Adding a Menu Group
~~~~~~~~~~~~~~~~~~~

To add a nested group of links in the menu the following syntax can be
used. It creates a dropdown in the menu.

**Syntax:**

.. code-block:: python

    register_menu_group(
        position=1,
        config={
            "label": "My Group Label",
            "items": {
                1: {
                    "label": "Link Label",
                    "url": "link_url",
                    "icon": "my-icon",
                },
                2: {
                    "model": "my_project.MyModel",
                    "name": "changelist",
                    "label": "MyModel List",
                    "icon": "my-model-list-class",
                },
            },
            "icon": "my-group-icon-class",
        },
    )

Following is the description of the configuration:

============= ============================================================
**Parameter** **Description**
``label``     (``str``) Display name for the link.
``items``     (``dict``) Items to be displayed in the dropdown. It can be
              a dict of custom links or model links with key as their
              position in the group.
``icon``      An **optional** ``str`` CSS class name for the icon. No icon
              is displayed if not provided.
============= ============================================================

The ``register_menu_subitem`` function
--------------------------------------

Allows adding an item to a registered group.

**Syntax:**

.. code-block:: python

    register_menu_subitem(group_position, item_position, config)

================== =======================================================
**Parameter**      **Description**
``group_position`` (``int``) Position of the group in which item should be
                   added.
``item_position``  (``int``) Position at which item should be added in the
                   group
``config``         (``dict``) Configuration of the item.
================== =======================================================

Code example:

.. code-block:: python

    from django.utils.translation import ugettext_lazy as _
    from openwisp_utils.admin_theme.menu import register_menu_subitem

    # To register a model link
    register_menu_subitem(
        group_position=10,
        item_position=2,
        config={
            "label": _("Users List"),
            "model": "auth.User",
            "name": "changelist",
            "icon": "list-icon",
        },
    )

    # To register a custom link
    register_menu_subitem(
        group_position=10,
        item_position=2,
        config={"label": _("My Link"), "url": "https://link.com"},
    )

An ``ImproperlyConfigured`` exception is raised if the group is not
already registered at ``group_position``.

An ``ImproperlyConfigured`` exception is raised if the group already has
an item registered at ``item_position``.

It is only possible to register links to specific models or custom URL. An
``ImproperlyConfigured`` exception is raised if the configuration of group
is provided in the function.

.. important::

    It is recommended to use ``register_menu_subitem`` in the ``ready``
    method of the ``AppConfig``.

How to Use Custom Icons in the Menu
-----------------------------------

Create a CSS file and use the following syntax to provide the image for
each icon used in the menu. The CSS class name should be the same as the
``icon`` parameter used in the configuration of a menu item or group. Also
icon being used should be in ``svg`` format.

Example:

.. code-block:: css

    .icon-class-name {
        mask-image: url(imageurl);
        -webkit-mask-image: url(imageurl);
    }

Follow the instructions in :ref:`Supplying custom CSS and JS for the admin
theme <utils_custom_admin_theme>` to know how to configure your OpenWISP
instance to load custom CSS files.
