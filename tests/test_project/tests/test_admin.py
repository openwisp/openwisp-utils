from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ..models import Operator, Project, RadiusAccounting
from . import CreateMixin

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

        change_params = {
            'name': 'test',
            'operator_set-TOTAL_FORMS': 1,
            'operator_set-INITIAL_FORMS': 1,
            'operator_set-MIN_NUM_FORMS': 0,
            'operator_set-MAX_NUM_FORMS': 1000,
            'operator_set-0-first_name': 'test2',
            'operator_set-0-last_name': 'test2',
            'operator_set-0-id': project.pk,
        }
        change_url = reverse('admin:test_project_project_change', args=[project.pk])
        self.client.post(change_url, change_params)
        self.assertContains(self.client.get(change_url), 'value="test2"')

    def test_custom_admin_site(self):
        url = reverse('admin:password_change_done')
        response = self.client.get(url)
        content = "Custom attribute in CustomAdminSite is working."
        # Check if CustomAdminSite worked
        self.assertContains(response, content)

    def test_timereadonlyadminmixin(self):
        url = reverse('admin:test_project_shelf_add')
        response = self.client.get(url)
        self.assertContains(response, 'readonly')

    def test_context_processor(self):
        url = reverse('admin:index')
        response = self.client.get(url)
        self.assertContains(response, 'class="shelf"')
