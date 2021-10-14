import logging

from django.conf import settings
from django.contrib import admin
from django.utils.translation import gettext_lazy

from . import settings as app_settings
from .dashboard import get_dashboard_context

logger = logging.getLogger(__name__)


class OpenwispAdminSite(admin.AdminSite):
    # <title>
    site_title = getattr(settings, 'OPENWISP_ADMIN_SITE_TITLE', 'OpenWISP Admin')
    # h1 text
    site_header = getattr(settings, 'OPENWISP_ADMIN_SITE_HEADER', 'OpenWISP')
    # text at the top of the admin index page
    index_title = gettext_lazy(
        getattr(settings, 'OPENWISP_ADMIN_INDEX_TITLE', 'Network Administration')
    )
    enable_nav_sidebar = False

    def index(self, request, extra_context=None):
        if app_settings.ADMIN_DASHBOARD_ENABLED:
            context = get_dashboard_context(request)
        else:
            context = {'dashboard_enabled': False}
        return super().index(request, extra_context=context)


def openwisp_admin(site_url=None):  # pragma: no cover
    """
    openwisp_admin function is deprecated
    """
    logger.warning(
        'WARNING! Calling openwisp_utils.admin_theme.admin.openwisp_admin() '
        'is not necessary anymore and is therefore deprecated.\nThis function '
        'will be removed in future versions of openwisp-utils and therefore '
        'it is recommended to remove any reference to it.\n'
    )
