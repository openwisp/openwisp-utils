import unittest

from django.template import engines
from openwisp_utils.loaders import DependencyLoader
from openwisp_utils.staticfiles import DependencyFinder


class TestDependencyDiscovery(unittest.TestCase):
    def test_dependency_finder(self):
        finder = DependencyFinder()
        self.assertIsInstance(finder.locations, list)
        self.assertIn("dependency_app", finder.locations[0][1])
        self.assertTrue(finder.find("dependency_app/dependency.css"))

    def test_dependency_loader(self):
        loader = DependencyLoader(engine=None)
        self.assertIsInstance(loader.get_dirs(), list)
        self.assertIn("dependency_app", loader.get_dirs()[0])

    def test_dependency_template_loading(self):
        template = engines["django"].get_template("dependency_app/dependency.html")
        self.assertEqual(template.render(), "dependency template\n")
