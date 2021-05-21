from django.apps import registry
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.utils.translation import gettext as _

from ..utils import SortedOrderedDict

MENU = SortedOrderedDict()


class BaseMenuItem:
    def __init__(self, config):
        if not isinstance(config, dict):
            raise ImproperlyConfigured(
                f'"config" should be a type of "dict". Error for config-{config}'
            )

    def get_context(self, request=None):
        return self.create_context(request)

    def create_context(self, request=None):
        return {'label': self.label, 'url': self.url, 'icon': self.icon}

    def set_label(self, config):
        label = config.get('label')
        if not label:
            raise ValueError(
                f'"label" is missing in a menu group having config-{config}'
            )
        if not isinstance(label, str):
            raise ValueError(f'"level" should be a type of "str" for config-{config}')
        self.label = _(label)


class MenuItem(BaseMenuItem):
    def __init__(self, config):
        super().__init__(config)
        name = config.get('name')
        model = config.get('model')
        if name:
            if not isinstance(name, str):
                raise ValueError(
                    f'"name" of menu item should be a type of "str". Error for config-{config}'
                )
            self.name = name
        else:
            raise ValueError(f'"name" is missing in the config-{config}')
        if not model:
            raise ValueError(f'"model" is missing in config-{config}')
        if not isinstance(model, str):
            raise ValueError(
                f'"model" of menu item should be a type of "str". Error for config-{config}'
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


class MenuGroup(BaseMenuItem):
    def __init__(self, config):
        super().__init__(config)
        items = config.get('items')
        possible_group_items = (MenuItem, MenuLink)
        self.set_label(config)
        if not items:
            raise ValueError(f'"items" are missing for "{self.label}" group')
        if not isinstance(items, dict):
            raise ValueError(f'"items" of "{self.label}" group is not a type of "dict"')
        for position, item in items.items():
            if not isinstance(position, int):
                raise ImproperlyConfigured(
                    f'Items position of group "{self.label}" should be type of "int"'
                )
            if not isinstance(item, possible_group_items):
                raise ValueError(
                    f'Invlid items are provided for "{self.label}" group.\
                    Items must be a type of {possible_group_items}'
                )
        self.items = SortedOrderedDict()
        self.set_items(items)
        self.icon = config.get('icon')

    def get_items(self):
        return self.items

    def set_items(self, items):
        for position in items:
            if not isinstance(position, int):
                raise ImproperlyConfigured(
                    f'"{self.label}" groups items key must be type of "int"'
                )
        self.items.update(items)

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


class MenuLink(BaseMenuItem):
    def __init__(self, config):
        super().__init__(config)
        url = config.get('url')
        self.set_label(config)
        if not url:
            raise ValueError(f'"url" is missing for menu link config- {config}')
        if not isinstance(url, str):
            raise ValueError(
                f'"url" must be a type of "str" in menu link config- {config}'
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


def register_menu_groups(groups):
    possible_menu_items = (MenuGroup, MenuItem, MenuLink)
    if not isinstance(groups, dict):
        raise ImproperlyConfigured('Supplied groups should be a type of "dict"')
    for position, group in groups.items():
        if not isinstance(position, int):
            raise ImproperlyConfigured('group position should be a type of "int"')
        if position in MENU:
            raise ValueError(
                f'Another group is already registered at position n. "{position}"'
            )
        if not isinstance(group, possible_menu_items):
            raise ValueError(f'group should be type of {possible_menu_items}')
    MENU.update(groups)


def build_menu_group(request):
    menu = []
    for item in MENU.values():
        item_context = item.get_context(request)
        if item_context:
            menu.append(item_context)
    return menu
