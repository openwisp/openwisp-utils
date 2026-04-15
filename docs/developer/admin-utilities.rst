Admin Utilities
===============

.. include:: ../partials/developer-docs.rst

.. contents:: **Table of Contents**:
    :depth: 2
    :local:

``openwisp_utils.admin.TimeReadonlyAdminMixin``
-----------------------------------------------

Admin mixin which adds two read only fields ``created`` and ``modified``.

This is an admin mixin for models inheriting ``TimeStampedEditableModel``
which adds the fields ``created`` and ``modified`` to the database.

``openwisp_utils.admin.ReadOnlyAdmin``
--------------------------------------

A read-only ``ModelAdmin`` base class.

Will include the ``id`` field by default, which can be excluded by
supplying the ``exclude`` attribute, e.g.:

.. code-block:: python

    from openwisp_utils.admin import ReadOnlyAdmin


    class PostAuthReadOnlyAdmin(ReadOnlyAdmin):
        exclude = ["id"]

``openwisp_utils.admin.AlwaysHasChangedMixin``
----------------------------------------------

A mixin designed for inline items and model forms, ensures the item is
created even if the default values are unchanged.

Without this, when creating new objects, inline items won't be saved
unless users change the default values.

``openwisp_utils.admin.CopyableFieldsAdmin``
--------------------------------------------

An admin class that allows to set admin fields to be read-only and makes
it easy to copy the fields contents.

Useful for auto-generated fields such as UUIDs, secret keys, tokens, etc.

``openwisp_utils.admin.ReceiveUrlAdmin``
----------------------------------------

An admin class that provides an URL as a read-only input field (to make it
easy and quick to copy/paste).

``openwisp_utils.admin.HelpTextStackedInline``
----------------------------------------------

.. figure:: https://github.com/openwisp/openwisp-utils/raw/media/docs/help-text-stacked-inline.png
    :align: center

A stacked inline admin class that displays a help text for entire inline
object. Following is an example:

.. code-block:: python

    from openwisp_utils.admin import HelpTextStackedInline


    class SubnetDivisionRuleInlineAdmin(
        MultitenantAdminMixin, TimeReadonlyAdminMixin, HelpTextStackedInline
    ):
        model = Model
        # It is required to set "help_text" attribute
        help_text = {
            # (required) Help text to display
            "text": _(
                "Please keep in mind that once the subnet division rule is created "
                'and used, changing "Size" and "Number of Subnets" and decreasing '
                '"Number of IPs" will not be possible.'
            ),
            # (optional) You can provide a link to documentation for user reference
            "documentation_url": ("https://github.com/openwisp/openwisp-utils"),
            # (optional) Icon to be shown along with help text. By default it uses
            # "/static/admin/img/icon-alert.svg"
            "image_url": "/static/admin/img/icon-alert.svg",
        }

``openwisp_utils.admin_theme.filters.InputFilter``
--------------------------------------------------

The ``admin_theme`` sub app of this package provides an input filter that
can be used in the *changelist* page to filter ``UUIDField`` or
``CharField``.

Code example:

.. code-block:: python

    from django.contrib import admin
    from openwisp_utils.admin_theme.filters import InputFilter
    from my_app.models import MyModel


    @admin.register(MyModel)
    class MyModelAdmin(admin.ModelAdmin):
        list_filter = [
            ("my_field", InputFilter),
            "other_field",
            # ...
        ]

By default ``InputFilter`` use exact lookup to filter items which matches
to the value being searched by the user. But this behavior can be changed
by modifying ``InputFilter`` as following:

.. code-block:: python

    from django.contrib import admin
    from openwisp_utils.admin_theme.filters import InputFilter
    from my_app.models import MyModel


    class MyInputFilter(InputFilter):
        lookup = "icontains"


    @admin.register(MyModel)
    class MyModelAdmin(admin.ModelAdmin):
        list_filter = [
            ("my_field", MyInputFilter),
            "other_field",
            # ...
        ]

