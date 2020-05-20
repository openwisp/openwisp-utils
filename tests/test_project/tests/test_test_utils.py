from django.dispatch import Signal
from django.test import TestCase
from openwisp_utils.tests import catch_signal
from openwisp_utils.utils import deep_merge_dicts

status_signal = Signal(providing_args=['status'])


class TestUtils(TestCase):
    def _generate_signal(self):
        status_signal.send(sender=self, status='working')

    def test_status_signal_emitted(self):
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
