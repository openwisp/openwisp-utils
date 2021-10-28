from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from . import settings as app_settings


def send_email(subject, body, recipients, extra_context={}):

    mail = EmailMultiAlternatives(
        subject=subject,
        body=strip_tags(body),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
    )
    context = dict(
        subject=subject,
        message=body,
        logo_url=app_settings.OPENWISP_EMAIL_LOGO,
        call_to_action_text='Find out more',
    )
    context.update(extra_context)

    if getattr(app_settings, 'OPENWISP_HTML_EMAIL', True):
        html_message = render_to_string(
            app_settings.OPENWISP_EMAIL_TEMPLATE, context=context,
        )
        mail.attach_alternative(html_message, 'text/html')
    mail.send()
