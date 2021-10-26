from collections import OrderedDict
from copy import deepcopy

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from django.utils.html import strip_tags

from . import settings as app_settings


class SortedOrderedDict(OrderedDict):
    def update(self, items):
        super().update(items)
        temp = deepcopy(self)
        temp = sorted((temp.items()), key=lambda x: x[0])
        self.clear()
        super().update(temp)


def get_random_key():
    """
    generates a random string of 32 characters
    """
    return get_random_string(length=32)


def register_menu_items(items, name_menu='OPENWISP_DEFAULT_ADMIN_MENU_ITEMS'):
    if not hasattr(settings, name_menu):
        setattr(settings, name_menu, items)
    else:
        current_menu = getattr(settings, name_menu)
        current_menu += items


def deep_merge_dicts(dict1, dict2):
    """
    returns a new dict which is the result of the merge of the two dicts,
    all elements are deepcopied to avoid modifying the original data structures
    """
    result = deepcopy(dict1)
    for key, value in dict2.items():
        if isinstance(value, dict):
            node = result.get(key, {})
            result[key] = deep_merge_dicts(node, value)
        else:
            result[key] = deepcopy(value)
    return result


def default_or_test(value, test):
    return value if not getattr(settings, 'TESTING', False) else test


def print_color(string, color_name, end='\n'):
    """
    Prints colored output on terminal from a selected range of colors.
    If color_name is not present then output won't be colored.
    """
    color_dict = {
        'white_bold': '37;1',
        'green_bold': '32;1',
        'yellow_bold': '33;1',
        'red_bold': '31;1',
        'reset': '0',
    }
    color = color_dict.get(color_name, '0')
    print(f'\033[{color}m{string}\033[0m', end=end)


def send_email(subject, body, recipient_email, url=None, extra_context={}):
    if url:
        body += '\n\nFor more information see {0}.'.format(url)

    mail = EmailMultiAlternatives(
        subject=subject,
        body=strip_tags(body),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient_email],
    )
    context = dict(
        subject=subject,
        message=body,
        logo_url=app_settings.OPENWISP_EMAIL_LOGO,
        call_to_action_text='Find out more',
        call_to_action_url=url,
    )
    context.update(extra_context)

    if getattr(app_settings, 'OPENWISP_HTML_EMAIL', True):
        html_message = render_to_string(
            app_settings.OPENWISP_EMAIL_TEMPLATE, context=context,
        )
        mail.attach_alternative(html_message, 'text/html')
    mail.send()
    return mail
