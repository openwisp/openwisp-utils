from django.core.exceptions import ImproperlyConfigured

from ..utils import SortedOrderedDict

DASHBOARD_CONFIG = SortedOrderedDict()


def _validate_element_config(config):
    query_params = config.get('query_params', None)

    assert query_params is not None
    assert 'name' in config
    assert 'app_label' in query_params
    assert 'model' in query_params
    assert 'group_by' in query_params
    return config


def register_dashboard_element(position, element_config):
    """
    Registers a dashboard element
    register_dashboard_element(str, dict)
    """
    if not isinstance(position, int):
        raise ImproperlyConfigured('Dashboard element name should be type `int`.')
    if not isinstance(element_config, dict):
        raise ImproperlyConfigured(
            'Dashboard element parameters should be type `dict`.'
        )
    if position in DASHBOARD_CONFIG:
        raise ImproperlyConfigured(
            f'Cannot register {element_config["name"]}. '
            f'A dashboard element is already registered for "{position}" position.'
        )

    validated_element_config = _validate_element_config(element_config)
    DASHBOARD_CONFIG.update({position: validated_element_config})


def unregister_dashboard_element(element_name):
    if not isinstance(element_name, str):
        raise ImproperlyConfigured('Dashboard element name should be type `str`')

    for key, value in DASHBOARD_CONFIG.items():
        if value['name'] == element_name:
            DASHBOARD_CONFIG.pop(key)
            break
    else:
        raise ImproperlyConfigured(f'No such dashboard element, {element_name}')
