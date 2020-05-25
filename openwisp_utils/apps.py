from django.apps import AppConfig
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


class UtilsAppConfig(AppConfig):
    name = 'openwisp_utils'
    label = 'utils'
    verbose_name = _('OpenWISP utils')

    DEFAULT_REST_FRAMEWORK = {
        'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.ScopedRateThrottle'],
        'DEFAULT_THROTTLE_RATES': {'anon': '40/hour'},
    }

    def ready(self, *args, **kwargs):
        self.configure_drf_defaults()

    def configure_drf_defaults(self):
        config = getattr(settings, 'REST_FRAMEWORK', {})
        for key in self.DEFAULT_REST_FRAMEWORK.keys():
            config.setdefault(key, self.DEFAULT_REST_FRAMEWORK[key])
        setattr(settings, 'REST_FRAMEWORK', config)
