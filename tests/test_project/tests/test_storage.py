import os
import shutil

from django.conf import settings
from django.contrib.staticfiles import storage
from django.core.management import call_command
from django.test import TestCase, override_settings
from openwisp_utils.tests import capture_stdout


def create_dir(*paths: str):
    """Returns Joined path

    joins two or more pathname using os.path.join and creates leaf directory
    and all the intermidiate ones according to the joined path using os.makedirs
    """
    joined_path = os.path.join(*paths)
    os.makedirs(joined_path, exist_ok=True)
    return joined_path


@override_settings(
    STATICFILES_STORAGE='openwisp_utils.storage.CompressStaticFilesStorage',
    STATIC_ROOT=create_dir(settings.BASE_DIR, 'test_storage_dir', 'test_static_root'),
    STATICFILES_DIRS=[
        create_dir(settings.BASE_DIR, 'test_storage_dir', 'test_staticfiles_dir')
    ],
    STATICFILES_FINDERS=['django.contrib.staticfiles.finders.FileSystemFinder'],
    OPENWISP_STATICFILES_VERSIONED_EXCLUDE=['*skip_this.txt'],
)
class TestCompressStaticFilesStorage(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        static_dir = settings.STATICFILES_DIRS[0]

        file1 = os.path.join(static_dir, 'skip_this.txt')
        with open(file1, 'w') as f:
            f.write('this will not be hashed')

        file2 = os.path.join(static_dir, 'this.txt')
        with open(file2, 'w') as f:
            f.write('this will be hashed')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(os.path.join(settings.BASE_DIR, 'test_storage_dir'))

    @capture_stdout()
    def test_hashed_name(self):
        call_command('collectstatic')
        hashed_files = storage.staticfiles_storage.hashed_files
        self.assertEqual(hashed_files['skip_this.txt'], 'skip_this.txt')
        self.assertNotEqual(hashed_files['this.txt'], 'this.txt')
