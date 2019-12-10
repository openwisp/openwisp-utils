from django.utils.module_loading import import_string

from .settings import OPENWISP_ADMIN_SITE_CLASS

admin_site_class = import_string(OPENWISP_ADMIN_SITE_CLASS)
admin_site = admin_site_class()
