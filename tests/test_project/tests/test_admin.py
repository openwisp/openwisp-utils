from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ..admin import ProjectAdmin
from ..models import Operator, Project, RadiusAccounting
from . import CreateMixin

User = get_user_model()


class TestAdmin(TestCase, CreateMixin):
    TEST_KEY = 'w1gwJxKaHcamUw62TQIPgYchwLKn3AA0'
    accounting_model = RadiusAccounting

    def setUp(self):
        user = User.objects.create_superuser(username='administrator',
                                             password='admin',
                                             email='test@test.org')
        self.client.force_login(user)
        self.site = AdminSite()

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
            'key': self.TEST_KEY,
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
        operator = Operator.objects.first()
        self.assertEqual(project.name, params['name'])
        self.assertEqual(operator.first_name, 'test')
        self.assertEqual(operator.last_name, 'test')

        change_params = {
            'name': 'test',
            'key': self.TEST_KEY,
            'operator_set-TOTAL_FORMS': 1,
            'operator_set-INITIAL_FORMS': 1,
            'operator_set-MIN_NUM_FORMS': 0,
            'operator_set-MAX_NUM_FORMS': 1000,
            'operator_set-0-first_name': 'test2',
            'operator_set-0-last_name': 'test2',
            'operator_set-0-id': operator.id,
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

    def test_uuid_field_in_change(self):
        p = Project.objects.create(name='test-project')
        path = reverse('admin:test_project_project_change', args=[p.pk])
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'field-uuid')

    def test_receive_url_admin(self):
        p = Project.objects.create(name='test_receive_url_admin_project')
        ma = ProjectAdmin(Project, self.site)

        url = ma.receive_url(p)
        self.assertIn(str(p.id), url)
        self.assertIn(p.key, url)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ok')
        self.assertContains(response, 'test_receive_url_admin_project')

    def test_receive_url_field_in_change(self):
        p = Project.objects.create(name='test')

        path = reverse('admin:test_project_project_change', args=[p.pk])
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'field-receive_url')

        ma = ProjectAdmin(Project, self.site)
        url = ma.receive_url(p)
        self.assertContains(response, url)
