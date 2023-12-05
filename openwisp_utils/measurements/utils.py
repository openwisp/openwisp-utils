from django.utils.html import escape
from django.utils.timezone import now


def _get_events(category, data):
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


def get_openwisp_module_events(module_versions):
    return _get_events('Openwisp Module', module_versions)


def get_os_detail_events(os_detail):
    return _get_events('OS Detail', os_detail)
