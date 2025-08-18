#!/usr/bin/env python
"""
Test script to verify the custom test runner behavior.
"""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the project to the path
sys.path.insert(0, "tests")
sys.path.insert(0, ".")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "openwisp2.settings")

import django
django.setup()

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase
from channels.testing import ChannelsLiveServerTestCase
from openwisp_utils.metric_collection.tests.runner import ChannelsParallelTestRunner


class DummyRegularTest(TestCase):
    """A regular test case for testing."""
    def test_dummy(self):
        self.assertTrue(True)


class DummySeleniumTest(StaticLiveServerTestCase):
    """A Selenium test case that should run serially."""
    def test_dummy_selenium(self):
        self.assertTrue(True)


class DummyChannelsTest(ChannelsLiveServerTestCase):
    """A Channels test case that should run serially."""
    def test_dummy_channels(self):
        self.assertTrue(True)


def test_runner_splits_correctly():
    """Test that the runner correctly identifies and splits test cases."""
    runner = ChannelsParallelTestRunner()
    
    # Create test cases
    regular_test = DummyRegularTest('test_dummy')
    selenium_test = DummySeleniumTest('test_dummy_selenium')
    channels_test = DummyChannelsTest('test_dummy_channels')
    
    # Test the _is_websocket_test method
    assert not runner._is_websocket_test(regular_test), "Regular test should not be identified as WebSocket test"
    assert runner._is_websocket_test(selenium_test), "Selenium test should be identified as WebSocket test"
    assert runner._is_websocket_test(channels_test), "Channels test should be identified as WebSocket test"
    
    # Create a test suite
    suite = unittest.TestSuite()
    suite.addTest(regular_test)
    suite.addTest(selenium_test)
    suite.addTest(channels_test)
    
    # Split the suite
    regular_suite, websocket_suite = runner._split_test_suite(suite)
    
    # Verify split
    assert regular_suite.countTestCases() == 1, f"Expected 1 regular test, got {regular_suite.countTestCases()}"
    assert websocket_suite.countTestCases() == 2, f"Expected 2 WebSocket tests, got {websocket_suite.countTestCases()}"
    
    print("✓ Test runner correctly splits test cases")
    print("✓ ChannelsLiveServerTestCase detection works")
    print("✓ StaticLiveServerTestCase detection works")
    return True


if __name__ == "__main__":
    try:
        test_runner_splits_correctly()
        print("All tests passed!")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)