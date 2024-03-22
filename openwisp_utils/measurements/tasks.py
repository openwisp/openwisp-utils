import logging

from celery import shared_task
from openwisp_utils.admin_theme.system_info import (
    get_enabled_openwisp_modules,
    get_openwisp_installation_method,
    get_openwisp_version,
    get_os_details,
)

from ..tasks import OpenwispCeleryTask
from ..utils import retryable_request
from .models import OpenwispVersion
from .utils import _get_events

USER_METRIC_COLLECTION_URL = 'https://analytics.openwisp.io/cleaninsights.php'

logger = logging.getLogger(__name__)


def post_usage_metrics(events):
    try:
        response = retryable_request(
            'post',
            url=USER_METRIC_COLLECTION_URL,
            json={
                'idsite': 5,
                'events': events,
            },
            max_retries=10,
        )
        assert response.status_code == 204
    except Exception as error:
        if isinstance(error, AssertionError):
            message = f'HTTP {response.status_code} Response'
        else:
            message = str(error)
        logger.error(
            f'Collection of usage metrics failed, max retries exceeded. Error: {message}'
        )


@shared_task(base=OpenwispCeleryTask)
def send_usage_metrics(category='Heartbeat'):
    assert category in ['Install', 'Heartbeat', 'Upgrade']
    current_versions = get_enabled_openwisp_modules()
    current_versions.update({'OpenWISP Version': get_openwisp_version()})
    current_versions.update(get_os_details())
    is_install, is_upgrade = OpenwispVersion.log_module_version_changes(
        current_versions
    )
    # Handle special conditions when the user forgot to execute the migrate
    # command, and an install or upgrade operation is detected in the Heartbeat
    # event. In such situation, we override the category.
    if category == 'Heartbeat':
        if is_install:
            category = 'Install'
        if is_upgrade:
            category = 'Upgrade'
    elif category == 'Upgrade' and not is_upgrade:
        # The task was triggered with "Upgrade" category, but no
        # upgrades were detected in the OpenWISP module versions.
        # This can occur when a user execute the migrate command without
        # upgrading the modules. We don't want to send upgrade
        # events in this scenario as it would lead to false
        # positives.
        return
    elif category == 'Install' and not is_install:
        # Similar to above, but for "Install" category
        return
    metrics = _get_events(category, current_versions)
    metrics.extend(
        _get_events(
            category, {'Installation Method': get_openwisp_installation_method()}
        )
    )
    post_usage_metrics(metrics)
