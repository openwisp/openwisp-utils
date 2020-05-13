from django.conf import settings

EXTENDED_APPS = getattr(settings, 'EXTENDED_APPS', [])

# API settings
REST_SWAGGER = getattr(settings, 'OPENWISP_REST_SWAGGER', True)
API_INFO = getattr(
    settings,
    'OPENWISP_API_INFO',
    {
        'title': 'OpenWISP API',
        'default_version': 'v1',
        'description': 'OpenWISP REST API',
    },
)
