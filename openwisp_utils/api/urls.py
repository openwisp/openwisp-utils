from django.conf.urls import url
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from openwisp_utils import settings as app_settings
from rest_framework import permissions

urlpatterns = []

if app_settings.REST_SWAGGER:
    schema_view = get_schema_view(
        openapi.Info(**app_settings.API_INFO),
        public=True,
        permission_classes=[permissions.AllowAny],
    )

    urlpatterns += [
        url(
            r'^swagger(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0),
            name='schema-json',
        ),
        url(
            r'^swagger/$',
            schema_view.with_ui('swagger', cache_timeout=0),
            name='schema-swagger-ui',
        ),
        url(
            r'^redoc/$',
            schema_view.with_ui('redoc', cache_timeout=0),
            name='schema-redoc',
        ),
    ]
