from django.conf.urls import include, url
from openwisp_utils.admin_theme.admin import admin
from openwisp_utils.admin_theme.admin import admin_site


urlpatterns = [
    url(r'^accounts/', include('openwisp_users.accounts.urls')),
    url(r'^admin/', admin_site.urls),
]