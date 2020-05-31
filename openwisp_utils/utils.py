from copy import deepcopy

from django.conf import settings
from django.utils.crypto import get_random_string


def get_random_key():
    """
    generates a random string of 32 characters
    """
    return get_random_string(length=32)


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
