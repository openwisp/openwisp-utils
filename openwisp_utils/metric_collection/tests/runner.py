from unittest.mock import patch

import requests
from django.test.runner import ParallelTestSuite
from openwisp_utils import utils
from openwisp_utils.tests import TimeLoggingTestRunner

success_response = requests.Response()
success_response.status_code = 204


def _mock_post_in_worker(*args):
    utils.requests.Session._original_post = utils.requests.Session.post
    patch.object(utils.requests.Session, "post", return_value=success_response).start()


class MockRequestPostParallelTestSuite(ParallelTestSuite):
    # Workers started with spawn or forkserver (the Linux default since
    # Python 3.14) don't inherit the runner's mock, so each applies it.
    process_setup = _mock_post_in_worker


class MockRequestPostRunner(TimeLoggingTestRunner):
    """This runner ensures that usage metrics are not sent in development when running tests."""

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
