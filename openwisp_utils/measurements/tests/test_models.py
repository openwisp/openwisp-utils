from unittest.mock import patch

import requests
from django.apps import apps
from django.db import migrations
from django.test import TestCase, override_settings
from freezegun import freeze_time

from .. import tasks
from ..models import OpenwispVersion
from . import (
    _ENABLED_OPENWISP_MODULES_RETURN_VALUE,
    _HEARTBEAT_EVENTS,
    _MODULES_UPGRADE_EXPECTED_EVENTS,
    _NEW_INSTALLATION_EVENTS,
    _OS_DETAILS_RETURN_VALUE,
)


class TestOpenwispVersion(TestCase):
    def test_get_upgraded_models_on_new_installation(self):
        self.assertEqual(
            OpenwispVersion.get_upgraded_modules(tasks.get_enabled_openwisp_modules()),
            {},
        )

    @patch.object(tasks, 'get_openwisp_version', return_value='23.0.0a')
    @patch.object(
        tasks,
        'get_enabled_openwisp_modules',
        return_value=_ENABLED_OPENWISP_MODULES_RETURN_VALUE,
    )
    @patch.object(
        tasks,
        'get_os_details',
        return_value=_OS_DETAILS_RETURN_VALUE,
    )
    @patch.object(tasks, 'post_clean_insights_events')
    @freeze_time('2023-12-01 00:00:00')
    def test_new_installation(self, mocked_post, *args):
        OpenwispVersion.objects.all().delete()
        tasks.send_clean_insights_measurements.delay()
        mocked_post.assert_called_with(_NEW_INSTALLATION_EVENTS)
        self.assertEqual(OpenwispVersion.objects.count(), 1)
        version = OpenwispVersion.objects.first()
        expected_module_version = {
            'OpenWISP Version': '23.0.0a',
            **_ENABLED_OPENWISP_MODULES_RETURN_VALUE,
        }
        self.assertEqual(version.module_version, expected_module_version)

    @patch.object(tasks, 'get_openwisp_version', return_value='23.0.0a')
    @patch.object(
        tasks,
        'get_enabled_openwisp_modules',
        return_value=_ENABLED_OPENWISP_MODULES_RETURN_VALUE,
    )
    @patch.object(
        tasks,
        'get_os_details',
        return_value=_OS_DETAILS_RETURN_VALUE,
    )
    @patch.object(tasks, 'post_clean_insights_events')
    @freeze_time('2023-12-01 00:00:00')
    def test_heartbeat(self, mocked_post, *args):
        expected_module_version = {
            'OpenWISP Version': '23.0.0a',
            **_ENABLED_OPENWISP_MODULES_RETURN_VALUE,
        }
        self.assertEqual(OpenwispVersion.objects.count(), 1)
        tasks.send_clean_insights_measurements.delay()
        mocked_post.assert_called_with(_HEARTBEAT_EVENTS)
        self.assertEqual(OpenwispVersion.objects.count(), 1)
        version = OpenwispVersion.objects.first()
        self.assertEqual(version.module_version, expected_module_version)

    @patch.object(tasks, 'get_openwisp_version', return_value='23.0.0a')
    @patch.object(
        tasks,
        'get_enabled_openwisp_modules',
        return_value=_ENABLED_OPENWISP_MODULES_RETURN_VALUE,
    )
    @patch.object(
        tasks,
        'get_os_details',
        return_value=_OS_DETAILS_RETURN_VALUE,
    )
    @patch.object(tasks, 'post_clean_insights_events')
    @freeze_time('2023-12-01 00:00:00')
    def test_modules_upgraded(self, mocked_post, *args):
        self.assertEqual(OpenwispVersion.objects.count(), 1)
        OpenwispVersion.objects.update(
            module_version={
                'OpenWISP Version': '22.10.0',
                'openwisp-utils': '1.0.5',
                'openwisp-users': '1.0.2',
            }
        )
        tasks.send_clean_insights_measurements.delay()
        mocked_post.assert_called_with(_MODULES_UPGRADE_EXPECTED_EVENTS)

        self.assertEqual(OpenwispVersion.objects.count(), 1)
        version = OpenwispVersion.objects.first()
        expected_module_version = {
            'OpenWISP Version': '23.0.0a',
            **_ENABLED_OPENWISP_MODULES_RETURN_VALUE,
        }
        self.assertEqual(version.module_version, expected_module_version)

    @patch('time.sleep')
    @patch('logging.Logger.warning')
    @patch('logging.Logger.error')
    def test_post_clean_insights_events_400_response(
        self, mocked_error, mocked_warning, *args
    ):
        bad_response = requests.Response()
        bad_response.status_code = 400
        with patch.object(requests, 'post', return_value=bad_response) as mocked_post:
            tasks.send_clean_insights_measurements.delay()
        mocked_post.assert_called_once()
        mocked_warning.assert_not_called()
        mocked_error.assert_called_with(
            'Maximum tries reach to upload Clean Insights measurements. Error: HTTP 400 Response'
        )

    @patch('time.sleep')
    @patch('logging.Logger.warning')
    @patch('logging.Logger.error')
    def test_post_clean_insights_events_500_response(
        self, mocked_error, mocked_warning, *args
    ):
        bad_response = requests.Response()
        bad_response.status_code = 500
        with patch.object(requests, 'post', return_value=bad_response) as mocked_post:
            tasks.send_clean_insights_measurements.delay()
        self.assertEqual(len(mocked_post.mock_calls), 3)
        self.assertEqual(len(mocked_warning.mock_calls), 3)
        mocked_warning.assert_called_with(
            'Error posting clean insights events: HTTP 500 Response. Retrying in 5 seconds.'
        )
        mocked_error.assert_called_with(
            'Maximum tries reach to upload Clean Insights measurements. Error: HTTP 500 Response'
        )

    @patch('time.sleep')
    @patch('logging.Logger.warning')
    @patch('logging.Logger.error')
    def test_post_clean_insights_events_204_response(
        self, mocked_error, mocked_warning, *args
    ):
        bad_response = requests.Response()
        bad_response.status_code = 204
        with patch.object(
            tasks.requests, 'post', return_value=bad_response
        ) as mocked_post:
            tasks.send_clean_insights_measurements.delay()
        self.assertEqual(len(mocked_post.mock_calls), 1)
        mocked_warning.assert_not_called()
        mocked_error.assert_not_called()

    @patch('time.sleep')
    @patch('logging.Logger.warning')
    @patch('logging.Logger.error')
    @patch(
        'requests.post',
        side_effect=requests.ConnectionError('Error connecting to the server'),
    )
    def test_post_clean_insights_events_connection_error(
        self, mocked_post, mocked_error, mocked_warning, *args
    ):
        tasks.send_clean_insights_measurements.delay()
        self.assertEqual(len(mocked_post.mock_calls), 3)
        self.assertEqual(len(mocked_warning.mock_calls), 3)
        mocked_warning.assert_called_with(
            'Error posting clean insights events: Error connecting to the server. Retrying in 5 seconds.'
        )
        mocked_error.assert_called_with(
            'Maximum tries reach to upload Clean Insights measurements. Error: Error connecting to the server'
        )

    @patch.object(tasks.send_clean_insights_measurements, 'delay')
    def test_post_migrate_receiver(self, mocked_task, *args):
        app = apps.get_app_config('measurements')

        with self.subTest('Test task not called when plan is empty'):
            app.post_migrate_receiver(plan=[])
            mocked_task.assert_not_called()
        mocked_task.reset_mock()

        with self.subTest(
            'Test task not called when first migration in plan is not for ContentTypes'
        ):
            app.post_migrate_receiver(
                plan=[
                    (
                        migrations.Migration(
                            name='0001_initial', app_label='openwisp_users'
                        ),
                        False,
                    )
                ]
            )
            mocked_task.assert_not_called()
        mocked_task.reset_mock()
        plan = [
            (
                migrations.Migration(name='0001_initial', app_label='contenttypes'),
                False,
            )
        ]

        with self.subTest(
            'Test task called when first migration in plan is for ContentTypes'
        ):
            app.post_migrate_receiver(plan=plan)
            mocked_task.assert_called()
        mocked_task.reset_mock()

        with self.subTest('Test task not called in development'):
            with override_settings(DEBUG=True):
                app.post_migrate_receiver(plan=plan)
            mocked_task.assert_not_called()
