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
                # OS Details, Install, Hearthbeat, Upgrade
                'category': category,
                # Name of OW module or OS parameter
                'action': escape(key),
                # Actual version of OW module, OS or general OW version
                'name': escape(value),
                # Value is always 1
                'value': 1,
                # Event happened only 1 time, we do not aggregate
                'times': 1,
                'period_start': unix_time,
                'period_end': unix_time,
            }
        )
    return events
