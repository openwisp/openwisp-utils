import unittest

from openwisp_utils.loaders import DependencyLoader
from openwisp_utils.staticfiles import DependencyFinder


class TestDependencyDiscovery(unittest.TestCase):
    def test_dependency_finder(self):
        finder = DependencyFinder()
        self.assertIsInstance(finder.locations, list)
        self.assertIn('django_loci', finder.locations[0][1])

    def test_dependency_loader(self):
        loader = DependencyLoader(engine=None)
        self.assertIsInstance(loader.get_dirs(), list)
        self.assertIn('openwisp_controller', loader.get_dirs()[0])
