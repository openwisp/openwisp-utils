from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


class MetricCollectionAdminSiteHelper:
    """Collection of helper methods for the OpenWISP Admin Theme

    Designed to be used in the admin_theme to show the constent info
    message and allow superusers to opt out.
    """

    @classmethod
    def is_enabled(cls):
        return 'openwisp_utils.metric_collection' in getattr(
            settings, 'INSTALLED_APPS', []
        )

    @classmethod
    def is_enabled_and_superuser(cls, user):
        return cls.is_enabled() and user.is_superuser

    @classmethod
    def show_consent_info(cls, request):
        """Consent screen logic

        Unless already shown, this method adds a message (using the Django
        Message Framework) to the request passed in as argument to inform
        the super user about the OpenWISP metric collection feature and
        the possibility to opt out.
        """
        if not cls.is_enabled_and_superuser(request.user):
            return

        consent = cls._get_consent()

        if not consent.shown_once:
            messages.warning(
                request,
                mark_safe(
                    _(
                        'We gather anonymous usage '
                        'metrics to enhance OpenWISP. '
                        'You can opt out from the '
                        '<a href="{url}">System Information page</a>.'
                    ).format(url=reverse('admin:ow-info'))
                ),
            )
            # Update the field in DB after showing the message for the
            # first time.
            consent._meta.model.objects.update(shown_once=True)

    @classmethod
    def manage_form(cls, request, context):
        if not cls.is_enabled_and_superuser(request.user):
            return

        from .admin import ConsentForm

        consent = cls._get_consent()

        if request.POST:
            form = ConsentForm(request.POST, instance=consent)
            form.full_clean()
            form.save()
        else:
            form = ConsentForm(instance=consent)

        context.update(
            {
                'metric_collection_installed': cls.is_enabled(),
                'metric_consent_form': form,
            }
        )

    @classmethod
    def _get_consent(cls):
        if not cls.is_enabled():
            return None

        from .models import Consent

        consent = Consent.objects.first()
        if not consent:
            consent = Consent.objects.create()
        return consent
