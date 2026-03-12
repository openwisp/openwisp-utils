from unittest import TestResult, skip

from django.test import SimpleTestCase
from django.test.runner import RemoteTestResult
from openwisp_utils.tests.selenium import SeleniumTestMixin


class TestSeleniumMixinSkipHandling(SimpleTestCase):
    def _run_skipped_test(self, result_class):
        class SkippedSeleniumTest(SeleniumTestMixin, SimpleTestCase):
            retry_max = 0
            retry_delay = 0

            @classmethod
            def setUpClass(cls):
                pass

            @classmethod
            def tearDownClass(cls):
                pass

            @skip("skip propagation regression test")
            def test_skip(self):
                pass

        test = SkippedSeleniumTest("test_skip")
        if result_class is RemoteTestResult:
            result = result_class(stream=None, descriptions=None, verbosity=0)
        else:
            result = result_class()
        test._setup_and_call(result)
        return result

    def test_setup_and_call_propagates_skip_to_standard_result(self):
        result = self._run_skipped_test(TestResult)

        self.assertEqual(len(result.skipped), 1)
        self.assertEqual(result.skipped[0][1], "skip propagation regression test")

    def test_setup_and_call_records_skip_event_for_remote_result(self):
        result = self._run_skipped_test(RemoteTestResult)

        self.assertIn(("addSkip", 0, "skip propagation regression test"), result.events)
