from django.apps import registry
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.utils.translation import gettext as _

from ..utils import SortedOrderedDict

MENU = SortedOrderedDict()


class BaseMenuItem:
    '''
    It is a base class for all types of menu items.
    It is used to create context for menu items and for
    handing some common validations.
    '''

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
            raise ValueError(f'"label" is missing in the config- {config}')
        if not isinstance(label, str):
            raise ValueError(
                f'"level" should be a type of "str". Error for config- {config}'
            )
        self.label = _(label)


class ModelLink(BaseMenuItem):
    '''
    It is used create a link for a model like "list view" and "add view".
    Parameters of config: name, model, label, icon
    '''

    def __init__(self, config):
        super().__init__(config)
        name = config.get('name')
        model = config.get('model')
        if name:
            if not isinstance(name, str):
                raise ValueError(
                    f'"name" should be a type of "str". Error for config-{config}'
                )
            self.name = name
        else:
            raise ValueError(f'"name" is missing in the config-{config}')
        if not model:
            raise ValueError(f'"model" is missing in config-{config}')
        if not isinstance(model, str):
            raise ValueError(
                f'"model" should be a type of "str". Error for config-{config}'
            )
        self.model = model
        self.label = _(self.get_label(config))
        self.icon = config.get('icon')

    def get_label(self, config=None):
        label = config.get('label')
        if label:
            return label
        app_label, model = config['model'].split('.')
        model_class = registry.apps.get_model(app_label, model)
        return f'{model_class._meta.verbose_name_plural} {self.name}'

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

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return (
            self.label == other.label
            and self.model == other.model
            and self.icon == self.icon
        )


class MenuLink(BaseMenuItem):
    '''
    It is used create any general link by supplying url.
    Parameters of config: label, url, icon
    '''

    def __init__(self, config):
        super().__init__(config)
        url = config.get('url')
        self.set_label(config)
        if not url:
            raise ValueError(f'"url" is missing in the config- {config}')
        if not isinstance(url, str):
            raise ValueError(
                f'"url" should be a type of "str". Error for the config- {config}'
            )
        self.url = url
        self.icon = config.get('icon')

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return (
            self.label == other.label
            and self.url == other.url
            and self.icon == other.icon
        )


class MenuGroup(BaseMenuItem):
    '''
    It is used create a dropdown in the menu.
    Parameters of config: label, items, icon
    items should be a type of MenuLink or MenuItem
    '''

    def __init__(self, config):
        super().__init__(config)
        items = config.get('items')
        self.set_label(config)
        if not items:
            raise ValueError(f'"items" is missing in the config- {config}')
        if not isinstance(items, dict):
            raise ValueError(
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
                    f'"key" should be type of "int". Error in "items" of config- {config}'
                )

            if not isinstance(item, dict):
                raise ImproperlyConfigured(
                    f'Each value of "items" should be a type of "dict". Error in "items" of config- {config}'
                )

        if item.get('url'):
            # It is a menu link
            try:
                _items[position] = MenuLink(config=item)
            except ValueError as e:
                raise ValueError(
                    f'{e}. "items" of config- {config} should have a valid json'
                )
            except ImproperlyConfigured as e:
                raise ImproperlyConfigured(
                    f'{e}. "items" of config- {config} should have a valid json'
                )
        else:
            # It is a menu item
            try:
                _items[position] = ModelLink(config=item)
            except ValueError as e:
                raise ValueError(
                    f'{e}. "items" of config- {config} should have a valid json'
                )
            except ImproperlyConfigured as e:
                raise ImproperlyConfigured(
                    f'{e}. "items" of config- {config} should have a valid json'
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

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        if self.label != other.label or self.icon != other.icon:
            return False
        if len(self.items) != len(other.items):
            return False
        for first, second in zip(self.items.values(), other.items.values()):
            if not first.__eq__(second):
                return False
        return True


def register_menu_groups(groups):
    if not isinstance(groups, dict):
        raise ImproperlyConfigured('Supplied groups should be a type of "dict"')
    for position, config in groups.items():
        if not isinstance(position, int):
            raise ImproperlyConfigured('group position should be a type of "int"')
        if position in MENU:
            raise ValueError(
                f'Another group is already registered at position n. "{position}"'
            )
        if not isinstance(config, dict):
            raise ImproperlyConfigured(
                f'Config should be a type of "dict" but supplied {config} at \
                position {position} in the register_menu_groups function'
            )
        if config.get('url'):
            # It is a menu link
            groups[position] = MenuLink(config=config)
        elif config.get('items'):
            # It is a menu group
            groups[position] = MenuGroup(config=config)
        else:
            # It is a menu item
            groups[position] = ModelLink(config=config)
    MENU.update(groups)


def build_menu_group(request):
    menu = []
    for item in MENU.values():
        item_context = item.get_context(request)
        if item_context:
            menu.append(item_context)
    return menu
