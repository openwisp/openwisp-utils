from django.core.exceptions import ImproperlyConfigured

from ..utils import SortedOrderedDict

DASHBOARD_CONFIG = SortedOrderedDict()


def _validate_element_config(config):
    query_params = config.get('query_params', None)

    assert query_params is not None
    assert 'app_label' in query_params
    assert 'model' in query_params
    assert 'group_by' in query_params
    try:
        assert 'order' in config
    except AssertionError:
        config['order'] = len(DASHBOARD_CONFIG.keys())
    return config


def register_dashboard_element(element_name, element_config):
    """
    Registers a dashboard element
    register_dashboard_element(str, dict)
    """
    if not isinstance(element_name, str):
        raise ImproperlyConfigured('Dashboard element name should be type `str`.')
    if not isinstance(element_config, dict):
        raise ImproperlyConfigured(
            'Dashboard element parameters should be type `dict`.'
        )
    if element_name in DASHBOARD_CONFIG:
        raise ImproperlyConfigured(
            f'{element_name} is an already registered Dashboard Element.'
        )

    validated_element_config = _validate_element_config(element_config)
    DASHBOARD_CONFIG.update({element_name: validated_element_config})


def unregister_dashboard_element(element_name):
    if not isinstance(element_name, str):
        raise ImproperlyConfigured('Dashboard element name should be type `str`')
    if element_name not in DASHBOARD_CONFIG:
        raise ImproperlyConfigured(f'No such dashboard element, {element_name}')

    DASHBOARD_CONFIG.pop(element_name)
