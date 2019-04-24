from django.contrib import admin
from django.utils.translation import ugettext_lazy

from django.conf import settings


def openwisp_admin(site_url=None):
    # <title>
    admin.site.site_title = getattr(settings,
                                    'OPENWISP_ADMIN_SITE_TITLE',
                                    'OpenWISP Admin')
    # link to frontend
    admin.site.site_url = site_url
    # h1 text
    admin.site.site_header = getattr(settings,
                                     'OPENWISP_ADMIN_SITE_HEADER',
                                     'OpenWISP')
    # text at the top of the admin index page
    admin.site.index_title = ugettext_lazy(
        getattr(settings,
                'OPENWISP_ADMIN_INDEX_TITLE',
                'Network administration')
    )
