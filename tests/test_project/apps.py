from django.db.models import Case, Count, Sum, When
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from openwisp_utils.admin_theme import (
    register_dashboard_chart,
    register_dashboard_template,
)
from openwisp_utils.admin_theme.menu import register_menu_group, register_menu_subitem
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
    default_auto_field = 'django.db.models.AutoField'

    def ready(self, *args, **kwargs):
        super().ready(*args, **kwargs)
        self.register_default_menu_items()
        self.register_dashboard_charts()
        self.register_menu_groups()

    def register_default_menu_items(self):
        items = [{'model': 'test_project.Shelf'}]
        register_menu_items(items)
        # Required only for testing
        register_menu_items(items, name_menu='OPENWISP_TEST_ADMIN_MENU_ITEMS')

    def register_dashboard_charts(self):
        register_dashboard_chart(
            position=0,
            config={
                'name': _('Operator Project Distribution'),
                'query_params': {
                    'app_label': 'test_project',
                    'model': 'operator',
                    'group_by': 'project__name',
                },
                'colors': {'Utils': 'red', 'User': 'orange'},
                'labels': {'Utils': _('Utils'), 'User': _('User')},
                'quick_link': {
                    'url': reverse_lazy('admin:test_project_operator_changelist'),
                    'label': 'Open Operators list',
                    'title': 'View complete list of operators',
                    'custom_css_classes': ['negative-top-20'],
                },
            },
        )
        register_dashboard_chart(
            position=1,
            config={
                'name': _('Operator presence in projects'),
                'query_params': {
                    'app_label': 'test_project',
                    'model': 'project',
                    'annotate': {
                        'with_operator': Count(
                            Case(
                                When(
                                    operator__isnull=False,
                                    then=1,
                                )
                            )
                        ),
                        'without_operator': Count(
                            Case(
                                When(
                                    operator__isnull=True,
                                    then=1,
                                )
                            )
                        ),
                    },
                    'aggregate': {
                        'with_operator__sum': Sum('with_operator'),
                        'without_operator__sum': Sum('without_operator'),
                    },
                },
                'colors': {
                    'with_operator__sum': '#267126',
                    'without_operator__sum': '#353c44',
                },
                'labels': {
                    'with_operator__sum': _('Projects with operators'),
                    'without_operator__sum': _('Projects without operators'),
                },
                'filters': {
                    'key': 'with_operator',
                    'with_operator__sum': 'true',
                    'without_operator__sum': 'false',
                },
            },
        )
        register_dashboard_template(
            position=0,
            config={
                'template': 'dashboard_test.html',
                'css': ('dashboard-test.css',),
                'js': ('dashboard-test.js',),
            },
            extra_config={'test_extra_config1': 'dashboard-test.config1'},
        )
        register_dashboard_template(
            position=1,
            config={
                'template': 'dashboard_test.html',
            },
            extra_config={'test_extra_config2': 'dashboard-test.config2'},
        )

    def register_menu_groups(self):
        auth_config = {
            'label': _('Authentication And Authorization'),
            'items': {
                2: {
                    'label': 'Add user',
                    'model': 'auth.User',
                    'name': 'add',
                    'icon': 'add-user',
                },
                1: {
                    'model': 'auth.User',
                    'name': 'changelist',
                    'icon': 'user',
                    'label': _('Users'),
                },
            },
            'icon': 'auth',
        }
        docs_config = {
            'label': _('Docs'),
            'items': {
                1: {
                    'label': _('OpenWISP'),
                    'url': 'https://openwisp.org/',
                    'icon': 'link',
                }
            },
            'icon': 'docs',
        }
        register_menu_group(
            position=31,
            config={
                'model': 'test_project.Shelf',
                'name': 'changelist',
                'label': _('Shelfs'),
                'icon': 'shelf',
            },
        )
        register_menu_group(position=32, config=auth_config)
        register_menu_group(position=33, config=docs_config)
        register_menu_subitem(
            group_position=33,
            item_position=2,
            config={
                'label': _('Code'),
                'url': 'https://openwisp.org/thecode.html',
                'icon': 'code',
            },
        )


del ApiAppConfig
