from django.dispatch import Signal
from django.test import TestCase, override_settings
from django.test.utils import captured_stderr, captured_stdout
from openwisp_utils.tests import TimeLoggingTestRunner, catch_signal
from openwisp_utils.utils import deep_merge_dicts, print_color

status_signal = Signal(providing_args=['status'])


class TestUtils(TestCase):
    def _generate_signal(self):
        status_signal.send(sender=self, status='working')

    def test_status_signal_emitted(self):
        """ Tests the catch_signal test utility function """
        with catch_signal(status_signal) as handler:
            self._generate_signal()
        handler.assert_called_once_with(
            status='working', sender=self, signal=status_signal,
        )

    def test_deep_merge_dicts(self):
        dict1 = {
            'key1': 'value1',
            'key2': {'key2-1': 'value2-1', 'unchanged': 'unchanged'},
            'unchanged': 'unchanged',
        }
        dict2 = {
            'key1': 'value1-final',
            'key2': {'key2-1': 'value2-1-final', 'key2-2': 'value2-2'},
        }
        merged = {
            'key1': 'value1-final',
            'key2': {
                'key2-1': 'value2-1-final',
                'key2-2': 'value2-2',
                'unchanged': 'unchanged',
            },
            'unchanged': 'unchanged',
        }
        self.assertDictEqual(deep_merge_dicts(dict1, dict2), merged)

    @override_settings(OPENWISP_SLOW_TEST_THRESHOLD=[0.0, 0.0])
    def test_time_logging_runner(self):
        runner = TimeLoggingTestRunner()
        suite = runner.build_suite(
            ['test_project.tests.test_test_utils.TestUtils.test_status_signal_emitted'],
        )
        with captured_stdout() as stdout, captured_stderr() as stderr:
            runner.run_suite(suite)
        self.assertIn('slow tests (>0.0s)', stdout.getvalue())
        self.assertIn('Total slow tests detected: 1', stdout.getvalue())
        self.assertIn('Ran 1 test', stderr.getvalue())
        self.assertIn('OK', stderr.getvalue())

    def test_print_color(self):
        with captured_stdout() as stdout:
            print_color('This is the printed in Red Bold', color_name='red_bold')
        expected = '\033[31;1mThis is the printed in Red Bold\033[0m\n'
        self.assertEqual(stdout.getvalue(), expected)
        with captured_stdout() as stdout:
            print_color(
                'This is the printed in Red Bold', color_name='red_bold', end=''
            )
        expected = '\033[31;1mThis is the printed in Red Bold\033[0m'
        self.assertEqual(stdout.getvalue(), expected)
        with captured_stdout() as stdout:
            print_color('This is the printed in Red Bold', color_name='invalid')
        expected = '\033[0mThis is the printed in Red Bold\033[0m\n'
        self.assertEqual(stdout.getvalue(), expected)
