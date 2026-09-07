import unittest

from django.template import TemplateDoesNotExist, engines
from openwisp_utils.loaders import DependencyLoader
from openwisp_utils.staticfiles import DependencyFinder


class TestDependencyDiscovery(unittest.TestCase):
    def test_dependency_finder(self):
        finder = DependencyFinder()
        self.assertIsInstance(finder.locations, list)
        self.assertTrue(
            any("dependency_app" in path for _, path in finder.locations),
            "Dependency finder did not discover the fixture static directory",
        )
        self.assertTrue(finder.find("dependency_app/dependency.css"))

    def test_missing_dependency_static_file(self):
        finder = DependencyFinder()
        self.assertFalse(finder.find("dependency_app/missing.css"))

    def test_dependency_loader(self):
        loader = DependencyLoader(engine=None)
        self.assertIsInstance(loader.get_dirs(), list)
        self.assertTrue(
            any("dependency_app" in path for path in loader.get_dirs()),
            "Dependency loader did not discover the fixture template directory",
        )

    def test_dependency_template_loading(self):
        template = engines["django"].get_template("dependency_app/dependency.html")
        self.assertEqual(template.render(), "dependency template\n")

    def test_missing_dependency_template(self):
        with self.assertRaises(TemplateDoesNotExist):
            engines["django"].get_template("dependency_app/missing.html")
