from django.apps import AppConfig

from . import settings as app_settings
from .checks import admin_theme_settings_checks


class OpenWispAdminThemeConfig(AppConfig):
    app_label = 'openwisp_admin'
    name = 'openwisp_utils.admin_theme'

    def ready(self):
        admin_theme_settings_checks(self)
        # monkey patch django.contrib.admin.apps.AdminConfig.default_site
        # in order to supply our customized admin site class
        # this is necessary in order to avoid having to modify
        # many other openwisp modules and repos
        from django.contrib import admin

        admin.apps.AdminConfig.default_site = app_settings.ADMIN_SITE_CLASS
