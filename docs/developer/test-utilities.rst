Test Utilities
==============

.. include:: ../partials/developer-docs.rst

.. contents:: **Table of Contents**:
    :depth: 2
    :local:

``openwisp_utils.tests.catch_signal``
-------------------------------------

This method can be used to mock a signal call in order to easily verify
that the signal has been called.

Usage example as a context-manager:

.. code-block:: python

    from openwisp_utils.tests import catch_signal

    with catch_signal(openwisp_signal) as handler:
        model_instance.trigger_signal()
        handler.assert_called_once_with(
            arg1="value1",
            arg2="value2",
            sender=ModelName,
            signal=openwisp_signal,
        )

.. _utils_time_logging_test_runner:

``openwisp_utils.tests.TimeLoggingTestRunner``
----------------------------------------------

.. figure:: https://raw.githubusercontent.com/openwisp/openwisp-utils/media/docs/TimeLoggingTestRunner.png
    :align: center

This class extends the `default test runner provided by Django
<https://docs.djangoproject.com/en/4.2/ref/settings/#std:setting-TEST_RUNNER>`_
and logs the time spent by each test, making it easier to spot slow tests
by highlighting time taken by it in yellow (time shall be highlighted in
red if it crosses the second threshold).

By default tests are considered slow if they take more than 0.3 seconds
but you can control this with :ref:`OPENWISP_SLOW_TEST_THRESHOLD
<openwisp_slow_test_threshold>`.

In order to switch to this test runner you have set the following in your
`settings.py`:

.. code-block:: python

    TEST_RUNNER = "openwisp_utils.tests.TimeLoggingTestRunner"

``openwisp_utils.tests.capture_stdout``
---------------------------------------

This decorator can be used to capture standard output produced by tests,
either to silence it or to write assertions.

Example usage:

.. code-block:: python

    from openwisp_utils.tests import capture_stdout


    @capture_stdout()
    def test_something(self):
        function_generating_output()  # pseudo code


    @capture_stdout()
    def test_something_again(self, captured_ouput):
        # pseudo code
        function_generating_output()
        # now you can create assertions on the captured output
        self.assertIn("expected stdout", captured_ouput.getvalue())
        # if there are more than one assertions, clear the captured output first
        captured_error.truncate(0)
        captured_error.seek(0)
        # you can create new assertion now
        self.assertIn("another output", captured_ouput.getvalue())

**Notes**:

- If assertions need to be made on the captured output, an additional
  argument (in the example above is named ``captured_output``) can be
  passed as an argument to the decorated test method, alternatively it can
  be omitted.
- A ``StingIO`` instance is used for capturing output by default but if
  needed it's possible to pass a custom ``StringIO`` instance to the
  decorator function.

``openwisp_utils.tests.capture_stderr``
---------------------------------------

Equivalent to ``capture_stdout``, but for standard error.

Example usage:

.. code-block:: python

    from openwisp_utils.tests import capture_stderr


    @capture_stderr()
    def test_error(self):
        function_generating_error()  # pseudo code


    @capture_stderr()
    def test_error_again(self, captured_error):
        # pseudo code
        function_generating_error()
        # now you can create assertions on captured error
        self.assertIn("expected error", captured_error.getvalue())
        # if there are more than one assertions, clear the captured error first
        captured_error.truncate(0)
        captured_error.seek(0)
        # you can create new assertion now
        self.assertIn("another expected error", captured_error.getvalue())

``openwisp_utils.tests.capture_any_output``
-------------------------------------------

Equivalent to ``capture_stdout`` and ``capture_stderr``, but captures both
types of output (standard output and standard error).

Example usage:

.. code-block:: python

    from openwisp_utils.tests import capture_any_output


    @capture_any_output()
    def test_something_out(self):
        function_generating_output()  # pseudo code


    @capture_any_output()
    def test_out_again(self, captured_output, captured_error):
        # pseudo code
        function_generating_output_and_errors()
        # now you can create assertions on captured error
        self.assertIn("expected stdout", captured_output.getvalue())
        self.assertIn("expected stderr", captured_error.getvalue())

``openwisp_utils.tests.AssertNumQueriesSubTestMixin``
-----------------------------------------------------

