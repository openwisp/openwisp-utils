from collections import OrderedDict
from copy import deepcopy

from django.conf import settings
from django.utils.crypto import get_random_string


class SortedOrderedDict(OrderedDict):
    def update(self, items):
        super().update(items)
        temp = deepcopy(self)
        temp = sorted((temp.items()), key=lambda x: x[0])
        self.clear()
        super().update(temp)


def get_random_key():
    """
    generates a random string of 32 characters
    """
    return get_random_string(length=32)


def register_menu_items(items, name_menu='OPENWISP_DEFAULT_ADMIN_MENU_ITEMS'):
    if not hasattr(settings, name_menu):
        setattr(settings, name_menu, items)
    else:
        current_menu = getattr(settings, name_menu)
        current_menu += items


def register_default_menu_group_item(items):
    menu_group_name = 'OPENWISP_DEFAULT_ADMIN_MENU_GROUPS'
    if not hasattr(settings, menu_group_name):
        default_group = OrderedDict()
        default_group['Default'] = {
            'items': get_sorted_items(items)  # can also add default icon
        }
        setattr(settings, menu_group_name, default_group)
    else:
        default_group = getattr(settings, menu_group_name)
        default_group['Default']['items'] += get_sorted_items(items)


def register_menu_groups(
    menu_groups, menu_group_name='OPENWISP_ADMIN_MENU_GROUPS', preference=[]
):
    if not hasattr(settings, menu_group_name):
        menu = OrderedDict()
        setattr(settings, menu_group_name, menu)
    else:
        menu = getattr(settings, menu_group_name)
    group_map = {}
    for group in menu_groups:
        if group.get('name', None) is None:
            raise ValueError('name key missing in a group')
        if menu.get(group['name'], None) is not None:
            # menu name already present
            raise ValueError(
                f'Can\'t create menu group. {group["name"]} group already present in the menu.'
            )
        if group_map.get(group['name'], None) is None:
            if group.get('config', None) is None:
                raise ValueError(f'config not provided to {group["name"]} group')
            if group['config'].get('items', None) is None:
                raise ValueError(f'{group["name"]} do not contain any item')
            elif not isinstance(group['config']['items'], list):
                raise ValueError(
                    f'items must be a list, check {group["name"]} group items'
                )
            group_map[group['name']] = group['config']
        else:
            # provided same group name multiple times
            raise ValueError('Two menu groups can not have same name.')
    for group in preference:
        if group_map.get(group, None) is None:
            if menu.get(group):
                # same group has given multiple preference or
                # already present in menu.
                raise ValueError(
                    f'{group} group has provided multiple preferences \
                    or group with this name is already present in the menu'
                )
            else:
                raise ValueError(f'{group} is not any group name')
        menu[group] = group_map[group]
        menu[group]['items'] = get_sorted_items(menu[group]['items'], group)
        del group_map[group]
    # add remaining groups
    for group in group_map.keys():
        menu[group] = group_map[group]


def get_sorted_items(items, group='Default Group'):
    '''
    Returns a sorted ordered dic of items of a group in the order of \
    position provided to each item.
    '''
    _items = {}
    for item in items:
        if not isinstance(item, dict):
            raise ValueError(f"'{group}' contains an item which is not a dict.")
        if not isinstance(item['position'], int):
            raise ValueError(
                f"'{group}' contains an item whose position's value is not int"
            )
        if _items.get(item['position'], None) is None:
            _items[item['position']] = item['config']
        else:
            raise ValueError(
                f"Multiple items of '{group}' group have same position. It needs to be unique"
            )
    return OrderedDict(sorted(_items.items(), key=lambda x: x[0]))


def deep_merge_dicts(dict1, dict2):
    """
    returns a new dict which is the result of the merge of the two dicts,
    all elements are deepcopied to avoid modifying the original data structures
    """
    result = deepcopy(dict1)
    for key, value in dict2.items():
        if isinstance(value, dict):
            node = result.get(key, {})
            result[key] = deep_merge_dicts(node, value)
        else:
            result[key] = deepcopy(value)
    return result


def default_or_test(value, test):
    return value if not getattr(settings, 'TESTING', False) else test


def print_color(string, color_name, end='\n'):
    """
    Prints colored output on terminal from a selected range of colors.
    If color_name is not present then output won't be colored.
    """
    color_dict = {
        'white_bold': '37;1',
        'green_bold': '32;1',
        'yellow_bold': '33;1',
        'red_bold': '31;1',
        'reset': '0',
    }
    color = color_dict.get(color_name, '0')
    print(f'\033[{color}m{string}\033[0m', end=end)
