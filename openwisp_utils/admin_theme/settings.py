from django.conf import settings

ADMIN_SITE_CLASS = getattr(
    settings,
    'OPENWISP_ADMIN_SITE_CLASS',
    'openwisp_utils.admin_theme.admin.OpenwispAdminSite',
)

OPENWISP_ADMIN_THEME_LINKS = getattr(settings, 'OPENWISP_ADMIN_THEME_LINKS', [])
OPENWISP_ADMIN_THEME_JS = getattr(settings, 'OPENWISP_ADMIN_THEME_JS', [])
