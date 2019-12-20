from django.conf.urls import url
from openwisp_utils.admin_theme.admin import admin, openwisp_admin

openwisp_admin()

urlpatterns = [
    url(r'^admin/', admin.site.urls),
]
