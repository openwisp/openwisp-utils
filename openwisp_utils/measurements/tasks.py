import logging

from celery import shared_task
from openwisp_utils.admin_theme.system_info import (
    get_enabled_openwisp_modules,
    get_openwisp_version,
    get_os_details,
)

from ..tasks import OpenwispCeleryTask
from ..utils import retryable_request
from .models import OpenwispVersion
from .utils import _get_events, get_openwisp_module_metrics, get_os_detail_metrics

USER_METRIC_COLLECTION_URL = 'https://analytics.openwisp.io/cleaninsights.php'

logger = logging.getLogger(__name__)


def post_usage_metrics(events):
    try:
        print('retrying request')
        response = retryable_request(
            'post',
            url=USER_METRIC_COLLECTION_URL,
            json={
                'idsite': 5,
                'events': events,
            },
            max_retries=10,
        )
        print(response.status_code, ' response code from measurement tasks')
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
def send_usage_metrics(upgrade_only=False):
    current_versions = get_enabled_openwisp_modules()
    current_versions.update({'OpenWISP Version': get_openwisp_version()})
    metrics = []
    metrics.extend(get_os_detail_metrics(get_os_details()))
    if OpenwispVersion.is_new_installation():
        metrics.extend(_get_events('Install', current_versions))
        OpenwispVersion.objects.create(module_version=current_versions)
    else:
        upgraded_modules = OpenwispVersion.get_upgraded_modules(current_versions)
        metrics.extend(_get_events('Upgrade', upgraded_modules))
        if not upgrade_only:
            metrics.extend(get_openwisp_module_metrics(current_versions))
    post_usage_metrics(metrics)
