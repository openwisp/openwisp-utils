import os
from os import path

from django.test import TestCase
from openwisp_utils.qa import check_commit_message, check_migration_name

# TODO: To be removed when we drop python 2.7 support
# Mock is a standard library from python3.3-pre onwards
# from unittest.mock import patch
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


MIGRATIONS_DIR = path.join(path.dirname(path.dirname(path.abspath(__file__))), 'migrations')


class TestQa(TestCase):
    _test_migration_file = '%s/0002_auto_20181001_0421.py' % MIGRATIONS_DIR

    def setUp(self):
        # Create a fake migration file with default name
        open(self._test_migration_file, 'w').close()

    def test_qa_call_check_migration_name_pass(self):
        options = [
            'checkmigrations',
            '--migrations-to-ignore', '2',
            '--migration-path', MIGRATIONS_DIR,
            '--quiet'
        ]
        with patch('argparse._sys.argv', options):
            try:
                check_migration_name()
            except (SystemExit, Exception) as e:
                self.fail(e)

    def test_qa_call_check_migration_name_failure(self):
        options = [
            [
                'checkmigrations',
                '--migrations-to-ignore', '1',
                '--migration-path', MIGRATIONS_DIR,
                '--quiet'
            ],
            [
                'checkmigrations',
                '--migration-path', MIGRATIONS_DIR,
                '--quiet'
            ],
            ['checkmigrations']
        ]
        for option in options:
            with patch('argparse._sys.argv', option):
                try:
                    check_migration_name()
                except (SystemExit, Exception):
                    pass
                else:
                    self.fail('SystemExit or Exception not raised')

    def test_qa_call_check_commit_message_pass(self):
        options = [
            [
                'commitcheck',
                '--quiet', '--message',
                "[qa] Minor clean up operations"
            ],
            [
                'commitcheck',
                '--quiet', '--message',
                "[qa] Updated more file and fix problem #20\n\n"
                "Added more files Fixes #20"
            ],
            [
                'commitcheck',
                '--quiet', '--message',
                "[qa] Improved Y #2\n\n"
                "Related to #2"
            ],
            [
                'commitcheck',
                '--quiet', '--message',
                "[qa] Finished task #2\n\n"
                "Closes #2\nRelated to #1"
            ],
            [
                'commitcheck',
                '--quiet', '--message',
                "[qa] Finished task #2\n\n"
                "Related to #2\nCloses #1"
            ],
            [
                'commitcheck',
                '--quiet', '--message',
                "[qa] Finished task #2\n\n"
                "Related to #2\nRelated to #1"
            ],
            # noqa
            [
                'commitcheck',
                '--quiet', '--message',
                "[qa] Improved Y #20\n\n"
                "Simulation of a special unplanned case\n\n#noqa"
            ]
        ]
        for option in options:
            with patch('argparse._sys.argv', option):
                try:
                    check_commit_message()
                except (SystemExit, Exception) as e:
                    msg = 'Check failed:\n\n{}' \
                          '\n\nOutput:{}'.format(option[-1], e)
                    self.fail(msg)

    def test_qa_call_check_commit_message_failure(self):
        options = [
            ['commitcheck'],
            [
                'commitcheck',
                '--quiet', '--message',
                'Hello World',
            ],
            [
                'commitcheck',
                '--quiet', '--message',
                '[qa] hello World',
            ],
            [
                'commitcheck',
                '--quiet', '--message',
                '[qa] Hello World.',
            ],
            [
                'commitcheck',
                '--quiet', '--message',
                '[qa] Hello World.\nFixes #20',
            ],
            [
                'commitcheck',
                '--quiet', '--message',
                "[qa] Fixed problem #20"
                "\n\nFixed problem X #20"
            ],
            [
                'commitcheck',
                '--quiet', '--message',
                "[qa] Finished task #2\n\n"
                "Resolves problem described in #2"
            ],
            [
                'commitcheck',
                '--quiet', '--message',
                "[qa] Fixed problem\n\n"
                "Failure #2\nRelated to #1"
            ],
            [
                'commitcheck',
                '--quiet', '--message',
                "[qa] Updated file and fixed problem\n\n"
                "Added more files. Fixes #20"
            ],
            [
                'commitcheck',
                '--quiet', '--message',
                "[qa] Improved Y\n\n"
                "Related to #2"
            ],
            [
                'commitcheck',
                '--quiet', '--message',
                "[qa] Improved Y #2\n\n"
                "Updated files"
            ],
            [
                'commitcheck',
                '--quiet', '--message',
                "[qa] Improved Y #20\n\n"
                "Related to #32 Fixes #30 Fix #40"
            ]
        ]
        for option in options:
            with patch('argparse._sys.argv', option):
                try:
                    check_commit_message()
                except (SystemExit, Exception):
                    pass
                else:
                    self.fail('SystemExit or Exception not raised')

    def tearDown(self):
        os.unlink(self._test_migration_file)
