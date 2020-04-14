import importlib
import os

from django.template.loaders.filesystem import Loader as FilesystemLoader

from .settings import EXTENDED_APPS


class DependencyLoader(FilesystemLoader):
    """
    A template loader that looks in templates dir of
    django-apps listed in dependencies. Default values is []
    """

    dependencies = EXTENDED_APPS

    def get_dirs(self):
        dirs = []
        for dependency in self.dependencies:
            module = importlib.import_module(dependency)
            dirs.append('{0}/templates'.format(os.path.dirname(module.__file__)))
        return dirs
