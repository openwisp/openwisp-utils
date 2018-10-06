import os
from os import path

from django.test import TestCase
# TODO: To be removed when we drop python 2.7 support
# Mock is a standard library from python3.3-pre onwards
# from unittest.mock import patch
from mock import patch
from openwisp_utils.ci import check_migration_name, initialize

MIGRATIONS_DIR = path.join(path.dirname(path.dirname(path.abspath(__file__))), 'migrations')


class TestCI(TestCase):
    _test_migration_file = '%s/0002_auto_20181001_0421.py' % MIGRATIONS_DIR

    def setUp(self):
        # Create a fake migration file with default name
        open(self._test_migration_file, 'w').close()

    def test_migration_name_pass(self):
        check_migration_name(MIGRATIONS_DIR, 2)

    def test_migration_name_fail(self):
        self.assertRaises(Exception, check_migration_name,
                          MIGRATIONS_DIR, 1)

    def test_ci_initialize_pass(self):
        options = [['checkmigrations', '--migrations-to-ignore', '2',
                    '--migration-path', MIGRATIONS_DIR],
                   ['checkmigrations', '--no-migration-name']]
        for option in options:
            with patch('argparse._sys.argv', option):
                initialize()

    def test_ci_initialize_fail(self):
        options = [
            [
                'checkmigrations', '--migrations-to-ignore', '1',
                '--migration-path', MIGRATIONS_DIR
            ],
            ['checkmigrations', '--migration-path', MIGRATIONS_DIR],
            ['checkmigrations']
        ]
        for option in options:
            with patch('argparse._sys.argv', option):
                try:
                    initialize()
                except (SystemExit, Exception):
                    pass
                else:
                    self.fail('SystemExit or Exception not raised')

    def tearDown(self):
        os.unlink(self._test_migration_file)
