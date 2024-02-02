from unittest.mock import MagicMock

import requests
from django.test.runner import DiscoverRunner
from openwisp_utils import utils

success_response = requests.Response()
success_response.status_code = 204


class MockRequestPostRunner(DiscoverRunner):
    """
    This runner ensures that Clean Insights events are
    not sent in development when running tests.
    """

    def setup_databases(self, **kwargs):
        utils.requests.post = MagicMock(return_value=success_response)
        return super().setup_databases(**kwargs)
