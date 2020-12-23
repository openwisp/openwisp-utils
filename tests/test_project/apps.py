from openwisp_utils.admin_theme.schema import register_dashboard_element
from openwisp_utils.api.apps import ApiAppConfig
from openwisp_utils.utils import register_menu_items


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
        self.register_default_menu_items()

    def register_default_menu_items(self):
        items = [{'model': 'test_project.Shelf'}]
        register_menu_items(items)
        # Required only for testing
        register_menu_items(items, name_menu='OPENWISP_TEST_ADMIN_MENU_ITEMS')

    register_dashboard_element(
        'Project Graph',
        {
            'query_params': {
                'app_label': 'test_project',
                'model': 'operator',
                'group_by': 'project__name',
            },
        },
    )
