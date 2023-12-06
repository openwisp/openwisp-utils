import logging
import time

import requests
from celery import shared_task
from openwisp_utils.admin_theme.system_info import (
    get_enabled_openwisp_modules,
    get_openwisp_version,
    get_os_details,
)

from .models import OpenwispVersion
from .utils import _get_events, get_openwisp_module_events, get_os_detail_events

CLEAN_INSIGHTS_URL = 'https://metrics.cleaninsights.org/cleaninsights.php'
MAX_TRIES = 3

logger = logging.getLogger(__name__)


def post_clean_insights_events(events):
    tries = 0
    while tries < MAX_TRIES:
        try:
            response = requests.post(
                CLEAN_INSIGHTS_URL,
                json={
                    'idsite': 33,
                    'events': events,
                },
            )
            assert response.status_code == 204
            return
        except Exception as error:
            tries += 1
            if isinstance(error, AssertionError):
                message = f'HTTP {response.status_code} Response'
                if response.status_code in (400, 404):
                    # Retrying sending data would result in the
                    # same error.
                    break
            else:
                message = str(error)
            logger.warning(
                f'Error posting clean insights events: {message}. Retrying in 5 seconds.'
            )
            time.sleep(5)
    logger.error(
        f'Maximum tries reach to upload Clean Insights measurements. Error: {message}'
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
