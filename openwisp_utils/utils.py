from django.utils.crypto import get_random_string


def get_random_key():
    """
    generates a device key of 32 characters
    """
    return get_random_string(length=32)
