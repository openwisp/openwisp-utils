from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from openwisp_utils.admin import ReadOnlyAdmin
from openwisp_utils.admin_theme import settings as admin_theme_settings
from openwisp_utils.admin_theme.apps import OpenWispAdminThemeConfig
from openwisp_utils.admin_theme.checks import admin_theme_settings_checks

from ..admin import ProjectAdmin
from ..models import Operator, Project, RadiusAccounting
from . import AdminTestMixin, CreateMixin

User = get_user_model()


class TestAdmin(AdminTestMixin, CreateMixin, TestCase):
    TEST_KEY = 'w1gwJxKaHcamUw62TQIPgYchwLKn3AA0'
    accounting_model = RadiusAccounting

    def test_radiusaccounting_change(self):
        options = dict(username='bobby', session_id='1')
        obj = self._create_radius_accounting(**options)
        response = self.client.get(
            reverse('admin:test_project_radiusaccounting_change', args=[obj.pk])
        )
        self.assertContains(response, 'ok')
        self.assertNotContains(response, 'errors')

    def test_radiusaccounting_changelist(self):
        url = reverse('admin:test_project_radiusaccounting_changelist')
        response = self.client.get(url)
        self.assertNotContains(response, 'Add accounting')

    def test_alwayshaschangedmixin(self):
        project_query = Project.objects.filter(name='test')
        operator_query = Operator.objects.filter(first_name='test')
        self.assertEqual(project_query.count(), 0)
        self.assertEqual(operator_query.count(), 0)
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
        r = self.client.post(url, params, follow=True)
        self.assertNotContains(r, 'error')
        self.assertEqual(project_query.count(), 1)
        self.assertEqual(operator_query.count(), 1)
        project = project_query.first()
        operator = operator_query.first()
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

    def test_readonlyadmin_exclude(self):
        class TestReadOnlyAdmin(ReadOnlyAdmin):
            exclude = ['id']

        modeladmin = TestReadOnlyAdmin(RadiusAccounting, AdminSite)
        self.assertEqual(modeladmin.readonly_fields, ['session_id', 'username'])

    def test_readonlyadmin_fields(self):
        class TestReadOnlyAdmin(ReadOnlyAdmin):
            pass

        modeladmin = TestReadOnlyAdmin(RadiusAccounting, AdminSite)
        self.assertEqual(modeladmin.readonly_fields, ['id', 'session_id', 'username'])

    def test_context_processor(self):
        url = reverse('admin:index')
        response = self.client.get(url)
        self.assertContains(response, 'class="shelf-icon"')

    def test_superuser_always_sees_menu_items(self):
        url = reverse('admin:index')
        r = self.client.get(url)
        self.assertContains(r, 'class="shelf-icon"')

    def test_operator_with_perm_can_see_menu_item(self):
        user = User.objects.create(
            username='operator',
            password='pass',
            email='email@email',
            is_staff=True,
            is_superuser=False,
        )
        permission = Permission.objects.filter(codename__endswith='shelf')
        user.user_permissions.add(*permission)
        user.refresh_from_db()
        self.client.force_login(user)
        url = reverse('admin:index')
        r = self.client.get(url)
        self.assertContains(r, 'class="shelf-icon"')

    def test_operator_without_perm_cant_see_menu_item(self):
        user = User.objects.create(
            username='operator',
            password='pass',
            email='email@email',
            is_staff=True,
            is_superuser=False,
        )
        self.client.force_login(user)
        url = reverse('admin:index')
        r = self.client.get(url)
        self.assertNotContains(r, 'class="shelf-icon"')

    def test_menu_visibility(self):
        with self.subTest("Test menu is visible when user is logged in"):
            url = reverse('admin:index')
            response = self.client.get(url)
            self.assertContains(response, 'id="menu"')

        with self.subTest("Test menu is not visible when user is not logged in"):
            self.client.logout()
            response = self.client.get('/admin/login/')
            self.assertNotContains(response, 'id="menu"')

    def test_uuid_field_in_change(self):
        p = Project.objects.create(name='test-project')
        path = reverse('admin:test_project_project_change', args=[p.pk])
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'field-uuid')

    def test_uuid_field_in_add(self):
        path = reverse('admin:test_project_project_add')
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'field-uuid')
        self.assertContains(response, 'field-receive_url')

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
        expected_receive_url = 'http://testserver/api/v1/receive_project/'
        response = self.client.get(path)
        self.assertContains(response, 'field-receive_url')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, expected_receive_url)

    def test_admin_theme_css_setting(self):
        # test for improper configuration : not a list
        setattr(
            admin_theme_settings, 'OPENWISP_ADMIN_THEME_LINKS', 'string instead of list'
        )
        self.assertIn(
            'OPENWISP_ADMIN_THEME_LINKS',
            str(admin_theme_settings_checks(OpenWispAdminThemeConfig)[0]),
        )
        # test for improper configuration : list_elements != type(dict)
        setattr(
            admin_theme_settings,
            'OPENWISP_ADMIN_THEME_LINKS',
            ['/static/custom-admin-theme.css'],
        )
        self.assertIn(
            'OPENWISP_ADMIN_THEME_LINKS',
            str(admin_theme_settings_checks(OpenWispAdminThemeConfig)[0]),
        )
        # test for improper configuration: dict missing required keys
        setattr(admin_theme_settings, 'OPENWISP_ADMIN_THEME_LINKS', [{'wrong': True}])
        self.assertIn(
            'OPENWISP_ADMIN_THEME_LINKS',
            str(admin_theme_settings_checks(OpenWispAdminThemeConfig)[0]),
        )
        # test with desired configuration
        setattr(
            admin_theme_settings,
            'OPENWISP_ADMIN_THEME_LINKS',
            [
                {
                    'href': '/static/custom-admin-theme.css',
                    'rel': 'stylesheet',
                    'type': 'text/css',
                    'media': 'all',
                }
            ],
        )
        response = self.client.get(reverse('admin:index'))
        self.assertContains(response, '/static/custom-admin-theme.css" media="all"')

    def test_admin_theme_js_setting(self):
        # test for improper configuration : not a list
        setattr(
            admin_theme_settings, 'OPENWISP_ADMIN_THEME_JS', 'string instead of list'
        )
        self.assertIn(
            'OPENWISP_ADMIN_THEME_JS',
            str(admin_theme_settings_checks(OpenWispAdminThemeConfig)[0]),
        )
        # test for improper configuration : list_elements != type(str)
        setattr(admin_theme_settings, 'OPENWISP_ADMIN_THEME_JS', [0, 1, 2])
        self.assertIn(
            'OPENWISP_ADMIN_THEME_JS',
            str(admin_theme_settings_checks(OpenWispAdminThemeConfig)[0]),
        )
        # test with desired configuration
        setattr(
            admin_theme_settings,
            'OPENWISP_ADMIN_THEME_JS',
            ['/static/openwisp-utils/js/uuid.js'],
        )
        response = self.client.get(reverse('admin:index'))
        self.assertContains(response, 'src="/static/openwisp-utils/js/uuid.js"')

    def test_login(self):
        url = reverse('admin:login')
        with self.subTest('Test with logged in user'):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, reverse('admin:index'))

        with self.subTest('Test with logged out user'):
            self.client.logout()
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'login')
