from django.db import models
from openwisp_utils.base import TimeStampedEditableModel
from packaging.version import parse as parse_version


class OpenwispVersion(TimeStampedEditableModel):
    modified = None
    module_version = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ('-created',)

    # @classmethod
    # def is_new_installation(cls):
    #     return not cls.objects.exists()

    @classmethod
    def log_module_version_changes(cls, current_versions):
        """
        TODO: update this
        Retrieves a dictionary of upgraded modules based on current versions.
        Also updates the OpenwispVersion object with the new versions.

        Args:
            current_versions (dict): A dictionary containing the current versions of modules.

        Returns:
            dict: A dictionary containing the upgraded modules and their versions.
                  An empty dict means no modules were upgraded.
        """
        openwisp_version = cls.objects.first()
        # First installation
        if not openwisp_version:
            cls.objects.create(module_version=current_versions)
            return {}
        # Compare old modules in the DB with current modules
        old_versions = openwisp_version.module_version
        upgraded_modules = {}
        for module, version in current_versions.items():
            if module in old_versions and parse_version(
                old_versions[module]
            ) < parse_version(version):
                upgraded_modules[module] = version
            openwisp_version.module_version[module] = version
        # Log version changes
        if upgraded_modules:
            OpenwispVersion.objects.create(
                module_version=openwisp_version.module_version
            )
        return upgraded_modules
