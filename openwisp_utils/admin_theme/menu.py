from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext as _
from django.apps import registry
from django.urls import reverse

from ..utils import SortedOrderedDict

MENU = SortedOrderedDict()


class BaseMenuItem:
    def __init__(self, config):
        if not isinstance(config, dict):
            raise ImproperlyConfigured(f'Provided config is not a dict {config}')

    def get_context(self,request):
        return self.create_context()
    def create_context(self):
        return {
            'label': self.label,
            'url': self.url,
            'icon':self.icon
        }

class MenuItem(BaseMenuItem):
    def __init__(self, config):
        super().__init__(config)
        if config.get('name', None) is not None:
            if not isinstance(config['name'], str):
                raise ValueError('Menu item name must be a string')
            self.name = config['name']
        else:
            self.name = None
        if config.get('model', None) is None:
            raise ValueError(f'Menu item must have a model {config}')
        self.model = config['model']
        self.label = _(self.get_label(config))
        self.icon = config.get('icon', None)
        self.url = self.create_url()
    
    def create_url(self):
        print(self.model)
        app_label, model = self.model.split('.')
        model_label = model.lower()
        url = reverse('admin:auth_user_add')
        # url =  reverse(f'admin:{app_label}_{model_label}_{self.name}')
        print(url)
        return url

    def get_label(self, config=None):
        if config:
            if config.get('label', None) is not None:
                return config['label']
            app_label, model = config['model'].split('.')
            model_class = registry.apps.get_model(app_label, model)
            return f'{model_class._meta.verbose_name_plural} {self.name}'
        return self.label

    def create_context(self,request):
        app_label, model = self.model.split('.')
        model_label = model.lower()
        url = reverse('admin:auth_user_add')
        view_perm = f'{app_label}.view_{model_label}'
        change_perm = f'{app_label}.change_{model_label}'
        user = request.user
        has_permission_method = (
                    user.has_permission
                    if hasattr(user, 'has_permission')
                    else user.has_perm
                )
        if has_permission_method(view_perm) or has_permission_method(
                    change_perm
                ):
            return {
                'label':self.label, 'url':self.url, 'icon':self.icon
            }
        return None

class MenuGroup(BaseMenuItem):
    def __init__(self, config):
        super().__init__(config)
        if config.get('label', None) is None:
            raise ValueError('Group must have a label')
        if not isinstance(config['label'], str):
            raise ValueError('Group label must be a string')
        self.label = _(config['label'])
        if config.get('items', None) is None:
            raise ValueError(f'{self.label} group must contain items')
        if not isinstance(config['items'], dict):
            raise ValueError(f'Items of {self.label} group is not a dict')
        for position,item in config['items'].items():
            print(position,item)
            if not isinstance(position,int):
                raise ImproperlyConfigured(f'Items position of group {self.label} must be an int')
            if not (isinstance(item, MenuItem) or isinstance(item, MenuLink)):
                raise ValueError(
                    f'Invlid items are provided for {self.label} group'
                )
        self.items = SortedOrderedDict()
        self.set_items(config['items'])
        self.icon = config.get('icon',None)

    def get_items(self):
        return self.items

    def set_items(self, items):
        for position, _ in items.items():
            if not isinstance(position, int):
                raise ImproperlyConfigured(
                    f'{self.label} groups items key must be an int'
                )
        self.items.update(items)

    def create_context(self,request):
        _items=[]
        for _,item in self.items:
            context = item.get_context(request)
            if context:
                _items.append(context)
        
        if not _items:
            return None
        return {'label':self.label,'items':_items,'icon': self.icon}



class MenuLink(BaseMenuItem):
    def __init__(self, config):
        if config.get('label', None) is None:
            raise ValueError('label is missing for menu link')
        self.label = config['label']

        if config.get('url', None) is None:
            raise ValueError('url is missing for menu link')
        self.url = config['url']
        self.icon = config.get('icon', None)


def register_menu_groups(groups):
    if not isinstance(groups, dict):
        raise ImproperlyConfigured('groups need to a dict')
    for position, group in groups.items():
        if not isinstance(position, int):
            raise ImproperlyConfigured(f'group position is not int')
        if not (
            isinstance(group, MenuGroup)
            or isinstance(group, MenuItem)
            or isinstance(group, MenuLink)
        ):
            raise ValueError(f'Invalid group at position {position}')
    MENU.update(groups)


def build_menu_group(request):
    menu = []
    for _,item in MENU.items():
        item_context = item.get_context(request)
        print(item_context)
        if item_context:
            menu.append(item_context)






# def build_menu_groups(request):
#     default_groups = getattr(settings, 'OPENWISP_DEFAULT_ADMIN_MENU_GROUPS', {})
#     custom_groups = getattr(settings, 'OPENWISP_ADMIN_MENU_GROUPS', {})
#     groups = default_groups
#     groups.update(custom_groups)
#     menu_groups = []
#     for name, config in groups.items():
#         items = config['items']
#         _group = {}
#         _items = []
#         _group['name'] = name
#         for _, item in items.items():
#             if item.get('model', None):
#                 app_label, model = item['model'].split('.')
#                 model_class = registry.apps.get_model(app_label, model)
#                 model_label = model.lower()
#                 uuid = item['name']
#                 url = reverse(f'admin:{app_label}_{model_label}_{uuid}')
#                 label = item.get(
#                     'label', model_class._meta.verbose_name_plural + ' ' + uuid
#                 )
#                 view_perm = f'{app_label}.view_{model_label}'
#                 change_perm = f'{app_label}.change_{model_label}'
#                 user = request.user
#                 has_permission_method = (
#                     user.has_permission
#                     if hasattr(user, 'has_permission')
#                     else user.has_perm
#                 )
#                 if has_permission_method(view_perm) or has_permission_method(
#                     change_perm
#                 ):
#                     _items.append(
#                         {
#                             'url': url,
#                             'label': label,
#                             'class': model_label,
#                             'icon': item.get('icon', ''),
#                         }
#                     )
#             elif item.get('link', None):
#                 _items.append(
#                     {
#                         'url': item['link'],
#                         'label': item['label'],
#                         'icon': item.get('icon', ''),
#                     }
#                 )
#         if _items:
#             _group['icon'] = config.get('icon', '')
#             _group['items'] = _items
#             menu_groups.append(_group)
#     return menu_groups
