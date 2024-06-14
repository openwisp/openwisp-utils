REST API Utilities
------------------

.. include:: ../partials/developer-docs.rst

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
