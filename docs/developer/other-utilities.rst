Other Utilities
===============

.. include:: ../partials/developer-docs.rst

.. contents:: **Table of Contents**:
    :depth: 2
    :local:

Model Utilities
---------------

``openwisp_utils.base.UUIDModel``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Model class which provides a UUID4 primary key.

``openwisp_utils.base.TimeStampedEditableModel``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Model class inheriting ``UUIDModel`` which provides two additional fields:

- ``created``
- ``modified``

Which use respectively ``AutoCreatedField``, ``AutoLastModifiedField``
from ``model_utils.fields`` (self-updating fields providing the creation
date-time and the last modified date-time).

REST API Utilities
------------------

``openwisp_utils.api.serializers.ValidatedModelSerializer``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A model serializer which calls the model instance ``full_clean()``.

Useful to avoid duplicating model validation logic in the REST framework
serializers.

An optional ``exclude_validation`` property with a list of field names can
be supplied to exclude specific fields from validation.

Usage:

.. code-block:: python

    from openwisp_utils.api.serializers import ValidatedModelSerializer


    class BaseConfigSerializer(ValidatedModelSerializer):
        exclude_validation = ["device"]

``openwisp_utils.api.apps.ApiAppConfig``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you're creating an OpenWISP module which provides a REST API built with
Django REST Framework, chances is that you may need to define some default
settings to control its throttling or other aspects.

Here's how to easily do it:

.. code-block:: python

    from django.conf import settings
    from django.utils.translation import ugettext_lazy as _
    from openwisp_utils.api.apps import ApiAppConfig


    class MyModuleConfig(ApiAppConfig):
        name = "my_openwisp_module"
        label = "my_module"
        verbose_name = _("My OpenWISP Module")

        # assumes API is enabled by default
        API_ENABLED = getattr(settings, "MY_OPENWISP_MODULE_API_ENABLED", True)
        # set throttling rates for your module here
        REST_FRAMEWORK_SETTINGS = {
            "DEFAULT_THROTTLE_RATES": {"my_module": "400/hour"},
        }

Every openwisp module which has an API should use this class to configure
its own default settings, which will be merged with the settings of the
other modules.

Storage Utilities
-----------------

.. _utils_compress_static_files_storage:

``openwisp_utils.storage.CompressStaticFilesStorage``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A static storage backend for minification and compression inheriting from
`django-minify-compress-staticfiles's
<https://github.com/openwisp/django-minify-compress-staticfiles>`_
``MinicompressStorage`` class.

Adds support for excluding file types using
:ref:`OPENWISP_STATICFILES_VERSIONED_EXCLUDE
<openwisp_staticfiles_versioned_exclude>` setting.

To use point ``STORAGES["staticfiles"]`` to
``openwisp_utils.storage.CompressStaticFilesStorage`` in ``settings.py``.

.. code-block:: python

    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "openwisp_utils.storage.CompressStaticFilesStorage",
        },
    }

Other Utilities
---------------

``openwisp_utils.utils.get_random_key``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Generates an random string of 32 characters.

``openwisp_utils.utils.deep_merge_dicts``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Returns a new ``dict`` which is the result of the merge of the two
dictionaries, all elements are deep-copied to avoid modifying the original
data structures.

Usage:

.. code-block:: python

    from openwisp_utils.utils import deep_merge_dicts

    mergd_dict = deep_merge_dicts(dict1, dict2)

``openwisp_utils.utils.default_or_test``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the program is being executed during automated tests the value supplied
in the ``test`` argument will be returned, otherwise the one supplied in
the ``value`` argument is returned.

.. code-block:: python

    from openwisp_utils.utils import default_or_test

    THROTTLE_RATE = getattr(
        settings,
        "THROTTLE_RATE",
        default_or_test(value="20/day", test=None),
    )

``openwisp_utils.utils.print_color``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**default colors**: ``['white_bold', 'green_bold', 'yellow_bold',
'red_bold']``

If you want to print a string in ``Red Bold``, you can do it as below.

.. code-block:: python

    from openwisp_utils.utils import print_color

    print_color("This is the printed in Red Bold", color_name="red_bold")

You may also provide the ``end`` argument similar to built-in print
method.

``openwisp_utils.utils.SorrtedOrderedDict``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Extends ``collections.SortedDict`` and implements logic to sort inserted
items based on ``key`` value. Sorting is done at insert operation which
incurs memory space overhead.

.. _utils_openwispcelerytask:

``openwisp_utils.tasks.OpenwispCeleryTask``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A custom celery task class that sets hard and soft time limits of celery
tasks using :ref:`OPENWISP_CELERY_HARD_TIME_LIMIT
<openwisp_celery_hard_time_limit>` and
:ref:`OPENWISP_CELERY_SOFT_TIME_LIMIT <openwisp_celery_soft_time_limit>`
settings respectively.

Usage:

.. code-block:: python

    from celery import shared_task

    from openwisp_utils.tasks import OpenwispCeleryTask


    @shared_task(base=OpenwispCeleryTask)
    def your_celery_task():
        pass

**Note:** This task class should be used for regular background tasks but
not for complex background tasks which can take a long time to execute
(e.g.: firmware upgrades, network operations with retry mechanisms).

``openwisp_utils.utils.retryable_request``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A utility function for making HTTP requests with built-in retry logic.
This function is useful for handling transient errors encountered during
HTTP requests by automatically retrying failed requests with exponential
backoff. It provides flexibility in configuring various retry parameters
to suit different use cases.

Usage:

.. code-block:: python

    from openwisp_utils.utils import retryable_request

    response = retryable_request(
        method="GET",
        url="https://openwisp.org",
        timeout=(4, 8),
        max_retries=3,
        backoff_factor=1,
        backoff_jitter=0.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=(
            "HEAD",
            "GET",
            "PUT",
            "DELETE",
            "OPTIONS",
            "TRACE",
            "POST",
        ),
        retry_kwargs=None,
        headers={"Authorization": "Bearer token"},
    )

**Paramters:**

- ``method`` (str): The HTTP method to be used for the request in lower
  case (e.g., 'get', 'post', etc.).
- ``timeout`` (tuple): A tuple containing two elements: connection timeout
  and read timeout in seconds (default: (4, 8)).
- ``max_retries`` (int): The maximum number of retry attempts in case of
  request failure (default: 3).
- ``backoff_factor`` (float): A factor by which the retry delay increases
  after each retry (default: 1).
- ``backoff_jitter`` (float): A jitter to apply to the backoff factor to
  prevent retry storms (default: 0.0).
- ``status_forcelist`` (tuple): A tuple of HTTP status codes for which
  retries should be attempted (default: (429, 500, 502, 503, 504)).
- ``allowed_methods`` (tuple): A tuple of HTTP methods that are allowed
  for the request (default: ('HEAD', 'GET', 'PUT', 'DELETE', 'OPTIONS',
  'TRACE', 'POST')).
- ``retry_kwargs`` (dict): Additional keyword arguments to be passed to
  the retry mechanism (default: None).
- ``**kwargs``: Additional keyword arguments to be passed to the
  underlying request method (e.g. 'headers', etc.).

This method will raise a ``requests.exceptions.RetryError`` if the request
remains unsuccessful even after all retry attempts have been exhausted.
This exception indicates that the operation could not be completed
successfully despite the retry mechanism.
