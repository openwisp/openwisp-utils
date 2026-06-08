import importlib
import sys
from types import ModuleType
from unittest import TestResult, TestSuite, skip

from django.conf import settings
from django.db.backends.base.base import BaseDatabaseWrapper
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


class TestSerializeDbConnectionLifecycle(SimpleTestCase):
    def setUp(self):
        self.original_connect = BaseDatabaseWrapper.connect
        self.original_close = BaseDatabaseWrapper._close
        self.original_serialized = SeleniumTestMixin._db_conn_serialized
        self.original_engine = settings.DATABASES["default"]["ENGINE"]

    def tearDown(self):
        # The helper patches process-wide Django methods, so restore them.
        BaseDatabaseWrapper.connect = self.original_connect
        BaseDatabaseWrapper._close = self.original_close
        SeleniumTestMixin._db_conn_serialized = self.original_serialized
        settings.DATABASES["default"]["ENGINE"] = self.original_engine

    def _reset_state(self):
        BaseDatabaseWrapper.connect = self.original_connect
        BaseDatabaseWrapper._close = self.original_close
        SeleniumTestMixin._db_conn_serialized = False

    def _set_db_methods(self):
        calls = []

        def connect(self):
            calls.append("connect")
            return "connected"

        def close(self):
            calls.append("close")
            return "closed"

        BaseDatabaseWrapper.connect = connect
        BaseDatabaseWrapper._close = close
        return connect, close, calls

    def test_sqlite_patches_connect_and_close(self):
        settings.DATABASES["default"]["ENGINE"] = "django.db.backends.sqlite3"
        self._reset_state()
        connect, close, calls = self._set_db_methods()
        SeleniumTestMixin._serialize_db_connection_lifecycle()
        self.assertIs(BaseDatabaseWrapper.connect.__wrapped__, connect)
        self.assertIs(BaseDatabaseWrapper._close.__wrapped__, close)
        self.assertEqual(BaseDatabaseWrapper.connect(object()), "connected")
        self.assertEqual(BaseDatabaseWrapper._close(object()), "closed")
        self.assertEqual(calls, ["connect", "close"])

    def test_patching_is_idempotent(self):
        class FirstSeleniumTest(SeleniumTestMixin):
            pass

        class SecondSeleniumTest(SeleniumTestMixin):
            pass

        settings.DATABASES["default"]["ENGINE"] = "django.db.backends.sqlite3"
        self._reset_state()
        self._set_db_methods()
        FirstSeleniumTest._serialize_db_connection_lifecycle()
        connect = BaseDatabaseWrapper.connect
        close = BaseDatabaseWrapper._close
        SecondSeleniumTest._serialize_db_connection_lifecycle()
        self.assertIs(BaseDatabaseWrapper.connect, connect)
        self.assertIs(BaseDatabaseWrapper._close, close)

    def test_non_sqlite_backend_is_not_patched(self):
        settings.DATABASES["default"]["ENGINE"] = "django.db.backends.postgresql"
        self._reset_state()
        connect, close, _ = self._set_db_methods()
        SeleniumTestMixin._serialize_db_connection_lifecycle()
        self.assertIs(BaseDatabaseWrapper.connect, connect)
        self.assertIs(BaseDatabaseWrapper._close, close)


class TestSpatiaLiteFindLibraryMemoization(SimpleTestCase):
    def test_find_library_is_memoized(self):
        target = "openwisp_utils.db.backends.spatialite.base"
        spatialite_module_path = "django.contrib.gis.db.backends.spatialite"
        spatialite_base_module_path = f"{spatialite_module_path}.base"
        original_target = sys.modules.pop(target, None)
        original_spatialite = sys.modules.get(spatialite_module_path)
        original_spatialite_base = sys.modules.get(spatialite_base_module_path)
        spatialite_module = ModuleType(spatialite_module_path)
        spatialite_base_module = ModuleType(spatialite_base_module_path)
        calls = []

        def find_library(name):
            calls.append(name)
            return f"lib{name}.so"

        try:
            # Avoid importing Django's real GIS backend, which requires GDAL.
            spatialite_base_module.DatabaseWrapper = object
            spatialite_base_module.find_library = find_library
            spatialite_module.base = spatialite_base_module
            sys.modules[spatialite_module_path] = spatialite_module
            sys.modules[spatialite_base_module_path] = spatialite_base_module
            importlib.import_module(target)
            self.assertEqual(
                spatialite_base_module.find_library("spatialite"),
                "libspatialite.so",
            )
            self.assertEqual(
                spatialite_base_module.find_library("spatialite"),
                "libspatialite.so",
            )
            self.assertEqual(calls, ["spatialite"])
        finally:
            sys.modules.pop(target, None)
            if original_target is not None:
                sys.modules[target] = original_target
            if original_spatialite is None:
                sys.modules.pop(spatialite_module_path, None)
            else:
                sys.modules[spatialite_module_path] = original_spatialite
            if original_spatialite_base is None:
                sys.modules.pop(spatialite_base_module_path, None)
            else:
                sys.modules[spatialite_base_module_path] = original_spatialite_base
