import os
from os import path
from unittest.mock import Mock, patch

from django.test import TestCase
from openwisp_utils.qa import (
    check_commit_message,
    check_migration_name,
    check_rst_files,
    read_rst_file,
)
from openwisp_utils.tests import capture_stderr, capture_stdout

MIGRATIONS_DIR = path.join(
    path.dirname(path.dirname(path.abspath(__file__))), 'migrations'
)


class TestQa(TestCase):
    _test_migration_file = '%s/0002_auto_20181001_0421.py' % MIGRATIONS_DIR
    _test_rst_file = 'TEST.rst'

    def setUp(self):
        # Create a fake migration file with default name
        open(self._test_migration_file, 'w').close()
        # Create a fake rst file
        open(self._test_rst_file, 'w').close()

    def tearDown(self):
        os.unlink(self._test_migration_file)
        os.unlink(self._test_rst_file)

    def test_qa_call_check_migration_name_pass(self):
        options = [
            'checkmigrations',
            '--migrations-to-ignore',
            '2',
            '--migration-path',
            MIGRATIONS_DIR,
            '--quiet',
        ]
        with patch('argparse._sys.argv', options):
            try:
                check_migration_name()
            except (SystemExit, Exception) as e:
                self.fail(e)

    @capture_stderr()
    def test_qa_call_check_migration_name_failure(self):
        options = [
            [
                'checkmigrations',
                '--migrations-to-ignore',
                '1',
                '--migration-path',
                MIGRATIONS_DIR,
                '--quiet',
            ],
            ['checkmigrations', '--migration-path', MIGRATIONS_DIR, '--quiet'],
            ['checkmigrations'],
        ]
        for option in options:
            with patch('argparse._sys.argv', option), self.subTest(option):
                with self.assertRaises(SystemExit):
                    check_migration_name()

    @capture_stdout()
    def test_migration_failure_message(self, captured_output):
        bad_migration = ['checkmigrations', '--migration-path', MIGRATIONS_DIR]
        with patch('argparse._sys.argv', bad_migration):
            try:
                check_migration_name()
            except (SystemExit):
                message = 'must be renamed to something more descriptive'
                self.assertIn(message, captured_output.getvalue())
            else:
                self.fail('SystemExit not raised')

    def test_qa_call_check_commit_message_pass(self):
        options = [
            ['commitcheck', '--quiet', '--message', '[qa] Minor clean up operations'],
            [
                'commitcheck',
                '--quiet',
                '--message',
                '[qa] Updated more file and fix problem #20\n\n'
                'Added more files Fixes #20',
            ],
            [
                'commitcheck',
                '--quiet',
                '--message',
                '[qa] Improved Y #2\n\nRelated to #2',
            ],
            [
                'commitcheck',
                '--quiet',
                '--message',
                '[qa] Finished task #2\n\nCloses #2\nRelated to #1',
            ],
            [
                'commitcheck',
                '--quiet',
                '--message',
                '[qa] Finished task #2\n\nRelated to #2\nCloses #1',
            ],
            [
                'commitcheck',
                '--quiet',
                '--message',
                '[qa] Finished task #2\n\nRelated to #2\nRelated to #1',
            ],
            # noqa
            [
                'commitcheck',
                '--quiet',
                '--message',
                '[qa] Improved Y #20\n\n'
                'Simulation of a special unplanned case\n\n#noqa',
            ],
            [
                'commitcheck',
                '--quiet',
                '--message',
                '[fix] Fixed extensibility of openwisp-users and added sample_users test app #377\n\n'
                'Closes #377\r\n\r\nCo-authored-by: Ajay Tripathi <ajay39in@gmail.com>',
            ],
            [
                'commitcheck',
                '--quiet',
                '--message',
                '[feature] Allow device name to be configured as not unique #443\n\n'
                'Unique device names can now be turned off.\n\nCloses #443.',
            ],
        ]
        for option in options:
            with patch('argparse._sys.argv', option), self.subTest(option):
                try:
                    check_commit_message()
                except (SystemExit, Exception) as e:
                    msg = 'Check failed:\n\n{}\n\nOutput:{}'.format(option[-1], e)
                    self.fail(msg)

    @capture_stderr()
    def test_qa_call_check_commit_message_failure(self):
        options = [
            ['commitcheck'],
            ['commitcheck', '--quiet', '--message', 'Hello World'],
            ['commitcheck', '--quiet', '--message', '[qa] hello World'],
            ['commitcheck', '--quiet', '--message', '[qa] Hello World.'],
            ['commitcheck', '--quiet', '--message', '[qa] Hello World.\nFixes #20'],
            [
                'commitcheck',
                '--quiet',
                '--message',
                '[qa] Fixed problem #20\n\nFixed problem X #20',
            ],
            [
                'commitcheck',
                '--quiet',
                '--message',
                '[qa] Finished task #2\n\nResolves problem described in #2',
            ],
            [
                'commitcheck',
                '--quiet',
                '--message',
                '[qa] Fixed problem\n\nFailure #2\nRelated to #1',
            ],
            [
                'commitcheck',
                '--quiet',
                '--message',
                '[qa] Updated file and fixed problem\n\nAdded more files. Fixes #20',
            ],
            ['commitcheck', '--quiet', '--message', '[qa] Improved Y\n\nRelated to #2'],
            [
                'commitcheck',
                '--quiet',
                '--message',
                '[qa] Improved Y #2\n\nUpdated files',
            ],
            [
                'commitcheck',
                '--quiet',
                '--message',
                '[qa] Improved Y #20\n\nRelated to #32 Fixes #30 Fix #40',
            ],
            # issue 136
            ['commitcheck', '--quiet', '--message', '[qa] Fixed issue #20'],
        ]
        for option in options:
            with patch('argparse._sys.argv', option), self.subTest(option):
                with self.assertRaises(SystemExit):
                    check_commit_message()

    @capture_stdout()
    def test_commit_failure_message(self, captured_output):
        bad_commit = [
            'commitcheck',
            '--message',
            '[qa] Updated file and fixed problem\n\nAdded more files. Fixes #20',
        ]
        with patch('argparse._sys.argv', bad_commit):
            try:
                check_commit_message()
            except (SystemExit):
                message = 'Your commit message does not follow our commit message style guidelines'
                self.assertIn(message, captured_output.getvalue())
            else:
                self.fail('SystemExit not raised')

    def test_qa_call_check_commit_message_merge(self):
        options = [
            [
                'commitcheck',
                '--quiet',
                '--message',
                'Merge pull request #17 from TheOneAboveAllTitan/issues/16\n\n'
                '[monitoring] Added migration to create ping for existing devices. #16',
            ],
            [
                'commitcheck',
                '--quiet',
                '--message',
                "Merge branch 'issue-21' into master",
            ],
        ]
        for option in options:
            with patch('argparse._sys.argv', option), self.subTest(option):
                try:
                    check_commit_message()
                except (SystemExit, Exception) as e:
                    msg = 'Check failed:\n\n{}\n\nOutput:{}'.format(option[-1], e)
                    self.fail(msg)

    def test_qa_call_check_commit_message_bump_version(self):
        options = [
            ['commitcheck', '--quiet', '--message', 'Bumped VERSION to 0.4.0'],
            ['commitcheck', '--quiet', '--message', 'Bumped VERSION to 1.4.3 beta'],
            [
                'commitcheck',
                '--quiet',
                '--message',
                'Bump style-loader from 1.3.0 to 2.0.0',
            ],
        ]
        for option in options:
            with patch('argparse._sys.argv', option), self.subTest(option):
                try:
                    check_commit_message()
                except (SystemExit, Exception) as e:
                    msg = 'Check failed:\n\n{}\n\nOutput:{}'.format(option[-1], e)
                    self.fail(msg)

    def test_qa_call_check_rst_file(self):
        try:
            read_rst_file(self._test_rst_file)
        except (SystemExit, Exception) as e:
            msg = 'Check failed:\n\nOutput:{}'.format(e)
            self.fail(msg)

    @patch('readme_renderer.rst.clean', Mock(return_value=None))
    # Here the value is mocked because the error occurs in some versions of library only
    @capture_stdout()
    def test_qa_call_check_rst_file_clean_failure(self, captured_output):
        try:
            check_rst_files()
        except ValueError:
            message = 'Output Failed'
            self.assertIn(message, captured_output.getvalue())
        except (SystemExit):
            pass
        else:
            self.fail('SystemExit not raised')

    @capture_stdout()
    def test_qa_call_check_rst_file_syntax(self):
        with open(self._test_rst_file, 'a+') as f:
            f.write('Test File \n======= \n.. code:: python')
        with self.assertRaises(SystemExit):
            check_rst_files()
