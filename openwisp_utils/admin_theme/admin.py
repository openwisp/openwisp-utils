from django.conf import settings
from django.contrib import admin
from django.utils.translation import ugettext_lazy


class OpenwispAdminSite(admin.AdminSite):
    # <title>
    site_title = getattr(settings,
                         'OPENWISP_ADMIN_SITE_TITLE',
                         'OpenWISP Admin')
    # h1 text
    site_header = getattr(settings,
                          'OPENWISP_ADMIN_SITE_HEADER',
                          'OpenWISP')
    # text at the top of the admin index page
    index_title = ugettext_lazy(
        getattr(settings,
                'OPENWISP_ADMIN_INDEX_TITLE',
                'Network administration')
    )


def openwisp_admin(site_url=None):
    """
    openwisp_admin function is deprecated and discouraged to use,
    you should use admin_site object from openwisp_utils.admin_theme.site instead
    """
    admin.site.site_title = OpenwispAdminSite.site_title
    admin.site.site_url = site_url  # link to frontend
    admin.site.site_header = OpenwispAdminSite.site_header
    admin.site.index_title = OpenwispAdminSite.index_title
