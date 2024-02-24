from django.utils.html import escape
from django.utils.timezone import now


def _get_events(category, data):
    """
    This function takes a category and data representing usage metrics,
    and returns a list of events in a format accepted by the
    Clean Insights Matomo Proxy (CIMP) API.

    Read the "Event Measurement Schema" in the CIMP documentation:
    https://cutt.ly/SwBkC40A
    """
    events = []
    unix_time = int(now().timestamp())
    for key, value in data.items():
        events.append(
            {
                'category': category,
                'action': escape(key),
                'name': escape(value),
                'value': 1,
                'times': 1,
                'period_start': unix_time,
                'period_end': unix_time,
            }
        )
    return events


def get_openwisp_module_metrics(module_versions):
    return _get_events('Heartbeat', module_versions)


def get_os_detail_metrics(os_detail):
    return _get_events('OS Detail', os_detail)
