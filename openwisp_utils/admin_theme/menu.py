from django.apps import registry
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse

from ..utils import SortedOrderedDict

MENU = SortedOrderedDict()


class BaseMenuItem:
    """
    It is a base class for all types of menu items.
    It is used to handle some common functions.
    """

    def __init__(self, config):
        if not isinstance(config, dict):
            raise ImproperlyConfigured(
                f'"config" should be a type of "dict". Error for config- {config}'
            )

    def get_context(self, request=None):
        return self.create_context(request)

    def create_context(self, request=None):
        return {'label': self.label, 'url': self.url, 'icon': self.icon}

    def set_label(self, config):
        label = config.get('label')
        if not label:
            raise ImproperlyConfigured(f'"label" is missing in the config- {config}')
        self.label = label


class ModelLink(BaseMenuItem):
    """
    It is to used create a link for a model, like "list view" and "add view".
    Parameters for the config: name, model, label, icon
    """

    def __init__(self, config):
        super().__init__(config)
        name = config.get('name')
        model = config.get('model')
        if name:
            if not isinstance(name, str):
                raise ImproperlyConfigured(
                    f'"name" should be a type of "str". Error for config-{config}'
                )
            self.name = name
        else:
            raise ImproperlyConfigured(f'"name" is missing in the config-{config}')
        if not model:
            raise ImproperlyConfigured(f'"model" is missing in config-{config}')
        if not isinstance(model, str):
            raise ImproperlyConfigured(
                f'"model" should be a type of "str". Error for config-{config}'
            )
        self.model = model
        self.set_label(config)
        self.icon = config.get('icon')

    def set_label(self, config=None):
        if config.get('label'):
            return super().set_label(config)
        app_label, model = config['model'].split('.')
        model_class = registry.apps.get_model(app_label, model)
        self.label = f'{model_class._meta.verbose_name_plural} {self.name}'

    def create_context(self, request):
        app_label, model = self.model.split('.')
        model_label = model.lower()
        url = reverse(f'admin:{app_label}_{model_label}_{self.name}')
        view_perm = f'{app_label}.view_{model_label}'
        change_perm = f'{app_label}.change_{model_label}'
        user = request.user
        has_permission_method = (
            user.has_permission if hasattr(user, 'has_permission') else user.has_perm
        )
        if has_permission_method(view_perm) or has_permission_method(change_perm):
            return {'label': self.label, 'url': url, 'icon': self.icon}
        return None


class MenuLink(BaseMenuItem):
    """
    It is used to create any general link by supplying a custom url.
    Parameters of config: label, url and icon.
    """

    def __init__(self, config):
        super().__init__(config)
        url = config.get('url')
        self.set_label(config)
        if not url:
            raise ImproperlyConfigured(f'"url" is missing in the config- {config}')
        if not isinstance(url, str):
            raise ImproperlyConfigured(
                f'"url" should be a type of "str". Error for the config- {config}'
            )
        self.url = url
        self.icon = config.get('icon')


class MenuGroup(BaseMenuItem):
    """
    It is used to create a dropdown in the menu.
    Parameters of config: label, items and icon.
    each item in items should repesent a config for MenuLink or ModelLink
    """

    def __init__(self, config):
        super().__init__(config)
        items = config.get('items')
        self.set_label(config)
        if not items:
            raise ImproperlyConfigured(f'"items" is missing in the config- {config}')
        if not isinstance(items, dict):
            raise ImproperlyConfigured(
                f'"items" should be a type of "dict". Error for the config- {config}'
            )
        self.items = SortedOrderedDict()
        self.set_items(items, config)
        self.icon = config.get('icon')

    def get_items(self):
        return self.items

    def set_items(self, items, config):
        _items = {}
        for position, item in items.items():
            if not isinstance(position, int):
                raise ImproperlyConfigured(
                    f'"key" should be type of "int". Error for "items" of config- {config}'
                )

            if not isinstance(item, dict):
                raise ImproperlyConfigured(
                    f'Each value of "items" should be a type of "dict". Error for "items" of config- {config}'
                )
            if item.get('url'):
                # It is a menu link
                try:
                    _items[position] = MenuLink(config=item)
                except ImproperlyConfigured as e:
                    raise ImproperlyConfigured(
                        f'{e}. "items" of config- {config} should have a valid json'
                    )
            elif item.get('model'):
                # It is a model link
                try:
                    _items[position] = ModelLink(config=item)
                except ImproperlyConfigured as e:
                    raise ImproperlyConfigured(
                        f'{e}. "items" of config- {config} should have a valid json'
                    )
            else:
                raise ImproperlyConfigured(
                    f'"items" should have a valid config. Error for config- {config}'
                )
        self.items.update(_items)

    def create_context(self, request):
        _items = []
        for item in self.items.values():
            context = item.get_context(request)
            if context:
                _items.append(context)
        if not _items:
            return None
        return {'label': self.label, 'sub_items': _items, 'icon': self.icon}


def register_menu_group(position, config):
    if not isinstance(position, int):
        raise ImproperlyConfigured('group position should be a type of "int"')
    if not isinstance(config, dict):
        raise ImproperlyConfigured('config should be a type of "dict"')
    if position in MENU:
        raise ImproperlyConfigured(
            f'Another group is already registered at position "{position}"'
        )
    if config.get('url'):
        # It is a menu link
        group_class = MenuLink(config=config)
    elif config.get('items'):
        # It is a menu group
        group_class = MenuGroup(config=config)
    elif config.get('model'):
        # It is a model link
        group_class = ModelLink(config=config)
    else:
        # Unknown
        raise ImproperlyConfigured(f'Invalid config provided at position {position}')
    MENU.update({position: group_class})


def build_menu_groups(request):
    menu = []
    for item in MENU.values():
        item_context = item.get_context(request)
        if item_context:
            menu.append(item_context)
    return menu
