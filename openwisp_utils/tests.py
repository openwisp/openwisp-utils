from contextlib import contextmanager
from unittest import mock


@contextmanager
def catch_signal(signal):
    """
    Catches django signal and returns mock call for the same
    """
    handler = mock.Mock()
    signal.connect(handler)
    yield handler
    signal.disconnect(handler)
