import unittest

from openwisp_utils.staticfiles import DependencyFinder


class TestStaticFinders(unittest.TestCase):
    def test_dependency_finder(self):
        finder = DependencyFinder()
        self.assertIsInstance(finder.locations, list)
        self.assertIn('django_netjsonconfig', finder.locations[0][1])
