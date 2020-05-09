from django.conf import settings

EXTENDED_APPS = getattr(settings, 'EXTENDED_APPS', [])
REST_SWAGGER = getattr(settings, 'OPENWISP_REST_SWAGGER', True)
