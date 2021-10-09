from django.contrib import admin
from django.urls import include, path
from test_project.views import non_admin_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('test-non-admin/', non_admin_view, name='test_non_admin'),
    path('api/v1/', include('openwisp_utils.api.urls')),
    path('api/v1/', include('test_project.api.urls')),
]
