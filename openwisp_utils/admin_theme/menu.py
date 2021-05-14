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

    def get_context(self, request):
        return self.create_context(request)

    def create_context(self, request):
        return {'label': self.label, 'url': self.url, 'icon': self.icon}


class MenuItem(BaseMenuItem):
    def __init__(self, config):
        super().__init__(config)
        if config.get('name'):
            if not isinstance(config['name'], str):
                raise ValueError(
                    f'"name" of menu item should be a type of "str". Error for config-{config}'
                )
            self.name = config['name']
        else:
            raise ValueError(f'"name" is missing in the config-{config}')
        if not config.get('model'):
            raise ValueError(f'"model" is missing in config-{config}')
        self.model = config['model']
        self.label = _(self.get_label(config))
        self.icon = config.get('icon')

    def get_label(self, config=None):
        if config:
            if config.get('label'):
                return config['label']
            app_label, model = config['model'].split('.')
            model_class = registry.apps.get_model(app_label, model)
            return f'{model_class._meta.verbose_name_plural} {self.name}'
        return self.label

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


class MenuGroup(BaseMenuItem):
    def __init__(self, config):
        super().__init__(config)
        if not config.get('label'):
            raise ValueError(
                '"label" is missing in a menu group having config-{config}'
            )
        if not isinstance(config['label'], str):
            raise ValueError('"level" should be a type of "str" for config-{config}')
        self.label = _(config['label'])
        if not config.get('items'):
            raise ValueError(f'"items" are missing for "{self.label}" group')
        if not isinstance(config['items'], dict):
            raise ValueError(f'"items" of "{self.label}" group is not a type of "dict"')
        for position, item in config['items'].items():
            if not isinstance(position, int):
                raise ImproperlyConfigured(
                    f'Items position of group "{self.label}" should be type of "int"'
                )
            if not (isinstance(item, MenuItem) or isinstance(item, MenuLink)):
                raise ValueError(f'Invlid items are provided for "{self.label}" group')
        self.items = SortedOrderedDict()
        self.set_items(config['items'])
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


class MenuLink(BaseMenuItem):
    def __init__(self, config):
        super().__init__(config)
        if not config.get('label'):
            raise ValueError(
                '"label" is missing for a menu link having config - {config}'
            )
        self.label = config['label']
        if not config.get('url'):
            raise ValueError('"url" is missing for menu link config- {config}')
        self.url = config['url']
        self.icon = config.get('icon')


def register_menu_groups(groups):
    if not isinstance(groups, dict):
        raise ImproperlyConfigured('Supplied groups should be a type of "dict"')
    for position, group in groups.items():
        if not isinstance(position, int):
            raise ImproperlyConfigured('group position should be a type of "int"')
        if position in MENU:
            raise ValueError(
                f'Another group is already registered at position n. "{position}":'
            )
        if not (
            isinstance(group, MenuGroup)
            or isinstance(group, MenuItem)
            or isinstance(group, MenuLink)
        ):
            raise ValueError(
                'group should be type of "MenuGroup", "MenuItem" or "MenuLink"'
            )
    MENU.update(groups)


def build_menu_group(request):
    menu = []
    for item in MENU.values():
        item_context = item.get_context(request)
        if item_context:
            menu.append(item_context)
    return menu
