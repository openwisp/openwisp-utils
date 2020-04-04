from django.dispatch import Signal
from django.test import TestCase
from openwisp_utils.tests import catch_signal

status_signal = Signal(providing_args=['status'])


class TestUtils(TestCase):
    def _generate_signal(self):
        status_signal.send(sender=self,
                           status='working')

    def test_status_signal_emitted(self):
        with catch_signal(status_signal) as handler:
            self._generate_signal()
        handler.assert_called_once_with(
            status='working',
            sender=self,
            signal=status_signal,
        )
