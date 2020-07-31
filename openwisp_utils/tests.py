from contextlib import contextmanager
from time import time
from unittest import TextTestResult, mock

from django.conf import settings
from django.test.runner import DiscoverRunner

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
            f'\nSummary of slow tests (>{self.slow_test_threshold[0]}s)\n',
            'white_bold',
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
