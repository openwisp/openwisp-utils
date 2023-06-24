from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TestCase

from ..models import OrganizationRadiusSettings, Project
from . import CreateMixin


class TestModel(TestCase):
    TEST_KEY = 'w1gwJxKaHcamUw62TQIPgYchwLKn3AA0'

    def test_key_validator(self):
        p = Project.objects.create(name='test_project')
        p.key = 'key/key'
        with self.assertRaises(ValidationError):
            p.full_clean()
        p.key = 'key.key'
        with self.assertRaises(ValidationError):
            p.full_clean()
        p.key = 'key key'
        with self.assertRaises(ValidationError):
            p.full_clean()
        p.key = self.TEST_KEY
        p.full_clean()


class TestFallbackFields(CreateMixin, TestCase):
    org_radius_settings_model = OrganizationRadiusSettings

    def test_fallback_field_falsy_values(self):
        org_rad_settings = self._create_org_radius_settings()

        def _verify_none_database_value(field_name):
            setattr(org_rad_settings, field_name, '')
            org_rad_settings.full_clean()
            org_rad_settings.save()
            with connection.cursor() as cursor:
                cursor.execute(
                    f'SELECT {field_name} FROM'
                    f' {org_rad_settings._meta.app_label}_{org_rad_settings._meta.model_name}'
                    f' WHERE id = \'{org_rad_settings.id}\';',
                )
                row = cursor.fetchone()
            self.assertEqual(row[0], None)

        with self.subTest('Test "greeting_text" field'):
            _verify_none_database_value('greeting_text')

        with self.subTest('Test "password_reset_url" field'):
            _verify_none_database_value('password_reset_url')

        with self.subTest('Test "extra_config" field'):
            _verify_none_database_value('extra_config')

    def test_fallback_boolean_choice_field(self):
        org_rad_settings = self._create_org_radius_settings()

        with self.subTest('Test is_active set to None'):
            org_rad_settings.is_active = None
            # Ensure fallback value is returned
            self.assertEqual(org_rad_settings.get_field_value('is_active'), False)

        with self.subTest('Test fallback value changed'):
            with patch.object(
                # The fallback value is set on project startup, hence
                # it also requires mocking.
                OrganizationRadiusSettings._meta.get_field('is_active'),
                'fallback',
                True,
            ):
                org_rad_settings.is_active = None
                self.assertEqual(org_rad_settings.get_field_value('is_active'), True)

        with self.subTest('Test overriding default value'):
            org_rad_settings.is_active = True
            self.assertEqual(org_rad_settings.get_field_value('is_active'), True)

    def test_fallback_char_choice_field(self):
        org_rad_settings = self._create_org_radius_settings()

        with self.subTest('Test is_first_name_required set to None'):
            org_rad_settings.is_first_name_required = None
            # Ensure fallback value is returned
            self.assertEqual(
                org_rad_settings.get_field_value('is_first_name_required'), 'disabled'
            )

        with self.subTest('Test fallback value changed'):
            with patch.object(
                # The fallback value is set on project startup, hence
                # it also requires mocking.
                OrganizationRadiusSettings._meta.get_field('is_first_name_required'),
                'fallback',
                'mandatory',
            ):
                org_rad_settings.is_first_name_required = None
                self.assertEqual(
                    org_rad_settings.get_field_value('is_first_name_required'),
                    'mandatory',
                )

        with self.subTest('Test overriding default value'):
            org_rad_settings.is_first_name_required = 'allowed'
            self.assertEqual(
                org_rad_settings.get_field_value('is_first_name_required'), 'allowed'
            )
