from django.conf.urls import include, url
from openwisp_utils.admin_theme.admin import admin, openwisp_admin

openwisp_admin()

urlpatterns = [
    url(r'^accounts/', include('openwisp_users.accounts.urls')),
    url(r'^admin/', include(admin.site.urls)),
]
