from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from openwisp_utils.admin_theme import settings as admin_theme_settings
from openwisp_utils.admin_theme.apps import OpenWispAdminThemeConfig
from openwisp_utils.admin_theme.checks import admin_theme_settings_checks

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
        content = 'Custom attribute in CustomAdminSite is working.'
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
        ma.receive_url_baseurl = 'http://chanedbasedurl'

        url = ma.receive_url(p)

        self.assertIn(str(p.id), url)
        self.assertIn(p.key, url)
        self.assertIn('http://chanedbasedurl', url)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test_receive_url_admin_project')

    def test_receive_url_field_in_change(self):
        p = Project.objects.create(name='test_receive_url_change')
        path = reverse('admin:test_project_project_change', args=[p.pk])
        expected_receive_url = 'http://testserver/test_api/receive_project/'
        response = self.client.get(path)
        self.assertContains(response, 'field-receive_url')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, expected_receive_url)

    def test_admin_theme_css_setting(self):
        # test for improper configuration : not a list
        setattr(admin_theme_settings, 'OPENWISP_ADMIN_THEME_LINKS', 'string instead of list')
        self.assertIn('OPENWISP_ADMIN_THEME_LINKS',
                      str(admin_theme_settings_checks(OpenWispAdminThemeConfig)[0]))
        # test for improper configuration : list_elements != type(dict)
        setattr(admin_theme_settings, 'OPENWISP_ADMIN_THEME_LINKS',
                ['/static/custom-admin-theme.css'])
        self.assertIn('OPENWISP_ADMIN_THEME_LINKS',
                      str(admin_theme_settings_checks(OpenWispAdminThemeConfig)[0]))
        # test for improper configuration: dict missing required keys
        setattr(admin_theme_settings, 'OPENWISP_ADMIN_THEME_LINKS', [{'wrong': True}])
        self.assertIn('OPENWISP_ADMIN_THEME_LINKS',
                      str(admin_theme_settings_checks(OpenWispAdminThemeConfig)[0]))
        # test with desired configuration
        setattr(admin_theme_settings, 'OPENWISP_ADMIN_THEME_LINKS',
                [{
                    'href': '/static/custom-admin-theme.css',
                    'rel': 'stylesheet',
                    'type': 'text/css',
                    'media': 'all'
                }])
        response = self.client.get(reverse('admin:index'))
        self.assertContains(response, '/static/custom-admin-theme.css" media="all"')

    def test_admin_theme_js_setting(self):
        # test for improper configuration : not a list
        setattr(admin_theme_settings, 'OPENWISP_ADMIN_THEME_JS', 'string instead of list')
        self.assertIn('OPENWISP_ADMIN_THEME_JS',
                      str(admin_theme_settings_checks(OpenWispAdminThemeConfig)[0]))
        # test for improper configuration : list_elements != type(str)
        setattr(admin_theme_settings, 'OPENWISP_ADMIN_THEME_JS', [0, 1, 2])
        self.assertIn('OPENWISP_ADMIN_THEME_JS',
                      str(admin_theme_settings_checks(OpenWispAdminThemeConfig)[0]))
        # test with desired configuration
        setattr(admin_theme_settings, 'OPENWISP_ADMIN_THEME_JS',
                ['/static/openwisp-utils/js/uuid.js'])
        response = self.client.get(reverse('admin:index'))
        self.assertContains(response, 'src="/static/openwisp-utils/js/uuid.js"')
