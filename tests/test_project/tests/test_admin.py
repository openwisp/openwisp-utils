from unittest.mock import MagicMock, patch

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.urls import reverse
from openwisp_utils.admin import CopyableFieldError, CopyableFieldsAdmin, ReadOnlyAdmin
from openwisp_utils.admin_theme import settings as admin_theme_settings
from openwisp_utils.admin_theme.apps import OpenWispAdminThemeConfig, _staticfy
from openwisp_utils.admin_theme.checks import admin_theme_settings_checks
from openwisp_utils.admin_theme.filters import InputFilter, SimpleInputFilter

from ..admin import ProjectAdmin, ShelfAdmin
from ..models import (
    Operator,
    OrganizationRadiusSettings,
    Project,
    RadiusAccounting,
    Shelf,
)
from . import AdminTestMixin, CreateMixin

User = get_user_model()


class TestAdmin(AdminTestMixin, CreateMixin, TestCase):
    TEST_KEY = 'w1gwJxKaHcamUw62TQIPgYchwLKn3AA0'
    accounting_model = RadiusAccounting
    org_radius_settings_model = OrganizationRadiusSettings

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
        self.assertContains(response, '<span class="shelf icon">')

    def test_superuser_always_sees_menu_items(self):
        url = reverse('admin:index')
        r = self.client.get(url)
        self.assertContains(r, '<span class="shelf icon">')

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
        self.assertContains(r, '<span class="shelf icon">')

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
        self.assertNotContains(r, '<span class="shelf icon">')

    def test_menu_items_visibility(self):
        with self.subTest("Test menu items are visible when user is logged in"):
            url = reverse('admin:index')
            response = self.client.get(url)
            self.assertContains(response, 'class="nav"')

        with self.subTest("Test menu items are not visible when user is not logged in"):
            self.client.logout()
            response = self.client.get('/admin/login/')
            self.assertNotContains(response, 'id="nav"')

    def test_menu_on_non_admin_page(self):
        url = reverse('menu-test-view')
        with self.subTest('Test menu visibility when user is a staff'):
            user = User.objects.create(
                username='tester',
                password='pass',
                email='email@email',
                is_staff=True,
                is_superuser=False,
            )
            self.client.force_login(user)
            response = self.client.get(url)
            self.assertContains(response, 'class="nav"')
            self.assertContains(
                response, '<strong>Does user has staff privileges?:</strong> True'
            )
            self.client.logout()

        with self.subTest('Test menu visibility when user is not staff'):
            # Test with non staff user
            user = User.objects.create(
                username='tester2',
                password='pass',
                email='email@email',
                is_staff=False,
                is_superuser=False,
            )
            self.client.force_login(user)
            response = self.client.get(url)
            self.assertNotContains(response, 'class="nav"')
            self.assertContains(
                response, '<strong>Does user has staff privileges?:</strong> False'
            )

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

    def test_copyablefields_admin(self):
        class TestCopyableFieldAdmin(CopyableFieldsAdmin):
            copyable_fields = ('session_id', 'username')

        options = dict(username='bobby', session_id='1')
        radius_acc = self._create_radius_accounting(**options)
        ma = TestCopyableFieldAdmin(RadiusAccounting, AdminSite)
        path = reverse(
            'admin:test_project_radiusaccounting_change', args=[radius_acc.pk]
        )
        self.assertEqual(
            ma.get_readonly_fields(self.client.request, radius_acc),
            TestCopyableFieldAdmin.copyable_fields,
        )
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'field-username')
        self.assertContains(response, 'field-session_id')

    def test_invalid_copyablefields_admin_error(self):
        class TestCopyableFieldAdmin(CopyableFieldsAdmin):
            pass

        ma = TestCopyableFieldAdmin(Project, AdminSite)
        ma.copyable_fields = ('invalid_field',)
        copyable_field_err = "('invalid_field',) not in TestCopyableFieldAdmin.fields"
        with self.assertRaises(CopyableFieldError) as err:
            ma.get_fields(self.client.request)
        self.assertIn(copyable_field_err, err.exception.args[0])

    def test_copyablefields_admin_fields_order(self):
        path = reverse('admin:test_project_project_add')
        self.client.get(path)
        ma = ProjectAdmin(Project, self.site)
        # 'uuid' should be missing from ma.get_fields()
        # because we're testing the project admin add form,
        # and now we're adding it here again only to assert the admin field order
        self.assertEqual(ma.fields, ('uuid', *ma.get_fields(self.client.request)))
        self.assertEqual(
            ma.readonly_fields, ma.get_readonly_fields(self.client.request)
        )

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

    def test_stacked_inline_help_text(self):
        project = Project.objects.create(name='test_receive_url_change')
        Operator.objects.create(first_name='Jane', last_name='Doe', project=project)
        path = reverse('admin:test_project_project_change', args=[project.pk])
        response = self.client.get(path)
        self.assertContains(
            response, 'Only added operators will have permission to access the project.'
        )
        self.assertContains(response, 'https://github.com/openwisp/openwisp-utils/')
        # Response should contain static in 'icon_url'
        self.assertContains(
            response, '<img src="/static/admin/img/icon-alert.svg">', html=True
        )

    def test_admin_theme_css_setting(self):
        # test for improper configuration : not a list
        with patch.object(
            admin_theme_settings, 'OPENWISP_ADMIN_THEME_LINKS', 'string instead of list'
        ):
            self.assertIn(
                'OPENWISP_ADMIN_THEME_LINKS',
                str(admin_theme_settings_checks(OpenWispAdminThemeConfig)[0]),
            )
        # test for improper configuration : list_elements != type(dict)
        with patch.object(
            admin_theme_settings,
            'OPENWISP_ADMIN_THEME_LINKS',
            ['/static/custom-admin-theme.css'],
        ):
            self.assertIn(
                'OPENWISP_ADMIN_THEME_LINKS',
                str(admin_theme_settings_checks(OpenWispAdminThemeConfig)[0]),
            )
        # test for improper configuration: dict missing required keys
        with patch.object(
            admin_theme_settings, 'OPENWISP_ADMIN_THEME_LINKS', [{'wrong': True}]
        ):
            self.assertIn(
                'OPENWISP_ADMIN_THEME_LINKS',
                str(admin_theme_settings_checks(OpenWispAdminThemeConfig)[0]),
            )
        # test with desired configuration
        # Here openwisp_utils.admin_theme.theme.THEME_LINKS has been
        # mocked instead of app_settings.OPENWISP_ADMIN_THEME_LINKS
        # because openwisp_utils.admin_theme.theme.THEME_LINKS creates
        # a copy of app_settings.OPENWISP_ADMIN_THEME_LINKS at project
        # startup. Therefore, mocking app_settings.OPENWISP_ADMIN_THEME_LINKS
        # will have no effect here.
        with patch(
            'openwisp_utils.admin_theme.theme.THEME_LINKS',
            [
                {
                    'href': '/static/custom-admin-theme.css',
                    'rel': 'stylesheet',
                    'type': 'text/css',
                    'media': 'all',
                }
            ],
        ):
            response = self.client.get(reverse('admin:index'))
            self.assertContains(response, '/static/custom-admin-theme.css" media="all"')

        # test if files are loaded with staticfiles
        response = self.client.get(reverse('admin:index'))
        self.assertContains(response, '/static/admin/css/openwisp.css" media="all"')
        self.assertContains(response, '/static/menu-test.css" media="all"')
        self.assertContains(response, 'href="/static/ui/openwisp/images/favicon.png"')
        self.assertContains(response, '/static/dummy.js')

    def test_admin_theme_static_backward_compatible(self):
        # test for backward compatibility
        with patch('openwisp_utils.admin_theme.apps.static', side_effect=ValueError):
            self.assertEqual(
                _staticfy('admin/css/openwisp.css'), 'admin/css/openwisp.css'
            )
        # test static files are loaded with staticfiles
        self.assertEqual(
            _staticfy('admin/css/openwisp.css'), '/static/admin/css/openwisp.css'
        )

    def test_admin_theme_js_setting(self):
        # test for improper configuration : not a list
        with patch.object(
            admin_theme_settings, 'OPENWISP_ADMIN_THEME_JS', 'string instead of list'
        ):
            self.assertIn(
                'OPENWISP_ADMIN_THEME_JS',
                str(admin_theme_settings_checks(OpenWispAdminThemeConfig)[0]),
            )
        # test for improper configuration : list_elements != type(str)
        with patch.object(admin_theme_settings, 'OPENWISP_ADMIN_THEME_JS', [0, 1, 2]):
            self.assertIn(
                'OPENWISP_ADMIN_THEME_JS',
                str(admin_theme_settings_checks(OpenWispAdminThemeConfig)[0]),
            )
        # test with desired configuration
        # Here openwisp_utils.admin_theme.theme.THEME_JS has been
        # mocked instead of app_settings.OPENWISP_ADMIN_THEME_JS
        # because openwisp_utils.admin_theme.theme.THEME_JS creates
        # a copy of app_settings.OPENWISP_ADMIN_THEME_JS at project
        # startup. Therefore, mocking app_settings.OPENWISP_ADMIN_THEME_JS
        # will have no effect here.
        with patch(
            'openwisp_utils.admin_theme.theme.THEME_JS',
            ['/static/openwisp-utils/js/uuid.js'],
        ):
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

    def test_filters(self):
        with self.subTest('Test when number of filters is less than equal to 4'):
            url = reverse('admin:test_project_operator_changelist')
            response = self.client.get(url)
            real_count = self._assert_contains(
                response,
                'class="ow-filter',
                status_code=response.status_code,
                msg_prefix='',
                html=False,
            )[1]
            self.assertLessEqual(real_count, 4)
            self.assertNotContains(response, 'id="ow-apply-filter"')

        with self.subTest('Test when number of filters is greater than 5'):
            url = reverse('admin:test_project_shelf_changelist')
            response = self.client.get(url)
            real_count = self._assert_contains(
                response,
                'class="ow-filter',
                status_code=response.status_code,
                msg_prefix='',
                html=False,
            )[1]
            self.assertGreater(real_count, 5)
            self.assertContains(response, 'id="ow-apply-filter"')

    def test_simple_input_filter(self):
        class TestFilter(SimpleInputFilter):
            title = 'Test'
            parameter_name = 'test'

        filter = TestFilter(
            request=None, params={}, model=Shelf, model_admin=ShelfAdmin
        )
        with self.assertRaises(NotImplementedError):
            filter.queryset(None, None)

    def test_input_filter(self):
        with self.assertRaises(ImproperlyConfigured):
            field = MagicMock()
            field.target_field = True
            InputFilter(
                field,
                request=None,
                params={},
                model=Shelf,
                model_admin=ShelfAdmin,
                field_path='mocked',
            )
        with self.assertRaises(ImproperlyConfigured):
            InputFilter(
                Shelf.created_at,
                request=None,
                params={},
                model=Shelf,
                model_admin=ShelfAdmin,
                field_path='created_at',
            )

    def test_ow_auto_filter_view(self):
        url = reverse('admin:ow-auto-filter')
        url = f'{url}?app_label=test_project&model_name=shelf&field_name=book'
        user = User.objects.create(
            username='operator',
            password='pass',
            email='email@email',
            is_staff=True,
            is_superuser=False,
        )
        self.client.force_login(user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_ow_auto_filter_view_reverse_relation(self):
        url = reverse('admin:ow-auto-filter')
        url = f'{url}?app_label=test_project&model_name=shelf&field_name=book'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_ow_autocomplete_filter_uuid_exception(self):
        url = reverse('admin:test_project_book_changelist')
        url = f'{url}?shelf__id=invalid'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '“invalid” is not a valid UUID.')

    def test_organization_radius_settings_admin(self):
        org_rad_settings = self._create_org_radius_settings(
            is_active=True,
            is_first_name_required=None,
            greeting_text=None,
            password_reset_url='http://localhost:8000/reset-password/',
        )
        url = reverse(
            'admin:test_project_organizationradiussettings_change',
            args=[org_rad_settings.pk],
        )

        with self.subTest('Test default values are rendered'):
            response = self.client.get(url)
            # Overridden value is selected for BooleanChoiceField
            self.assertContains(
                response,
                '<select name="is_active" id="id_is_active">'
                '<option value="">Default (Disabled)</option>'
                '<option value="True" selected>Enabled</option>'
                '<option value="False">Disabled</option></select>',
                html=True,
            )
            # Default value is selected for FallbackCharChoiceField
            self.assertContains(
                response,
                '<select name="is_first_name_required" id="id_is_first_name_required">'
                '<option value="" selected>Default (Disabled)</option>'
                '<option value="disabled">Disabled</option>'
                '<option value="allowed">Allowed</option>'
                '<option value="mandatory">Mandatory</option></select>',
                html=True,
            )
            # Default value is used for FallbackCharField
            self.assertContains(
                response,
                '<input type="text" name="greeting_text" value="Welcome to OpenWISP!"'
                ' class="vTextField" maxlength="200" id="id_greeting_text">',
            )
            # Overridden value is used for the FallbackURLField
            self.assertContains(
                response,
                '<input type="url" name="password_reset_url"'
                ' value="http://localhost:8000/reset-password/"'
                ' class="vURLField" maxlength="200" id="id_password_reset_url">',
            )

        with self.subTest('Test overriding default values from admin'):
            payload = {
                # Setting the default value for FallbackBooleanChoiceField
                'is_active': '',
                # Overriding the default value for FallbackCharChoiceField
                'is_first_name_required': 'allowed',
                # Overriding the default value for FallbackCharField
                'greeting_text': 'Greeting text',
                # Setting the default value for FallbackURLField
                'password_reset_url': '',
                # Setting the default value for FallbackTextField
                'extra_config': '',
            }
            response = self.client.post(url, payload, follow=True)
            self.assertEqual(response.status_code, 200)
            org_rad_settings.refresh_from_db()
            self.assertEqual(org_rad_settings.get_field_value('is_active'), False)
            self.assertEqual(
                org_rad_settings.get_field_value('is_first_name_required'), 'allowed'
            )
            self.assertEqual(
                org_rad_settings.get_field_value('greeting_text'), 'Greeting text'
            )
            self.assertEqual(
                org_rad_settings.get_field_value('password_reset_url'),
                'http://localhost:8000/admin/password_change/',
            )
            self.assertEqual(
                org_rad_settings.get_field_value('extra_config'), 'no data'
            )
