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
        url = reverse('admin:{}_{}_changelist'.format(app_label, model_label))
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
