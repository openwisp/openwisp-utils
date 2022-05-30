from collections import OrderedDict
from copy import deepcopy
from unittest import TestCase as UnitTestCase
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase as DjangoTestCase
from django.urls import reverse
from openwisp_utils.admin_theme import (
    register_dashboard_chart,
    register_dashboard_template,
    unregister_dashboard_chart,
    unregister_dashboard_template,
)
from openwisp_utils.admin_theme.dashboard import get_dashboard_context

from ..models import Project
from . import AdminTestMixin
from .utils import MockRequest, MockUser


class TestDashboardSchema(UnitTestCase):
    @patch('openwisp_utils.admin_theme.dashboard.DASHBOARD_CHARTS', OrderedDict())
    def test_register_dashboard_chart(self):
        from openwisp_utils.admin_theme.dashboard import DASHBOARD_CHARTS

        dashboard_element = {
            'name': 'Test Chart',
            'query_params': {
                'app_label': 'app_label',
                'model': 'model_name',
                'group_by': 'property',
            },
            'colors': {'value1': 'red', 'value2': 'green'},
        }

        with self.subTest('Registering new dashboard element'):
            register_dashboard_chart(-1, dashboard_element)
            self.assertIn(-1, DASHBOARD_CHARTS)

        with self.subTest('Registering a chart at existing position'):
            with self.assertRaises(ImproperlyConfigured):
                register_dashboard_chart(-1, dashboard_element)

        with self.subTest('Unregistering a chart that does not exists'):
            with self.assertRaises(ImproperlyConfigured):
                unregister_dashboard_chart('Chart Test')

        with self.subTest('Unregistering "Test Chart"'):
            unregister_dashboard_chart('Test Chart')
            self.assertNotIn(-1, DASHBOARD_CHARTS)

        with self.subTest('Invalid "quick_link" config'):
            invalid_config = deepcopy(dashboard_element)
            invalid_config['quick_link'] = {'register': True}
            with self.assertRaises(AssertionError) as context:
                register_dashboard_chart(-2, invalid_config)
            self.assertEqual(
                str(context.exception), 'url must be defined when using quick_link'
            )
            invalid_config['quick_link']['url'] = '/'
            with self.assertRaises(AssertionError) as context:
                register_dashboard_chart(-2, invalid_config)
            self.assertEqual(
                str(context.exception), 'label must be defined when using quick_link'
            )
            invalid_config['quick_link']['label'] = 'index'
            invalid_config['quick_link']['custom_css_classes'] = 'custom'
            with self.assertRaises(AssertionError) as context:
                register_dashboard_chart(-2, invalid_config)
            self.assertEqual(
                str(context.exception),
                'custom_css_classes must be either a list or a tuple',
            )

    def test_miscellaneous_DASHBOARD_CHARTS_validation(self):
        with self.subTest('Registering with incomplete config'):
            with self.assertRaises(AssertionError):
                register_dashboard_chart(-1, dict())

        with self.subTest('Registering with invalid position argument'):
            with self.assertRaises(ImproperlyConfigured):
                register_dashboard_chart(['Test Chart'], dict())

        with self.subTest('Registering with invalid config'):
            with self.assertRaises(ImproperlyConfigured):
                register_dashboard_chart(-1, tuple())

        with self.subTest('Unregistering with invalid name'):
            with self.assertRaises(ImproperlyConfigured):
                unregister_dashboard_chart(dict())

        with self.subTest('Test filters required when not group_by'):
            with self.assertRaises(AssertionError) as ctx:
                register_dashboard_chart(
                    -1,
                    {
                        'name': 'Test Chart',
                        'query_params': {
                            'app_label': 'app_label',
                            'model': 'model_name',
                            'annotate': {},
                        },
                    },
                )
            self.assertIn('filters', str(ctx.exception))

    @patch('openwisp_utils.admin_theme.dashboard.DASHBOARD_TEMPLATES', OrderedDict())
    def test_register_dashboard_template(self):
        from openwisp_utils.admin_theme.dashboard import DASHBOARD_TEMPLATES

        dashboard_element = {
            'template': 'password_change_done.html',
        }

        with self.subTest('Registering new dashboard template'):
            register_dashboard_template(-1, dashboard_element)
            self.assertIn(-1, DASHBOARD_TEMPLATES)
            self.assertEqual(DASHBOARD_TEMPLATES[-1][0], dashboard_element)

        with self.subTest('Registering a dashboard template at existing position'):
            with self.assertRaises(ImproperlyConfigured):
                register_dashboard_template(-1, dashboard_element)

        with self.subTest('Unregistering a dashboard template that does not exists'):
            with self.assertRaises(ImproperlyConfigured):
                unregister_dashboard_template('test.html')

        with self.subTest('Unregistering "password_change_done.html"'):
            unregister_dashboard_template('password_change_done.html')
            self.assertNotIn(-1, DASHBOARD_TEMPLATES)

    def test_miscellaneous_DASHBOARD_TEMPLATES_validation(self):
        with self.subTest('Registering with incomplete config'):
            with self.assertRaises(AssertionError):
                register_dashboard_template(-1, dict())

        with self.subTest('Registering with invalid position argument'):
            with self.assertRaises(ImproperlyConfigured):
                register_dashboard_template(['template.html'], dict())

        with self.subTest('Registering with invalid config'):
            with self.assertRaises(ImproperlyConfigured):
                register_dashboard_template(0, tuple())

        with self.subTest('Unregistering with invalid template path'):
            with self.assertRaises(ImproperlyConfigured):
                unregister_dashboard_template(dict())

        with self.subTest('Registering with invalid extra_config'):
            dashboard_element = {'template': 'test.html'}
            with self.assertRaises(ImproperlyConfigured):
                register_dashboard_template(1, dashboard_element, 'test')

    @patch('openwisp_utils.admin_theme.dashboard.DASHBOARD_TEMPLATES', OrderedDict())
    @patch('openwisp_utils.admin_theme.dashboard.DASHBOARD_CHARTS', OrderedDict())
    def test_dashboard_after_charts(self):
        register_dashboard_template(
            position=0,
            config={'template': 'password_change_done.html'},
            after_charts=False,
        )
        register_dashboard_template(
            position=1,
            config={'template': 'password_change_redirect.html'},
            after_charts=True,
        )
        mocked_user = MockUser(is_superuser=True)
        mocked_request = MockRequest(user=mocked_user)
        context = get_dashboard_context(mocked_request)
        self.assertEqual(
            context['dashboard_templates_before_charts'], ['password_change_done.html']
        )
        self.assertEqual(
            context['dashboard_templates_after_charts'],
            ['password_change_redirect.html'],
        )


