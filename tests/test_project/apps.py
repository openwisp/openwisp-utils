from django.apps import AppConfig
from django.conf import settings

from openwisp_utils import settings as app_settings


class TestAppConfig(AppConfig):
    name = 'test_project'
    label = 'test_project'

    _default_drf = {
        'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.ScopedRateThrottle'],
        'DEFAULT_THROTTLE_RATES': {
            'anon': app_settings.API_RATE_ANON,
        },
    }

    def ready(self, *args, **kwargs):
        super(TestAppConfig, self).ready(*args, **kwargs)
        self.add_default_menu_items()
        self.configure_drf_defaults()

    def add_default_menu_items(self):
        menu_setting = 'OPENWISP_DEFAULT_ADMIN_MENU_ITEMS'
        items = [
            {'model': 'test_project.Shelf'},
        ]
        setattr(settings, menu_setting, items)

    def configure_drf_defaults(self):
        config = getattr(settings, 'REST_FRAMEWORK', {})
        config.update(self._default_drf)
        setattr(settings, 'REST_FRAMEWORK', config)
