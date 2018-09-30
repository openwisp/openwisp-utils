import os

from django.test import TestCase
# TODO: To be removed when we drop python 2.7 support
# Mock is a standard library from python3.3-pre onwards
# from unittest.mock import patch
from mock import patch
from openwisp_utils.ci import check_migration_name, initialize


class TestCI(TestCase):

    def setUp(self):
        # Create a fake migration file with default name
        open('./tests/test_project/migrations/0002_auto_20181001_0421.py',
             'w').close()
        self.migrations_path = os.path.abspath(
            'tests/test_project/migrations/')

    def test_migration_name_pass(self):
        check_migration_name(self.migrations_path, 2)

    def test_migration_name_fail(self):
        self.assertRaises(Exception, check_migration_name,
                          self.migrations_path, 1)

    def test_ci_initialize_pass(self):
        options = [['checkmigrations', '--migrations-to-ignore', '2',
                    '--migration-path', './tests/test_project/migrations/'],
                   ['checkmigrations', '--no-migration-name']]
        for option in options:
            with patch('argparse._sys.argv', option):
                initialize()

    def test_ci_initialize_fail(self):
        options = [['checkmigrations', '--migrations-to-ignore', '1',
                    '--migration-path', './tests/test_project/migrations/'],
                   ['checkmigrations', '--migration-path',
                    './tests/test_project/migrations/'], ['checkmigrations']]
        for option in options:
            with patch('argparse._sys.argv', option):
                self.assertRaises(Exception, initialize)

    def tearDown(self):
        os.unlink('./tests/test_project/migrations/0002_auto_20181001_0421.py')
