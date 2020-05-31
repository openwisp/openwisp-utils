from django.conf import settings
from openwisp_utils.api.apps import ApiAppConfig


class TestAppConfig(ApiAppConfig):
    name = 'test_project'
    label = 'test_project'

    API_ENABLED = True
    REST_FRAMEWORK_SETTINGS = {
        'DEFAULT_THROTTLE_RATES': {'test': '10/minute'},
        'TEST': True,
    }

    def ready(self, *args, **kwargs):
        super().ready(*args, **kwargs)
        self.add_default_menu_items()

    def add_default_menu_items(self):
        menu_setting = 'OPENWISP_DEFAULT_ADMIN_MENU_ITEMS'
        items = [
            {'model': 'test_project.Shelf'},
        ]
        setattr(settings, menu_setting, items)
