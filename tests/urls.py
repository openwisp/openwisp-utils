from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('openwisp_utils.api.urls')),
    path('api/v1/', include('test_project.api.urls')),
]
