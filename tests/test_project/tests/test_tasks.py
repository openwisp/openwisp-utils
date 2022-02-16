from unittest import TestCase

from celery import shared_task
from openwisp_utils.tasks import OpenwispCeleryTask


class TestOpenwispCeleryTask(TestCase):
    def test_default_time_limits(self):
        @shared_task(base=OpenwispCeleryTask)
        def do_nothing():
            pass

        self.assertEqual(do_nothing.soft_time_limit, 30)
        self.assertEqual(do_nothing.time_limit, 120)
