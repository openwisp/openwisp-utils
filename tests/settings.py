import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = '@s8$swhj9du^aglt5+@ut^)wepr+un1m7r*+ixcq(-5i^st=y^'

SELENIUM_HEADLESS = True if os.environ.get('SELENIUM_HEADLESS', False) else False

DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # test project
    'test_project',
    'openwisp_utils.admin_theme',
    'django.contrib.sites',
    # admin
    'django.contrib.admin',
    'admin_auto_filters',
    # rest framework
    'rest_framework',
    'drf_yasg',
]

EXTENDED_APPS = ('openwisp_controller', 'django_loci')  # Just for testing purposes

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'openwisp_utils.staticfiles.DependencyFinder',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'urls'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
STATIC_URL = '/static/'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'OPTIONS': {
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
                'openwisp_utils.loaders.DependencyLoader',
            ],
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'openwisp_utils.admin_theme.context_processor.menu_groups',
                'openwisp_utils.admin_theme.context_processor.admin_theme_settings',
                'test_project.context_processors.test_theme_helper',
            ],
        },
    }
]

DATABASES = {
    'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': 'openwisp_utils.db'}
}

OPENWISP_ADMIN_SITE_CLASS = 'test_project.site.CustomAdminSite'

SITE_ID = 1
EMAIL_PORT = '1025'
LOGIN_REDIRECT_URL = 'admin:index'
ACCOUNT_LOGOUT_REDIRECT_URL = LOGIN_REDIRECT_URL

# during development only
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# only for automated test purposes
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'test_project.api.throttling.CustomScopedRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {'anon': '20/hour'},
}

CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}
OPENWISP_TEST_ADMIN_MENU_ITEMS = [{'model': 'test_project.Project'}]

OPENWISP_ADMIN_THEME_LINKS = [
    {
        'type': 'text/css',
        'href': 'admin/css/openwisp.css',
        'rel': 'stylesheet',
        'media': 'all',
    },
    {
        'type': 'text/css',
        'href': 'menu-test.css',
        'rel': 'stylesheet',
        'media': 'all',
    },  # custom css for testing menu icons
    {
        'type': 'image/x-icon',
        'href': 'ui/openwisp/images/favicon.png',
        'rel': 'icon',
    },
]
OPENWISP_ADMIN_THEME_JS = ['dummy.js']

# local settings must be imported before test runner otherwise they'll be ignored
try:
    from local_settings import *
except ImportError:
    pass
