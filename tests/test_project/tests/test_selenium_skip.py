from unittest import TestResult, TestSuite, skip

from django.test import SimpleTestCase
from django.test.runner import RemoteTestRunner
from openwisp_utils.tests.selenium import SeleniumTestMixin


class SeleniumRetryTestMixin(SeleniumTestMixin, SimpleTestCase):
    retry_delay = 0

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass


class TestSeleniumMixinSkipHandling(SimpleTestCase):
    def _run_skipped_standard_test(self):
        class SkippedSeleniumTest(SeleniumTestMixin, SimpleTestCase):
            retry_max = 0
            retry_delay = 0

            @skip("skip propagation regression test")
            def test_skip(self):
                pass

        test = SkippedSeleniumTest("test_skip")
        result = TestResult()
        test._setup_and_call(result)
        return result

    def _run_skipped_remote_suite(self):
        class DummyWebDriver:
            def quit(self):
                pass

        class SkippedSeleniumTest(SeleniumTestMixin, SimpleTestCase):
            retry_max = 0
            retry_delay = 0

            @classmethod
            def get_webdriver(cls):
                return DummyWebDriver()

            @skip("first skip propagation regression test")
            def test_first_skip(self):
                pass

            @skip("second skip propagation regression test")
            def test_second_skip(self):
                pass

        suite = TestSuite(
            [
                SkippedSeleniumTest("test_first_skip"),
                SkippedSeleniumTest("test_second_skip"),
            ]
        )
        return RemoteTestRunner().run(suite)

    def test_setup_and_call_propagates_skip_to_standard_result(self):
        result = self._run_skipped_standard_test()
        self.assertEqual(len(result.skipped), 1)
        self.assertEqual(result.skipped[0][1], "skip propagation regression test")

    def test_setup_and_call_preserves_remote_skip_events_for_multiple_tests(self):
        result = self._run_skipped_remote_suite()
        self.assertEqual(
            result.events,
            [
                ("startTest", 0),
                ("addSkip", 0, "first skip propagation regression test"),
                ("stopTest", 0),
                ("startTest", 1),
                ("addSkip", 1, "second skip propagation regression test"),
                ("stopTest", 1),
            ],
        )


class TestSeleniumMixinRetryHandling(SimpleTestCase):
    def test_setup_and_call_stops_after_required_successful_retries(self):
        class FlakySeleniumTest(SeleniumRetryTestMixin):
            retry_max = 5

            def test_flaky(self):
                if not hasattr(self, "calls"):
                    self.calls = 0
                self.calls += 1
                if self.calls == 1:
                    self.fail("failing first call")

        test = FlakySeleniumTest("test_flaky")
        result = TestResult()
        test._setup_and_call(result)
        self.assertTrue(result.wasSuccessful())
        self.assertEqual(test.calls, 3)

    def test_setup_and_call_allows_non_consecutive_successful_retries(self):
        class FlakySeleniumTest(SeleniumRetryTestMixin):
            retry_max = 5

            def test_flaky(self):
                if not hasattr(self, "calls"):
                    self.calls = 0
                self.calls += 1
                if self.calls in [1, 3]:
                    self.fail("intermittent failure")

        test = FlakySeleniumTest("test_flaky")
        result = TestResult()
        test._setup_and_call(result)
        self.assertTrue(result.wasSuccessful())
        self.assertEqual(test.calls, 4)

    def test_setup_and_call_fails_when_retry_successes_are_insufficient(self):
        class FlakySeleniumTest(SeleniumRetryTestMixin):
            retry_max = 5

            def test_flaky(self):
                if not hasattr(self, "calls"):
                    self.calls = 0
                self.calls += 1
                if self.calls != 2:
                    self.fail("too flaky")

        test = FlakySeleniumTest("test_flaky")
        result = TestResult()
        test._setup_and_call(result)
        self.assertFalse(result.wasSuccessful())
        self.assertEqual(test.calls, 6)
