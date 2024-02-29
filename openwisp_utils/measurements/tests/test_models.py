from datetime import datetime, timezone
from unittest.mock import patch

import requests
from django.apps import apps
from django.db import migrations
from django.test import TestCase, override_settings
from freezegun import freeze_time
from urllib3.response import HTTPResponse

from .. import tasks
from ..models import OpenwispVersion
from . import (
    _ENABLED_OPENWISP_MODULES_RETURN_VALUE,
    _HEARTBEAT_METRICS,
    _MODULES_UPGRADE_EXPECTED_METRICS,
    _NEW_INSTALLATION_METRICS,
    _OS_DETAILS_RETURN_VALUE,
)


class TestOpenwispVersion(TestCase):
    def setUp(self):
        # The post_migrate signal creates the first OpenwispVersion object
        # and uses the actual modules installed in the Python environment.
        # This would cause tests to fail when other modules are also installed.
        # import ipdb; ipdb.set_trace()
        OpenwispVersion.objects.update(
            module_version={
                'OpenWISP Version': '23.0.0a',
                **_ENABLED_OPENWISP_MODULES_RETURN_VALUE,
            },
            created=datetime.strptime(
                '2023-11-01 00:00:00', '%Y-%m-%d %H:%M:%S'
            ).replace(tzinfo=timezone.utc),
        )

    def test_get_upgraded_modules_when_openwispversion_object_does_not_exist(self):
        OpenwispVersion.objects.all().delete()
        self.assertEqual(
            OpenwispVersion.get_upgraded_modules(tasks.get_enabled_openwisp_modules()),
            {},
        )

    def test_get_upgraded_modules_on_new_installation(self):
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
    @patch.object(tasks, 'post_usage_metrics')
    @freeze_time('2023-12-01 00:00:00')
    def test_new_installation(self, mocked_post, *args):
        OpenwispVersion.objects.all().delete()
        tasks.send_usage_metrics.delay()
        mocked_post.assert_called_with(_NEW_INSTALLATION_METRICS)
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
    @patch.object(tasks, 'post_usage_metrics')
    @freeze_time('2023-12-01 00:00:00')
    def test_heartbeat(self, mocked_post, *args):
        expected_module_version = {
            'OpenWISP Version': '23.0.0a',
            **_ENABLED_OPENWISP_MODULES_RETURN_VALUE,
        }
        self.assertEqual(OpenwispVersion.objects.count(), 1)
        tasks.send_usage_metrics.delay()
        mocked_post.assert_called_with(_HEARTBEAT_METRICS)
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
    @patch.object(tasks, 'post_usage_metrics')
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
        tasks.send_usage_metrics.delay()
        mocked_post.assert_called_with(_MODULES_UPGRADE_EXPECTED_METRICS)

        self.assertEqual(OpenwispVersion.objects.count(), 2)
        version = OpenwispVersion.objects.first()
        expected_module_version = {
            'OpenWISP Version': '23.0.0a',
            **_ENABLED_OPENWISP_MODULES_RETURN_VALUE,
        }
        self.assertEqual(version.module_version, expected_module_version)

    @freeze_time('2023-12-01 00:00:00')
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
    @patch.object(tasks, 'post_usage_metrics')
    @patch.object(tasks, 'get_openwisp_module_metrics')
    def test_send_usage_metrics_upgrade_only_flag(
        self, mocked_get_openwisp_module_metrics, *args
    ):
        self.assertEqual(OpenwispVersion.objects.count(), 1)
        # Store old versions of OpenWISP modules in OpenwispVersion object
        OpenwispVersion.objects.update(
            module_version={
                'OpenWISP Version': '22.10.0',
                'openwisp-utils': '1.0.5',
                'openwisp-users': '1.0.2',
            }
        )
        tasks.send_usage_metrics.delay(upgrade_only=True)
        mocked_get_openwisp_module_metrics.assert_not_called()
        self.assertEqual(OpenwispVersion.objects.count(), 2)
        version = OpenwispVersion.objects.first()
        expected_module_version = {
            'OpenWISP Version': '23.0.0a',
            **_ENABLED_OPENWISP_MODULES_RETURN_VALUE,
        }
        self.assertEqual(version.module_version, expected_module_version)

    @patch('time.sleep')
    @patch('logging.Logger.warning')
    @patch('logging.Logger.error')
    def test_post_usage_metrics_400_response(self, mocked_error, mocked_warning, *args):
        bad_response = requests.Response()
        bad_response.status_code = 400
        with patch.object(
            requests.Session, 'post', return_value=bad_response
        ) as mocked_post:
            tasks.send_usage_metrics.delay()
        mocked_post.assert_called_once()
        mocked_warning.assert_not_called()
        mocked_error.assert_called_with(
            'Collection of usage metrics failed, max retries exceeded.'
            ' Error: HTTP 400 Response'
        )

    @patch('urllib3.util.retry.Retry.sleep')
    @patch(
        'urllib3.connectionpool.HTTPConnection.getresponse',
        return_value=HTTPResponse(status=500, version='1.1'),
    )
    @patch('logging.Logger.error')
    def test_post_usage_metrics_500_response(
        self, mocked_error, mocked_getResponse, *args
    ):
        tasks.send_usage_metrics.delay()
        self.assertEqual(len(mocked_getResponse.mock_calls), 11)
        mocked_error.assert_called_with(
            'Collection of usage metrics failed, max retries exceeded.'
            ' Error: HTTPSConnectionPool(host=\'analytics.openwisp.io\', port=443):'
            ' Max retries exceeded with url: /cleaninsights.php (Caused by ResponseError'
            '(\'too many 500 error responses\'))'
        )

    @patch('time.sleep')
    @patch('logging.Logger.warning')
    @patch('logging.Logger.error')
    def test_post_usage_metrics_204_response(self, mocked_error, mocked_warning, *args):
        bad_response = requests.Response()
        bad_response.status_code = 204
        with patch.object(
            requests.Session, 'post', return_value=bad_response
        ) as mocked_post:
            tasks.send_usage_metrics.delay()
        self.assertEqual(len(mocked_post.mock_calls), 1)
        mocked_warning.assert_not_called()
        mocked_error.assert_not_called()

    @patch('urllib3.util.retry.Retry.sleep')
    @patch(
        'urllib3.connectionpool.HTTPConnectionPool._get_conn',
        side_effect=OSError,
    )
    @patch('logging.Logger.error')
    def test_post_usage_metrics_connection_error(
        self, mocked_error, mocked_get_conn, *args
    ):
        tasks.send_usage_metrics.delay()
        mocked_error.assert_called_with(
            'Collection of usage metrics failed, max retries exceeded.'
            ' Error: HTTPSConnectionPool(host=\'analytics.openwisp.io\', port=443):'
            ' Max retries exceeded with url: /cleaninsights.php'
            ' (Caused by ProtocolError(\'Connection aborted.\', OSError()))'
        )
        self.assertEqual(mocked_get_conn.call_count, 11)

    @patch.object(tasks.send_usage_metrics, 'delay')
    def test_post_migrate_receiver(self, mocked_task, *args):
        app = apps.get_app_config('measurements')

        with self.subTest(
            'Test task is called for checking upgrades when plan is empty'
        ):
            app.post_migrate_receiver(plan=[])
            mocked_task.assert_called_with(upgrade_only=True)
        mocked_task.reset_mock()

        with self.subTest(
            'Test task is called for checking upgrades '
            'when first migration in plan is not for ContentTypes'
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
            mocked_task.assert_called_with(upgrade_only=True)
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
            mocked_task.assert_called_with()
        mocked_task.reset_mock()

        with self.subTest('Test task not called in development'):
            with override_settings(DEBUG=True):
                app.post_migrate_receiver(plan=plan)
            mocked_task.assert_not_called()
