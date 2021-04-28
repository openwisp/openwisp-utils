import logging

from django.apps import registry
from django.conf import settings
from django.urls import reverse

from . import settings as app_settings


def menu_items(request):
    menu = build_menu(request)
    if menu:
        logging.warning(
            'Register_menu_items is deprecated. Plase update to use register_menu_group'
        )
    menu_groups = build_menu_groups(request)
    return {
        'openwisp_menu_items': menu,
        'openwisp_menu_groups': menu_groups,
        'show_userlinks_block': getattr(
            settings, 'OPENWISP_ADMIN_SHOW_USERLINKS_BLOCK', False
        ),
    }


def build_menu_groups(request):
    default_groups = getattr(settings, 'OPENWISP_DEFAULT_ADMIN_MENU_GROUPS', {})
    custom_groups = getattr(settings, 'OPENWISP_ADMIN_MENU_GROUPS', {})
    groups = default_groups
    groups.update(custom_groups)
    menu_groups = []
    for name, config in groups.items():
        items = config['items']
        _group = {}
        _items = []
        _group['name'] = name
        for _, item in items.items():
            if item.get('model', None):
                app_label, model = item['model'].split('.')
                model_class = registry.apps.get_model(app_label, model)
                model_label = model.lower()
                uuid = item['name']
                url = reverse(f'admin:{app_label}_{model_label}_{uuid}')
                label = item.get(
                    'label', model_class._meta.verbose_name_plural + ' ' + uuid
                )
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
                    _items.append(
                        {
                            'url': url,
                            'label': label,
                            'class': model_label,
                            'icon': item.get('icon', ''),
                        }
                    )
            elif item.get('link', None):
                _items.append(
                    {
                        'url': item['link'],
                        'label': item['label'],
                        'icon': item.get('icon', ''),
                    }
                )
        if _items:
            _group['icon'] = config.get('icon', '')
            _group['items'] = _items
            menu_groups.append(_group)
    return menu_groups


def build_menu(request):
    default_items = getattr(settings, 'OPENWISP_DEFAULT_ADMIN_MENU_ITEMS', [])
    custom_items = getattr(settings, 'OPENWISP_ADMIN_MENU_ITEMS', [])
    items = custom_items or default_items
    menu = []
    # loop over each item to build the menu
    # and check user has permission to see each item
    for item in items:
        app_label, model = item['model'].split('.')
        model_class = registry.apps.get_model(app_label, model)
        model_label = model.lower()
        url = reverse(f'admin:{app_label}_{model_label}_changelist')
        label = item.get('label', model_class._meta.verbose_name_plural)
        view_perm = f'{app_label}.view_{model_label}'
        change_perm = f'{app_label}.change_{model_label}'
        user = request.user
        # use cached helper from openwisp-users if available
        has_permission_method = (
            user.has_permission if hasattr(user, 'has_permission') else user.has_perm
        )
        if has_permission_method(view_perm) or has_permission_method(change_perm):
            menu.append({'url': url, 'label': label, 'class': model_label})
    return menu


def admin_theme_settings(request):
    return {
        'OPENWISP_ADMIN_THEME_LINKS': app_settings.OPENWISP_ADMIN_THEME_LINKS,
        'OPENWISP_ADMIN_THEME_JS': app_settings.OPENWISP_ADMIN_THEME_JS,
    }
