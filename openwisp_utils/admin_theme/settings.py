from django.conf import settings

ADMIN_SITE_CLASS = getattr(settings,
                           'OPENWISP_ADMIN_SITE_CLASS',
                           'openwisp_utils.admin_theme.admin.OpenwispAdminSite')

OPENWISP_ADMIN_THEME_CSS = getattr(settings, 'OPENWISP_ADMIN_THEME_CSS', [])
OPENWISP_ADMIN_THEME_JS = getattr(settings, 'OPENWISP_ADMIN_THEME_JS', [])