To know about other lookups that can be used please check `Django Lookup
API Reference
<https://docs.djangoproject.com/en/4.2/ref/models/lookups/#django.db.models.Lookup>`__

``openwisp_utils.admin_theme.filters.SimpleInputFilter``
--------------------------------------------------------

A stripped down version of
``openwisp_utils.admin_theme.filters.InputFilter`` that provides
flexibility to customize filtering. It can be used to filter objects using
indirectly related fields.

The derived filter class should define the ``queryset`` method as shown in
following example:

.. code-block:: python

    from django.contrib import admin
    from openwisp_utils.admin_theme.filters import SimpleInputFilter
    from my_app.models import MyModel


    class MyInputFilter(SimpleInputFilter):
        parameter_name = "shelf"
        title = _("Shelf")

        def queryset(self, request, queryset):
            if self.value() is not None:
                return queryset.filter(name__icontains=self.value())


    @admin.register(MyModel)
    class MyModelAdmin(admin.ModelAdmin):
        list_filter = [
            MyInputFilter,
            "other_field",
            # ...
        ]

``openwisp_utils.admin_theme.filters.AutocompleteFilter``
---------------------------------------------------------

The ``admin_theme`` sub app of this package provides an auto complete
filter that uses the *django-autocomplete* widget to load filter data
asynchronously.

This filter can be helpful when the number of objects is too large to load
all at once which may cause the slow loading of the page.

.. code-block:: python

    from django.contrib import admin
    from openwisp_utils.admin_theme.filters import AutocompleteFilter
    from my_app.models import MyModel, MyOtherModel


    class MyAutoCompleteFilter(AutocompleteFilter):
        field_name = "field"
        parameter_name = "field_id"
        title = _("My Field")


    @admin.register(MyModel)
    class MyModelAdmin(admin.ModelAdmin):
        list_filter = [MyAutoCompleteFilter, ...]


    @admin.register(MyOtherModel)
    class MyOtherModelAdmin(admin.ModelAdmin):
        search_fields = ["id"]

To customize or know more about it, please refer to the
`django-admin-autocomplete-filter documentation
<https://github.com/farhan0581/django-admin-autocomplete-filter#usage>`_.

Customizing the Submit Row in OpenWISP Admin
--------------------------------------------

In the OpenWISP admin interface, the ``submit_line.html`` template
controls the rendering of action buttons in the model form's submit row.
OpenWISP Utils extends this template to allow the addition of custom
buttons.

To add custom buttons, you can use the ``additional_buttons`` context
variable. This variable should be a list of dictionaries, each
representing a button with customizable properties such as type, class,
value, title, URL, or even raw HTML content.

Here's an example of adding a custom button with both standard properties
and raw HTML to the submit row in the ``change_view`` method:

.. code-block:: python

    from django.contrib import admin
    from django.utils.safestring import mark_safe
    from .models import MyModel


    @admin.register(MyModel)
    class MyModelAdmin(admin.ModelAdmin):
        def change_view(self, request, object_id, form_url="", extra_context=None):
            extra_context = extra_context or {}
            extra_context["additional_buttons"] = [
                {
                    "type": "button",
                    "class": "btn btn-secondary",
                    "value": "Custom Action",
                    "title": "Perform a custom action",
                    "url": "https://example.com",
                },
                {
                    "raw_html": mark_safe(
                        '<button type="button" class="btn btn-warning" '
                        "onclick=\"alert('This is a raw HTML button!')\">"
                        "Raw HTML Button</button>"
                    )
                },
            ]
            return super().change_view(request, object_id, form_url, extra_context)

In this example, two buttons are added to the submit row:

1. A standard button labeled "Custom Action" with a link to
   `https://example.com`.
2. A button rendered using raw HTML that triggers an alert when clicked,
   labeled "Raw HTML Button." The raw HTML is wrapped in `mark_safe` to
   ensure it is rendered correctly.

The `mark_safe` function is necessary to ensure that the raw HTML is
rendered as HTML and not escaped as plain text.
