from django.apps import AppConfig
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _

from . import settings as app_settings
from .checks import admin_theme_settings_checks
from .menu import register_menu_group


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
        OPENWISP_ADMIN_THEME_LINKS = getattr(
            app_settings, 'OPENWISP_ADMIN_THEME_LINKS', []
        )
        OPENWISP_ADMIN_THEME_JS = getattr(app_settings, 'OPENWISP_ADMIN_THEME_JS', [])

        css_files = []

        for css_file in OPENWISP_ADMIN_THEME_LINKS:
            link = css_file['href']
            link = link.replace('/static/', '')
            css_file['href'] = static(link)
            css_files.append(css_file)

        js_files = []

        for link in OPENWISP_ADMIN_THEME_JS:
            link = link.replace('/static/', '')
            js_files.append(static(link))

        setattr(app_settings, 'OPENWISP_ADMIN_THEME_LINKS', css_files)
        setattr(app_settings, 'OPENWISP_ADMIN_THEME_JS', js_files)