class TestAdminDashboard(AdminTestMixin, DjangoTestCase):
    def test_index_content(self):
        response = self.client.get(reverse('admin:index'))
        self.assertContains(response, 'Operator Project Distribution')
        self.assertContains(response, '\'values\': [1, 1]')
        self.assertContains(response, '\'labels\': [\'User\', \'Utils\']')
        self.assertContains(response, '\'colors\': [\'orange\', \'red\']')
        self.assertContains(
            response,
            (
                '\'quick_link\': {\'url\': \'/admin/test_project/operator/\','
                ' \'label\': \'Open Operators list\', \'title\':'
                ' \'View complete list of operators\', \'custom_css_classes\':'
                ' [\'negative-top-20\']'
            ),
        )
        self.assertContains(
            response, '<div style="display:none">Testing dashboard</div>'
        )
        self.assertContains(response, 'dashboard-test.js')
        self.assertContains(response, 'dashboard-test.css')
        self.assertContains(response, 'dashboard-test.config1')
        self.assertContains(response, 'dashboard-test.config2')
        self.assertContains(response, 'jquery.init.js')
        self.assertContains(response, 'Operator presence in projects')
        self.assertContains(response, 'with_operator')
        self.assertContains(response, 'without_operator')
        self.assertContains(response, 'project__name__exact')

        with self.subTest('Test no data'):
            Project.objects.all().delete()
            response = self.client.get(reverse('admin:index'))
            self.assertContains(response, "'values': []")

    def test_non_existent_model(self):
        register_dashboard_chart(
            -1,
            {
                'name': 'Test Chart',
                'query_params': {
                    'app_label': 'app_label',
                    'model': 'model_name',
                    'group_by': 'property',
                },
            },
        )
        with self.assertRaises(ImproperlyConfigured):
            self.client.get(reverse('admin:index'))
        unregister_dashboard_chart('Test Chart')

    @patch('openwisp_utils.admin_theme.settings.ADMIN_DASHBOARD_ENABLED', False)
    def test_dashboard_disabled(self):
        with self.subTest('Test redirect from login page'):
            response = self.client.get(reverse('admin:login'))
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, reverse('admin:index'))

        with self.subTest('Test "Dashboard" is absent from menu items'):
            response = self.client.get(reverse('admin:index'))
            self.assertNotContains(response, 'Dashboard')
