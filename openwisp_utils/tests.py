import io
import sys
from contextlib import contextmanager
from time import time
from unittest import TextTestResult, mock

from django.conf import settings
from django.db import DEFAULT_DB_ALIAS, connections
from django.test.runner import DiscoverRunner
from django.test.utils import CaptureQueriesContext

from .utils import print_color


@contextmanager
def catch_signal(signal):
    """
    Catches django signal and returns mock call for the same
    """
    handler = mock.Mock()
    signal.connect(handler)
    yield handler
    signal.disconnect(handler)


class TimeLoggingTestResult(TextTestResult):
    def __init__(self, *args, **kwargs):
        self.test_timings = []
        self.slow_test_threshold = self._get_slow_test_threshold()
        super().__init__(*args, **kwargs)

    def _get_slow_test_threshold(self):
        slow_test_threshold = getattr(
            settings, 'OPENWISP_SLOW_TEST_THRESHOLD', [0.3, 1]
        )
        assert isinstance(slow_test_threshold, list)
        assert len(slow_test_threshold) == 2
        return slow_test_threshold

    def startTest(self, test):
        self._start_time = time()
        super().startTest(test)

    def addSuccess(self, test):
        elapsed = time() - self._start_time
        name = self.getDescription(test)
        self.test_timings.append((name, elapsed))
        super().addSuccess(test)

    def display_slow_tests(self):
        print_color(
            f'\nSummary of slow tests (>{self.slow_test_threshold[0]}s)\n', 'white_bold'
        )
        self._module = None
        slow_tests_counter = 0
        for name, elapsed in self.test_timings:
            if elapsed > self.slow_test_threshold[0]:
                slow_tests_counter += 1
                # Remove docstring if present
                name = name.split('\n')[0]
                name, module = name.split()
                if module != self._module:
                    self._module = module
                    print_color(f'{module}', 'yellow_bold')
                color = (
                    'red_bold'
                    if elapsed > self.slow_test_threshold[1]
                    else 'yellow_bold'
                )
                print_color(f'  ({elapsed:.2f}s)', color, end=' ')
                print(name)
        print_color(f'\nTotal slow tests detected: {slow_tests_counter}', 'white_bold')
        return self.test_timings

    def stopTestRun(self):
        self.display_slow_tests()
        super().stopTestRun()


class TimeLoggingTestRunner(DiscoverRunner):
    def get_resultclass(self):
        return TimeLoggingTestResult


class CaptureOutput(object):
    def __call__(self, function):
        def wrapped_function(*args, **kwargs):
            if hasattr(self, 'stdout'):
                sys.stdout = self.stdout
            if hasattr(self, 'stderr'):
                sys.stderr = self.stderr
            original_args = list(args)
            args = list(args)
            try:
                if hasattr(self, 'stdout'):
                    args.append(self.stdout)
                if hasattr(self, 'stderr'):
                    args.append(self.stderr)
                function(*args, **kwargs)
            except TypeError:
                function(*original_args, **kwargs)
            finally:
                if hasattr(self, 'stdout'):
                    self.stdout.close()
                    sys.stdout = sys.__stdout__
                if hasattr(self, 'stderr'):
                    self.stderr.close()
                    sys.stderr = sys.__stderr__

        return wrapped_function


class capture_stdout(CaptureOutput):
    def __init__(self, stdout=None, **kwargs):
        self.kwargs = kwargs
        self.stdout = stdout or io.StringIO()


class capture_stderr(CaptureOutput):
    def __init__(self, stderr=None, **kwargs):
        self.kwargs = kwargs
        self.stderr = stderr or io.StringIO()


class capture_any_output(CaptureOutput):
    def __init__(self, stdout=None, stderr=None, **kwargs):
        self.kwargs = kwargs
        self.stdout = stdout or io.StringIO()
        self.stderr = stderr or io.StringIO()


class _AssertNumQueriesContextSubTest(CaptureQueriesContext):
    """
    Needed to execute assertNumQueries in a subTest
    """

    def __init__(self, test_case, num, connection):
        self.test_case = test_case
        self.num = num
        super().__init__(connection)

    def __exit__(self, exc_type, exc_value, traceback):
        super().__exit__(exc_type, exc_value, traceback)
        if exc_type is not None:
            return
        executed = len(self)
        with self.test_case.subTest(f'Expecting {self.num} SQL queries'):
            self.test_case.assertEqual(
                executed,
                self.num,
                "%d queries executed, %d expected\nCaptured queries were:\n%s"
                % (
                    executed,
                    self.num,
                    '\n'.join(
                        '%d. %s' % (i, query['sql'])
                        for i, query in enumerate(self.captured_queries, start=1)
                    ),
                ),
            )


class AssertNumQueriesSubTestMixin:
    def assertNumQueries(self, num, func=None, *args, using=DEFAULT_DB_ALIAS, **kwargs):
        conn = connections[using]

        context = _AssertNumQueriesContextSubTest(self, num, conn)
        if func is None:
            return context

        with context:
            func(*args, **kwargs)
