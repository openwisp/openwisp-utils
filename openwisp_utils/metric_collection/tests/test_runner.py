import unittest
from unittest.mock import MagicMock, patch

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase

try:
    from channels.testing import ChannelsLiveServerTestCase
    channels_available = True
except ImportError:
    ChannelsLiveServerTestCase = None
    channels_available = False

from .runner import ChannelsParallelTestRunner


class DummyRegularTest(TestCase):
    """A regular test case for testing the runner."""
    def test_dummy(self):
        self.assertTrue(True)


class DummySeleniumTest(StaticLiveServerTestCase):
    """A Selenium test case that should run serially."""
    def test_dummy_selenium(self):
        self.assertTrue(True)


if channels_available:
    class DummyChannelsTest(ChannelsLiveServerTestCase):
        """A Channels test case that should run serially."""
        def test_dummy_channels(self):
            self.assertTrue(True)


class TestChannelsParallelTestRunner(TestCase):
    """Test cases for the ChannelsParallelTestRunner."""

    def setUp(self):
        self.runner = ChannelsParallelTestRunner()

    def test_is_websocket_test_regular(self):
        """Test that regular test cases are not identified as WebSocket tests."""
        regular_test = DummyRegularTest('test_dummy')
        self.assertFalse(self.runner._is_websocket_test(regular_test))

    def test_is_websocket_test_selenium(self):
        """Test that Selenium test cases are identified as WebSocket tests."""
        selenium_test = DummySeleniumTest('test_dummy_selenium')
        self.assertTrue(self.runner._is_websocket_test(selenium_test))

    @unittest.skipUnless(channels_available, "channels not installed")
    def test_is_websocket_test_channels(self):
        """Test that Channels test cases are identified as WebSocket tests."""
        channels_test = DummyChannelsTest('test_dummy_channels')
        self.assertTrue(self.runner._is_websocket_test(channels_test))

    def test_split_test_suite_basic(self):
        """Test that the test suite is correctly split between regular and WebSocket tests."""
        # Create test cases
        regular_test = DummyRegularTest('test_dummy')
        selenium_test = DummySeleniumTest('test_dummy_selenium')
        
        # Create a test suite
        suite = unittest.TestSuite()
        suite.addTest(regular_test)
        suite.addTest(selenium_test)
        
        # Split the suite
        regular_suite, websocket_suite = self.runner._split_test_suite(suite)
        
        # Verify split
        self.assertEqual(regular_suite.countTestCases(), 1,
                         "Should have 1 regular test")
        self.assertEqual(websocket_suite.countTestCases(), 1,
                         "Should have 1 WebSocket test")

    @unittest.skipUnless(channels_available, "channels not installed")
    def test_split_test_suite_with_channels(self):
        """Test that the test suite correctly handles Channels tests."""
        # Create test cases
        regular_test = DummyRegularTest('test_dummy')
        selenium_test = DummySeleniumTest('test_dummy_selenium')
        channels_test = DummyChannelsTest('test_dummy_channels')
        
        # Create a test suite
        suite = unittest.TestSuite()
        suite.addTest(regular_test)
        suite.addTest(selenium_test)
        suite.addTest(channels_test)
        
        # Split the suite
        regular_suite, websocket_suite = self.runner._split_test_suite(suite)
        
        # Verify split
        self.assertEqual(regular_suite.countTestCases(), 1,
                         "Should have 1 regular test")
        self.assertEqual(websocket_suite.countTestCases(), 2,
                         "Should have 2 WebSocket tests (Selenium + Channels)")

    def test_split_test_suite_nested(self):
        """Test that nested test suites are correctly handled."""
        # Create test cases
        regular_test1 = DummyRegularTest('test_dummy')
        regular_test2 = DummyRegularTest('test_dummy')
        selenium_test = DummySeleniumTest('test_dummy_selenium')
        
        # Create nested suites
        inner_suite1 = unittest.TestSuite()
        inner_suite1.addTest(regular_test1)
        inner_suite1.addTest(selenium_test)
        
        inner_suite2 = unittest.TestSuite()
        inner_suite2.addTest(regular_test2)
        
        outer_suite = unittest.TestSuite()
        outer_suite.addTest(inner_suite1)
        outer_suite.addTest(inner_suite2)
        
        # Split the suite
        regular_suite, websocket_suite = self.runner._split_test_suite(outer_suite)
        
        # Verify split
        self.assertEqual(regular_suite.countTestCases(), 2,
                         "Should have 2 regular tests")
        self.assertEqual(websocket_suite.countTestCases(), 1,
                         "Should have 1 WebSocket test")

    def test_split_test_suite_empty(self):
        """Test that empty test suites are handled correctly."""
        empty_suite = unittest.TestSuite()
        
        regular_suite, websocket_suite = self.runner._split_test_suite(empty_suite)
        
        self.assertEqual(regular_suite.countTestCases(), 0,
                         "Should have 0 regular tests")
        self.assertEqual(websocket_suite.countTestCases(), 0,
                         "Should have 0 WebSocket tests")

    def test_split_test_suite_only_regular(self):
        """Test that suites with only regular tests work correctly."""
        # Create only regular tests
        regular_test1 = DummyRegularTest('test_dummy')
        regular_test2 = DummyRegularTest('test_dummy')
        
        suite = unittest.TestSuite()
        suite.addTest(regular_test1)
        suite.addTest(regular_test2)
        
        regular_suite, websocket_suite = self.runner._split_test_suite(suite)
        
        self.assertEqual(regular_suite.countTestCases(), 2,
                         "Should have 2 regular tests")
        self.assertEqual(websocket_suite.countTestCases(), 0,
                         "Should have 0 WebSocket tests")

    def test_split_test_suite_only_websocket(self):
        """Test that suites with only WebSocket tests work correctly."""
        # Create only WebSocket tests
        selenium_test1 = DummySeleniumTest('test_dummy_selenium')
        selenium_test2 = DummySeleniumTest('test_dummy_selenium')
        
        suite = unittest.TestSuite()
        suite.addTest(selenium_test1)
        suite.addTest(selenium_test2)
        
        regular_suite, websocket_suite = self.runner._split_test_suite(suite)
        
        self.assertEqual(regular_suite.countTestCases(), 0,
                         "Should have 0 regular tests")
        self.assertEqual(websocket_suite.countTestCases(), 2,
                         "Should have 2 WebSocket tests")

    @patch.object(ChannelsParallelTestRunner, '_split_test_suite')
    @patch('openwisp_utils.tests.utils.TimeLoggingTestRunner.run_suite')
    def test_run_suite_serial_mode(self, mock_parent_run, mock_split):
        """Test that when parallel is 1, the suite runs normally without splitting."""
        # Set up runner in serial mode
        self.runner.parallel = 1
        self.runner.verbosity = 0
        
        # Mock the parent run_suite method
        mock_result = MagicMock()
        mock_parent_run.return_value = mock_result
        
        test_suite = unittest.TestSuite()
        
        # Mock the patch context for requests
        with patch('openwisp_utils.utils.requests.Session.post'):
            result = self.runner.run_suite(test_suite)
        
        # Verify that split was not called and parent was called directly
        mock_split.assert_not_called()
        mock_parent_run.assert_called_once()
        self.assertEqual(result, mock_result)

    @patch('openwisp_utils.tests.utils.TimeLoggingTestRunner.run_suite')
    def test_run_suite_parallel_mode_mixed_tests(self, mock_parent_run):
        """Test that in parallel mode, tests are split and run appropriately."""
        # Set up runner in parallel mode
        self.runner.parallel = 2
        self.runner.verbosity = 1
        
        # Create a mixed test suite
        regular_test = DummyRegularTest('test_dummy')
        selenium_test = DummySeleniumTest('test_dummy_selenium')
        
        suite = unittest.TestSuite()
        suite.addTest(regular_test)
        suite.addTest(selenium_test)
        
        # Mock parent run_suite calls
        mock_regular_result = MagicMock()
        mock_regular_result.errors = []
        mock_regular_result.failures = []
        mock_regular_result.skipped = []
        mock_regular_result.testsRun = 1
        
        mock_websocket_result = MagicMock()
        mock_websocket_result.errors = []
        mock_websocket_result.failures = []
        mock_websocket_result.skipped = []
        mock_websocket_result.testsRun = 1
        
        mock_parent_run.side_effect = [mock_regular_result, mock_websocket_result]
        
        # Capture stdout to verify messages
        import io
        import sys
        captured_output = io.StringIO()
        original_stdout = sys.stdout
        sys.stdout = captured_output
        
        try:
            # Mock the patch context for requests
            with patch('openwisp_utils.utils.requests.Session.post'):
                result = self.runner.run_suite(suite)
            
            # Verify that parent run_suite was called twice (regular + websocket)
            self.assertEqual(mock_parent_run.call_count, 2)
            
            # Verify that the parallel setting was manipulated correctly
            # It should be reset to 2 after running websocket tests
            self.assertEqual(self.runner.parallel, 2)
            
            # Verify messages were printed
            output = captured_output.getvalue()
            self.assertIn("regular tests in parallel", output)
            self.assertIn("WebSocket/Selenium tests serially", output)
            
            # Verify results were merged
            self.assertEqual(result.testsRun, 2)
            
        finally:
            sys.stdout = original_stdout