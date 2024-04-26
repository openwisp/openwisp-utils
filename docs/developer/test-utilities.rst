Test utilities
--------------

.. include:: /partials/developers-docs-warning.rst

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

``openwisp_utils.test_selenium_mixins.SeleniumTestMixin``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This mixin provides basic setup for Selenium tests with method to
open URL and login and logout a user.
