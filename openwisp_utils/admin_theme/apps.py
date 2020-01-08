import django
from django.apps import AppConfig
from django.utils.module_loading import import_string

from . import settings as app_settings


class OpenWispAdminThemeConfig(AppConfig):
    app_label = 'openwisp_admin'
    name = 'openwisp_utils.admin_theme'

    def ready(self):
        # monkey patch django.contrib.admin.apps.AdminConfig.default_site
        # in order to supply our customized admin site class
        # this is necessary in order to avoid having to modify
        # many other openwisp modules and repos
        from django.contrib import admin
        admin.apps.AdminConfig.default_site = app_settings.ADMIN_SITE_CLASS
        # this is a hack needed to support older django versions
        # TODO: remove this when support to python 2
        # and to older django versions is dropped
        if django.VERSION < (2, 1):
            site_class = import_string(app_settings.ADMIN_SITE_CLASS)
            admin.site = site_class()
            admin.sites.site = admin.site
            admin.autodiscover_modules('admin', register_to=admin.site)