This mixin overrides the `assertNumQueries
<https://docs.djangoproject.com/en/4.2/topics/testing/tools/#django.test.TransactionTestCase.assertNumQueries>`_
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
            print("This will be printed anyway.")

``openwisp_utils.tests.SeleniumTestMixin``
------------------------------------------

This mixin provides the core Selenium setup logic and reusable test
methods that must be used across all OpenWISP modules based on Django to
enforce best practices and avoid flaky tests.

It includes a built-in retry mechanism that can automatically repeat
failing tests to identify transient (flaky) failures. You can customize
this behavior using the following class attributes:

- ``retry_max``: The maximum number of times to retry a failing test.
  Defaults to ``5``.
- ``retry_delay``: The number of seconds to wait between retries. Defaults
  to ``0``.
- ``retry_threshold``: The minimum ratio of successful retries required
  for the test to be considered as passed. If the success ratio falls
  below this threshold, the test is marked as failed. Defaults to ``0.8``.

**Example usage:**

.. code-block:: python

    from openwisp_utils.tests import SeleniumTestMixin
    from django.contrib.staticfiles.testing import StaticLiveServerTestCase


    class MySeleniumTest(SeleniumTestMixin, StaticLiveServerTestCase):
        retry_max = 10
        retry_delay = 0
        retry_threshold = 0.9

        def test_something(self):
            self.open("/some-url/")
            # Your test logic here

.. _selenium_dependencies:

Selenium Dependencies
~~~~~~~~~~~~~~~~~~~~~

Running browser tests with Selenium requires that both ``geckodriver`` and
``chromedriver`` are installed locally.

1. Download the appropriate ``geckodriver`` and ``chromedriver`` for your
   OS and architecture (e.g., ``linux-64``).
2. Extract the downloaded files.
3. Make the programs available on your system by copying the executable
   files to a directory included in your ``PATH``. For example, on a
   typical Linux system, this could be ``/usr/local/bin/geckodriver`` and
   ``/usr/local/bin/chromedriver``.

The Python dependencies for running Selenium tests are included as extra
dependencies in ``openwisp-utils`` (``openwisp-utils[selenium]``). These
should be automatically installed when setting up the development
environment. All the OpenWISP modules using ``SeleniumTestMixin`` are
already depending on ``openwisp-utils[selenium]``.

Methods
~~~~~~~

- ``setUpClass()`` (``@classmethod``): Initializes the Selenium WebDriver
  with Firefox and applies custom settings to improve test reliability. -
  Uses the ``SELENIUM_HEADLESS`` environment variable to determine whether
  to run in headless mode. - Uses the ``GECKO_BIN`` environment variable
  to specify a custom Firefox binary location. - Uses the ``GECKO_LOG``
  environment variable to enable GeckoDriver logging to
  ``geckodriver.log``. - Configures preferences to disable hardware
  acceleration and increase timeouts.
- ``tearDownClass()`` (``@classmethod``): Quits the Selenium WebDriver to
  clean up resources after the test class has finished executing.
- ``open(url, driver=None, timeout=5)``: Opens a URL in the browser. -
  Waits for the page to fully load before returning. - Ensures the
  ``#main-content`` element is present before proceeding.
- ``login(username=None, password=None, driver=None)``: Logs into the
  Django admin dashboard. - Defaults to using ``admin`` / ``password``
  credentials. - Navigates to ``/admin/login/`` and fills in the login
  form.
- ``find_element(by, value, timeout=2, wait_for='visibility')``: Finds an
  element using Selenium's ``find_element`` method. - Waits for the
  element based on the specified ``wait_for`` condition (``visibility``,
  ``presence``).
- ``wait_for_visibility(by, value, timeout=2)``: Waits until an element is
  visible.
- ``wait_for_invisibility(by, value, timeout=2)``: Waits until an element
  is no longer visible.
- ``wait_for_presence(by, value, timeout=2)``: Waits until an element is
  present in the DOM.
- ``wait_for(method, by, value, timeout=2)``: General method for waiting
  for an element based on a given condition. - Uses Selenium's
  ``WebDriverWait`` and Expected Conditions (``EC``). - If the timeout is
  reached, the test fails with a descriptive error message.
