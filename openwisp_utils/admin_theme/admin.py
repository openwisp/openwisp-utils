import logging

from django.conf import settings
from django.contrib import admin, messages
from django.shortcuts import render
from django.urls import path, reverse
from django.utils.module_loading import import_string
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy
from django.utils.translation import gettext_lazy as _

from . import settings as app_settings
from .dashboard import get_dashboard_context
from .system_info import (
    get_enabled_openwisp_modules,
    get_openwisp_version,
    get_os_details,
)

logger = logging.getLogger(__name__)


class OpenwispAdminSite(admin.AdminSite):
    # <title>
    site_title = getattr(settings, 'OPENWISP_ADMIN_SITE_TITLE', 'OpenWISP Admin')
    # h1 text
    site_header = getattr(settings, 'OPENWISP_ADMIN_SITE_HEADER', 'OpenWISP')
    # text at the top of the admin index page
    index_title = gettext_lazy(
        getattr(settings, 'OPENWISP_ADMIN_INDEX_TITLE', 'Network Administration')
    )
    enable_nav_sidebar = False

    def index(self, request, extra_context=None):
        if app_settings.ADMIN_DASHBOARD_ENABLED:
            context = get_dashboard_context(request)
        else:
            context = {'dashboard_enabled': False}
        if self.is_metric_collection_installed() and request.user.is_superuser:
            from ..measurements.models import MetricCollectionConsent

            consent_obj = self.get_metric_collection_consent_obj()
            if not consent_obj.has_shown_disclaimer:
                messages.warning(
                    request,
                    mark_safe(
                        _(
                            'We collect anonymous usage metrics that helps to improve OpenWISP.'
                            ' You can opt-out from sharing these metrics from the '
                            '<a href="{url}">System Information page</a>.'
                        ).format(url=reverse('admin:ow-info'))
                    ),
                )
                # Update the field in DB after showing the message for the
                # first time.
                MetricCollectionConsent.objects.update(has_shown_disclaimer=True)
        return super().index(request, extra_context=context)

    def openwisp_info(self, request, *args, **kwargs):
        context = {
            'enabled_openwisp_modules': get_enabled_openwisp_modules(),
            'system_info': get_os_details(),
            'openwisp_version': get_openwisp_version(),
            'title': _('System Information'),
            'site_title': self.site_title,
        }

        if self.is_metric_collection_installed() and request.user.is_superuser:
            from ..measurements.admin import MetricCollectionConsentForm

            consent_obj = self.get_metric_collection_consent_obj()
            if request.POST:
                form = MetricCollectionConsentForm(request.POST, instance=consent_obj)
                form.full_clean()
                form.save()
            else:
                form = MetricCollectionConsentForm(instance=consent_obj)
            context.update(
                {
                    'metric_collection_installed': self.is_metric_collection_installed(),
                    'metric_consent_form': form,
                }
            )
        return render(request, 'admin/openwisp_info.html', context)

    def is_metric_collection_installed(self):
        return 'openwisp_utils.measurements' in getattr(settings, 'INSTALLED_APPS', [])

    def get_metric_collection_consent_obj(self):
        if not self.is_metric_collection_installed():
            return None
        from ..measurements.models import MetricCollectionConsent

        consent_obj = MetricCollectionConsent.objects.first()
        if not consent_obj:
            consent_obj = MetricCollectionConsent.objects.create()
        return consent_obj

    def get_urls(self):
        autocomplete_view = import_string(app_settings.AUTOCOMPLETE_FILTER_VIEW)
        return [
            path(
                'ow-auto-filter/',
                self.admin_view(autocomplete_view.as_view(admin_site=self)),
                name='ow-auto-filter',
            ),
            path(
                'openwisp-system-info/',
                self.admin_view(self.openwisp_info),
                name='ow-info',
            ),
        ] + super().get_urls()


def openwisp_admin(site_url=None):  # pragma: no cover
    """
    openwisp_admin function is deprecated
    """
    logger.warning(
        'WARNING! Calling openwisp_utils.admin_theme.admin.openwisp_admin() '
        'is not necessary anymore and is therefore deprecated.\nThis function '
        'will be removed in future versions of openwisp-utils and therefore '
        'it is recommended to remove any reference to it.\n'
    )
