from collections import OrderedDict
from unittest import TestCase
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from openwisp_utils.admin_theme import (
    register_dashboard_element,
    unregister_dashboard_element,
)


class TestDashboardSchema(TestCase):
    @patch('openwisp_utils.admin_theme.schema.DASHBOARD_SCHEMA', OrderedDict())
    def test_register_dashboard_element(self):
        from openwisp_utils.admin_theme.schema import DASHBOARD_SCHEMA

        dashboard_element = {
            'query_params': {
                'app_label': 'app_label',
                'model': 'model_name',
                'group_by': 'property',
            },
            'colors': {'value1': 'red', 'value2': 'green'},
        }

        with self.subTest('Registering new dashboard element'):
            register_dashboard_element('Test Chart', dashboard_element)
            self.assertIn('Test Chart', DASHBOARD_SCHEMA)

        with self.subTest('Re-registering a dashboard element'):
            with self.assertRaises(ImproperlyConfigured):
                register_dashboard_element('Test Chart', dashboard_element)

        with self.subTest('Unregistering a dashboard element which does not exists'):
            with self.assertRaises(ImproperlyConfigured):
                unregister_dashboard_element('Chart Test')

        with self.subTest('Unregistering "Test Chart"'):
            unregister_dashboard_element('Test Chart')
            self.assertNotIn('Test Chart', DASHBOARD_SCHEMA)

    def test_miscellaneous_dashboard_schema_validation(self):
        with self.subTest('Registering with incomplete dashboard element schema'):
            with self.assertRaises(AssertionError):
                register_dashboard_element('Test Chart', dict())

        with self.subTest('Registering with improper dashboard element name'):
            with self.assertRaises(ImproperlyConfigured):
                register_dashboard_element(['Test Chart'], dict())

        with self.subTest('Registering with improper dashboard element schema'):
            with self.assertRaises(ImproperlyConfigured):
                register_dashboard_element('Test Chart', tuple())

        with self.subTest('Unregistering with improper dashboard element name'):
            with self.assertRaises(ImproperlyConfigured):
                unregister_dashboard_element(dict())
