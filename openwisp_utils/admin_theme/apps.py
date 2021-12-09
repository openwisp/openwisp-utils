from django.apps import AppConfig
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _

from . import settings as app_settings
from .checks import admin_theme_settings_checks
from .menu import register_menu_group


def _staticfy(value):
    try:
        return static(value)
    # maintain backward compatibility
    except ValueError:
        return value


class OpenWispAdminThemeConfig(AppConfig):
    app_label = 'openwisp_admin'
    name = 'openwisp_utils.admin_theme'

    def ready(self):
        admin_theme_settings_checks(self)
        self.register_menu_groups()
        self.modify_admin_theme_settings_links()
        # monkey patch django.contrib.admin.apps.AdminConfig.default_site
        # in order to supply our customized admin site class
        # this is necessary in order to avoid having to modify
        # many other openwisp modules and repos
        from django.contrib import admin

        admin.apps.AdminConfig.default_site = app_settings.ADMIN_SITE_CLASS

    def register_menu_groups(self):
        # register dashboard item
        register_menu_group(
            position=10,
            config={'label': _('Home'), 'url': '/admin', 'icon': 'ow-dashboard-icon'},
        )

    def modify_admin_theme_settings_links(self):
        link_files = []
        for link_file in app_settings.OPENWISP_ADMIN_THEME_LINKS:
            href = link_file['href']
            href = href.replace('/static/', '')
            link_file['href'] = _staticfy(href)
            link_files.append(link_file)

        js_files = []
        for js_file in app_settings.OPENWISP_ADMIN_THEME_JS:
            js_file = js_file.replace('/static/', '')
            js_files.append(_staticfy(js_file))

        app_settings.OPENWISP_ADMIN_THEME_LINKS = link_files
        app_settings.OPENWISP_ADMIN_THEME_JS = js_files
