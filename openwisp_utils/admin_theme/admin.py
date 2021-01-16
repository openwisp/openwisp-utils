import copy
import logging

from django.conf import settings
from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, reverse
from django.utils.translation import ugettext_lazy
from swapper import load_model

from .schema import DASHBOARD_SCHEMA

logger = logging.getLogger(__name__)


class OpenwispAdminSite(admin.AdminSite):
    # <title>
    site_title = getattr(settings, 'OPENWISP_ADMIN_SITE_TITLE', 'OpenWISP Admin')
    # h1 text
    site_header = getattr(settings, 'OPENWISP_ADMIN_SITE_HEADER', 'OpenWISP')
    # text at the top of the admin index page
    index_title = ugettext_lazy(
        getattr(settings, 'OPENWISP_ADMIN_INDEX_TITLE', 'Network administration')
    )
    enable_nav_sidebar = False

    def login(self, *args, **kwargs):
        response = super().login(*args, **kwargs)
        if isinstance(response, HttpResponseRedirect):
            response = HttpResponseRedirect(reverse('admin:ow_dashboard'))
        return response

    def ow_dashboard(self, request, extra_context=None):
        context = {
            'is_popup': False,
            'has_permission': True,
        }
        schema = copy.deepcopy(DASHBOARD_SCHEMA)

        for key, value in schema.items():
            app_label, model_name, group_by = value['query_params'].values()
            try:
                model = load_model(app_label, model_name)
            except ImproperlyConfigured:
                raise ImproperlyConfigured(
                    f'Error adding dashboard element {key}.'
                    f'REASON: {app_label}.{model_name} could not be loaded.'
                )

            # Filter query according to organization of user
            if hasattr(model, 'organization_id') and not request.user.is_superuser:
                qs = model.objects.filter(
                    organization_id__in=request.user.organizations_managed
                )
            else:
                qs = model.objects.all()

            qs = qs.values(group_by).annotate(count=Count(group_by))

            # Organize data for representation using Plotly.js
            # Create a list of labels and values from the queryset
            # where each element in the form of
            # {group_by : '<label>', 'count': <value>}
            values = []
            labels = []
            for obj in qs:
                labels.append(obj[group_by])
                values.append(obj['count'])
            schema[key]['query_params'] = {'values': values, 'labels': labels}
            schema[key]['target_link'] = f'/admin/{app_label}/{model_name}/?{group_by}='

        context.update({'dashboard_schema': dict(schema)})
        return render(request, template_name='admin/ow_dashboard.html', context=context)

    def get_urls(self):
        url_patterns = super().get_urls()

        url_patterns += [
            path(
                'ow-dashboard', self.admin_view(self.ow_dashboard), name='ow_dashboard'
            ),
        ]

        return url_patterns


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
