from django.utils.crypto import get_random_string


def get_random_key():
    """
    generates a device key of 32 characters
    """
    return get_random_string(length=32)


def deep_merge_dicts(dict1, dict2):
    result = dict1.copy()
    for key, value in dict2.items():
        if isinstance(value, dict):
            node = result.get(key, {})
            result[key] = deep_merge_dicts(node, value)
        else:
            result[key] = value
    return result
