from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from . import CreateMixin
from ..models import Operator, Project, RadiusAccounting

User = get_user_model()


class TestAdmin(TestCase, CreateMixin):
    accounting_model = RadiusAccounting

    def setUp(self):
        user = User.objects.create_superuser(username='administrator',
                                             password='admin',
                                             email='test@test.org')
        self.client.force_login(user)

    def test_radiusaccounting_change(self):
        options = dict(username='bobby', session_id='1')
        obj = self._create_radius_accounting(**options)
        response = self.client.get(reverse(
                                   'admin:test_project_radiusaccounting_change',
                                   args=[obj.pk]))
        self.assertContains(response, 'ok')
        self.assertNotContains(response, 'errors')

    def test_radiusaccounting_changelist(self):
        url = reverse('admin:test_project_radiusaccounting_changelist')
        response = self.client.get(url)
        self.assertNotContains(response, 'Add accounting')

    def test_alwayshaschangedmixin(self):
        self.assertEqual(Project.objects.count(), 0)
        self.assertEqual(Operator.objects.count(), 0)
        params = {
            'name': 'test',
            'operator_set-TOTAL_FORMS': 1,
            'operator_set-INITIAL_FORMS': 0,
            'operator_set-MIN_NUM_FORMS': 0,
            'operator_set-MAX_NUM_FORMS': 1000,
            'operator_set-0-first_name': 'test',
            'operator_set-0-last_name': 'test',
            'operator_set-0-project': '',
            'operator_set-0-id': '',
        }
        url = reverse('admin:test_project_project_add')
        r = self.client.post(url, params,
                             follow=True)
        self.assertNotContains(r, 'error')
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(Operator.objects.count(), 1)
        project = Project.objects.first()
        self.assertEqual(project.name, params['name'])

    def test_custom_admin_site(self):
        url = reverse('admin:password_change_done')
        response = self.client.get(url)
        content = str(response.content)
        # Check if CustomAdminSite worked
        self.assertIn(
            "Custom attribute in CustomAdminSite is working.", content)
