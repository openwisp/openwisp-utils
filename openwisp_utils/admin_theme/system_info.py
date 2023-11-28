import platform
from collections import OrderedDict

import pkg_resources
from django.conf import settings
from django.utils.module_loading import import_string

EXTRA_OPENWISP_PACKAGES = ['netdiff', 'netjsonconfig']


def get_installed_openwisp_packages():
    dists = pkg_resources.working_set
    return {
        dist.key: dist.version
        for dist in dists
        if dist.key.startswith('openwisp') or dist.key in EXTRA_OPENWISP_PACKAGES
    }


def get_openwisp_version():
    try:
        return import_string('openwisp2.__openwisp_version__')
    except ImportError:
        return None


def get_enabled_openwisp_modules():
    enabled_packages = {}
    installed_packages = get_installed_openwisp_packages()
    extra_packages = {}
    for package, version in installed_packages.items():
        if package in EXTRA_OPENWISP_PACKAGES:
            extra_packages[package] = version
            continue
        package_name = package.replace('-', '_')
        if package_name in settings.INSTALLED_APPS:
            enabled_packages[package] = version
        else:
            # check for sub-apps
            for app in settings.INSTALLED_APPS:
                if app.startswith(package_name + '.'):
                    enabled_packages[package] = version
                    break
    enabled_packages = OrderedDict(sorted(enabled_packages.items()))
    enabled_packages.update(OrderedDict(sorted(extra_packages.items())))
    return enabled_packages


def get_os_details():
    uname = platform.uname()
    return {
        'os_version': uname.version,
        'kernel_version': uname.release,
        'hardware_platform': uname.machine,
    }
