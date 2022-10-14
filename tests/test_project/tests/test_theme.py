from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from openwisp_utils.admin_theme import settings as app_settings
from openwisp_utils.admin_theme.context_processor import admin_theme_settings
from openwisp_utils.admin_theme.theme import (
    register_theme_js,
    register_theme_link,
    unregister_theme_js,
    unregister_theme_link,
)


class TestThemeHelpers(TestCase):
    def test_registering_unregistering_links(self):
        links = [
            {
                'href': '/static/custom-admin-theme.css',
                'rel': 'stylesheet',
                'type': 'text/css',
                'media': 'all',
            }
        ]

        with self.subTest('Test registering single link'):
            with self.assertRaises(ImproperlyConfigured) as context:
                register_theme_link(links[0])
            self.assertEqual(
                str(context.exception),
                '"openwisp_utils.admin_theme.theme.register_theme_link"'
                ' accepts "list" of links',
            )

        with self.subTest('Test registering list of links'):
            register_theme_link(links)
            admin_theme = admin_theme_settings(None)
            self.assertIn(links[0], admin_theme['OPENWISP_ADMIN_THEME_LINKS'])
            self.assertListEqual(
                admin_theme['OPENWISP_ADMIN_THEME_LINKS'],
                app_settings.OPENWISP_ADMIN_THEME_LINKS + links,
            )

        with self.subTest('Test duplicate registration of links'):
            with self.assertRaises(ImproperlyConfigured) as error:
                register_theme_link(links)
            self.assertEqual(
                str(error.exception),
                f'{links[0]["href"]} is already present in OPENWISP_ADMIN_THEME_LINKS',
            )

        with self.subTest('Test unregistering single link'):
            with self.assertRaises(ImproperlyConfigured) as context:
                unregister_theme_link(links[0])
            self.assertEqual(
                str(context.exception),
                '"openwisp_utils.admin_theme.theme.unregister_theme_link"'
                ' accepts "list" of links',
            )

        with self.subTest('Test unregistering non-existent link'):
            with self.assertRaises(ImproperlyConfigured) as context:
                unregister_theme_link(
                    [
                        {
                            'href': '/static/non-existent.css',
                            'rel': 'stylesheet',
                            'type': 'text/css',
                            'media': 'all',
                        }
                    ]
                )
            self.assertEqual(
                str(context.exception),
                '/static/non-existent.css was not added to OPENWISP_ADMIN_THEME_LINKS',
            )

        with self.subTest('Test unregistering list of link'):
            unregister_theme_link(links)
            admin_theme = admin_theme_settings(None)
            self.assertNotIn(links[0], admin_theme['OPENWISP_ADMIN_THEME_LINKS'])

    @patch('openwisp_utils.admin_theme.theme.THEME_JS', ['dummy.js'])
    def test_registering_unregistering_js(self):
        jss = ['/static/openwisp-utils/js/uuid.js']

        with self.subTest('Test registering single js'):
            with self.assertRaises(ImproperlyConfigured) as context:
                register_theme_js(jss[0])
            self.assertEqual(
                str(context.exception),
                '"openwisp_utils.admin_theme.theme.register_theme_js"'
                ' accepts "list" of JS',
            )

        with self.subTest('Test registering list of js'):
            register_theme_js(jss)
            admin_theme = admin_theme_settings(None)
            self.assertIn(jss[0], admin_theme['OPENWISP_ADMIN_THEME_JS'])
            self.assertListEqual(
                admin_theme['OPENWISP_ADMIN_THEME_JS'],
                app_settings.OPENWISP_ADMIN_THEME_JS + jss,
            )

        with self.subTest('Test duplicate registration of js'):
            with self.assertRaises(ImproperlyConfigured) as error:
                register_theme_js(jss)
            self.assertEqual(
                str(error.exception),
                f'{jss[0]} is already present in OPENWISP_ADMIN_THEME_JS',
            )

        with self.subTest('Test unregistering single js'):
            with self.assertRaises(ImproperlyConfigured) as context:
                unregister_theme_js(jss[0])
            self.assertEqual(
                str(context.exception),
                '"openwisp_utils.admin_theme.theme.unregister_theme_js"'
                ' accepts "list" of JS',
            )

        with self.subTest('Test unregistering non-existent link'):
            with self.assertRaises(ImproperlyConfigured) as context:
                unregister_theme_js(['/static/non-existent.js'])
            self.assertEqual(
                str(context.exception),
                '/static/non-existent.js was not added to OPENWISP_ADMIN_THEME_JS',
            )

        with self.subTest('Test unregistering list of js'):
            unregister_theme_js(jss)
            admin_theme = admin_theme_settings(None)
            self.assertNotIn(jss[0], admin_theme['OPENWISP_ADMIN_THEME_JS'])
