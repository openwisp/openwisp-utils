from django.conf import settings

EXTENDED_APPS = getattr(settings, 'EXTENDED_APPS', [])

# API settings
API_DOCS = getattr(settings, 'OPENWISP_API_DOCS', True)
API_INFO = getattr(
    settings,
    'OPENWISP_API_INFO',
    {
        'title': 'OpenWISP API',
        'default_version': 'v1',
        'description': 'OpenWISP REST API',
    },
)

OPENWISP_EMAIL_TEMPLATE = getattr(
    settings, 'OPENWISP_EMAIL_TEMPLATE', 'openwisp-utils/email_template.html',
)

OPENWISP_EMAIL_LOGO = getattr(
    settings,
    'OPENWISP_EMAIL_LOGO',
    'https://raw.githubusercontent.com/openwisp/openwisp-utils/master/openwisp_utils/'
    'static/openwisp-utils/images/openwisp-logo.png',
)
