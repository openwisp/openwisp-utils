from unittest.mock import patch

import requests
from django.test.runner import ParallelTestSuite
from openwisp_utils import utils
from openwisp_utils.tests import TimeLoggingTestRunner

success_response = requests.Response()
success_response.status_code = 204


def _mock_post_in_worker(*args):
    """Prevent test workers from making real HTTP POST requests.

    Workers started with spawn (the macOS default) or forkserver (the
    Linux default since Python 3.14) don't inherit the runner's mock or
    _original_post. Without this setup, tests may send real HTTP requests,
    including usage metrics. Tests that restore _original_post also fail
    with AttributeError.

    Save the real post method so error-handling tests can restore it while
    mocking the lower-level network operations.
    """
    utils.requests.Session._original_post = utils.requests.Session.post
    patch.object(utils.requests.Session, "post", return_value=success_response).start()


class MockRequestPostParallelTestSuite(ParallelTestSuite):
    """Prevent workers using spawn or forkserver from making real HTTP POST requests."""

    process_setup = _mock_post_in_worker


class MockRequestPostRunner(TimeLoggingTestRunner):
    """Prevent database setup and tests from making real HTTP POST requests."""

    parallel_test_suite = MockRequestPostParallelTestSuite

    def setup_databases(self, **kwargs):
        utils.requests.Session._original_post = utils.requests.Session.post
        with patch.object(
            utils.requests.Session, "post", return_value=success_response
        ):
            return super().setup_databases(**kwargs)

    def run_suite(self, suite, **kwargs):
        with patch.object(
            utils.requests.Session, "post", return_value=success_response
        ):
            return super().run_suite(suite)
