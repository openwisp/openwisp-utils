from django.core.exceptions import ImproperlyConfigured

from ..utils import SortedOrderedDict

DASHBOARD_SCHEMA = SortedOrderedDict()


def _validate_element_params(schema):
    query_params = schema.get('query_params', None)

    assert query_params is not None
    assert 'app_label' in query_params
    assert 'model' in query_params
    assert 'group_by' in query_params
    try:
        assert 'order' in schema
    except AssertionError:
        schema['order'] = len(DASHBOARD_SCHEMA.keys())
    return schema


def register_dashboard_element(element_name, element_params):
    """
    Registers a dashboard element
    register_dashboard_element(str, dict)
    """
    if not isinstance(element_name, str):
        raise ImproperlyConfigured('Dashboard element name should be type `str`.')
    if not isinstance(element_params, dict):
        raise ImproperlyConfigured(
            'Dashboard element parameters should be type `dict`.'
        )
    if element_name in DASHBOARD_SCHEMA:
        raise ImproperlyConfigured(
            f'{element_name} is an already registered Dashboard Element.'
        )

    validated_element_params = _validate_element_params(element_params)
    DASHBOARD_SCHEMA.update({element_name: validated_element_params})


def unregister_dashboard_element(element_name):
    if not isinstance(element_name, str):
        raise ImproperlyConfigured('Dashboard element name should be type `str`')
    if element_name not in DASHBOARD_SCHEMA:
        raise ImproperlyConfigured(f'No such dashboard element, {element_name}')

    DASHBOARD_SCHEMA.pop(element_name)
