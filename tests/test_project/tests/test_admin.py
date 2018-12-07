from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from . import CreateMixin
from ..models import Project, RadiusAccounting

User = get_user_model()


class TestAdmin(TestCase, CreateMixin):
    accounting_model = RadiusAccounting
    project_model = Project

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
        self.project_model.objects.count()
        options = dict(name='test')
        params = self._get_defaults(options)
        p = self.project_model(**params)
        p.full_clean()
        p.save()
        self.assertEqual(self.project_model.objects.count(), 1)
        project = self.project_model.objects.first()
        self.assertEqual(project.name, params['name'])
