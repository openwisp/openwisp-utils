import logging

from celery import shared_task
from openwisp_utils.admin_theme.system_info import (
    get_enabled_openwisp_modules,
    get_openwisp_version,
    get_os_details,
)

from ..utils import retryable_request
from .models import OpenwispVersion
from .utils import _get_events, get_openwisp_module_events, get_os_detail_events

CLEAN_INSIGHTS_URL = 'https://analytics.openwisp.io/cleaninsights.php'
MAX_TRIES = 3

logger = logging.getLogger(__name__)


def post_clean_insights_events(events):
    try:
        response = retryable_request(
            'post',
            url=CLEAN_INSIGHTS_URL,
            json={
                'idsite': 5,
                'events': events,
            },
        )
        assert response.status_code == 204
    except Exception as error:
        if isinstance(error, AssertionError):
            message = f'HTTP {response.status_code} Response'
        else:
            message = str(error)
        logger.error(
            f'Maximum tries reached to upload Clean Insights measurements. Error: {message}'
        )


@shared_task
def send_clean_insights_measurements(upgrade_only=False):
    current_versions = get_enabled_openwisp_modules()
    current_versions.update({'OpenWISP Version': get_openwisp_version()})
    events = []
    events.extend(get_os_detail_events(get_os_details()))
    if OpenwispVersion.is_new_installation():
        events.extend(_get_events('Install', current_versions))
        OpenwispVersion.objects.create(module_version=current_versions)
    else:
        upgraded_modules = OpenwispVersion.get_upgraded_modules(current_versions)
        events.extend(_get_events('Upgrade', upgraded_modules))
        if not upgrade_only:
            events.extend(get_openwisp_module_events(current_versions))
    post_clean_insights_events(events)
