# TODO: remove once all openwisp modules are using admin_site
import warnings

from django.apps import registry
from django.conf import settings
from django.contrib.admin import site
from django.urls import reverse
from openwisp_utils.admin_theme.site import admin_site


def menu_items(request):
    menu = build_menu(request)
    return {
        'openwisp_menu_items': menu,
        'show_userlinks_block': getattr(
            settings,
            'OPENWISP_ADMIN_SHOW_USERLINKS_BLOCK',
            False
        )
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
        url = reverse('admin:{}_{}_changelist'.format(app_label,
                                                      model.lower()))
        label = item.get('label', model_class._meta.verbose_name_plural)
        try:
            model_admin = admin_site._registry[model_class]
        except KeyError:
            model_admin = site._registry[model_class]
            warnings.warn('default django admin.site is deprecated by OpenWISP \
                           please consider moving our to new admin_site')
        if not request or model_admin.has_module_permission(request):
            menu.append({
                'url': url,
                'label': label,
                'class': model.lower()
            })
    return menu
