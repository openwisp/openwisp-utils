from django.db import models
from openwisp_utils.base import TimeStampedEditableModel
from packaging.version import parse as parse_version


class OpenwispVersion(TimeStampedEditableModel):
    module_version = models.JSONField(default=dict, blank=True)

    @classmethod
    def is_new_installation(cls):
        return not cls.objects.exists()

    @classmethod
    def get_upgraded_modules(cls, current_versions):
        """
        Retrieves a dictionary of upgraded modules based on current versions.
        Also updates the OpenwispVersion model with the new versions.

        Args:
            current_versions (dict): A dictionary containing the current versions of modules.

        Returns:
            dict: A dictionary containing the upgraded modules and their versions.
        """
        openwisp_version = cls.objects.first()
        if not openwisp_version:
            cls.objects.create(module_version=current_versions)
            return {}
        old_versions = openwisp_version.module_version
        upgraded_modules = {}
        for module, version in current_versions.items():
            if module in old_versions and parse_version(
                old_versions[module]
            ) < parse_version(version):
                upgraded_modules[module] = version
            openwisp_version.module_version[module] = version
        if upgraded_modules:
            openwisp_version.save()
        return upgraded_modules
