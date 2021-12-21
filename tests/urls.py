from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('openwisp_utils.api.urls')),
    path('api/v1/', include('test_project.api.urls')),
    # Only used for tests
    path(
        'menu-test-view/',
        TemplateView.as_view(template_name='test_project/menu_test.html'),
        name='menu-test-view',
    ),
]
