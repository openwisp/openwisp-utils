Code utilities
--------------

.. include:: /partials/developers-docs-warning.rst

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

``openwisp_utils.utils.retryable_request``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A utility function for making HTTP requests with built-in retry logic.
This function is useful for handling transient errors encountered during HTTP
requests by automatically retrying failed requests with exponential backoff.
It provides flexibility in configuring various retry parameters to suit
different use cases.

Usage:

.. code-block:: python

    from openwisp_utils.utils import retryable_request

    response = retryable_request(
        method='GET',
        url='https://openwisp.org',
        timeout=(4, 8),
        max_retries=3,
        backoff_factor=1,
        backoff_jitter=0.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=('HEAD', 'GET', 'PUT', 'DELETE', 'OPTIONS', 'TRACE', 'POST'),
        retry_kwargs=None,
        headers={'Authorization': 'Bearer token'}
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
- ``backoff_jitter`` (float): A jitter to apply to the backoff factor to prevent
  retry storms (default: 0.0).
- ``status_forcelist`` (tuple): A tuple of HTTP status codes for which retries
  should be attempted (default: (429, 500, 502, 503, 504)).
- ``allowed_methods`` (tuple): A tuple of HTTP methods that are allowed for
  the request (default: ('HEAD', 'GET', 'PUT', 'DELETE', 'OPTIONS', 'TRACE', 'POST')).
- ``retry_kwargs`` (dict): Additional keyword arguments to be passed to the
  retry mechanism (default: None).
- ``**kwargs``: Additional keyword arguments to be passed to the underlying request
  method (e.g. 'headers', etc.).

Note: This method will raise a requests.exceptions.RetryError if the request
remains unsuccessful even after all retry attempts have been exhausted.
This exception indicates that the operation could not be completed successfully
despite the retry mechanism.
