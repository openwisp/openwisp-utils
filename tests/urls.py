from django.conf.urls import url
from django.contrib import admin
from django.urls import include

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/v1/', include('openwisp_utils.api.urls')),
    url(r'^test_api/', include('test_project.test_api.urls')),
]
