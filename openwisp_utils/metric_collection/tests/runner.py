import unittest
from unittest.mock import patch

import requests
from openwisp_utils import utils
from openwisp_utils.tests import TimeLoggingTestRunner

success_response = requests.Response()
success_response.status_code = 204


class ChannelsParallelTestRunner(TimeLoggingTestRunner):
    """
    Custom test runner that runs non-WebSocket tests in parallel 
    and WebSocket tests serially when --parallel is used.
    
    This ensures that tests inheriting from ChannelsLiveServerTestCase
    are run serially to avoid port conflicts and WebSocket connection issues.
    """

    def _is_websocket_test(self, test_case):
        """
        Check if a test case is a WebSocket test that should run serially.
        
        Args:
            test_case: The test case to check
            
        Returns:
            bool: True if the test should run serially
        """
        test_class = test_case.__class__
        
        # Check for ChannelsLiveServerTestCase
        try:
            from channels.testing import ChannelsLiveServerTestCase
            if issubclass(test_class, ChannelsLiveServerTestCase):
                return True
        except ImportError:
            # channels is not installed, skip this check
            pass
        
        # Check for StaticLiveServerTestCase (Selenium tests)
        # These often have similar issues with parallel execution
        try:
            from django.contrib.staticfiles.testing import StaticLiveServerTestCase
            if issubclass(test_class, StaticLiveServerTestCase):
                return True
        except ImportError:
            pass
            
        return False

    def _split_test_suite(self, suite):
        """
        Split test suite into regular tests and WebSocket tests.
        
        Args:
            suite: The test suite to split
            
        Returns:
            tuple: (regular_tests_suite, websocket_tests_suite)
        """
        regular_tests = unittest.TestSuite()
        websocket_tests = unittest.TestSuite()
        
        def extract_tests(test_item):
            if isinstance(test_item, unittest.TestSuite):
                for sub_item in test_item:
                    extract_tests(sub_item)
            else:
                # This is an individual test case
                if self._is_websocket_test(test_item):
                    websocket_tests.addTest(test_item)
                else:
                    regular_tests.addTest(test_item)
        
        extract_tests(suite)
        return regular_tests, websocket_tests

    def run_suite(self, suite, **kwargs):
        with patch.object(
            utils.requests.Session, "post", return_value=success_response
        ):
            # If not running in parallel mode, run normally
            if self.parallel == 1:
                return super().run_suite(suite)
            
            # Split the test suite
            regular_tests, websocket_tests = self._split_test_suite(suite)
            
            # Create a combined result object
            result = None
            
            # Run regular tests in parallel if there are any
            if regular_tests.countTestCases() > 0:
                if self.verbosity >= 1:
                    print(f"Running {regular_tests.countTestCases()} regular tests in parallel...")
                
                # Run regular tests in parallel
                result = super().run_suite(regular_tests)
            
            # Run WebSocket tests serially if there are any
            if websocket_tests.countTestCases() > 0:
                if self.verbosity >= 1:
                    print(f"Running {websocket_tests.countTestCases()} WebSocket/Selenium tests serially...")
                
                # Temporarily disable parallel execution for WebSocket tests
                original_parallel = self.parallel
                self.parallel = 1
                
                try:
                    # Run WebSocket tests serially
                    serial_result = super().run_suite(websocket_tests)
                    
                    # If we have previous results, merge them
                    if result is not None:
                        # Merge the results
                        result.errors.extend(serial_result.errors)
                        result.failures.extend(serial_result.failures)
                        result.skipped.extend(getattr(serial_result, 'skipped', []))
                        result.testsRun += serial_result.testsRun
                    else:
                        result = serial_result
                        
                finally:
                    # Restore parallel setting
                    self.parallel = original_parallel
            
            # If no tests were found, run the original suite
            if result is None:
                result = super().run_suite(suite)
                
            return result


class MockRequestPostRunner(ChannelsParallelTestRunner):
    """This runner ensures that usage metrics are not sent in development when running tests."""
    
    def setup_databases(self, **kwargs):
        utils.requests.Session._original_post = utils.requests.Session.post
        with patch.object(
            utils.requests.Session, "post", return_value=success_response
        ):
            return super().setup_databases(**kwargs)
