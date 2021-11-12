from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings
from openwisp_utils.admin_theme import settings as app_settings
from openwisp_utils.admin_theme.email import send_email


class TestEmail(TestCase):
    @override_settings(DEFAULT_FROM_EMAIL='test@openwisp.io')
    def test_email(self):
        send_email(
            'Test mail',
            '',
            'This is a test email',
            ['devkapilbansal@gmail.com'],
        )
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox.pop()
        # test from email
        self.assertEqual(email.from_email, 'test@openwisp.io')
        # test image logo
        self.assertIn(
            'https://raw.githubusercontent.com/openwisp/openwisp-utils/master/'
            'openwisp_utils/static/openwisp-utils/images/openwisp-logo.png',
            email.alternatives[0][0],
        )
        # test email doesn't contain link
        self.assertNotIn('<a href', email.alternatives[0][0])

    def test_email_action_text_and_url(self):
        send_email(
            'Test mail',
            '',
            'This is a test email',
            ['devkapilbansal@gmail.com', 'test123@openwisp.io'],
            extra_context={
                'call_to_action_text': 'Click me',
                'call_to_action_url': 'https://openwisp.io/docs/index.html',
            },
        )
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox.pop()
        self.assertIn('Click me</a>\n', email.alternatives[0][0])
        self.assertIn(
            '<a href="https://openwisp.io/docs/index.html" class="btn">',
            email.alternatives[0][0],
        )

    @patch.object(app_settings, 'OPENWISP_HTML_EMAIL', False)
    def test_no_html_email(self):
        send_email(
            'Test mail',
            'This is a test email',
            'Email body in html message',
            ['devkapilbansal@gmail.com', 'test123@openwisp.io'],
        )
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox.pop()
        self.assertEqual(email.subject, 'Test mail')
        self.assertEqual(email.body, 'This is a test email')
        self.assertFalse(email.alternatives)

    def test_blank_html_body(self):
        send_email(
            'Test mail',
            'This is a test email',
            '',
            ['devkapilbansal@gmail.com', 'test123@openwisp.io'],
        )
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox.pop()
        self.assertEqual(email.subject, 'Test mail')
        self.assertEqual(email.body, 'This is a test email')
        self.assertFalse(email.alternatives)
