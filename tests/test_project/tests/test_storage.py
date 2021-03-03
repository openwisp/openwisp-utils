import os
import shutil
import tempfile

from django.conf import settings
from django.contrib.staticfiles import storage
from django.core.management import call_command
from django.test import TestCase, override_settings


@override_settings(
    STATICFILES_STORAGE='openwisp_utils.storage.CompressStaticFilesStorage',
    STATIC_ROOT=os.path.join(settings.BASE_DIR, 'test_static_root'),
    STATICFILES_FINDERS=['django.contrib.staticfiles.finders.FileSystemFinder',],
    OPENWISP_STATICFILES_VERSIONED_EXCLUDE=['*skip_this.txt'],
)
class TestCompressStaticFilesStorage(TestCase):
    def setUp(self):
        temp_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(temp_dir, 'test'))

        self.file1 = os.path.join(temp_dir, 'test', 'skip_this.txt')
        with open(self.file1, 'w') as f:
            f.write('this will not be hashed')

        self.file2 = os.path.join(temp_dir, 'test', 'this.txt')
        with open(self.file2, 'w') as f:
            f.write('this will be hashed')

        self.patched_settings = self.settings(STATICFILES_DIRS=[temp_dir])
        self.patched_settings.enable()
        self.addCleanup(shutil.rmtree, temp_dir)

    def tearDown(self):
        shutil.rmtree(settings.STATIC_ROOT)

    def test_hashed_name(self):
        call_command('collectstatic')
        hashed_files = storage.staticfiles_storage.hashed_files
        self.assertEqual(hashed_files['test/skip_this.txt'], 'test/skip_this.txt')
        self.assertNotEqual(hashed_files['test/this.txt'], 'test/this.txt')
