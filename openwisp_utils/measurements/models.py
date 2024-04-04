from django.db import models
from openwisp_utils.base import TimeStampedEditableModel
from packaging.version import parse as parse_version


class OpenwispVersion(TimeStampedEditableModel):
    modified = None
    module_version = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ('-created',)

    @classmethod
    def log_module_version_changes(cls, current_versions):
        """
        Returns a tuple of booleans indicating:
         - whether this is a new installation,
         - whether any OpenWISP modules has been upgraded.
        """
        openwisp_version = cls.objects.first()
        if not openwisp_version:
            # If no OpenwispVersion object is present,
            # it means that this is a new installation and
            # we don't need to check for upgraded modules.
            cls.objects.create(module_version=current_versions)
            return True, False
        # Check which installed modules have been upgraded by comparing
        # the currently installed versions in current_versions with the
        # versions stored in the OpenwispVersion object. The return value
        # is a dictionary of module:version pairs that have been upgraded.
        old_versions = openwisp_version.module_version
        upgraded_modules = {}
        for module, version in current_versions.items():
            # The OS version does not follow semver,
            # therefore it's handled differently.
            if module in ['kernel_version', 'os_version', 'hardware_platform']:
                if old_versions.get(module) != version:
                    upgraded_modules[module] = version
            elif (
                # Check if a new OpenWISP module was enabled
                # on an existing installation
                module not in old_versions
                or (
                    # Check if an OpenWISP module was upgraded
                    module in old_versions
                    and parse_version(old_versions[module]) < parse_version(version)
                )
            ):
                upgraded_modules[module] = version
            openwisp_version.module_version[module] = version
        # Log version changes
        if upgraded_modules:
            OpenwispVersion.objects.create(module_version=current_versions)
            return False, True
        return False, False
