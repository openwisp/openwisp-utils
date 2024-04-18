from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, modify_settings
from django.urls import reverse

from ..models import MetricCollectionConsent

User = get_user_model()


class TestMetricCollectionConsent(TestCase):
    def _get_user(self, **kwargs):
        opts = dict(
            username='tester',
            email='tester@example.com',
            password='tester',
        )
        opts.update(kwargs)
        return User.objects.create(**opts)

    def test_metric_collection_disclaimer(self):
        expected_message = (
            '<li class="warning">We collect anonymous usage metrics that'
            ' helps to improve OpenWISP. You can opt-out from sharing these'
            ' metrics from the <a href="/admin/openwisp-system-info/">'
            'System Information page</a>.</li>'
        )
        non_superuser = self._get_user(is_staff=True, is_superuser=False)
        superuser1 = self._get_user(
            username='superuser',
            email='superuser@example.com',
            is_staff=True,
            is_superuser=True,
        )
        superuser2 = self._get_user(
            username='superuser1',
            email='superuser1@example.com',
            is_staff=True,
            is_superuser=True,
        )
        path = reverse('admin:index')
        with self.subTest('Test message not shown to non-superuser'):
            self.client.force_login(non_superuser)
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, expected_message)
            # MetricCollectionConsent object is only created when
            # superuser access the index page for the first time
            self.assertEqual(MetricCollectionConsent.objects.count(), 0)

        with self.subTest('Test message shown once to superuser'):
            self.client.force_login(superuser1)
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, expected_message)
            self.assertEqual(MetricCollectionConsent.objects.count(), 1)
            consent_obj = MetricCollectionConsent.objects.first()
            self.assertEqual(consent_obj.has_shown_disclaimer, True)

        with self.subTest('Test message not shown again to superuser'):
            self.client.force_login(superuser1)
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, expected_message)
            # THere can be only atmost 1 object of MetricCollectionConsent
            self.assertEqual(MetricCollectionConsent.objects.count(), 1)
            consent_obj.refresh_from_db()
            self.assertEqual(consent_obj.has_shown_disclaimer, True)

        with self.subTest('Test message not shown to another superuser'):
            self.client.force_login(superuser2)
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, expected_message)
            # THere can be only atmost 1 object of MetricCollectionConsent
            self.assertEqual(MetricCollectionConsent.objects.count(), 1)
            consent_obj.refresh_from_db()
            self.assertEqual(consent_obj.has_shown_disclaimer, True)

    @patch('test_project.apps.TestAppConfig.register_default_menu_items')
    @patch('test_project.apps.TestAppConfig.register_dashboard_charts')
    @patch('test_project.apps.TestAppConfig.register_menu_groups')
    @patch(
        'openwisp_utils.admin_theme.apps.OpenWispAdminThemeConfig.register_menu_groups'
    )
    @modify_settings(INSTALLED_APPS={'remove': ['openwisp_utils.metrics_collection']})
    def test_metric_collection_disclaimer_metrics_collection_app_not_installed(
        self, *args
    ):
        superuser = self._get_user(is_staff=True, is_superuser=True)
        self.client.force_login(superuser)
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'messagelist')

    def test_metric_collection_consent_change(self):
        non_superuser = self._get_user(is_staff=True, is_superuser=False)
        superuser = self._get_user(
            username='superuser',
            email='superuser@example.com',
            is_staff=True,
            is_superuser=True,
        )
        consent_obj = MetricCollectionConsent.objects.create()
        path = reverse('admin:ow-info')
        with self.subTest('Test unauthenticated user makes post request'):
            response = self.client.post(path, {'user_consented': False})
            self.assertEqual(response.status_code, 302)
            self.assertEqual(
                response.url, '/admin/login/?next=/admin/openwisp-system-info/'
            )
            consent_obj.refresh_from_db()
            self.assertEqual(consent_obj.user_consented, True)

        self.client.force_login(non_superuser)
        with self.subTest('Test non-superuser makes post request'):
            response = self.client.post(path, {'user_consented': False})
            self.assertEqual(response.status_code, 200)
            consent_obj.refresh_from_db()
            self.assertEqual(consent_obj.user_consented, True)

        self.client.force_login(superuser)
        with self.subTest('Test superuser makes a get request'):
            response = self.client.get(path, {'user_consented': True})
            self.assertEqual(response.status_code, 200)
            consent_obj.refresh_from_db()
            # GET request would not have any affect on changing the consent_obj
            self.assertEqual(consent_obj.user_consented, True)

        with self.subTest('Test superuser opt-out using post request'):
            response = self.client.post(path, {'user_consented': False})
            self.assertEqual(response.status_code, 200)
            consent_obj.refresh_from_db()
            self.assertEqual(consent_obj.user_consented, False)

        with self.subTest('Test superuser opt-in using post request'):
            response = self.client.post(path, {'user_consented': True})
            self.assertEqual(response.status_code, 200)
            consent_obj.refresh_from_db()
            self.assertEqual(consent_obj.user_consented, True)

        with self.subTest('Test changing "has_shown_disclaimer" field'):
            self.assertEqual(consent_obj.has_shown_disclaimer, False)
            response = self.client.post(path, {'has_shown_disclaimer': True})
            self.assertEqual(response.status_code, 200)
            consent_obj.refresh_from_db()
            # There should be no change to the field because it is
            # not part of the form.
            self.assertEqual(consent_obj.has_shown_disclaimer, False)
