from django.conf.urls import url
from openwisp_utils.admin_theme.site import admin_site

urlpatterns = [
    url(r'^admin/', admin_site.urls),
]
