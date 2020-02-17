from django.core.checks import Error, register

from . import settings as app_settings


@register()
def admin_theme_settings_checks(app_configs, **kwargs):
    errors = []
    is_list_of_str = all(isinstance(item, str) for item in app_settings.OPENWISP_ADMIN_THEME_CSS)
    if not isinstance(app_settings.OPENWISP_ADMIN_THEME_CSS, list) or not is_list_of_str:
        errors.append(
            Error(
                msg='Improperly Configured',
                hint='OPENWISP_ADMIN_THEME_CSS should be a list of strings.',
                obj='OPENWISP_ADMIN_THEME_CSS',
            )
        )
    is_list_of_str = all(isinstance(item, str) for item in app_settings.OPENWISP_ADMIN_THEME_JS)
    if not isinstance(app_settings.OPENWISP_ADMIN_THEME_JS, list) or not is_list_of_str:
        errors.append(
            Error(
                msg='Improperly Configured',
                hint='OPENWISP_ADMIN_THEME_JS should be a list of strings.',
                obj='OPENWISP_ADMIN_THEME_JS',
            )
        )
    return errors
