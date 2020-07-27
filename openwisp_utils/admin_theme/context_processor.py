from django.apps import registry
from django.conf import settings
from django.urls import reverse

from . import settings as app_settings


def menu_items(request):
    menu = build_menu(request)
    return {
        'openwisp_menu_items': menu,
        'show_userlinks_block': getattr(
            settings, 'OPENWISP_ADMIN_SHOW_USERLINKS_BLOCK', False
        ),
    }


def build_menu(request=None):
    default_items = getattr(settings, 'OPENWISP_DEFAULT_ADMIN_MENU_ITEMS', [])
    custom_items = getattr(settings, 'OPENWISP_ADMIN_MENU_ITEMS', [])
    items = custom_items or default_items
    menu = []
    # loop over each item to build the menu
    # and check user has permission to see each item
    for item in items:
        app_label, model = item['model'].split('.')
        model_class = registry.apps.get_model(app_label, model)
        url = reverse('admin:{}_{}_changelist'.format(app_label, model.lower()))
        label = item.get('label', model_class._meta.verbose_name_plural)
        has_permission = False
        for perm in request.user.get_all_permissions():
            try:
                obj = perm.split('.', 1)[1].split('_')[1]
                if model.lower() == obj:
                    has_permission = True
            except IndexError:
                continue
        if not request or has_permission:
            menu.append({'url': url, 'label': label, 'class': model.lower()})
    return menu


def admin_theme_settings(request):
    return {
        'OPENWISP_ADMIN_THEME_LINKS': app_settings.OPENWISP_ADMIN_THEME_LINKS,
        'OPENWISP_ADMIN_THEME_JS': app_settings.OPENWISP_ADMIN_THEME_JS,
    }
