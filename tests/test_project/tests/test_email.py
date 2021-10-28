from django.core import mail
from django.test import TestCase, override_settings
from openwisp_utils.admin_theme.email import send_email


class TestEmail(TestCase):
    @override_settings(DEFAULT_FROM_EMAIL='test@openwisp.io')
    def test_from_email(self):
        send_email(
            'Test mail', 'This is a test email', ['devkapilbansal@gmail.com'],
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].from_email, 'test@openwisp.io')
        self.assertIn(
            'https://raw.githubusercontent.com/openwisp/openwisp-utils/master/'
            'openwisp_utils/static/openwisp-utils/images/openwisp-logo.png',
            mail.outbox[0].alternatives[0][0],
        )

    def test_email_action_text(self):
        send_email(
            'Test mail',
            'This is a test email',
            ['devkapilbansal@gmail.com', 'test123@openwisp.io'],
            extra_context={
                'call_to_action_text': 'Click on me',
                'call_to_action_url': 'https://openwisp.io/docs/index.html',
            },
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Click on me </a>\n', mail.outbox[0].alternatives[0][0])
        self.assertIn(
            '<a href="https://openwisp.io/docs/index.html" class="btn">',
            mail.outbox[0].alternatives[0][0],
        )
