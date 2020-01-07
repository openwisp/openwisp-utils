import logging

from django.apps import registry
from django.conf import settings
from django.contrib.admin import site
from django.urls import reverse
from openwisp_utils.admin_theme.site import admin_site

logger = logging.getLogger(__name__)


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
    log_warning = False
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
        # TODO: remove once all modules are upgraded to the new OpenWISP admin_site
        except KeyError:
            model_admin = site._registry[model_class]
            log_warning = True
        if not request or model_admin.has_module_permission(request):
            menu.append({
                'url': url,
                'label': label,
                'class': model.lower()
            })
    if log_warning:
        logger.warning(
            'The default django admin.site is deprecated in OpenWISP; please '
            'consider moving to the usage of the configurable admin_site '
            'available in openwisp_utils.admin_theme.site'
        )
    return menu
