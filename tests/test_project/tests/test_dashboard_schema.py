from collections import OrderedDict
from unittest import TestCase
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from openwisp_utils.admin_theme import (
    register_dashboard_element,
    unregister_dashboard_element,
)


class TestDashboardConfig(TestCase):
    @patch('openwisp_utils.admin_theme.dashboard.DASHBOARD_CONFIG', OrderedDict())
    def test_register_dashboard_element(self):
        from openwisp_utils.admin_theme.dashboard import DASHBOARD_CONFIG

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
            register_dashboard_element(-1, dashboard_element)
            self.assertIn(-1, DASHBOARD_CONFIG)

        with self.subTest('Registering a dashboard element at existing position'):
            with self.assertRaises(ImproperlyConfigured):
                register_dashboard_element(-1, dashboard_element)

        with self.subTest('Unregistering a dashboard element that does not exists'):
            with self.assertRaises(ImproperlyConfigured):
                unregister_dashboard_element('Chart Test')

        with self.subTest('Unregistering "Test Chart"'):
            unregister_dashboard_element('Test Chart')
            self.assertNotIn('Test Chart', DASHBOARD_CONFIG)

    def test_miscellaneous_DASHBOARD_CONFIG_validation(self):
        with self.subTest('Registering with incomplete dashboard element config'):
            with self.assertRaises(AssertionError):
                register_dashboard_element(-1, dict())

        with self.subTest('Registering with invalid position argument'):
            with self.assertRaises(ImproperlyConfigured):
                register_dashboard_element(['Test Chart'], dict())

        with self.subTest('Registering with invalid dashboard element config'):
            with self.assertRaises(ImproperlyConfigured):
                register_dashboard_element('Test Chart', tuple())

        with self.subTest('Unregistering with invalid dashboard element name'):
            with self.assertRaises(ImproperlyConfigured):
                unregister_dashboard_element(dict())
