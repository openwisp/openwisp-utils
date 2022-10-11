from django.core.exceptions import ImproperlyConfigured

from . import settings as app_settings

THEME_LINKS = app_settings.OPENWISP_ADMIN_THEME_LINKS.copy()
THEME_JS = app_settings.OPENWISP_ADMIN_THEME_JS.copy()


def register_theme_link(links):
    if not isinstance(links, list):
        raise ImproperlyConfigured(
            '"openwisp_utils.admin_theme.theme.register_theme_link"'
            ' accepts "list" of links.'
        )
    # We don't raise ImproperlyConfigured exception if
    # link is already present in THEME_LINKS because
    # user might specify a link in project settings which is
    # already registered by an application.
    # This would lead to time-consuming debugging for little returns.
    for link in links:
        if link not in THEME_LINKS:
            THEME_LINKS.append(link)


def unregister_theme_link(links):
    if not isinstance(links, list):
        raise ImproperlyConfigured(
            '"openwisp_utils.admin_theme.theme.unregister_theme_link"'
            ' accepts "list" of links.'
        )
    for link in links:
        try:
            THEME_LINKS.remove(link)
        except ValueError:
            raise ImproperlyConfigured(
                f'{link["href"]} was not added to OPENWISP_ADMIN_THEME_LINKS'
            )


def register_theme_js(jss):
    if not isinstance(jss, list):
        raise ImproperlyConfigured(
            '"openwisp_utils.admin_theme.theme.register_theme_js"'
            ' accepts "list" of JS.'
        )
    # We don't raise ImproperlyConfigured exception if
    # js is already present in THEME_JS because
    # user might specify a js in project settings which is
    # already registered by an application.
    # This would lead to time-consuming debugging for little returns.
    for js in jss:
        if js not in THEME_JS:
            THEME_JS.append(js)


def unregister_theme_js(jss):
    if not isinstance(jss, list):
        raise ImproperlyConfigured(
            '"openwisp_utils.admin_theme.theme.unregister_theme_js"'
            ' accepts "list" of JS.'
        )
    for js in jss:
        try:
            THEME_JS.remove(js)
        except ValueError:
            raise ImproperlyConfigured(f'{js} was not added to OPENWISP_ADMIN_THEME_JS')
