from django.apps import AppConfig
from django.conf import settings


class TestAppConfig(AppConfig):
    name = 'test_project'
    label = 'test_project'

    def ready(self, *args, **kwargs):
        super(TestAppConfig, self).ready(*args, **kwargs)
        self.add_default_menu_items()

    def add_default_menu_items(self):
        menu_setting = 'OPENWISP_DEFAULT_ADMIN_MENU_ITEMS'
        items = [
            {'model': 'test_project.Shelf'},
        ]
        setattr(settings, menu_setting, items)
